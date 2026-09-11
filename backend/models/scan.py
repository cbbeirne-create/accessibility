"""Scan-related Pydantic models and enums."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, HttpUrl


class ScanStatus(str, Enum):
    pending = 'pending'
    completed = 'completed'
    error = 'error'


class ScanTool(str, Enum):
    axe_core = 'axe-core'
    wave = 'wave'
    equalweb = 'equalweb'
    accessibe = 'accessibe'


class ScanRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: HttpUrl
    status: ScanStatus = Field(default=ScanStatus.pending)
    score: Optional[int] = Field(default=None, ge=0, le=100)
    issues: Optional[Dict[str, Any]] = Field(default=None)
    tool: Optional[ScanTool] = Field(default=ScanTool.axe_core)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = Field(default=None)
    user_id: str
    organization_id: Optional[str] = Field(default=None)
    full_page_screenshot: Optional[str] = Field(default=None)
    full_page_screenshot_key: Optional[str] = Field(default=None)
    full_page_screenshot_url: Optional[str] = Field(default=None)
    evidence_screenshots: Optional[Dict[str, str]] = Field(default=None)
    evidence_screenshot_keys: Optional[Dict[str, str]] = Field(default=None)
    evidence_screenshot_urls: Optional[Dict[str, str]] = Field(default=None)
    scan_metadata: Optional[Dict[str, Any]] = Field(default=None)
    scheduled_scan_id: Optional[str] = Field(default=None)


class ScanRequestCreate(BaseModel):
    url: HttpUrl
    tool: Optional[ScanTool] = Field(default=ScanTool.axe_core)
