import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from influxdb_client import Point

from govee_h5072_logger.model import Model
from govee_h5072_logger.thermometer import Thermometer


@dataclass(frozen=True)
class DataPoint:
  device_name: str
  nick_name: str
  model: Model

  temperature_c: Decimal
  humidity_percent: Decimal
  battery_percent: int | None
  rssi: int

  @classmethod
  def build(cls, thermometer: Thermometer, byte_data: bytes, rssi: int) -> Self:
    if thermometer.model == Model.H5072:
      temperature_c, humidity_percent, battery_percent = DataPoint._parse_h5072(byte_data)
    elif thermometer.model == Model.H5105:
      temperature_c, humidity_percent = DataPoint._parse_h5105(byte_data)
      battery_percent = None
    else:
      raise NotImplementedError(f'Data parsing is not available for model {thermometer.model}.')

    return cls(thermometer.device_name, thermometer.nick_name, thermometer.model, temperature_c, humidity_percent,
               battery_percent, rssi)

  def _point_with_common_tags(self) -> Point:
    point = Point('thermometer')
    point.tag('device_name', self.device_name)
    point.tag('nick_name', self.nick_name)
    point.tag('model', self.model.name)
    return point

  def to_points(self) -> list[Point]:
    time_ns = time.time_ns()
    points: list[Point] = []

    temperature = self._point_with_common_tags()
    temperature.tag('scale_factor', 10).tag('unit', '°C')
    temperature.field('temperature', int(self.temperature_c * 10))
    temperature.time(time_ns)  # type: ignore
    points.append(temperature)

    humidity = self._point_with_common_tags()
    humidity.tag('scale_factor', 10).tag('unit', '%RH')
    humidity.field('humidity', int(self.humidity_percent * 10))
    humidity.time(time_ns)  # type: ignore
    points.append(humidity)

    if self.battery_percent is not None:
      battery = self._point_with_common_tags()
      battery.tag('scale_factor', 1).tag('unit', '%')
      battery.field('battery', self.battery_percent)
      battery.time(time_ns)  # type: ignore
      points.append(battery)

    rssi = self._point_with_common_tags()
    rssi.tag('scale_factor', 1).tag('unit', 'dBm')
    rssi.field('rssi', self.rssi)
    rssi.time(time_ns)  # type: ignore
    points.append(rssi)

    return points

  @staticmethod
  def _parse_h5072(byte_data: bytes) -> tuple[Decimal, Decimal, int]:
    encoded_data = int.from_bytes(byte_data[1:4], byteorder='big')
    if encoded_data == 0xff_ffff:
      raise ValueError('Invalid encoded data 0xff_ffff. This might happen when humidity is at 100%.')

    is_negative = (encoded_data & 0x80_0000 != 0)
    encoded_data &= 0x7f_ffff

    temperature_c = Decimal((encoded_data // 1000) * (-1 if is_negative else 1)) / 10
    humidity_percent = Decimal(encoded_data % 1000) / 10
    battery_percent = int.from_bytes(byte_data[4:5], byteorder='big')

    return (temperature_c, humidity_percent, battery_percent)

  @staticmethod
  def _parse_h5105(byte_data: bytes) -> tuple[Decimal, Decimal]:
    encoded_data = int.from_bytes(byte_data[2:5], byteorder='big')
    if encoded_data == 0xff_ffff:
      raise ValueError('Invalid encoded data 0xff_ffff. This might happen when humidity is at 100%.')

    is_negative = (encoded_data & 0x80_0000 != 0)
    encoded_data &= 0x7f_ffff

    temperature_c = Decimal((encoded_data // 1000) * (-1 if is_negative else 1)) / 10
    humidity_percent = Decimal(encoded_data % 1000) / 10

    return (temperature_c, humidity_percent)
