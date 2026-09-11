"""Scheduled recurring accessibility scan API routes."""
import logging
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ...core.database import db
from ...core.security import get_current_user
from ...models.scheduled import ScheduledScan, ScheduledScanCreate, ScheduledScanUpdate
from ...models.user import User
from ...services.entitlements import get_effective_plan, get_limits
from ...services.url_security import UnsafeScanTarget, validate_scan_url

router = APIRouter()
logger = logging.getLogger(__name__)


async def _check_limit(user: User) -> bool:
    limits = await get_limits(user)
    limit = limits["scheduled_scans"]
    if limit == -1:
        return True
    count = await db.scheduled_scans.count_documents({"user_id": user.id})
    return count < limit


async def _validate_url(url: str) -> None:
    try:
        await validate_scan_url(url)
    except UnsafeScanTarget as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/scheduled-scans", response_model=List[ScheduledScan])
async def get_scheduled_scans(current_user: User = Depends(get_current_user)):
    rows = await db.scheduled_scans.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
    return [ScheduledScan(**row) for row in rows]


@router.post("/scheduled-scans", response_model=ScheduledScan)
async def create_scheduled_scan(input: ScheduledScanCreate, current_user: User = Depends(get_current_user)):
    if not current_user.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email address before scheduling scans")

    normalized_url = str(input.url).rstrip("/")
    await _validate_url(normalized_url)

    existing = await db.scheduled_scans.find_one({"user_id": current_user.id, "url": normalized_url})
    if existing:
        raise HTTPException(status_code=400, detail="A scheduled scan already exists for this URL")
    if not await _check_limit(current_user):
        raise HTTPException(status_code=403, detail="Scheduled scan limit reached for your effective plan")

    now = datetime.now(timezone.utc)
    scheduled_scan = ScheduledScan(
        user_id=current_user.id,
        url=normalized_url,
        interval_days=input.interval_days,
        next_run=now + timedelta(days=input.interval_days),
        enabled=True,
        created_at=now,
        updated_at=now,
    )
    await db.scheduled_scans.insert_one(scheduled_scan.dict())
    return scheduled_scan


@router.get("/scheduled-scans/{scheduled_id}", response_model=ScheduledScan)
async def get_scheduled_scan(scheduled_id: str, current_user: User = Depends(get_current_user)):
    row = await db.scheduled_scans.find_one({"id": scheduled_id, "user_id": current_user.id})
    if not row:
        raise HTTPException(status_code=404, detail="Scheduled scan not found")
    return ScheduledScan(**row)


@router.put("/scheduled-scans/{scheduled_id}", response_model=ScheduledScan)
async def update_scheduled_scan(
    scheduled_id: str,
    update_data: ScheduledScanUpdate,
    current_user: User = Depends(get_current_user),
):
    scheduled = await db.scheduled_scans.find_one({"id": scheduled_id, "user_id": current_user.id})
    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled scan not found")

    update_dict = {"updated_at": datetime.now(timezone.utc)}
    if update_data.url is not None:
        normalized_url = str(update_data.url).rstrip("/")
        await _validate_url(normalized_url)
        update_dict["url"] = normalized_url
    if update_data.interval_days is not None:
        update_dict["interval_days"] = update_data.interval_days
        update_dict["next_run"] = datetime.now(timezone.utc) + timedelta(days=update_data.interval_days)
    if update_data.enabled is not None:
        update_dict["enabled"] = update_data.enabled
        if update_data.enabled:
            interval = update_data.interval_days or scheduled.get("interval_days", 7)
            update_dict["next_run"] = datetime.now(timezone.utc) + timedelta(days=interval)

    await db.scheduled_scans.update_one(
        {"id": scheduled_id, "user_id": current_user.id}, {"$set": update_dict}
    )
    updated = await db.scheduled_scans.find_one({"id": scheduled_id, "user_id": current_user.id})
    return ScheduledScan(**updated)


@router.delete("/scheduled-scans/{scheduled_id}")
async def delete_scheduled_scan(scheduled_id: str, current_user: User = Depends(get_current_user)):
    result = await db.scheduled_scans.delete_one({"id": scheduled_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scheduled scan not found")
    return {"message": "Scheduled scan deleted successfully"}


@router.post("/scheduled-scans/{scheduled_id}/toggle", response_model=ScheduledScan)
async def toggle_scheduled_scan(scheduled_id: str, current_user: User = Depends(get_current_user)):
    scheduled = await db.scheduled_scans.find_one({"id": scheduled_id, "user_id": current_user.id})
    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled scan not found")

    new_enabled = not scheduled.get("enabled", True)
    update = {"enabled": new_enabled, "updated_at": datetime.now(timezone.utc)}
    if new_enabled:
        if not current_user.email_verified:
            raise HTTPException(status_code=403, detail="Verify your email address before scheduling scans")
        await _validate_url(scheduled["url"])
        update["next_run"] = datetime.now(timezone.utc) + timedelta(days=scheduled.get("interval_days", 7))

    await db.scheduled_scans.update_one(
        {"id": scheduled_id, "user_id": current_user.id}, {"$set": update}
    )
    updated = await db.scheduled_scans.find_one({"id": scheduled_id, "user_id": current_user.id})
    return ScheduledScan(**updated)


@router.get("/scheduled-scans/limits/info")
async def get_scheduled_scan_limits_info(current_user: User = Depends(get_current_user)):
    limits = await get_limits(current_user)
    plan = await get_effective_plan(current_user)
    limit = limits["scheduled_scans"]
    count = await db.scheduled_scans.count_documents({"user_id": current_user.id})
    return {
        "plan": plan,
        "limit": limit,
        "used": count,
        "remaining": -1 if limit == -1 else max(0, limit - count),
        "can_create": limit == -1 or count < limit,
    }
