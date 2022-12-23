import asyncio
import cProfile
import signal
import time
from typing import NoReturn

from absl import app, flags, logging
from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.domain.write_precision import WritePrecision

from govee_h5072_logger.sqlite import (delete_records, get_connection, init_records, read_records)
from govee_h5072_logger.thermometerrecord import ThermometerRecord

_INFLUXDB_URL = flags.DEFINE_string(
    name='influxdb_url',
    default=None,
    required=True,
    help='InfluxDB server API url (ex. http://localhost:8086).',
)

_INFLUXDB_TOKEN = flags.DEFINE_string(
    name='influxdb_token',
    default=None,
    required=True,
    help='token to authenticate to the InfluxDB 2.x.',
)

_INFLUXDB_ORG = flags.DEFINE_string(
    name='influxdb_org',
    default=None,
    required=True,
    help='organization name.',
)

_INFLUXDB_BUCKET = flags.DEFINE_string(
    name='influxdb_bucket',
    default=None,
    required=True,
    help='specifies the destination bucket for collected metrics.',
)

_INFLUXDB_BUCKET_DERIVED = flags.DEFINE_string(
    name='influxdb_bucket_derived',
    default=None,
    required=True,
    help='specifies the destination bucket for derived metrics.',
)


def cprofile_main() -> None:
  cProfile.runctx(statement='main()',
                  globals=globals(),
                  locals=locals(),
                  filename=f'profile/writerecrdstoinfluxdb.{int(time.time())}.prof')


def main() -> None:
  app.run(lambda args: asyncio.run(_write_records_to_influxdb(args), debug=True))


async def _write_records_to_influxdb(_: list[str]) -> None:
  await init_records()

  sigterm_event = asyncio.Event()
  asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, sigterm_event.set)
  tasks = [
      asyncio.create_task(sigterm_event.wait(), name='sigterm_event.wait()'),
      asyncio.create_task(_write_records(), name='write_records()'),
  ]

  try:
    completed_tasks, pending_tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
  except asyncio.CancelledError:
    # Handles SIGINT. Exiting normally instead of propagating CancelledError.
    # https://docs.python.org/3/library/asyncio-task.html#task-cancellation
    # https://docs.python.org/3/library/asyncio-runner.html#handling-keyboard-interruption
    completed_tasks = []
    pending_tasks = tasks

  logging.warn('completed_tasks = %s', completed_tasks)
  logging.info('pending_tasks = %s', pending_tasks)

  for task in pending_tasks:
    task.cancel()
  await asyncio.wait(pending_tasks, return_when=asyncio.ALL_COMPLETED)


async def _write_records() -> NoReturn:
  async with get_connection() as connection, InfluxDBClientAsync(
      url=_INFLUXDB_URL.value, token=_INFLUXDB_TOKEN.value,
      org=_INFLUXDB_ORG.value) as influxdb_client:
    await influxdb_client.ping()
    influxdb_write_api = influxdb_client.write_api()

    while True:
      records = await read_records(connection)

      points = _to_influxdb_points(list(records.values()))
      await influxdb_write_api.write(bucket=_INFLUXDB_BUCKET.value, record=points)

      derived_points = _to_influxdb_points_derived(records)
      await influxdb_write_api.write(bucket=_INFLUXDB_BUCKET_DERIVED.value, record=derived_points)

      await delete_records(connection, list(records.keys()))
      await asyncio.sleep(10)


def _to_influxdb_points(records: list[ThermometerRecord]) -> list[Point]:
  return [point for record in records for point in record.to_influxdb_points()]


def _to_influxdb_points_derived(records: dict[int, ThermometerRecord]) -> list[Point]:
  # yapf: disable
  return [
      Point
          .measurement('rowid')
          .tag('nick_name', record.nick_name)
          .tag('device_name', record.device_name)
          .field('rowid', rowid)
          .time(record.timestamp_ns, write_precision=WritePrecision.NS)
      for rowid, record in records.items()
  ]
  # yapf: enable
