"""Distributed rate limiting for sensitive API routes using MongoDB fixed windows."""
import time
from datetime import datetime, timedelta, timezone

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .database import db


class RateLimitMiddleware(BaseHTTPMiddleware):
    POLICIES = {
        "/api/auth/login": (10, 60),
        "/api/auth/signup": (5, 300),
        "/api/auth/forgot-password": (5, 300),
        "/api/auth/resend-verification": (5, 300),
        "/api/auth/refresh": (30, 60),
        "/api/scans": (20, 60),
    }

    @staticmethod
    def _client_key(request: Request) -> str:
        # Use the socket peer address unless/until an explicitly trusted reverse-proxy
        # boundary is configured. This avoids accepting spoofable forwarding headers.
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        policy = self.POLICIES.get(request.url.path)
        if not policy or request.method == "OPTIONS":
            return await call_next(request)

        limit, window = policy
        key = f"{request.url.path}:{self._client_key(request)}"
        now_ts = int(time.time())
        bucket_ts = (now_ts // window) * window
        bucket_start = datetime.fromtimestamp(bucket_ts, tz=timezone.utc)
        expires_at = bucket_start + timedelta(seconds=window + 60)
        query = {"key": key, "bucket_start": bucket_start}
        update = {
            "$inc": {"count": 1},
            "$setOnInsert": {"expires_at": expires_at},
        }

        try:
            record = await db.rate_limits.find_one_and_update(
                query,
                update,
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            # Two instances can race to create the same window. The unique index ensures
            # one wins; the loser retries as a plain atomic increment.
            record = await db.rate_limits.find_one_and_update(
                query,
                {"$inc": {"count": 1}},
                return_document=ReturnDocument.AFTER,
            )

        if record and int(record.get("count", 0)) > limit:
            retry_after = max(1, bucket_ts + window - now_ts)
            return JSONResponse(
                {"detail": "Too many requests. Please try again later."},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
