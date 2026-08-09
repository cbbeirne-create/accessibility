"""
Scheduler Service for running scheduled scans.
This service checks for due scheduled scans and executes them.
"""
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from ..core.config import settings
from ..models.scheduled import Notification
from ..services.playwright_engine import perform_accessibility_scan

logger = logging.getLogger(__name__)


class SchedulerService:
    """Background scheduler service for running scheduled scans."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.running = False
        self.check_interval = 60  # Check every 60 seconds
    
    async def initialize(self):
        """Initialize database connection."""
        self.client = AsyncIOMotorClient(settings.MONGO_URL)
        self.db = self.client[settings.DB_NAME]
        logger.info("Scheduler service initialized")
    
    async def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
        self.running = False
        logger.info("Scheduler service closed")
    
    async def create_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: dict = None
    ):
        """Create an in-app notification for a user."""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            data=data or {}
        )
        await self.db.notifications.insert_one(notification.dict())
        logger.info(f"Created notification for user {user_id}: {title}")
    
    async def run_scheduled_scan(self, scheduled_scan: dict):
        """Execute a scheduled scan."""
        scheduled_id = scheduled_scan.get("id")
        user_id = scheduled_scan.get("user_id")
        url = scheduled_scan.get("url")
        interval_days = scheduled_scan.get("interval_days", 7)
        
        logger.info(f"Running scheduled scan {scheduled_id} for URL: {url}")
        
        try:
            # Create a new scan request
            import uuid
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
                "createdAt": now,
                "scheduled_scan_id": scheduled_id  # Track origin
            }
            
            await self.db.scan_requests.insert_one(scan_data)
            
            # Increment user scan count
            await self.db.users.update_one(
                {"id": user_id},
                {"$inc": {"scans_used_this_month": 1}}
            )
            
            # Run the actual scan
            await perform_accessibility_scan(scan_id, url, "axe-core")
            
            # Get the completed scan to extract score
            completed_scan = await self.db.scan_requests.find_one({"id": scan_id})
            score = completed_scan.get("score") if completed_scan else None
            status = completed_scan.get("status", "error") if completed_scan else "error"
            
            # Update the scheduled scan record
            next_run = now + timedelta(days=interval_days)
            await self.db.scheduled_scans.update_one(
                {"id": scheduled_id},
                {"$set": {
                    "last_run": now,
                    "last_scan_id": scan_id,
                    "last_score": score,
                    "next_run": next_run,
                    "updated_at": now
                }}
            )
            
            # Create notification
            if status == "completed":
                await self.create_notification(
                    user_id=user_id,
                    notification_type="scheduled_scan_complete",
                    title="Scheduled Scan Complete",
                    message=f"Your scheduled scan for {url} completed with a score of {score}/100.",
                    data={
                        "scan_id": scan_id,
                        "scheduled_id": scheduled_id,
                        "url": url,
                        "score": score
                    }
                )
            else:
                await self.create_notification(
                    user_id=user_id,
                    notification_type="scheduled_scan_failed",
                    title="Scheduled Scan Failed",
                    message=f"Your scheduled scan for {url} failed. Please check the URL and try again.",
                    data={
                        "scan_id": scan_id,
                        "scheduled_id": scheduled_id,
                        "url": url
                    }
                )
            
            logger.info(f"Scheduled scan {scheduled_id} completed with score {score}")
            
        except Exception as e:
            logger.error(f"Error running scheduled scan {scheduled_id}: {e}")
            
            # Update scheduled scan with error info
            now = datetime.now(timezone.utc)
            next_run = now + timedelta(days=interval_days)
            await self.db.scheduled_scans.update_one(
                {"id": scheduled_id},
                {"$set": {
                    "last_run": now,
                    "next_run": next_run,
                    "updated_at": now
                }}
            )
            
            # Notify user of failure
            await self.create_notification(
                user_id=user_id,
                notification_type="scheduled_scan_failed",
                title="Scheduled Scan Failed",
                message=f"Your scheduled scan for {url} failed due to an error.",
                data={
                    "scheduled_id": scheduled_id,
                    "url": url,
                    "error": str(e)
                }
            )
    
    async def check_and_run_due_scans(self):
        """Check for and run any due scheduled scans."""
        now = datetime.now(timezone.utc)
        
        # Find all enabled scheduled scans that are due
        due_scans = await self.db.scheduled_scans.find({
            "enabled": True,
            "next_run": {"$lte": now}
        }).to_list(100)
        
        if due_scans:
            logger.info(f"Found {len(due_scans)} scheduled scans due for execution")
        
        for scheduled_scan in due_scans:
            try:
                await self.run_scheduled_scan(scheduled_scan)
            except Exception as e:
                logger.error(f"Error processing scheduled scan {scheduled_scan.get('id')}: {e}")
    
    async def run_scheduler_loop(self):
        """Main scheduler loop that runs continuously."""
        self.running = True
        logger.info("Scheduler loop started")
        
        while self.running:
            try:
                await self.check_and_run_due_scans()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
            
            # Wait before next check
            await asyncio.sleep(self.check_interval)
        
        logger.info("Scheduler loop stopped")


# Global scheduler instance
scheduler = SchedulerService()


async def start_scheduler():
    """Start the background scheduler."""
    await scheduler.initialize()
    asyncio.create_task(scheduler.run_scheduler_loop())
    logger.info("Background scheduler started")


async def stop_scheduler():
    """Stop the background scheduler."""
    await scheduler.close()
    logger.info("Background scheduler stopped")
