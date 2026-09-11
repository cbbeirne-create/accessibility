"""Durable Mongo-backed scan job queue."""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from pymongo import ReturnDocument

from ..core.database import db
from ..models.scheduled import Notification
from .playwright_engine import perform_accessibility_scan

logger = logging.getLogger(__name__)
POLL_SECONDS = float(os.environ.get('SCAN_QUEUE_POLL_SECONDS', '1'))
LEASE_MINUTES = int(os.environ.get('SCAN_JOB_LEASE_MINUTES', '10'))


def _now():
    return datetime.now(timezone.utc)


async def enqueue_scan_job(scan_id: str, url: str, tool: str, user_id: str) -> str:
    existing = await db.scan_jobs.find_one({'scan_id': scan_id, 'status': {'$in': ['queued', 'running']}})
    if existing:
        return existing['id']
    job_id = str(uuid.uuid4())
    await db.scan_jobs.insert_one({
        'id': job_id,
        'scan_id': scan_id,
        'url': url,
        'tool': str(tool),
        'user_id': user_id,
        'status': 'queued',
        'created_at': _now(),
        'attempts': 0,
        'locked_until': None,
        'worker_id': None,
        'last_error': None,
    })
    return job_id


async def claim_next_job(worker_id: str) -> Optional[dict]:
    now = _now()
    return await db.scan_jobs.find_one_and_update(
        {'$or': [
            {'status': 'queued'},
            {'status': 'running', 'locked_until': {'$lt': now}},
        ]},
        {'$set': {
            'status': 'running',
            'worker_id': worker_id,
            'locked_until': now + timedelta(minutes=LEASE_MINUTES),
            'started_at': now,
        }, '$inc': {'attempts': 1}},
        sort=[('created_at', 1)],
        return_document=ReturnDocument.AFTER,
    )


async def _notify_scheduled_completion(scan: dict, success: bool) -> None:
    scheduled_id = scan.get('scheduled_scan_id')
    if not scheduled_id:
        return
    score = scan.get('score')
    await db.scheduled_scans.update_one({'id': scheduled_id}, {'$set': {
        'last_score': score,
        'updated_at': _now(),
    }})
    notification = Notification(
        user_id=scan['user_id'],
        type='scheduled_scan_complete' if success else 'scheduled_scan_failed',
        title='Scheduled Scan Complete' if success else 'Scheduled Scan Failed',
        message=(
            f"Your scheduled scan for {scan.get('url')} completed with an Auditly health score of {score}/100."
            if success else
            f"Your scheduled scan for {scan.get('url')} failed."
        ),
        data={'scan_id': scan['id'], 'scheduled_id': scheduled_id, 'url': scan.get('url'), 'score': score},
    )
    await db.notifications.insert_one(notification.model_dump())


async def process_job(job: dict) -> None:
    try:
        result = await perform_accessibility_scan(job['scan_id'], job['url'], job['tool'])
        if not result or not result.get('success'):
            raise RuntimeError((result or {}).get('error', 'Scanner returned an unsuccessful result'))
        await db.scan_jobs.update_one({'id': job['id']}, {'$set': {
            'status': 'completed',
            'completed_at': _now(),
            'locked_until': None,
            'last_error': None,
        }})
        scan = await db.scan_requests.find_one({'id': job['scan_id']})
        if scan:
            await _notify_scheduled_completion(scan, True)
    except Exception as exc:
        logger.exception('Scan job %s failed', job.get('id'))
        attempts = int(job.get('attempts', 1))
        retry = attempts < 3
        await db.scan_jobs.update_one({'id': job['id']}, {'$set': {
            'status': 'queued' if retry else 'failed',
            'locked_until': None,
            'last_error': str(exc),
            'failed_at': _now() if not retry else None,
        }})
        if not retry:
            await db.scan_requests.update_one({'id': job['scan_id']}, {'$set': {
                'status': 'error',
                'error_message': 'Scan failed after multiple attempts.',
            }})
            scan = await db.scan_requests.find_one({'id': job['scan_id']})
            if scan:
                await _notify_scheduled_completion(scan, False)


async def worker_loop(worker_id: Optional[str] = None) -> None:
    worker_id = worker_id or f"{os.uname().nodename}-{uuid.uuid4().hex[:8]}"
    logger.info('Scan queue worker started: %s', worker_id)
    while True:
        job = await claim_next_job(worker_id)
        if not job:
            await asyncio.sleep(POLL_SECONDS)
            continue
        await process_job(job)
