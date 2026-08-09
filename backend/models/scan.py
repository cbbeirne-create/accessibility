"""
Scan-related Pydantic models and enums.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class ScanStatus(str, Enum):
    """Scan request status states."""
    pending = "pending"
    completed = "completed"
    error = "error"


class ScanTool(str, Enum):
    """Available accessibility scanning tools."""
    axe_core = "axe-core"
    wave = "wave"
    equalweb = "equalweb"
    accessibe = "accessibe"


class ScanRequest(BaseModel):
    """Complete scan request model for database storage."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: HttpUrl
    status: ScanStatus = Field(default=ScanStatus.pending)
    score: Optional[int] = Field(default=None, ge=0, le=100)
    issues: Optional[Dict[str, Any]] = Field(default=None)
    tool: Optional[ScanTool] = Field(default=ScanTool.axe_core)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = Field(default=None)
    user_id: str  # Required - linked to authenticated user
    organization_id: Optional[str] = Field(default=None)  # Team/org the scan belongs to
    # Visual evidence fields
    full_page_screenshot: Optional[str] = Field(default=None)  # Base64 encoded image
    evidence_screenshots: Optional[Dict[str, str]] = Field(default=None)  # Issue ID -> Base64 screenshot
    scan_metadata: Optional[Dict[str, Any]] = Field(default=None)  # Additional scan info


class ScanRequestCreate(BaseModel):
    """Model for creating a new scan request."""
    url: HttpUrl
    tool: Optional[ScanTool] = Field(default=ScanTool.axe_core)


class ScanRequestUpdate(BaseModel):
    """Model for updating an existing scan request."""
    status: Optional[ScanStatus] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
    issues: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
