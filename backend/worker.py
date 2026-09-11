"""Dedicated worker process for queued and scheduled accessibility scans."""
import asyncio
import logging

from backend.services.scan_queue import worker_loop
from backend.services.scheduler_service import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


async def main():
    await start_scheduler()
    try:
        await worker_loop()
    finally:
        await stop_scheduler()


if __name__ == '__main__':
    asyncio.run(main())
