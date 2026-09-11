"""Scheduled scan CRUD routes."""
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ...core.database import db
from ...core.security import get_current_user
from ...models.scheduled import ScheduledScan, ScheduledScanCreate, ScheduledScanUpdate
from ...models.user import User
from ...services.entitlements import get_effective_plan, scheduled_scan_limit
from ...services.url_safety import validate_scan_url

router = APIRouter()


def _now():
    return datetime.now(timezone.utc)


async def _require_available_slot(user: User) -> None:
    if not user.email_verified:
        raise HTTPException(status_code=403, detail='Verify your email before scheduling scans.')
    limit = await scheduled_scan_limit(user)
    if limit == -1:
        return
    count = await db.scheduled_scans.count_documents({'user_id': user.id})
    if count >= limit:
        raise HTTPException(status_code=403, detail=f'Your plan allows {limit} scheduled scan(s). Upgrade to Pro for unlimited scheduled scans.')


@router.get('/scheduled-scans', response_model=List[ScheduledScan])
async def get_scheduled_scans(current_user: User = Depends(get_current_user)):
    docs = await db.scheduled_scans.find({'user_id': current_user.id}).sort('created_at', -1).to_list(100)
    return [ScheduledScan(**doc) for doc in docs]


@router.post('/scheduled-scans', response_model=ScheduledScan)
async def create_scheduled_scan(input: ScheduledScanCreate, current_user: User = Depends(get_current_user)):
    url = (await validate_scan_url(str(input.url))).rstrip('/')
    if await db.scheduled_scans.find_one({'user_id': current_user.id, 'url': url}):
        raise HTTPException(status_code=400, detail='A scheduled scan already exists for this URL.')
    await _require_available_slot(current_user)
    now = _now()
    scan = ScheduledScan(
        user_id=current_user.id,
        url=url,
        interval_days=input.interval_days,
        next_run=now + timedelta(days=input.interval_days),
        created_at=now,
        updated_at=now,
    )
    await db.scheduled_scans.insert_one(scan.model_dump())
    return scan


@router.get('/scheduled-scans/limits/info')
async def get_limits_info(current_user: User = Depends(get_current_user)):
    limit = await scheduled_scan_limit(current_user)
    count = await db.scheduled_scans.count_documents({'user_id': current_user.id})
    return {
        'plan': await get_effective_plan(current_user),
        'limit': limit,
        'used': count,
        'remaining': -1 if limit == -1 else max(0, limit - count),
        'can_create': limit == -1 or count < limit,
    }


@router.get('/scheduled-scans/{scheduled_id}', response_model=ScheduledScan)
async def get_scheduled_scan(scheduled_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.scheduled_scans.find_one({'id': scheduled_id, 'user_id': current_user.id})
    if not doc:
        raise HTTPException(status_code=404, detail='Scheduled scan not found')
    return ScheduledScan(**doc)


@router.put('/scheduled-scans/{scheduled_id}', response_model=ScheduledScan)
async def update_scheduled_scan(scheduled_id: str, update: ScheduledScanUpdate, current_user: User = Depends(get_current_user)):
    existing = await db.scheduled_scans.find_one({'id': scheduled_id, 'user_id': current_user.id})
    if not existing:
        raise HTTPException(status_code=404, detail='Scheduled scan not found')
    values = {'updated_at': _now()}
    if update.url is not None:
        values['url'] = (await validate_scan_url(str(update.url))).rstrip('/')
    if update.interval_days is not None:
        values['interval_days'] = update.interval_days
        values['next_run'] = _now() + timedelta(days=update.interval_days)
    if update.enabled is not None:
        values['enabled'] = update.enabled
        if update.enabled:
            values['next_run'] = _now() + timedelta(days=update.interval_days or existing.get('interval_days', 7))
    await db.scheduled_scans.update_one({'id': scheduled_id, 'user_id': current_user.id}, {'$set': values})
    return ScheduledScan(**(await db.scheduled_scans.find_one({'id': scheduled_id, 'user_id': current_user.id})))


@router.delete('/scheduled-scans/{scheduled_id}')
async def delete_scheduled_scan(scheduled_id: str, current_user: User = Depends(get_current_user)):
    result = await db.scheduled_scans.delete_one({'id': scheduled_id, 'user_id': current_user.id})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail='Scheduled scan not found')
    return {'message': 'Scheduled scan deleted successfully'}


@router.post('/scheduled-scans/{scheduled_id}/toggle', response_model=ScheduledScan)
async def toggle_scheduled_scan(scheduled_id: str, current_user: User = Depends(get_current_user)):
    existing = await db.scheduled_scans.find_one({'id': scheduled_id, 'user_id': current_user.id})
    if not existing:
        raise HTTPException(status_code=404, detail='Scheduled scan not found')
    enabled = not existing.get('enabled', True)
    values = {'enabled': enabled, 'updated_at': _now()}
    if enabled:
        values['next_run'] = _now() + timedelta(days=existing.get('interval_days', 7))
    await db.scheduled_scans.update_one({'id': scheduled_id, 'user_id': current_user.id}, {'$set': values})
    return ScheduledScan(**(await db.scheduled_scans.find_one({'id': scheduled_id, 'user_id': current_user.id})))
