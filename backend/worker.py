"""Dedicated process for executing queued Playwright scans."""
import asyncio
import logging
import signal
import uuid
from datetime import datetime, timezone

from backend.core.database import close_db_connection, db
from backend.models.scheduled import Notification
from backend.services.playwright_engine import perform_accessibility_scan
from backend.services.scan_queue import claim_scan_job, complete_scan_job, fail_scan_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ScanWorker:
    def __init__(self):
        self.worker_id = str(uuid.uuid4())
        self.running = True

    async def _notify_scheduled_result(self, job: dict) -> None:
        scheduled_id = job.get("scheduled_scan_id")
        if not scheduled_id:
            return
        scan = await db.scan_requests.find_one({"id": job["scan_id"]})
        scheduled = await db.scheduled_scans.find_one({"id": scheduled_id})
        if not scan or not scheduled:
            return

        score = scan.get("score")
        await db.scheduled_scans.update_one(
            {"id": scheduled_id},
            {"$set": {"last_score": score, "updated_at": datetime.now(timezone.utc)}},
        )
        completed = scan.get("status") == "completed"
        notification = Notification(
            user_id=scheduled["user_id"],
            type="scheduled_scan_complete" if completed else "scheduled_scan_failed",
            title="Scheduled Scan Complete" if completed else "Scheduled Scan Failed",
            message=(
                f"Your scheduled scan for {scan['url']} completed with a health score of {score}/100."
                if completed
                else f"Your scheduled scan for {scan['url']} failed."
            ),
            data={"scan_id": scan["id"], "scheduled_id": scheduled_id, "url": scan["url"], "score": score},
        )
        await db.notifications.insert_one(notification.dict())

    async def run_job(self, job: dict) -> None:
        try:
            await perform_accessibility_scan(job["scan_id"], job["url"], job["tool"])
            scan = await db.scan_requests.find_one({"id": job["scan_id"]})
            if not scan or scan.get("status") != "completed":
                raise RuntimeError((scan or {}).get("error_message") or "Scan did not complete")
            await complete_scan_job(job["id"])
            await self._notify_scheduled_result(job)
        except Exception as exc:
            logger.exception("Scan job %s failed", job.get("id"))
            await fail_scan_job(job, str(exc))

    async def run(self) -> None:
        logger.info("Scan worker %s started", self.worker_id)
        while self.running:
            job = await claim_scan_job(self.worker_id)
            if not job:
                await asyncio.sleep(1)
                continue
            await self.run_job(job)

    def stop(self, *_args) -> None:
        self.running = False


async def main() -> None:
    worker = ScanWorker()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:
            pass
    try:
        await worker.run()
    finally:
        await close_db_connection()


if __name__ == "__main__":
    asyncio.run(main())
