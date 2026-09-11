"""Small distributed fixed-window rate limiter backed by MongoDB."""
import hashlib
import ipaddress
import time
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from pymongo import ReturnDocument

from ..core.config import settings
from ..core.database import db


def _client_identifier(request: Request) -> str:
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get('x-forwarded-for', '')
        candidate = forwarded.split(',')[0].strip() if forwarded else ''
        if candidate:
            try:
                return str(ipaddress.ip_address(candidate))
            except ValueError:
                pass
    return request.client.host if request.client else 'unknown'


async def enforce_rate_limit(request: Request, bucket: str, limit: int, window_seconds: int) -> None:
    identifier = _client_identifier(request)
    window = int(time.time()) // window_seconds
    key = hashlib.sha256(f'{bucket}:{identifier}:{window}'.encode()).hexdigest()
    now = datetime.now(timezone.utc)
    doc = await db.rate_limits.find_one_and_update(
        {'_id': key},
        {
            '$inc': {'count': 1},
            '$setOnInsert': {
                'bucket': bucket,
                'identifier_hash': hashlib.sha256(identifier.encode()).hexdigest(),
                'expires_at': now + timedelta(seconds=window_seconds * 2),
            },
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if doc and doc.get('count', 0) > limit:
        raise HTTPException(
            status_code=429,
            detail='Too many requests. Please try again shortly.',
            headers={'Retry-After': str(window_seconds)},
        )
