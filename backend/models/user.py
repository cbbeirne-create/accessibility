"""
User-related Pydantic models and enums.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserPlan(str, Enum):
    """User subscription plan types."""
    free = "free"
    pro = "pro"


class SubscriptionStatus(str, Enum):
    """Subscription status states."""
    active = "active"
    inactive = "inactive"
    canceled = "canceled"
    past_due = "past_due"


class User(BaseModel):
    """Complete user model for database storage."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: Optional[str] = None
    hashed_password: str
    plan: UserPlan = Field(default=UserPlan.free)
    subscription_status: SubscriptionStatus = Field(default=SubscriptionStatus.inactive)
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    scans_used_this_month: int = Field(default=0)
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = Field(default=True)
    # Password reset fields
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    # Email verification fields
    email_verified: bool = Field(default=False)
    email_verification_token: Optional[str] = None
    email_verification_expires: Optional[datetime] = None


class UserCreate(BaseModel):
    """Model for user registration request."""
    email: EmailStr
    full_name: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    """Model for user login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data."""
    email: Optional[str] = None


class UserProfile(BaseModel):
    """Public user profile response model."""
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    plan: UserPlan
    subscription_status: SubscriptionStatus
    scans_used_this_month: int
    scans_remaining: int
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    created_at: datetime
    email_verified: bool = False


# Password Reset Models
class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request model for password reset."""
    token: str
    new_password: str = Field(min_length=8, description="Password must be at least 8 characters")


class PasswordResetResponse(BaseModel):
    """Response model for password reset operations."""
    message: str
    success: bool


# Email Verification Models
class ResendVerificationRequest(BaseModel):
    """Request model for resending verification email."""
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    """Request model for email verification."""
    token: str


class EmailVerificationResponse(BaseModel):
    """Response model for email verification operations."""
    message: str
    success: bool
