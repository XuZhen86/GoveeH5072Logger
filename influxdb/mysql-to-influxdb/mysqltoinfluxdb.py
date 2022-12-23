# pip install absl-py aiomysql influxdb-client[async]
import asyncio
from decimal import Decimal

import aiomysql
from absl import app, flags, logging
from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

_SQL_USER = flags.DEFINE_string(name='sql_user',
                                default=None,
                                required=True,
                                help='Username to log in as.')

_SQL_PASSWORD = flags.DEFINE_string(name='sql_password',
                                    default=None,
                                    required=True,
                                    help='Password to use.')

_SQL_HOST = flags.DEFINE_string(name='sql_host',
                                default=None,
                                required=True,
                                help='Host where the database server is located.')

_SQL_PORT = flags.DEFINE_integer(name='sql_port', default=3306, help='MySQL port to use.')

_SQL_DATABASE_NAME = flags.DEFINE_string(name='sql_database_name',
                                         default=None,
                                         required=True,
                                         help='Database to use.')

_SQL_SCROLL = flags.DEFINE_integer(name='sql_scroll',
                                   default=0,
                                   required=False,
                                   help='Fast forward to this row number to resume uploading.')

_INFLUXDB_URL = flags.DEFINE_string(name='influxdb_url',
                                    default=None,
                                    required=True,
                                    help='InfluxDB server API url (ex. http://localhost:8086).')

_INFLUXDB_TOKEN = flags.DEFINE_string(name='influxdb_token',
                                      default=None,
                                      required=True,
                                      help='token to authenticate to the InfluxDB 2.x.')

_INFLUXDB_ORG = flags.DEFINE_string(name='influxdb_org',
                                    default=None,
                                    required=True,
                                    help='organization name.')

_INFLUXDB_BUCKET = flags.DEFINE_string(name='influxdb_bucket',
                                       default=None,
                                       required=True,
                                       help='specifies the destination bucket for writes.')

# The optimal batch size is 5000 lines of line protocol.
# https://docs.influxdata.com/influxdb/v2.5/write-data/best-practices/optimize-writes/#batch-writes
_INFLUXDB_BATCH_SIZE = 5000

_SQL_SELECT_ALL = '''
  SET STATEMENT max_statement_time=7200 FOR
  SELECT
    timestamp_ns,
    device_name,
    nick_name,
    temperature_c,
    humidity_percent,
    battery_percent,
    rssi,
    last_timestamp_ns
  FROM
    ThermometerRecord;
'''


async def _get_mysql_connection() -> aiomysql.Connection:
  return await aiomysql.connect(
      user=_SQL_USER.value,
      password=_SQL_PASSWORD.value,
      host=_SQL_HOST.value,
      port=_SQL_PORT.value,
      db=_SQL_DATABASE_NAME.value,
  )


async def _get_points(mysql_cursor: aiomysql.SSCursor) -> list[Point]:
  points: list[Point] = []

  while len(points) < _INFLUXDB_BATCH_SIZE and (row := await mysql_cursor.fetchone()) is not None:
    timestamp_ns: int = row[0]
    device_name: str = row[1]
    nick_name: str = row[2]
    temperature_c: Decimal = row[3]
    humidity_percent: Decimal = row[4]
    battery_percent: int = row[5]
    rssi: int = row[6]
    # last_timestamp_ns: int = row[7]

    points.extend([
        Point('temperature').tag('nick_name', nick_name).tag('device_name', device_name).field(
            'temperature_c_10x', int(temperature_c * 10)).time(timestamp_ns),
        Point('humidity').tag('nick_name', nick_name).tag('device_name', device_name).field(
            'humidity_percent_10x', int(humidity_percent * 10)).time(timestamp_ns),
        Point('battery').tag('nick_name',
                             nick_name).tag('device_name',
                                            device_name).field('battery_percent',
                                                               battery_percent).time(timestamp_ns),
        Point('signal').tag('nick_name', nick_name).tag('device_name',
                                                        device_name).field('rssi',
                                                                           rssi).time(timestamp_ns),
        # Latency will be calculated using InfluxDB Tasks.
        # Point('last_timestamp').tag('nick_name', nick_name).tag('device_name', device_name).field(
        #     'last_timestamp_ns', last_timestamp_ns).time(timestamp_ns),
    ])

  return points


async def main(_: list[str]) -> None:
  mysql_cursor: aiomysql.SSCursor
  async with await _get_mysql_connection() as mysql_connection, await mysql_connection.cursor(
      aiomysql.SSCursor
  ) as mysql_cursor, InfluxDBClientAsync(url=_INFLUXDB_URL.value,
                                         token=_INFLUXDB_TOKEN.value,
                                         org=_INFLUXDB_ORG.value) as influxdb_client:
    await influxdb_client.ping()
    influxdb_write_api = influxdb_client.write_api()

    await mysql_cursor.execute(_SQL_SELECT_ALL)
    await mysql_cursor.scroll(_SQL_SCROLL.value)

    n_rows: int = _SQL_SCROLL.value

    points: list[Point]
    while len((points := await _get_points(mysql_cursor))) > 0:
      await influxdb_write_api.write(bucket=_INFLUXDB_BUCKET.value, record=points)
      n_rows += len(points) // 4
      logging.info('n_rows = %s', n_rows)


def app_run_main():
  app.run(lambda args: asyncio.run(main(args), debug=False))


if __name__ == '__main__':
  app_run_main()
