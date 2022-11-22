import asyncio
import time
from decimal import Decimal
from queue import Queue

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from src.thermometer import Thermometer
from src.thermometerrecord import ThermometerRecord


def detection_callback(
    device: BLEDevice,
    advertisement_data: AdvertisementData,
    record_queue: Queue[ThermometerRecord],
    thermometers: list[Thermometer],
) -> None:
  device_name: str = device.name

  nick_name = None
  for t in thermometers:
    if t.device_name == device_name:
      nick_name = t.nick_name
  if nick_name is None:
    return

  manufacturer_data = advertisement_data.manufacturer_data
  byte_data = list(manufacturer_data.values())[0]

  encoded_data = int.from_bytes(byte_data[1:4], byteorder='big')
  if encoded_data & 0x800000 != 0:
    is_negative = True
    encoded_data ^= 0x800000
  else:
    is_negative = False

  temperature_c = Decimal(encoded_data // 1000) / 10 * (-1 if is_negative else 1)
  humidity_percent = Decimal(encoded_data % 1000) / 10
  battery_percent = int.from_bytes(byte_data[4:5], byteorder='big')

  record = ThermometerRecord(
      time.time_ns(),
      device_name,
      nick_name,
      temperature_c,
      humidity_percent,
      battery_percent,
      advertisement_data.rssi,
      None,
  )
  record_queue.put(record)


async def scan_devices(record_queue: Queue[ThermometerRecord],
                       thermometers: list[Thermometer]) -> None:
  async with BleakScanner(lambda d, a: detection_callback(d, a, record_queue, thermometers)):
    # Wait until the task was cancelled.
    await asyncio.Event().wait()
