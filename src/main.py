import asyncio
from queue import Queue

from absl import app

from src.bluetooth import scan_devices
from src.database import init_database, insert_records
from src.thermometer import thermometers_from_flags
from src.thermometerrecord import ThermometerRecord


async def main(_: list[str]) -> None:
  thermometers = thermometers_from_flags()
  await init_database(thermometers)

  record_queue: Queue[ThermometerRecord] = Queue()
  tasks = [
      asyncio.create_task(scan_devices(record_queue, thermometers)),
      asyncio.create_task(insert_records(record_queue, thermometers)),
  ]

  exception_tasks, pending_tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
  print(exception_tasks)

  for task in pending_tasks:
    task.cancel()
  await asyncio.wait(pending_tasks, return_when=asyncio.ALL_COMPLETED)


def app_run_govee_h5072_logger():
  app.run(lambda args: asyncio.run(main(args), debug=True))


if __name__ == '__main__':
  app_run_govee_h5072_logger()
