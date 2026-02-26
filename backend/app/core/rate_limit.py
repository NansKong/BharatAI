"""
Rate-limiting middleware using Redis sliding-window counters.

Policy:
  - Unauthenticated → per-IP: 60 requests / minute
  - Authenticated   → per-user: 300 requests / minute

Returns 429 Too Many Requests with Retry-After header when exceeded.
Response headers always include X-RateLimit-Limit and X-RateLimit-Remaining.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.core.config import settings
from fastapi import Request, Response
from starlette.middleware.base import (BaseHTTPMiddleware,
                                       RequestResponseEndpoint)
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Paths that should never be rate-limited
_EXEMPT = {
    "/health",
    "/health/db",
    "/health/redis",
    "/metrics",
    "/openapi.json",
    "/docs",
    "/redoc",
}

WINDOW_SECONDS = 60


def _extract_user_id(request: Request) -> Optional[str]:
    """Try to extract user ID from JWT without raising on failure."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        from app.core.security import decode_token

        payload = decode_token(auth[7:])
        return payload.get("sub")
    except Exception:
        return None


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip exempt paths and preflight requests
        if request.url.path in _EXEMPT or request.method == "OPTIONS":
            return await call_next(request)

        # Lazy import to avoid circular dependency at module load
        from app.core.redis import redis_client

        if redis_client is None:
            # Redis not ready — allow the request through
            return await call_next(request)

        # Determine rate-limit key and limit
        user_id = _extract_user_id(request)
        if user_id:
            key = f"rl:user:{user_id}"
            limit = settings.RATE_LIMIT_AUTH  # 300/min
        else:
            key = f"rl:ip:{_client_ip(request)}"
            limit = settings.RATE_LIMIT_ANON  # 60/min

        # Sliding window counter (Redis INCR + EXPIRE)
        try:
            pipe = redis_client.pipeline(transaction=True)
            pipe.incr(key)
            pipe.expire(key, WINDOW_SECONDS)
            results = await pipe.execute()
            count = int(results[0])
        except Exception:
            # If Redis is down, allow request through
            logger.warning("Rate limiter Redis error — passing through")
            return await call_next(request)

        remaining = max(0, limit - count)

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please slow down."},
                headers={
                    "Retry-After": str(WINDOW_SECONDS),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
