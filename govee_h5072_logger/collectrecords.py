import asyncio
import signal
import time
from decimal import Decimal
from queue import Empty, Queue

from absl import app, logging
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from line_protocol_cache.asyncproducer import AsyncLineProtocolCacheProducer

from govee_h5072_logger.thermometer import Thermometer, thermometers_from_flags
from govee_h5072_logger.thermometerrecord import ThermometerRecord


def main() -> None:
  app.run(lambda args: asyncio.run(_collect_records(args), debug=True))


async def _collect_records(_: list[str]) -> None:
  thermometers = thermometers_from_flags()

  sigterm_event = asyncio.Event()
  asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, sigterm_event.set)
  tasks = [
      asyncio.create_task(sigterm_event.wait(), name='sigterm_event.wait()'),
      asyncio.create_task(_produce_line_protocols(thermometers), name='produce_line_protocols()'),
  ]

  try:
    completed_tasks, pending_tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
  except asyncio.CancelledError:
    # Handles SIGINT. Exiting normally instead of propagating CancelledError.
    # https://docs.python.org/3/library/asyncio-task.html#task-cancellation
    # https://docs.python.org/3/library/asyncio-runner.html#handling-keyboard-interruption
    completed_tasks = []
    pending_tasks = tasks

  logging.warn('completed_tasks = %s', completed_tasks)
  logging.info('pending_tasks = %s', pending_tasks)

  for task in pending_tasks:
    task.cancel()
  await asyncio.wait(pending_tasks, return_when=asyncio.ALL_COMPLETED)


async def _produce_line_protocols(thermometers: dict[str, Thermometer]) -> None:
  record_queue: Queue[ThermometerRecord] = Queue()

  async with AsyncLineProtocolCacheProducer() as producer, BleakScanner(
      lambda d, a: _detection_callback(d, a, record_queue, thermometers)):
    line_protocols: list[str] = []
    while True:
      try:
        line_protocols += record_queue.get(block=False).to_influxdb_line_protocols()
      except Empty:
        await producer.put(line_protocols)
        line_protocols.clear()
        await asyncio.sleep(2)
        continue


def _detection_callback(
    device: BLEDevice,
    advertisement_data: AdvertisementData,
    record_queue: Queue[ThermometerRecord],
    thermometers: dict[str, Thermometer],
) -> None:
  if (not isinstance(device_name := device.name, str)
      or (thermometer := thermometers.get(device_name)) is None):
    return

  logging.debug('advertisement_data = %s', advertisement_data)
  manufacturer_data = advertisement_data.manufacturer_data
  byte_data = list(manufacturer_data.values())[0]

  encoded_data = int.from_bytes(byte_data[1:4], byteorder='big')
  if encoded_data & 0x800000 != 0:
    is_negative = True
    encoded_data ^= 0x800000
  else:
    is_negative = False

  record_queue.put(
      ThermometerRecord(
          timestamp_ns=time.time_ns(),
          device_name=thermometer.device_name,
          nick_name=thermometer.nick_name,
          temperature_c=Decimal(encoded_data // 1000) / 10 * (-1 if is_negative else 1),
          humidity_percent=Decimal(encoded_data % 1000) / 10,
          battery_percent=int.from_bytes(byte_data[4:5], byteorder='big'),
          rssi=advertisement_data.rssi,
      ))
