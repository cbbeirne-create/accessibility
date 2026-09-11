"""Authentication API routes: signup, login, refresh, logout, verification and password reset."""
import hashlib
import logging
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ...core.config import settings
from ...core.database import db
from ...core.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    get_user_by_email,
    revoke_refresh_token,
    rotate_refresh_token,
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

router = APIRouter(prefix='/auth')
logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path='/api/auth',
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        domain=settings.COOKIE_DOMAIN,
        path='/api/auth',
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )


async def _issue_session(response: Response, user_id: str) -> Token:
    access = create_access_token(user_id=user_id)
    refresh = await create_refresh_token(user_id=user_id)
    _set_refresh_cookie(response, refresh)
    return Token(access_token=access)


async def _reset_monthly_count_if_needed(user: dict) -> dict:
    now = _now()
    period_start = user.get('current_period_start')
    if isinstance(period_start, str):
        period_start = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
    if period_start and period_start.tzinfo is None:
        period_start = period_start.replace(tzinfo=timezone.utc)
    if not period_start or (now.year, now.month) > (period_start.year, period_start.month):
        next_month = 1 if now.month == 12 else now.month + 1
        next_year = now.year + 1 if now.month == 12 else now.year
        await db.users.update_one({'id': user['id']}, {'$set': {
            'current_period_start': now,
            'current_period_end': now.replace(year=next_year, month=next_month, day=1, hour=0, minute=0, second=0, microsecond=0),
            'scans_used_this_month': 0,
        }})
        user = await db.users.find_one({'id': user['id']})
    return user


def _create_stripe_customer(email: str, name: str | None):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not stripe.api_key:
        return None
    try:
        return stripe.Customer.create(email=email, name=name)
    except Exception as exc:
        logger.warning('Stripe customer creation failed during signup: %s', exc)
        return None


@router.post('/signup', response_model=Token)
async def signup(user_data: UserCreate, response: Response):
    if await get_user_by_email(str(user_data.email)):
        raise HTTPException(status_code=400, detail='Email already registered')

    verification_token = generate_verification_token()
    now = _now()
    customer = _create_stripe_customer(str(user_data.email), user_data.full_name)
    user = User(
        email=str(user_data.email).lower(),
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        stripe_customer_id=customer.id if customer else None,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        email_verified=False,
        email_verification_token=_token_hash(verification_token),
        email_verification_expires=now + timedelta(hours=24),
    )
    payload = user.model_dump()
    payload['email'] = str(payload['email'])
    await db.users.insert_one(payload)

    send_verification_email(
        email=str(user.email),
        verification_token=verification_token,
        user_name=user_data.full_name or str(user.email).split('@')[0],
    )
    return await _issue_session(response, user.id)


@router.post('/login', response_model=Token)
async def login(form_data: UserLogin, response: Response):
    user = await authenticate_user(str(form_data.email), form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail='Incorrect email or password', headers={'WWW-Authenticate': 'Bearer'})
    user = await _reset_monthly_count_if_needed(user)
    await db.users.update_one({'id': user['id']}, {'$set': {'last_login': _now()}})
    return await _issue_session(response, user['id'])


@router.post('/refresh', response_model=Token)
async def refresh(request: Request, response: Response):
    token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail='Refresh session not found')
    access, replacement = await rotate_refresh_token(token)
    _set_refresh_cookie(response, replacement)
    return Token(access_token=access)


@router.post('/logout')
async def logout(request: Request, response: Response):
    await revoke_refresh_token(request.cookies.get(settings.REFRESH_COOKIE_NAME))
    _clear_refresh_cookie(response)
    return {'message': 'Logged out'}


@router.post('/forgot-password', response_model=PasswordResetResponse)
async def forgot_password(request: ForgotPasswordRequest):
    generic = PasswordResetResponse(message='If an account with that email exists, you will receive a password reset link shortly.', success=True)
    try:
        user = await get_user_by_email(str(request.email))
        if not user:
            return generic
        token = generate_password_reset_token()
        await db.users.update_one({'id': user['id']}, {'$set': {
            'password_reset_token': _token_hash(token),
            'password_reset_expires': _now() + timedelta(hours=1),
        }})
        send_password_reset_email(
            email=str(user['email']),
            reset_token=token,
            user_name=user.get('full_name') or user['email'].split('@')[0],
        )
        return generic
    except Exception as exc:
        logger.warning('Forgot password processing failed: %s', exc)
        return generic


