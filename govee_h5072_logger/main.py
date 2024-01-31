import asyncio
from threading import Event

from absl import app, logging
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from line_protocol_cache.lineprotocolcache import LineProtocolCache

from govee_h5072_logger.datapoint import DataPoint
from govee_h5072_logger.thermometer import get_thermometer


def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData) -> None:
  if (device_name := device.name) is None:
    return
  try:
    thermometer = get_thermometer(device_name)
  except ValueError:
    return

  manufacturer_data = advertisement_data.manufacturer_data
  byte_data = list(manufacturer_data.values())[0]
  rssi = advertisement_data.rssi

  try:
    points = DataPoint.build(thermometer, byte_data, rssi).to_points()
  except ValueError as e:
    logging.warning(repr(e))
    return

  LineProtocolCache.put(points)


async def main(args: list[str]) -> None:
  async with LineProtocolCache(), BleakScanner(detection_callback):
    Event().wait()  # Sleep forever.


def app_run_main() -> None:
  app.run(lambda args: asyncio.run(main(args), debug=True))
