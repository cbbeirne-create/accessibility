"""User-related Pydantic models and enums."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserPlan(str, Enum):
    free = 'free'
    pro = 'pro'


class SubscriptionStatus(str, Enum):
    active = 'active'
    inactive = 'inactive'
    canceled = 'canceled'
    past_due = 'past_due'


class User(BaseModel):
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
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    email_verified: bool = Field(default=False)
    email_verification_token: Optional[str] = None
    email_verification_expires: Optional[datetime] = None
    organization_id: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: str = Field(min_length=12, max_length=128)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: EmailStr):
        return str(value).lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: EmailStr):
        return str(value).lower()


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class TokenData(BaseModel):
    user_id: Optional[str] = None


class UserProfile(BaseModel):
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
    organization_id: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=12, max_length=128, description='Password must be at least 12 characters')


class PasswordResetResponse(BaseModel):
    message: str
    success: bool


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    token: str


class EmailVerificationResponse(BaseModel):
    message: str
    success: bool
