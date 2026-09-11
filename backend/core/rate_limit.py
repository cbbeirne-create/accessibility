"""Small dependency-free rate limiter for sensitive API routes.

This is intentionally conservative and process-local. In horizontally scaled production
replace the backing store with Redis while retaining the same route policy.
"""
import asyncio
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    POLICIES = {
        "/api/auth/login": (10, 60),
        "/api/auth/signup": (5, 300),
        "/api/auth/forgot-password": (5, 300),
        "/api/auth/resend-verification": (5, 300),
        "/api/auth/refresh": (30, 60),
        "/api/scans": (20, 60),
    }

    def __init__(self, app):
        super().__init__(app)
        self.events = defaultdict(deque)
        self.lock = asyncio.Lock()

    @staticmethod
    def _client_key(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if forwarded:
            return forwarded
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        policy = self.POLICIES.get(request.url.path)
        if not policy or request.method == "OPTIONS":
            return await call_next(request)

        limit, window = policy
        key = f"{request.url.path}:{self._client_key(request)}"
        now = time.monotonic()
        async with self.lock:
            events = self.events[key]
            while events and events[0] <= now - window:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(window - (now - events[0])))
                return JSONResponse(
                    {"detail": "Too many requests. Please try again later."},
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                )
            events.append(now)

        return await call_next(request)
