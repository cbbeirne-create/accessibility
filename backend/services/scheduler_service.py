"""Distributed-safe scheduler for recurring accessibility scans."""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

from ..core.config import settings
from ..models.scheduled import Notification
from ..models.user import User
from .entitlements import reserve_scan_quota
from .playwright_engine import perform_accessibility_scan
from .url_security import UnsafeScanTarget, validate_scan_url

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.check_interval = 60
        self.lease_duration = timedelta(minutes=5)
        self.worker_id = str(uuid.uuid4())

    async def initialize(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URL)
        self.db = self.client[settings.DB_NAME]

    async def close(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        if self.client:
            self.client.close()
            self.client = None

    async def create_notification(self, user_id: str, notification_type: str, title: str, message: str, data=None):
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=data or {},
        )
        await self.db.notifications.insert_one(notification.dict())

    async def _advance_schedule(self, scheduled_scan: dict, *, last_scan_id=None, last_score=None) -> None:
        now = datetime.now(timezone.utc)
        update = {
            "last_run": now,
            "next_run": now + timedelta(days=scheduled_scan.get("interval_days", 7)),
            "updated_at": now,
            "lock_until": None,
            "locked_by": None,
        }
        if last_scan_id:
            update["last_scan_id"] = last_scan_id
        if last_score is not None:
            update["last_score"] = last_score
        await self.db.scheduled_scans.update_one({"id": scheduled_scan["id"]}, {"$set": update})

    async def run_scheduled_scan(self, scheduled_scan: dict):
        user_id = scheduled_scan["user_id"]
        url = scheduled_scan["url"]
        user_doc = await self.db.users.find_one({"id": user_id, "is_active": True})
        if not user_doc:
            await self._advance_schedule(scheduled_scan)
            return

        user = User(**user_doc)
        if not user.email_verified:
            await self.create_notification(
                user_id, "scheduled_scan_skipped", "Scheduled Scan Skipped",
                "Verify your email address before scheduled scans can run.", {"scheduled_id": scheduled_scan["id"]},
            )
            await self._advance_schedule(scheduled_scan)
            return

        try:
            await validate_scan_url(url)
        except UnsafeScanTarget as exc:
            await self.create_notification(
                user_id, "scheduled_scan_failed", "Scheduled Scan Blocked",
                f"The scheduled target is no longer permitted: {exc}", {"scheduled_id": scheduled_scan["id"], "url": url},
            )
            await self._advance_schedule(scheduled_scan)
            return

        if not await reserve_scan_quota(user):
            await self.create_notification(
                user_id, "scheduled_scan_skipped", "Scheduled Scan Skipped",
                "Your monthly scan allowance has been reached.", {"scheduled_id": scheduled_scan["id"], "url": url},
            )
            await self._advance_schedule(scheduled_scan)
            return

        scan_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        scan_data = {
            "id": scan_id,
            "url": url,
            "status": "pending",
            "score": None,
            "issues": None,
            "tool": "axe-core",
            "user_id": user_id,
            "organization_id": user.organization_id,
            "createdAt": now,
            "scheduled_scan_id": scheduled_scan["id"],
        }
        try:
            await self.db.scan_requests.insert_one(scan_data)
            await perform_accessibility_scan(scan_id, url, "axe-core")
            completed = await self.db.scan_requests.find_one({"id": scan_id})
            status = completed.get("status", "error") if completed else "error"
            score = completed.get("score") if completed else None
            await self._advance_schedule(scheduled_scan, last_scan_id=scan_id, last_score=score)

            if status == "completed":
                await self.create_notification(
                    user_id, "scheduled_scan_complete", "Scheduled Scan Complete",
                    f"Your scheduled scan for {url} completed with a health score of {score}/100.",
                    {"scan_id": scan_id, "scheduled_id": scheduled_scan["id"], "url": url, "score": score},
                )
            else:
                await self.create_notification(
                    user_id, "scheduled_scan_failed", "Scheduled Scan Failed",
                    f"Your scheduled scan for {url} failed.",
                    {"scan_id": scan_id, "scheduled_id": scheduled_scan["id"], "url": url},
                )
        except Exception as exc:
            logger.exception("Error running scheduled scan %s", scheduled_scan["id"])
            await self._advance_schedule(scheduled_scan)
            await self.create_notification(
                user_id, "scheduled_scan_failed", "Scheduled Scan Failed",
                "Your scheduled scan failed due to an internal error.",
                {"scheduled_id": scheduled_scan["id"], "url": url},
            )

    async def claim_due_scan(self):
        now = datetime.now(timezone.utc)
        return await self.db.scheduled_scans.find_one_and_update(
            {
                "enabled": True,
                "next_run": {"$lte": now},
                "$or": [
                    {"lock_until": None},
                    {"lock_until": {"$exists": False}},
                    {"lock_until": {"$lte": now}},
                ],
            },
            {"$set": {"lock_until": now + self.lease_duration, "locked_by": self.worker_id}},
            sort=[("next_run", 1)],
            return_document=ReturnDocument.AFTER,
        )

    async def check_and_run_due_scans(self):
        for _ in range(100):
            scheduled_scan = await self.claim_due_scan()
            if not scheduled_scan:
                return
            await self.run_scheduled_scan(scheduled_scan)

    async def run_scheduler_loop(self):
        self.running = True
        while self.running:
            try:
                await self.check_and_run_due_scans()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Error in scheduler loop")
            await asyncio.sleep(self.check_interval)


scheduler = SchedulerService()


async def start_scheduler():
    await scheduler.initialize()
    if not scheduler.task or scheduler.task.done():
        scheduler.task = asyncio.create_task(scheduler.run_scheduler_loop())


async def stop_scheduler():
    await scheduler.close()
