"""Authentication API routes: signup, login, refresh, logout and account recovery."""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ...core.config import settings
from ...core.database import db
from ...core.security import (
    authenticate_user,
    create_access_token,
    generate_refresh_token,
    get_current_user,
    get_password_hash,
    get_user_by_email,
    revoke_refresh_token,
    rotate_refresh_token,
    store_refresh_token,
)
from ...models.user import (
    EmailVerificationResponse,
    ForgotPasswordRequest,
    PasswordResetResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    Token,
    User,
    UserCreate,
    UserLogin,
    UserProfile,
    VerifyEmailRequest,
)
from ...services.email_service import (
    generate_password_reset_token,
    generate_verification_token,
    send_password_reset_email,
    send_verification_email,
)
from ...services.entitlements import get_effective_plan, get_limits

router = APIRouter(prefix="/auth")
logger = logging.getLogger(__name__)


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite="lax",
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path="/api/auth",
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite="lax",
    )


async def _issue_session(response: Response, user_id: str) -> Token:
    refresh_token = generate_refresh_token()
    await store_refresh_token(user_id, refresh_token)
    _set_refresh_cookie(response, refresh_token)
    return Token(access_token=create_access_token({"sub": user_id}), token_type="bearer")


async def check_and_reset_monthly_scan_count(user_id: str, current_period_start) -> bool:
    now = datetime.utcnow()
    if isinstance(current_period_start, str):
        current_period_start = datetime.fromisoformat(current_period_start.replace("Z", "+00:00")).replace(tzinfo=None)

    if not current_period_start or (now.year, now.month) > (current_period_start.year, current_period_start.month):
        next_month = now.month % 12 + 1
        next_year = now.year + 1 if now.month == 12 else now.year
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "current_period_start": now,
                "current_period_end": now.replace(day=1, month=next_month, year=next_year),
                "scans_used_this_month": 0,
            }},
        )
        return True
    return False


def create_stripe_customer(email: str, name=None):
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not stripe.api_key:
        return None
    try:
        return stripe.Customer.create(email=email, name=name)
    except Exception as exc:
        logger.error("Failed to create Stripe customer: %s", exc)
        return None


@router.post("/signup", response_model=Token)
async def signup(user_data: UserCreate, response: Response):
    if await get_user_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    stripe_customer = create_stripe_customer(str(user_data.email), user_data.full_name)
    now = datetime.utcnow()
    verification_token = generate_verification_token()
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        stripe_customer_id=stripe_customer.id if stripe_customer else None,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        email_verified=False,
        email_verification_token=verification_token,
        email_verification_expires=now + timedelta(hours=24),
    )
    document = user.dict()
    document["email"] = str(document["email"])
    await db.users.insert_one(document)

    send_verification_email(
        email=str(user.email),
        verification_token=verification_token,
        user_name=user.full_name or str(user.email).split("@")[0],
    )
    return await _issue_session(response, user.id)


@router.post("/login", response_model=Token)
async def login(form_data: UserLogin, response: Response):
    user = await authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})

    await check_and_reset_monthly_scan_count(user["id"], user.get("current_period_start"))
    await db.users.update_one({"id": user["id"]}, {"$set": {"last_login": datetime.utcnow()}})
    return await _issue_session(response, user["id"])


@router.post("/refresh", response_model=Token)
async def refresh_session(request: Request, response: Response):
    token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh session not found")

    user, new_token = await rotate_refresh_token(token)
    if not user or not new_token:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh session is invalid or expired")

    _set_refresh_cookie(response, new_token)
    return Token(access_token=create_access_token({"sub": user["id"]}), token_type="bearer")


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if token:
        await revoke_refresh_token(token)
    _clear_refresh_cookie(response)
    return {"message": "Logged out"}


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(request: ForgotPasswordRequest):
    generic = PasswordResetResponse(
        message="If an account with that email exists, you will receive a password reset link shortly.",
        success=True,
    )
    try:
        user = await get_user_by_email(request.email)
        if user:
            token = generate_password_reset_token()
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {"password_reset_token": token, "password_reset_expires": datetime.utcnow() + timedelta(hours=1)}},
            )
            send_password_reset_email(
                email=str(user["email"]),
                reset_token=token,
                user_name=user.get("full_name") or user["email"].split("@")[0],
            )
    except Exception as exc:
        logger.error("Forgot password error: %s", exc)
    return generic


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: ResetPasswordRequest):
    user = await db.users.find_one({"password_reset_token": request.token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    expires_at = user.get("password_reset_expires")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00")).replace(tzinfo=None)
    if not expires_at or datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "hashed_password": get_password_hash(request.new_password),
            "password_reset_token": None,
            "password_reset_expires": None,
        }},
    )
    await db.refresh_tokens.update_many(
        {"user_id": user["id"], "revoked_at": None},
        {"$set": {"revoked_at": datetime.now(timezone.utc)}},
    )
    return PasswordResetResponse(message="Your password has been reset successfully.", success=True)


@router.get("/verify-reset-token")
async def verify_reset_token(token: str):
    user = await db.users.find_one({"password_reset_token": token})
    if not user:
        return {"valid": False, "message": "Invalid reset token"}
    expires_at = user.get("password_reset_expires")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00")).replace(tzinfo=None)
    valid = bool(expires_at and datetime.utcnow() <= expires_at)
    return {"valid": valid, "message": "Token is valid" if valid else "Reset token has expired"}


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(request: VerifyEmailRequest):
    user = await db.users.find_one({"email_verification_token": request.token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    expires_at = user.get("email_verification_expires")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00")).replace(tzinfo=None)
    if expires_at and datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="Verification link has expired")

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"email_verified": True, "email_verification_token": None, "email_verification_expires": None}},
    )
    return EmailVerificationResponse(message="Your email has been verified successfully!", success=True)


@router.post("/resend-verification", response_model=EmailVerificationResponse)
async def resend_verification(request: ResendVerificationRequest):
    user = await get_user_by_email(request.email)
    generic = EmailVerificationResponse(
        message="If an account exists with this email, a verification link will be sent.", success=True
    )
    if not user or user.get("email_verified"):
        return generic

    token = generate_verification_token()
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"email_verification_token": token, "email_verification_expires": datetime.utcnow() + timedelta(hours=24)}},
    )
    send_verification_email(
        email=str(user["email"]),
        verification_token=token,
        user_name=user.get("full_name") or user["email"].split("@")[0],
    )
    return generic


@router.get("/verification-status")
async def get_verification_status(current_user: User = Depends(get_current_user)):
    return {"email_verified": current_user.email_verified, "email": current_user.email}


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    if await check_and_reset_monthly_scan_count(current_user.id, current_user.current_period_start):
        refreshed = await db.users.find_one({"id": current_user.id})
        if refreshed:
            current_user = User(**refreshed)

    effective_plan = await get_effective_plan(current_user)
    limits = await get_limits(current_user)
    monthly_limit = limits["monthly_scans"]
    scans_remaining = -1 if monthly_limit == -1 else max(0, monthly_limit - current_user.scans_used_this_month)

    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        plan=effective_plan,
        subscription_status=current_user.subscription_status,
        scans_used_this_month=current_user.scans_used_this_month,
        scans_remaining=scans_remaining,
        current_period_start=current_user.current_period_start,
        current_period_end=current_user.current_period_end,
        created_at=current_user.created_at,
        email_verified=current_user.email_verified,
        organization_id=current_user.organization_id,
    )