@router.post('/reset-password', response_model=PasswordResetResponse)
async def reset_password(request: ResetPasswordRequest):
    user = await db.users.find_one({'password_reset_token': _token_hash(request.token)})
    if not user:
        raise HTTPException(status_code=400, detail='Invalid or expired reset token.')
    expires_at = user.get('password_reset_expires')
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not expires_at or _now() > expires_at:
        raise HTTPException(status_code=400, detail='Invalid or expired reset token.')
    await db.users.update_one({'id': user['id']}, {'$set': {
        'hashed_password': get_password_hash(request.new_password),
        'password_reset_token': None,
        'password_reset_expires': None,
    }})
    await db.refresh_sessions.update_many({'user_id': user['id'], 'revoked_at': None}, {'$set': {'revoked_at': _now()}})
    return PasswordResetResponse(message='Your password has been reset successfully.', success=True)


@router.get('/verify-reset-token')
async def verify_reset_token(token: str):
    user = await db.users.find_one({'password_reset_token': _token_hash(token)})
    if not user:
        return {'valid': False, 'message': 'Invalid reset token'}
    expires_at = user.get('password_reset_expires')
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return {'valid': bool(expires_at and _now() <= expires_at), 'message': 'Token is valid' if expires_at and _now() <= expires_at else 'Reset token has expired'}


@router.post('/verify-email', response_model=EmailVerificationResponse)
async def verify_email(request: VerifyEmailRequest):
    user = await db.users.find_one({'email_verification_token': _token_hash(request.token)})
    if not user:
        raise HTTPException(status_code=400, detail='Invalid or expired verification token.')
    expires_at = user.get('email_verification_expires')
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not expires_at or _now() > expires_at:
        raise HTTPException(status_code=400, detail='Verification link has expired. Please request a new one.')
    await db.users.update_one({'id': user['id']}, {'$set': {
        'email_verified': True,
        'email_verification_token': None,
        'email_verification_expires': None,
    }})
    return EmailVerificationResponse(message='Your email has been verified successfully!', success=True)


@router.post('/resend-verification', response_model=EmailVerificationResponse)
async def resend_verification(request: ResendVerificationRequest):
    generic = EmailVerificationResponse(message='If an unverified account exists with this email, a verification link will be sent.', success=True)
    user = await get_user_by_email(str(request.email))
    if not user or user.get('email_verified'):
        return generic
    token = generate_verification_token()
    await db.users.update_one({'id': user['id']}, {'$set': {
        'email_verification_token': _token_hash(token),
        'email_verification_expires': _now() + timedelta(hours=24),
    }})
    send_verification_email(
        email=str(user['email']),
        verification_token=token,
        user_name=user.get('full_name') or user['email'].split('@')[0],
    )
    return generic


@router.get('/verification-status')
async def get_verification_status(current_user: User = Depends(get_current_user)):
    return {'email_verified': current_user.email_verified, 'email': current_user.email}


@router.get('/me', response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    user_data = await db.users.find_one({'id': current_user.id})
    if not user_data:
        raise HTTPException(status_code=404, detail='User not found')
    user_data = await _reset_monthly_count_if_needed(user_data)
    current_user = User(**user_data)
    effective_plan = await get_effective_plan(current_user)
    limits = await get_limits(current_user)
    remaining = -1 if limits['monthly_scans'] == -1 else max(0, limits['monthly_scans'] - current_user.scans_used_this_month)
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        plan=effective_plan,
        subscription_status=current_user.subscription_status,
        scans_used_this_month=current_user.scans_used_this_month,
        scans_remaining=remaining,
        current_period_start=current_user.current_period_start,
        current_period_end=current_user.current_period_end,
        created_at=current_user.created_at,
        email_verified=current_user.email_verified,
        organization_id=current_user.organization_id,
    )
