import asyncio
from dataclasses import asdict
from queue import Empty, Queue

import aiomysql
from absl import flags, logging

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
    nick_name = %(nick_name)s
  ORDER BY
    timestamp_ns DESC
  LIMIT
    1;
'''


async def _get_connection() -> aiomysql.Connection:
  return await aiomysql.connect(
      user=_SQL_USER.value,
      password=_SQL_PASSWORD.value,
      host=_SQL_HOST.value,
      port=_SQL_PORT.value,
      db=_SQL_DATABASE_NAME.value,
  )


async def init_database(thermometers: list[Thermometer]) -> None:
  cursor: aiomysql.Cursor
  async with await _get_connection() as connection, await connection.cursor() as cursor:
    await cursor.execute(thermometerrecord.SQL_CREATE_TABLE)
    await cursor.execute(thermometer.SQL_CREATE_TABLE)
    await cursor.executemany(thermometer.SQL_INSERT, [asdict(t) for t in thermometers])
    await connection.commit()


async def _get_last_timestamps(thermometers: list[Thermometer]) -> dict[str, int | None]:
  cursor: aiomysql.Cursor
  async with await _get_connection() as connection, await connection.cursor() as cursor:
    last_timestamps: dict[str, int | None] = {}

    for thermometer in thermometers:
      nick_name = thermometer.nick_name
      await cursor.execute(_SQL_SELECT_LAST_TIMESTAMP, {'nick_name': nick_name})
      result: tuple[int] | None = await cursor.fetchone()

      if result is None:
        last_timestamps[nick_name] = None
      else:
        last_timestamps[nick_name] = result[0]

    logging.debug('last_timestamps = %s', last_timestamps)
    return last_timestamps


async def insert_records(record_queue: Queue[ThermometerRecord],
                         thermometers: list[Thermometer]) -> None:
  last_timestamps = await _get_last_timestamps(thermometers)

  cursor: aiomysql.Cursor
  async with await _get_connection() as connection, await connection.cursor() as cursor:
    pending_records: list[ThermometerRecord] = []

    while True:
      try:
        record = record_queue.get(block=False)
      except Empty:
        logging.debug('len(pending_records) = %s', len(pending_records))
        logging.debug('pending_records = %s', pending_records)

        await cursor.executemany(thermometerrecord.SQL_INSERT, [asdict(r) for r in pending_records])
        await connection.commit()
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
