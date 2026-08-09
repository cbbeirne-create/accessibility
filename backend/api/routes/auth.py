"""
Authentication API routes: signup, login, password reset.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends

from ...core.config import settings
from ...core.database import db
from ...core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_user_by_email,
    authenticate_user
)
from ...models.user import (
    User, UserCreate, UserLogin, UserProfile,
    Token, UserPlan,
    ForgotPasswordRequest, ResetPasswordRequest, PasswordResetResponse,
    ResendVerificationRequest, VerifyEmailRequest, EmailVerificationResponse
)
from ...services.email_service import (
    send_password_reset_email, 
    generate_password_reset_token,
    send_verification_email,
    generate_verification_token
)

router = APIRouter(prefix="/auth")


def get_user_scan_limits(plan: UserPlan) -> Dict[str, Any]:
    """Get scan limits for user plan."""
    if plan == UserPlan.free:
        return {
            "monthly_scans": 2,
            "can_export_pdf": False,
            "can_export_json": True,
            "can_view_screenshots": True
        }
    elif plan == UserPlan.pro:
        return {
            "monthly_scans": -1,
            "can_export_pdf": True,
            "can_export_json": True,
            "can_view_screenshots": True
        }


async def check_and_reset_monthly_scan_count(user_id: str, current_period_start) -> bool:
    """Check if we're in a new month and reset the scan count if needed."""
    now = datetime.utcnow()
    
    if not current_period_start:
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "current_period_start": now,
                "current_period_end": now.replace(
                    day=1, 
                    month=now.month % 12 + 1 if now.month < 12 else 1,
                    year=now.year if now.month < 12 else now.year + 1
                ),
                "scans_used_this_month": 0
            }}
        )
        return True
    
    if isinstance(current_period_start, str):
        current_period_start = datetime.fromisoformat(current_period_start.replace('Z', '+00:00'))
    
    if (now.year > current_period_start.year or 
        (now.year == current_period_start.year and now.month > current_period_start.month)):
        next_month = now.month % 12 + 1 if now.month < 12 else 1
        next_year = now.year if now.month < 12 else now.year + 1
        
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "current_period_start": now,
                "current_period_end": now.replace(day=1, month=next_month, year=next_year),
                "scans_used_this_month": 0
            }}
        )
        logging.info(f"Reset monthly scan count for user {user_id} - new month detected")
        return True
    
    return False


def create_stripe_customer(email: str, name=None):
    """Create Stripe customer - returns None if Stripe is not configured."""
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    if not stripe.api_key or stripe.api_key.startswith('sk_test_your'):
        logging.warning("Stripe not configured - skipping customer creation")
        return None
    
    try:
        customer = stripe.Customer.create(email=email, name=name)
        return customer
    except Exception as e:
        logging.error(f"Failed to create Stripe customer: {e}")
        return None


@router.post("/signup", response_model=Token)
async def signup(user_data: UserCreate):
    """Create new user account and send verification email."""
    try:
        existing_user = await get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        stripe_customer = create_stripe_customer(user_data.email, user_data.full_name)
        stripe_customer_id = stripe_customer.id if stripe_customer else None
        
        # Generate email verification token
        verification_token = generate_verification_token()
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            stripe_customer_id=stripe_customer_id,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            email_verified=False,
            email_verification_token=verification_token,
            email_verification_expires=verification_expires
        )
        
        user_data_dict = user.dict()
        user_data_dict['email'] = str(user_data_dict['email'])
        await db.users.insert_one(user_data_dict)
        
        # Send verification email
        user_name = user_data.full_name or str(user_data.email).split('@')[0]
        send_verification_email(
            email=str(user_data.email),
            verification_token=verification_token,
            user_name=user_name
        )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Signup failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create account")


@router.post("/login", response_model=Token)
async def login(form_data: UserLogin):
    """Authenticate user and return access token."""
    user = await authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    current_period_start = user.get("current_period_start")
    if isinstance(current_period_start, str):
        current_period_start = datetime.fromisoformat(current_period_start.replace('Z', '+00:00'))
    
    await check_and_reset_monthly_scan_count(user["id"], current_period_start)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """Request a password reset email."""
    try:
        user = await get_user_by_email(request.email)
        
        if user:
            reset_token = generate_password_reset_token()
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {
                    "password_reset_token": reset_token,
                    "password_reset_expires": expires_at
                }}
            )
            
            user_name = user.get("full_name") or user.get("email", "").split("@")[0]
            email_sent = send_password_reset_email(
                email=str(user["email"]),
                reset_token=reset_token,
                user_name=user_name
            )
            
            if not email_sent:
                logging.warning(f"Failed to send reset email to {request.email}")
        
        return PasswordResetResponse(
            message="If an account with that email exists, you will receive a password reset link shortly.",
            success=True
        )
        
    except Exception as e:
        logging.error(f"Forgot password error: {e}")
        return PasswordResetResponse(
            message="If an account with that email exists, you will receive a password reset link shortly.",
            success=True
        )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: ResetPasswordRequest):
    """Reset password using a valid reset token."""
    try:
        user = await db.users.find_one({"password_reset_token": request.token})
        
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired reset token. Please request a new password reset."
            )
        
        expires_at = user.get("password_reset_expires")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            if datetime.utcnow() > expires_at:
                await db.users.update_one(
                    {"id": user["id"]},
                    {"$set": {
                        "password_reset_token": None,
                        "password_reset_expires": None
                    }}
                )
                raise HTTPException(
                    status_code=400,
                    detail="Reset token has expired. Please request a new password reset."
                )
        
        hashed_password = get_password_hash(request.new_password)
        
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "hashed_password": hashed_password,
                "password_reset_token": None,
                "password_reset_expires": None
            }}
        )
        
        logging.info(f"Password reset successful for user {user['id']}")
        
        return PasswordResetResponse(
            message="Your password has been reset successfully. You can now log in with your new password.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Reset password error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while resetting your password. Please try again."
        )


