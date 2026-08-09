"""
Notifications API routes.
Handles CRUD operations for in-app notifications.
"""
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Depends

from ...core.database import db
from ...core.security import get_current_user
from ...models.user import User
from ...models.scheduled import Notification

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/notifications", response_model=List[Notification])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get notifications for the authenticated user."""
    try:
        query = {"user_id": current_user.id}
        if unread_only:
            query["read"] = False
        
        notifications = await db.notifications.find(query).sort(
            "created_at", -1
        ).to_list(limit)
        
        return [Notification(**n) for n in notifications]
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")


@router.get("/notifications/unread-count")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    """Get count of unread notifications."""
    try:
        count = await db.notifications.count_documents({
            "user_id": current_user.id,
            "read": False
        })
        return {"count": count}
    except Exception as e:
        logger.error(f"Error counting notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to count notifications")


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    try:
        result = await db.notifications.update_one(
            {"id": notification_id, "user_id": current_user.id},
            {"$set": {"read": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notification")


@router.put("/notifications/read-all")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read for the current user."""
    try:
        result = await db.notifications.update_many(
            {"user_id": current_user.id, "read": False},
            {"$set": {"read": True}}
        )
        
        return {"message": f"Marked {result.modified_count} notifications as read"}
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notifications")


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification."""
    try:
        result = await db.notifications.delete_one({
            "id": notification_id,
            "user_id": current_user.id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


@router.delete("/notifications/clear-all")
async def clear_all_notifications(current_user: User = Depends(get_current_user)):
    """Clear all notifications for the current user."""
    try:
        result = await db.notifications.delete_many({"user_id": current_user.id})
        return {"message": f"Deleted {result.deleted_count} notifications"}
    except Exception as e:
        logger.error(f"Error clearing notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear notifications")
