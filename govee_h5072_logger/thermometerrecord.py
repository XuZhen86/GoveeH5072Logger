import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from absl import logging
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
            .time(self.timestamp_ns, write_precision=WritePrecision.NS),
        Point
            .measurement('humidity')
            .tag('nick_name', self.nick_name)
            .tag('device_name', self.device_name)
            .field('humidity_percent_10x', int(self.humidity_percent * 10))
            .time(self.timestamp_ns, write_precision=WritePrecision.NS),
        Point
            .measurement('battery')
            .tag('nick_name', self.nick_name)
            .tag('device_name',self.device_name)
            .field('battery_percent', self.battery_percent)
            .time(self.timestamp_ns, write_precision=WritePrecision.NS),
        Point
            .measurement('signal')
            .tag('nick_name', self.nick_name)
            .tag('device_name', self.device_name)
            .field('rssi', self.rssi)
            .time(self.timestamp_ns, write_precision=WritePrecision.NS),
    ]
    # yapf: enable

  def to_json_str(self) -> str:
    json_dict: dict[str, str | int] = {
        'timestamp_ns': self.timestamp_ns,
        'device_name': self.device_name,
        'nick_name': self.nick_name,
        'temperature_c_10x': int(self.temperature_c * 10),
        'humidity_percent_10x': int(self.humidity_percent * 10),
        'battery_percent': self.battery_percent,
        'rssi': self.rssi,
    }
    return json.dumps(json_dict, separators=(',', ':'))

  @classmethod
  def from_json_str(cls, json_str: str) -> Self | None:
    try:
      if (isinstance(json_dict := json.loads(json_str), dict)
          and isinstance(timestamp_ns := json_dict['timestamp_ns'], int)
          and isinstance(device_name := json_dict['device_name'], str)
          and isinstance(nick_name := json_dict['nick_name'], str)
          and isinstance(temperature_c_10x := json_dict['temperature_c_10x'], int)
          and isinstance(humidity_percent_10x := json_dict['humidity_percent_10x'], int)
          and isinstance(battery_percent := json_dict['battery_percent'], int)
          and isinstance(rssi := json_dict['rssi'], int)):
        return cls(
            timestamp_ns,
            device_name,
            nick_name,
            Decimal(temperature_c_10x) / 10,
            Decimal(humidity_percent_10x) / 10,
            battery_percent,
            rssi,
        )
    except:
      logging.error('Cannot convert json string "%s" to ThermometerRecord.', json_str)
      return None
