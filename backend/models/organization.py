"""
Organization-related Pydantic models for team functionality.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class OrganizationRole(str, Enum):
    """Organization member roles."""
    owner = "owner"
    member = "member"


class Organization(BaseModel):
    """Organization/Team model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(min_length=2, max_length=100)
    owner_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrganizationCreate(BaseModel):
    """Model for creating an organization."""
    name: str = Field(min_length=2, max_length=100)


class OrganizationUpdate(BaseModel):
    """Model for updating an organization."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)


class OrganizationMember(BaseModel):
    """Organization member relationship model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    user_id: str
    role: OrganizationRole = Field(default=OrganizationRole.member)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrganizationMemberInfo(BaseModel):
    """Member info for display (includes user details)."""
    user_id: str
    email: str
    full_name: Optional[str] = None
    role: OrganizationRole
    joined_at: datetime


class OrganizationInvite(BaseModel):
    """Organization invite model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    email: EmailStr
    token: str
    invited_by: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrganizationInviteCreate(BaseModel):
    """Model for creating an invite."""
    email: EmailStr


class OrganizationInviteInfo(BaseModel):
    """Invite info for display."""
    id: str
    email: str
    organization_name: str
    invited_by_name: Optional[str] = None
    expires_at: datetime
    created_at: datetime


class OrganizationWithMembers(BaseModel):
    """Organization with member list."""
    id: str
    name: str
    owner_id: str
    members: List[OrganizationMemberInfo] = []
    pending_invites: List[OrganizationInviteInfo] = []
    member_count: int = 0
    created_at: datetime


class OrganizationProfile(BaseModel):
    """Organization profile for user context."""
    id: str
    name: str
    role: OrganizationRole
    owner_id: str
    member_count: int
    is_owner: bool


class TransferOwnershipRequest(BaseModel):
    """Request to transfer organization ownership."""
    new_owner_id: str
