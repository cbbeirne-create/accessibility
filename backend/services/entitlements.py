"""Centralized subscription and organization entitlement rules."""
from typing import Any, Dict

from ..core.database import db
from ..models.user import User, UserPlan


PLAN_LIMITS: Dict[UserPlan, Dict[str, Any]] = {
    UserPlan.free: {
        "monthly_scans": 2,
        "scheduled_scans": 1,
        "can_export_pdf": False,
        "can_export_json": True,
        "can_view_screenshots": True,
    },
    UserPlan.pro: {
        "monthly_scans": -1,
        "scheduled_scans": -1,
        "can_export_pdf": True,
        "can_export_json": True,
        "can_view_screenshots": True,
    },
}


async def get_effective_plan(user: User) -> UserPlan:
    """Return the user's plan, inheriting an organization's owner plan when applicable."""
    if not user.organization_id:
        return user.plan

    org = await db.organizations.find_one({"id": user.organization_id})
    if not org:
        return user.plan

    owner = await db.users.find_one({"id": org.get("owner_id")})
    if not owner:
        return user.plan

    return UserPlan(owner.get("plan", UserPlan.free.value))


async def get_limits(user: User) -> Dict[str, Any]:
    return PLAN_LIMITS[await get_effective_plan(user)]


async def get_scan_scope(user: User) -> Dict[str, Any]:
    """Database scope for scan objects visible to this user.

    Personal scans created before organization_id was added may not contain the field,
    so the personal scope deliberately includes both null and missing values.
    """
    if user.organization_id:
        return {"organization_id": user.organization_id}
    return {
        "user_id": user.id,
        "$or": [
            {"organization_id": None},
            {"organization_id": {"$exists": False}},
        ],
    }


async def get_scan_by_id_for_user(scan_id: str, user: User):
    scope = await get_scan_scope(user)
    return await db.scan_requests.find_one({"id": scan_id, **scope})


async def reserve_scan_quota(user: User) -> bool:
    """Atomically reserve one monthly scan for the user."""
    limits = await get_limits(user)
    limit = limits["monthly_scans"]
    if limit == -1:
        result = await db.users.update_one({"id": user.id}, {"$inc": {"scans_used_this_month": 1}})
        return result.modified_count == 1

    result = await db.users.update_one(
        {
            "id": user.id,
            "$or": [
                {"scans_used_this_month": {"$lt": limit}},
                {"scans_used_this_month": {"$exists": False}},
            ],
        },
        {"$inc": {"scans_used_this_month": 1}},
    )
    return result.modified_count == 1


async def release_scan_quota(user_id: str) -> None:
    """Return a quota reservation when scan creation fails before execution begins."""
    await db.users.update_one(
        {"id": user_id, "scans_used_this_month": {"$gt": 0}},
        {"$inc": {"scans_used_this_month": -1}},
    )
