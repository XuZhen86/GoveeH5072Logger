import asyncio
import signal
from queue import Queue

from absl import app, logging

from src.bluetooth import scan_devices
from src.database import init_database, insert_records
from src.thermometer import thermometers_from_flags
from src.thermometerrecord import ThermometerRecord


async def main(_: list[str]) -> None:
  thermometers = thermometers_from_flags()
  await init_database(thermometers)

  sigterm_event = asyncio.Event()
  asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, sigterm_event.set)

  record_queue: Queue[ThermometerRecord] = Queue()
  tasks = [
      asyncio.create_task(sigterm_event.wait(), name='sigterm_event.wait()'),
      asyncio.create_task(scan_devices(record_queue, thermometers), name='scan_devices()'),
      asyncio.create_task(insert_records(record_queue, thermometers), name='insert_records()'),
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


def app_run_govee_h5072_logger():
  app.run(lambda args: asyncio.run(main(args), debug=True))


if __name__ == '__main__':
  app_run_govee_h5072_logger()
