"""Dedicated worker process for queued and scheduled accessibility scans."""
import asyncio
import logging

from backend.core.config import settings
from backend.services.scan_queue import worker_loop
from backend.services.scheduler_service import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


async def main():
    await start_scheduler()
    workers = [asyncio.create_task(worker_loop(f'worker-{index + 1}')) for index in range(max(1, settings.MAX_CONCURRENT_SCANS))]
    try:
        await asyncio.gather(*workers)
    finally:
        for task in workers:
            task.cancel()
        await stop_scheduler()


if __name__ == '__main__':
    asyncio.run(main())
