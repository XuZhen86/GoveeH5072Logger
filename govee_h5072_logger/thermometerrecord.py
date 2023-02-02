from dataclasses import dataclass
from decimal import Decimal

from influxdb_client import Point
from influxdb_client.domain.write_precision import WritePrecision


@dataclass
class ThermometerRecord:
  timestamp_ns: int
  device_name: str
  nick_name: str
  temperature_c: Decimal
  humidity_percent: Decimal
  battery_percent: int
  rssi: int

  def to_influxdb_points(self) -> list[Point]:
    # yapf: disable
    return [
        Point
            .measurement('temperature')
            .tag('nick_name', self.nick_name)
            .tag('device_name', self.device_name)
            .field('temperature_c_10x', int(self.temperature_c * 10))
            .time(self.timestamp_ns, write_precision=WritePrecision.NS),  # type: ignore
        Point
            .measurement('humidity')
            .tag('nick_name', self.nick_name)
            .tag('device_name', self.device_name)
            .field('humidity_percent_10x', int(self.humidity_percent * 10))
            .time(self.timestamp_ns, write_precision=WritePrecision.NS),  # type: ignore
        Point
            .measurement('battery')
            .tag('nick_name', self.nick_name)
            .tag('device_name',self.device_name)
            .field('battery_percent', self.battery_percent)
            .time(self.timestamp_ns, write_precision=WritePrecision.NS),  # type: ignore
        Point
            .measurement('signal')
            .tag('nick_name', self.nick_name)
            .tag('device_name', self.device_name)
            .field('rssi', self.rssi)
            .time(self.timestamp_ns, write_precision=WritePrecision.NS),  # type: ignore
    ]
    # yapf: enable

  def to_influxdb_line_protocols(self) -> list[str]:
    return [point.to_line_protocol() for point in self.to_influxdb_points()]
