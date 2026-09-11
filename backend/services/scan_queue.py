"""Durable Mongo-backed queue for Playwright scan jobs."""
import uuid
from datetime import datetime, timedelta, timezone

from pymongo import ReturnDocument

from ..core.database import db


async def enqueue_scan(scan_id: str, url: str, tool: str, *, scheduled_scan_id: str | None = None) -> None:
    now = datetime.now(timezone.utc)
    await db.scan_jobs.insert_one({
        "id": str(uuid.uuid4()),
        "scan_id": scan_id,
        "url": url,
        "tool": str(tool),
        "scheduled_scan_id": scheduled_scan_id,
        "status": "queued",
        "attempts": 0,
        "available_at": now,
        "created_at": now,
        "lock_until": None,
        "locked_by": None,
    })


async def claim_scan_job(worker_id: str, lease_seconds: int = 180):
    now = datetime.now(timezone.utc)
    return await db.scan_jobs.find_one_and_update(
        {
            "available_at": {"$lte": now},
            "$or": [
                {"status": "queued"},
                {"status": "retry"},
                {"status": "processing", "lock_until": {"$lte": now}},
            ],
        },
        {
            "$set": {
                "status": "processing",
                "locked_by": worker_id,
                "lock_until": now + timedelta(seconds=lease_seconds),
                "started_at": now,
            },
            "$inc": {"attempts": 1},
        },
        sort=[("available_at", 1), ("created_at", 1)],
        return_document=ReturnDocument.AFTER,
    )


async def complete_scan_job(job_id: str) -> None:
    await db.scan_jobs.update_one(
        {"id": job_id},
        {"$set": {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc),
            "lock_until": None,
            "locked_by": None,
        }},
    )


async def fail_scan_job(job: dict, error: str, max_attempts: int = 3) -> None:
    attempts = int(job.get("attempts", 1))
    now = datetime.now(timezone.utc)
    if attempts >= max_attempts:
        update = {
            "status": "failed",
            "failed_at": now,
            "last_error": error,
            "lock_until": None,
            "locked_by": None,
        }
    else:
        update = {
            "status": "retry",
            "available_at": now + timedelta(seconds=30 * attempts),
            "last_error": error,
            "lock_until": None,
            "locked_by": None,
        }
    await db.scan_jobs.update_one({"id": job["id"]}, {"$set": update})
