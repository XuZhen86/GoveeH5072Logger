import asyncio
from queue import Empty, Queue
from typing import NoReturn

import aiosqlite
from absl import flags, logging

from govee_h5072_logger.thermometerrecord import ThermometerRecord

_SQLITE_PATH = flags.DEFINE_string(
    name='sqlite_path',
    default='data/pending-thermometer-records.sqlite',
    help='',
)

_SQLITE_TIMEOUT_SECONDS = flags.DEFINE_float(
    name='sqlite_timeout_seconds',
    default=120.0,
    help='',
)

_SQL_CREATE_TABLE = '''
CREATE TABLE IF NOT EXISTS PendingThermometerRecords (
  record_json  TEXT  NOT NULL  UNIQUE
);
'''

_SQL_INSERT_ROW = '''
INSERT INTO PendingThermometerRecords (record_json)
VALUES (?);
'''

_SQL_SELECT_ROWS = '''
SELECT rowid, record_json
FROM PendingThermometerRecords
LIMIT 1000;
'''

_SQL_DELETE_ROW = '''
DELETE FROM PendingThermometerRecords
WHERE rowid = ?;
'''


def get_connection() -> aiosqlite.Connection:
  return aiosqlite.connect(_SQLITE_PATH.value, timeout=_SQLITE_TIMEOUT_SECONDS.value)


async def init_records() -> None:
  async with get_connection() as connection:
    await connection.execute(_SQL_CREATE_TABLE)
    await connection.commit()


async def insert_records(insert_record_queue: Queue[ThermometerRecord]) -> NoReturn:
  async with get_connection() as connection:
    while True:
      record = await _get_from_queue(insert_record_queue)
      await connection.execute(_SQL_INSERT_ROW, [record.to_json_str()])
      await connection.commit()
      insert_record_queue.task_done()


async def read_records(connection: aiosqlite.Connection) -> dict[int, ThermometerRecord]:
  async with connection.execute(_SQL_SELECT_ROWS) as cursor:
    rows = await cursor.fetchall()

  records: dict[int, ThermometerRecord] = {}

  for row in rows:
    if (isinstance(rowid := row[0], int) and isinstance(json_str := row[1], str)
        and (record := ThermometerRecord.from_json_str(json_str)) is not None):
      records[rowid] = record
    else:
      logging.error('Cannot convert row "%s" to ThermometerRecord.', row)

  return records


async def delete_records(connection: aiosqlite.Connection, rowids: list[int]) -> None:
  await connection.executemany(_SQL_DELETE_ROW, [[rowid] for rowid in rowids])
  await connection.commit()


async def _get_from_queue(record_queue: Queue[ThermometerRecord]) -> ThermometerRecord:
  while True:
    try:
      return record_queue.get(block=False)
    except Empty:
      await asyncio.sleep(1)
