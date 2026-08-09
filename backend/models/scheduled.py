"""
Scheduled Scan and Notification Pydantic models.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class ScheduledScan(BaseModel):
    """Model for scheduled recurring scans."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    url: str
    interval_days: int = Field(ge=1, le=365, description="Interval in days between scans")
    enabled: bool = Field(default=True)
    next_run: datetime
    last_run: Optional[datetime] = None
    last_scan_id: Optional[str] = None
    last_score: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ScheduledScanCreate(BaseModel):
    """Model for creating a new scheduled scan."""
    url: HttpUrl
    interval_days: int = Field(ge=1, le=365)


class ScheduledScanUpdate(BaseModel):
    """Model for updating a scheduled scan."""
    url: Optional[HttpUrl] = None
    interval_days: Optional[int] = Field(default=None, ge=1, le=365)
    enabled: Optional[bool] = None


class Notification(BaseModel):
    """Model for in-app notifications."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str  # scheduled_scan_complete, scan_failed, etc.
    title: str
    message: str
    read: bool = False
    data: Optional[Dict[str, Any]] = None  # Extra data like scan_id, url, score
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationCreate(BaseModel):
    """Model for creating a notification."""
    user_id: str
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
