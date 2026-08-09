"""
Scheduled Scans API routes.
Handles CRUD operations for scheduled recurring accessibility scans.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List

from fastapi import APIRouter, HTTPException, Depends

from ...core.database import db
from ...core.security import get_current_user
from ...models.user import User, UserPlan
from ...models.scheduled import (
    ScheduledScan, 
    ScheduledScanCreate, 
    ScheduledScanUpdate
)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_scheduled_scan_limits(plan: UserPlan) -> int:
    """Get scheduled scan limits based on user plan."""
    if plan == UserPlan.pro:
        return -1  # Unlimited
    return 1  # Free users get 1 scheduled scan


async def check_scheduled_scan_limit(user: User) -> bool:
    """Check if user can create more scheduled scans."""
    limit = get_scheduled_scan_limits(user.plan)
    if limit == -1:
        return True
    
    count = await db.scheduled_scans.count_documents({"user_id": user.id})
    return count < limit


@router.get("/scheduled-scans", response_model=List[ScheduledScan])
async def get_scheduled_scans(current_user: User = Depends(get_current_user)):
    """Get all scheduled scans for the authenticated user."""
    try:
        scheduled = await db.scheduled_scans.find(
            {"user_id": current_user.id}
        ).sort("created_at", -1).to_list(100)
        
        return [ScheduledScan(**s) for s in scheduled]
    except Exception as e:
        logger.error(f"Error fetching scheduled scans: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scheduled scans")


@router.post("/scheduled-scans", response_model=ScheduledScan)
async def create_scheduled_scan(
    input: ScheduledScanCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new scheduled scan."""
    try:
        # Check limit
        can_create = await check_scheduled_scan_limit(current_user)
        if not can_create:
            limit = get_scheduled_scan_limits(current_user.plan)
            raise HTTPException(
                status_code=403,
                detail=f"Scheduled scan limit reached. Your plan allows {limit} scheduled scan(s). Upgrade to Pro for unlimited."
            )
        
        # Check if URL already has a scheduled scan
        existing = await db.scheduled_scans.find_one({
            "user_id": current_user.id,
            "url": str(input.url).rstrip('/')
        })
        if existing:
            raise HTTPException(
                status_code=400,
                detail="A scheduled scan already exists for this URL. Edit the existing one instead."
            )
        
        # Calculate first run time (start from now + interval)
        now = datetime.now(timezone.utc)
        next_run = now + timedelta(days=input.interval_days)
        
        scheduled_scan = ScheduledScan(
            user_id=current_user.id,
            url=str(input.url).rstrip('/'),
            interval_days=input.interval_days,
            next_run=next_run,
            enabled=True,
            created_at=now,
            updated_at=now
        )
        
        await db.scheduled_scans.insert_one(scheduled_scan.dict())
        
        logger.info(f"Created scheduled scan {scheduled_scan.id} for user {current_user.id}")
        return scheduled_scan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scheduled scan: {e}")
        raise HTTPException(status_code=500, detail="Failed to create scheduled scan")


@router.get("/scheduled-scans/{scheduled_id}", response_model=ScheduledScan)
async def get_scheduled_scan(
    scheduled_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific scheduled scan."""
    try:
        scheduled = await db.scheduled_scans.find_one({
            "id": scheduled_id,
            "user_id": current_user.id
        })
        
        if not scheduled:
            raise HTTPException(status_code=404, detail="Scheduled scan not found")
        
        return ScheduledScan(**scheduled)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scheduled scan {scheduled_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scheduled scan")


@router.put("/scheduled-scans/{scheduled_id}", response_model=ScheduledScan)
async def update_scheduled_scan(
    scheduled_id: str,
    update_data: ScheduledScanUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a scheduled scan."""
    try:
        scheduled = await db.scheduled_scans.find_one({
            "id": scheduled_id,
            "user_id": current_user.id
        })
        
        if not scheduled:
            raise HTTPException(status_code=404, detail="Scheduled scan not found")
        
        update_dict = {"updated_at": datetime.now(timezone.utc)}
        
        if update_data.url is not None:
            update_dict["url"] = str(update_data.url).rstrip('/')
        
        if update_data.interval_days is not None:
            update_dict["interval_days"] = update_data.interval_days
            # Recalculate next_run based on new interval
            now = datetime.now(timezone.utc)
            update_dict["next_run"] = now + timedelta(days=update_data.interval_days)
        
        if update_data.enabled is not None:
            update_dict["enabled"] = update_data.enabled
            # If re-enabling, recalculate next_run
            if update_data.enabled:
                now = datetime.now(timezone.utc)
                interval = update_data.interval_days or scheduled.get("interval_days", 7)
                update_dict["next_run"] = now + timedelta(days=interval)
        
        await db.scheduled_scans.update_one(
            {"id": scheduled_id},
            {"$set": update_dict}
        )
        
        updated = await db.scheduled_scans.find_one({"id": scheduled_id})
        return ScheduledScan(**updated)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scheduled scan {scheduled_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update scheduled scan")


@router.delete("/scheduled-scans/{scheduled_id}")
async def delete_scheduled_scan(
    scheduled_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a scheduled scan."""
    try:
        result = await db.scheduled_scans.delete_one({
            "id": scheduled_id,
            "user_id": current_user.id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Scheduled scan not found")
        
        logger.info(f"Deleted scheduled scan {scheduled_id}")
        return {"message": "Scheduled scan deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scheduled scan {scheduled_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete scheduled scan")


@router.post("/scheduled-scans/{scheduled_id}/toggle", response_model=ScheduledScan)
async def toggle_scheduled_scan(
    scheduled_id: str,
    current_user: User = Depends(get_current_user)
):
    """Toggle a scheduled scan on/off."""
    try:
        scheduled = await db.scheduled_scans.find_one({
            "id": scheduled_id,
            "user_id": current_user.id
        })
        
        if not scheduled:
            raise HTTPException(status_code=404, detail="Scheduled scan not found")
        
        new_enabled = not scheduled.get("enabled", True)
        now = datetime.now(timezone.utc)
        
        update_dict = {
            "enabled": new_enabled,
            "updated_at": now
        }
        
        # If re-enabling, recalculate next_run
        if new_enabled:
            interval = scheduled.get("interval_days", 7)
            update_dict["next_run"] = now + timedelta(days=interval)
        
        await db.scheduled_scans.update_one(
            {"id": scheduled_id},
            {"$set": update_dict}
        )
        
        updated = await db.scheduled_scans.find_one({"id": scheduled_id})
        return ScheduledScan(**updated)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling scheduled scan {scheduled_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle scheduled scan")


@router.get("/scheduled-scans/limits/info")
async def get_scheduled_scan_limits_info(current_user: User = Depends(get_current_user)):
    """Get scheduled scan limits for the current user."""
    limit = get_scheduled_scan_limits(current_user.plan)
    count = await db.scheduled_scans.count_documents({"user_id": current_user.id})
    
    return {
        "plan": current_user.plan,
        "limit": limit,
        "used": count,
        "remaining": -1 if limit == -1 else max(0, limit - count),
        "can_create": limit == -1 or count < limit
    }
