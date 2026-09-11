"""Centralized plan, organization, quota, and authorization rules."""
from typing import Any, Dict

from fastapi import HTTPException
from pymongo import ReturnDocument

from ..core.database import db
from ..models.user import User, UserPlan

PLAN_LIMITS: Dict[UserPlan, Dict[str, Any]] = {
    UserPlan.free: {
        'monthly_scans': 2,
        'scheduled_scans': 1,
        'can_export_pdf': False,
        'can_export_json': True,
        'can_view_screenshots': True,
    },
    UserPlan.pro: {
        'monthly_scans': -1,
        'scheduled_scans': -1,
        'can_export_pdf': True,
        'can_export_json': True,
        'can_view_screenshots': True,
    },
}


async def get_effective_plan(user: User) -> UserPlan:
    if not user.organization_id:
        return user.plan
    org = await db.organizations.find_one({'id': user.organization_id})
    if not org:
        return user.plan
    owner = await db.users.find_one({'id': org['owner_id']})
    return UserPlan(owner.get('plan', UserPlan.free)) if owner else user.plan


async def get_limits(user: User) -> Dict[str, Any]:
    return PLAN_LIMITS[await get_effective_plan(user)]


async def scan_scope_query(user: User) -> dict:
    if user.organization_id:
        return {'organization_id': user.organization_id}
    return {'user_id': user.id, 'organization_id': None}


async def owned_scan_query(user: User, scan_id: str) -> dict:
    scope = await scan_scope_query(user)
    return {'id': scan_id, **scope}


async def get_authorized_scan(user: User, scan_id: str) -> dict:
    scan = await db.scan_requests.find_one(await owned_scan_query(user, scan_id))
    if not scan:
        raise HTTPException(status_code=404, detail='Scan not found')
    return scan


async def reserve_scan_quota(user: User) -> None:
    if not user.email_verified:
        raise HTTPException(status_code=403, detail='Verify your email before running accessibility scans.')
    limits = await get_limits(user)
    if limits['monthly_scans'] == -1:
        await db.users.update_one({'id': user.id}, {'$inc': {'scans_used_this_month': 1}})
        return
    updated = await db.users.find_one_and_update(
        {'id': user.id, 'scans_used_this_month': {'$lt': limits['monthly_scans']}},
        {'$inc': {'scans_used_this_month': 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=403, detail=f"Monthly scan limit reached ({limits['monthly_scans']}). Upgrade to Pro for unlimited scans.")


async def release_scan_quota(user_id: str) -> None:
    await db.users.update_one({'id': user_id, 'scans_used_this_month': {'$gt': 0}}, {'$inc': {'scans_used_this_month': -1}})


async def require_pdf_export(user: User) -> None:
    if not (await get_limits(user))['can_export_pdf']:
        raise HTTPException(status_code=403, detail='PDF export requires the Pro plan.')


async def scheduled_scan_limit(user: User) -> int:
    return (await get_limits(user))['scheduled_scans']
