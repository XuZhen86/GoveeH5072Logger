import asyncio
from dataclasses import asdict
from queue import Empty, Queue

from absl import flags
from pymysql import connect
from pymysql.connections import Connection
from pymysql.cursors import Cursor

import src.thermometer as thermometer
import src.thermometerrecord as thermometerrecord
from src.thermometer import Thermometer
from src.thermometerrecord import ThermometerRecord

_SQL_USER = flags.DEFINE_string(
    name='sql_user',
    default=None,
    required=True,
    help='Username to log in as.',
)

_SQL_PASSWORD = flags.DEFINE_string(
    name='sql_password',
    default=None,
    required=True,
    help='Password to use.',
)

_SQL_HOST = flags.DEFINE_string(
    name='sql_host',
    default=None,
    required=True,
    help='Host where the database server is located.',
)

_SQL_PORT = flags.DEFINE_integer(
    name='sql_port',
    default=3306,
    help='MySQL port to use.',
)

_SQL_DATABASE_NAME = flags.DEFINE_string(
    name='sql_database_name',
    default=None,
    required=True,
    help='Database to use.',
)

_SQL_SELECT_LAST_TIMESTAMP = '''
  SELECT
    timestamp_ns
  FROM
    ThermometerRecord
  WHERE
    nick_name = %s
  ORDER BY
    timestamp_ns DESC
  LIMIT
    1;
'''


def get_connection(use_database: str | None = None) -> Connection:
  return connect(
      user=_SQL_USER.value,
      password=_SQL_PASSWORD.value,
      host=_SQL_HOST.value,
      port=_SQL_PORT.value,
      database=use_database,
  )


def init_database(thermometers: list[Thermometer]) -> None:
  with get_connection(_SQL_DATABASE_NAME.value) as connection, connection.cursor(Cursor) as cursor:
    cursor.execute(thermometerrecord.SQL_CREATE_TABLE)
    cursor.execute(thermometer.SQL_CREATE_TABLE)
    cursor.executemany(thermometer.SQL_INSERT, [asdict(t) for t in thermometers])
    connection.commit()


def _get_last_timestamps(thermometers: list[Thermometer]) -> dict[str, int | None]:
  with get_connection(_SQL_DATABASE_NAME.value) as connection, connection.cursor(Cursor) as cursor:
    last_timestamps: dict[str, int | None] = {}

    for thermometer in thermometers:
      nick_name = thermometer.nick_name
      cursor.execute(_SQL_SELECT_LAST_TIMESTAMP, (nick_name,))
      result: tuple[int] | None = cursor.fetchone()

      if result is None:
        last_timestamps[nick_name] = None
      else:
        last_timestamps[nick_name] = result[0]

    return last_timestamps


async def insert_records(record_queue: Queue[ThermometerRecord],
                         thermometers: list[Thermometer]) -> None:
  last_timestamps = _get_last_timestamps(thermometers)

  with get_connection(_SQL_DATABASE_NAME.value) as connection, connection.cursor(Cursor) as cursor:
    pending_records: list[ThermometerRecord] = []

    while True:
      try:
        record = record_queue.get(block=False)
      except Empty:
        cursor.executemany(thermometerrecord.SQL_INSERT, [asdict(r) for r in pending_records])
        connection.commit()
        pending_records.clear()

        await asyncio.sleep(10)
        continue

      last_timestamp_ns = last_timestamps[record.nick_name]
      if last_timestamp_ns is None:
        record.last_timestamp_ns = record.timestamp_ns
      else:
        record.last_timestamp_ns = last_timestamp_ns
      last_timestamps[record.nick_name] = record.timestamp_ns

      pending_records.append(record)
      record_queue.task_done()
