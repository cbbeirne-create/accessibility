"""Security utilities: password hashing, JWT tokens, authentication and refresh tokens."""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as bcrypt_lib
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings
from .database import db

security = HTTPBearer()


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt_lib.hashpw(password_bytes, bcrypt_lib.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt_lib.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not configured")
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        **data,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def store_refresh_token(user_id: str, token: str) -> None:
    now = datetime.now(timezone.utc)
    await db.refresh_tokens.insert_one({
        "token_hash": hash_refresh_token(token),
        "user_id": user_id,
        "created_at": now,
        "expires_at": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "revoked_at": None,
    })


async def rotate_refresh_token(token: str):
    """Consume a valid refresh token and return (user, new_token)."""
    token_hash = hash_refresh_token(token)
    now = datetime.now(timezone.utc)
    record = await db.refresh_tokens.find_one({
        "token_hash": token_hash,
        "revoked_at": None,
        "expires_at": {"$gt": now},
    })
    if not record:
        return None, None

    user = await db.users.find_one({"id": record["user_id"], "is_active": True})
    if not user:
        return None, None

    new_token = generate_refresh_token()
    await db.refresh_tokens.update_one(
        {"token_hash": token_hash, "revoked_at": None},
        {"$set": {"revoked_at": now, "replaced_by": hash_refresh_token(new_token)}},
    )
    await store_refresh_token(user["id"], new_token)
    return user, new_token


async def revoke_refresh_token(token: str) -> None:
    await db.refresh_tokens.update_one(
        {"token_hash": hash_refresh_token(token), "revoked_at": None},
        {"$set": {"revoked_at": datetime.now(timezone.utc)}},
    )


async def get_user_by_email(email: str):
    return await db.users.find_one({"email": email})


async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user or not user.get("is_active", True):
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from ..models.user import User

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        if not settings.SECRET_KEY:
            raise credentials_exception
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        if payload.get("type") != "access":
            raise credentials_exception
        subject = payload.get("sub")
        if not subject:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # New tokens use immutable user IDs. Email fallback supports existing sessions during rollout.
    user = await db.users.find_one({"id": subject})
    if user is None and "@" in subject:
        user = await get_user_by_email(subject)
    if user is None or not user.get("is_active", True):
        raise credentials_exception

    return User(**user)
