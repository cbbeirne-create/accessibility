"""Password hashing, JWT access/refresh tokens, and authentication helpers."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as bcrypt_lib
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings
from .database import db

security = HTTPBearer(auto_error=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt_lib.hashpw(password_bytes, bcrypt_lib.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt_lib.checkpw(plain_password.encode('utf-8')[:72], hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def _encode_token(*, user_id: str, token_type: str, expires_delta: timedelta, jti: Optional[str] = None) -> str:
    now = _now()
    token_jti = jti or str(uuid.uuid4())
    payload = {
        'sub': user_id,
        'type': token_type,
        'jti': token_jti,
        'iat': int(now.timestamp()),
        'nbf': int(now.timestamp()),
        'exp': int((now + expires_delta).timestamp()),
        'iss': settings.JWT_ISSUER,
        'aud': settings.JWT_AUDIENCE,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(*, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    return _encode_token(
        user_id=user_id,
        token_type='access',
        expires_delta=expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


async def create_refresh_token(*, user_id: str) -> str:
    jti = str(uuid.uuid4())
    expires_at = _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token = _encode_token(user_id=user_id, token_type='refresh', expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), jti=jti)
    await db.refresh_sessions.insert_one({
        'jti_hash': hashlib.sha256(jti.encode()).hexdigest(),
        'user_id': user_id,
        'expires_at': expires_at,
        'created_at': _now(),
        'revoked_at': None,
    })
    return token


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail='Could not validate credentials') from exc
    if payload.get('type') != expected_type or not payload.get('sub') or not payload.get('jti'):
        raise HTTPException(status_code=401, detail='Invalid token')
    return payload


async def rotate_refresh_token(token: str) -> tuple[str, str]:
    payload = decode_token(token, 'refresh')
    jti_hash = hashlib.sha256(payload['jti'].encode()).hexdigest()
    session = await db.refresh_sessions.find_one({'jti_hash': jti_hash, 'revoked_at': None})
    if not session or session.get('expires_at') <= _now():
        raise HTTPException(status_code=401, detail='Refresh session expired')
    await db.refresh_sessions.update_one({'_id': session['_id']}, {'$set': {'revoked_at': _now()}})
    user = await db.users.find_one({'id': payload['sub'], 'is_active': {'$ne': False}})
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    return create_access_token(user_id=user['id']), await create_refresh_token(user_id=user['id'])


async def revoke_refresh_token(token: Optional[str]) -> None:
    if not token:
        return
    try:
        payload = decode_token(token, 'refresh')
    except HTTPException:
        return
    jti_hash = hashlib.sha256(payload['jti'].encode()).hexdigest()
    await db.refresh_sessions.update_one({'jti_hash': jti_hash}, {'$set': {'revoked_at': _now()}})


async def get_user_by_email(email: str):
    return await db.users.find_one({'email': email.lower()})


async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user or not verify_password(password, user['hashed_password']) or user.get('is_active') is False:
        return False
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from ..models.user import User
    payload = decode_token(credentials.credentials, 'access')
    user = await db.users.find_one({'id': payload['sub'], 'is_active': {'$ne': False}})
    if not user:
        raise HTTPException(status_code=401, detail='Could not validate credentials')
    return User(**user)
