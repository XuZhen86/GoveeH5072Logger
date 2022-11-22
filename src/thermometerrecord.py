from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ThermometerRecord:
  timestamp_ns: int
  device_name: str
  nick_name: str
  temperature_c: Decimal
  humidity_percent: Decimal
  battery_percent: int
  rssi: int
  last_timestamp_ns: int | None


SQL_CREATE_TABLE = '''
  CREATE TABLE IF NOT EXISTS ThermometerRecord (
    timestamp_ns       BIGINT UNSIGNED   NOT NULL  UNIQUE,
    device_name        TINYTEXT          NOT NULL,
    nick_name          TINYTEXT          NOT NULL,
    temperature_c      DECIMAL(3, 1)     NOT NULL,
    humidity_percent   DECIMAL(3, 1)     NOT NULL,
    battery_percent    TINYINT UNSIGNED  NOT NULL,
    rssi               TINYINT           NOT NULL,
    last_timestamp_ns  BIGINT UNSIGNED   NOT NULL
  );
'''

SQL_INSERT = '''
  INSERT INTO
    ThermometerRecord (
      timestamp_ns,
      device_name,
      nick_name,
      temperature_c,
      humidity_percent,
      battery_percent,
      rssi,
      last_timestamp_ns
    )
  VALUES
    (
      %(timestamp_ns)s,
      %(device_name)s,
      %(nick_name)s,
      %(temperature_c)s,
      %(humidity_percent)s,
      %(battery_percent)s,
      %(rssi)s,
      %(last_timestamp_ns)s
    );
'''
