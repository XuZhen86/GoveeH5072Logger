import asyncio
import signal

from absl import app, logging
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from line_protocol_cache.lineprotocolcache import LineProtocolCache

from govee_h5072_logger.datapoint import DataPoint
from govee_h5072_logger.thermometer import get_thermometer


def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData) -> None:
  if (device_mac := device.address) is None:
    return
  try:
    thermometer = get_thermometer(device_mac)
  except ValueError:
    return

  manufacturer_data = advertisement_data.manufacturer_data

  try:
    byte_data = list(manufacturer_data.values())[0]
  except IndexError as e:
    e.add_note(f'{list(manufacturer_data.values())=}')
    logging.exception('Error when extracting byte_data.')
    return

  rssi = advertisement_data.rssi

  try:
    points = DataPoint.build(thermometer, byte_data, rssi).to_points()
  except ValueError as e:
    e.add_note(f'{thermometer=}')
    e.add_note(f'{byte_data=}')
    e.add_note(f'{rssi=}')
    logging.exception('Error when building data point.')
    return

  LineProtocolCache.put(points)


async def main(args: list[str]) -> None:
  async with LineProtocolCache(), BleakScanner(detection_callback):
    # Signal handlers must be set in the main thread of the main interprer.
    # Asyncio should be running this in the main thread.
    stop_running = asyncio.Event()
    signal.signal(signal.SIGTERM, lambda signal_number, stack_frame: stop_running.set())

    await stop_running.wait()


def app_run_main() -> None:
  app.run(lambda args: asyncio.run(main(args), debug=True))
