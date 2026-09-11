"""Distributed-safe scheduler that enqueues due recurring scans."""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pymongo import ReturnDocument

from ..core.database import db
from ..models.scan import ScanRequest
from ..models.scheduled import Notification
from ..models.user import User
from .entitlements import reserve_scan_quota
from .scan_queue import enqueue_scan_job
from .url_safety import validate_scan_url

logger = logging.getLogger(__name__)


def _now():
    return datetime.now(timezone.utc)


class SchedulerService:
    def __init__(self):
        self.running = False
        self.task = None
        self.scheduler_id = f'scheduler-{uuid.uuid4().hex[:10]}'
        self.check_interval = 30

    async def create_notification(self, user_id: str, notification_type: str, title: str, message: str, data: dict | None = None):
        notification = Notification(user_id=user_id, type=notification_type, title=title, message=message, data=data or {})
        await db.notifications.insert_one(notification.model_dump())

    async def claim_due_scan(self):
        now = _now()
        return await db.scheduled_scans.find_one_and_update(
            {
                'enabled': True,
                'next_run': {'$lte': now},
                '$or': [{'lease_until': None}, {'lease_until': {'$exists': False}}, {'lease_until': {'$lt': now}}],
            },
            {'$set': {'lease_until': now + timedelta(minutes=5), 'lease_owner': self.scheduler_id}},
            sort=[('next_run', 1)],
            return_document=ReturnDocument.AFTER,
        )

    async def enqueue_due_scan(self, scheduled: dict):
        now = _now()
        interval = scheduled.get('interval_days', 7)
        next_run = now + timedelta(days=interval)
        user_data = await db.users.find_one({'id': scheduled['user_id'], 'is_active': {'$ne': False}})
        if not user_data:
            await db.scheduled_scans.update_one({'id': scheduled['id']}, {'$set': {'enabled': False, 'lease_until': None, 'updated_at': now}})
            return
        user = User(**user_data)
        try:
            url = await validate_scan_url(scheduled['url'])
            await reserve_scan_quota(user)
        except HTTPException as exc:
            await db.scheduled_scans.update_one({'id': scheduled['id']}, {'$set': {'next_run': next_run, 'lease_until': None, 'updated_at': now}})
            await self.create_notification(user.id, 'scheduled_scan_skipped', 'Scheduled Scan Skipped', str(exc.detail), {'scheduled_id': scheduled['id'], 'url': scheduled['url']})
            return

        scan = ScanRequest(
            url=url,
            user_id=user.id,
            organization_id=user.organization_id,
            scheduled_scan_id=scheduled['id'],
        )
        data = scan.model_dump()
        data['url'] = str(data['url'])
        try:
            await db.scan_requests.insert_one(data)
            await enqueue_scan_job(scan.id, url, 'axe-core', user.id)
        except Exception:
            await db.users.update_one({'id': user.id, 'scans_used_this_month': {'$gt': 0}}, {'$inc': {'scans_used_this_month': -1}})
            raise
        await db.scheduled_scans.update_one({'id': scheduled['id']}, {'$set': {
            'last_run': now,
            'last_scan_id': scan.id,
            'next_run': next_run,
            'lease_until': None,
            'lease_owner': None,
            'updated_at': now,
        }})

    async def tick(self):
        for _ in range(100):
            scheduled = await self.claim_due_scan()
            if not scheduled:
                break
            try:
                await self.enqueue_due_scan(scheduled)
            except Exception:
                logger.exception('Failed to enqueue scheduled scan %s', scheduled.get('id'))
                await db.scheduled_scans.update_one({'id': scheduled['id']}, {'$set': {'lease_until': None, 'lease_owner': None, 'next_run': _now() + timedelta(hours=1)}})

    async def loop(self):
        self.running = True
        while self.running:
            await self.tick()
            await asyncio.sleep(self.check_interval)

    async def start(self):
        if self.task and not self.task.done():
            return
        self.task = asyncio.create_task(self.loop())

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None


scheduler = SchedulerService()


async def start_scheduler():
    await scheduler.start()


async def stop_scheduler():
    await scheduler.stop()