@router.get("/verify-reset-token")
async def verify_reset_token(token: str):
    """Verify if a reset token is valid."""
    user = await db.users.find_one({"password_reset_token": token})
    
    if not user:
        return {"valid": False, "message": "Invalid reset token"}
    
    expires_at = user.get("password_reset_expires")
    if expires_at:
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        if datetime.utcnow() > expires_at:
            return {"valid": False, "message": "Reset token has expired"}
    
    return {"valid": True, "message": "Token is valid"}


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(request: VerifyEmailRequest):
    """Verify user email with token."""
    try:
        user = await db.users.find_one({"email_verification_token": request.token})
        
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired verification token."
            )
        
        # Check if already verified
        if user.get("email_verified"):
            return EmailVerificationResponse(
                message="Your email is already verified.",
                success=True
            )
        
        # Check expiration
        expires_at = user.get("email_verification_expires")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            if datetime.utcnow() > expires_at:
                raise HTTPException(
                    status_code=400,
                    detail="Verification link has expired. Please request a new one."
                )
        
        # Mark email as verified
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "email_verified": True,
                "email_verification_token": None,
                "email_verification_expires": None
            }}
        )
        
        logging.info(f"Email verified for user {user['id']}")
        
        return EmailVerificationResponse(
            message="Your email has been verified successfully!",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during verification. Please try again."
        )


@router.post("/resend-verification", response_model=EmailVerificationResponse)
async def resend_verification(request: ResendVerificationRequest):
    """Resend verification email to user."""
    try:
        user = await get_user_by_email(request.email)
        
        if not user:
            # Don't reveal if email exists
            return EmailVerificationResponse(
                message="If an account exists with this email, a verification link will be sent.",
                success=True
            )
        
        # Check if already verified
        if user.get("email_verified"):
            return EmailVerificationResponse(
                message="Your email is already verified.",
                success=True
            )
        
        # Generate new verification token
        verification_token = generate_verification_token()
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "email_verification_token": verification_token,
                "email_verification_expires": verification_expires
            }}
        )
        
        # Send verification email
        user_name = user.get("full_name") or str(user["email"]).split("@")[0]
        send_verification_email(
            email=str(user["email"]),
            verification_token=verification_token,
            user_name=user_name
        )
        
        return EmailVerificationResponse(
            message="Verification email sent! Please check your inbox.",
            success=True
        )
        
    except Exception as e:
        logging.error(f"Resend verification error: {e}")
        return EmailVerificationResponse(
            message="If an account exists with this email, a verification link will be sent.",
            success=True
        )


@router.get("/verification-status")
async def get_verification_status(current_user: User = Depends(get_current_user)):
    """Get email verification status for current user."""
    return {
        "email_verified": current_user.email_verified,
        "email": current_user.email
    }


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile with subscription info."""
    was_reset = await check_and_reset_monthly_scan_count(
        current_user.id, 
        current_user.current_period_start
    )
    
    if was_reset:
        user_data = await db.users.find_one({"id": current_user.id})
        if user_data:
            current_user = User(**user_data)
    
    # Get effective plan (if in org, inherits owner's plan)
    effective_plan = current_user.plan
    if current_user.organization_id:
        org = await db.organizations.find_one({"id": current_user.organization_id})
        if org:
            owner = await db.users.find_one({"id": org["owner_id"]})
            if owner:
                effective_plan = UserPlan(owner.get("plan", "free"))
    
    limits = get_user_scan_limits(effective_plan)
    scans_remaining = limits["monthly_scans"] - current_user.scans_used_this_month if limits["monthly_scans"] != -1 else -1
    
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        plan=effective_plan,  # Return effective plan
        subscription_status=current_user.subscription_status,
        scans_used_this_month=current_user.scans_used_this_month,
        scans_remaining=scans_remaining,
        current_period_start=current_user.current_period_start,
        current_period_end=current_user.current_period_end,
        created_at=current_user.created_at,
        email_verified=current_user.email_verified,
        organization_id=current_user.organization_id
    )
