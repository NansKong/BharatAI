"""
Redis caching decorators and invalidation helpers.

Provides a decorator for automatic cache-aside on FastAPI endpoints,
plus targeted invalidation functions for feed, leaderboard, and opportunities.
"""
from __future__ import annotations

import functools
import json
import logging
from typing import Any, Callable, Optional

from app.core.redis import cache_delete_pattern, cache_get, cache_set

logger = logging.getLogger(__name__)


# ── Cache-aside Decorator ─────────────────────────────────────────────────────


def cached_response(
    ttl: int,
    key_prefix: str,
    key_fn: Optional[Callable[..., str]] = None,
):
    """
    Decorator that caches the JSON-serializable return value of an async function.

    Usage::

        @cached_response(ttl=600, key_prefix="leaderboard", key_fn=lambda domain, **kw: domain or "overall")
        async def get_leaderboard(domain: str = None, ...):
            ...

    The decorated function MUST return a Pydantic model or dict.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build cache key
            suffix = key_fn(*args, **kwargs) if key_fn else ""
            raw_key = f"{key_prefix}:{suffix}" if suffix else key_prefix
            cache_key = f"cache:{raw_key}"

            # Try cache hit
            try:
                hit = await cache_get(cache_key)
                if hit is not None:
                    return json.loads(hit)
            except Exception:
                logger.warning("Cache read failed for %s", cache_key)

            # Cache miss — execute function
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                serializable = result
                if hasattr(result, "model_dump"):
                    serializable = result.model_dump(mode="json")
                elif hasattr(result, "dict"):
                    serializable = result.dict()
                await cache_set(cache_key, json.dumps(serializable, default=str), ttl)
            except Exception:
                logger.warning("Cache write failed for %s", cache_key)

            return result

        return wrapper

    return decorator


# ── Targeted Invalidation Helpers ─────────────────────────────────────────────


async def bust_feed_cache(user_id: str) -> None:
    """Invalidate all cached feed entries for a specific user."""
    await cache_delete_pattern(f"feed:{user_id}:*")
    logger.info("Busted feed cache for user %s", user_id)


async def bust_leaderboard_cache() -> None:
    """Invalidate all leaderboard caches."""
    await cache_delete_pattern("cache:leaderboard:*")
    logger.info("Busted leaderboard cache")


async def bust_opportunities_cache() -> None:
    """Invalidate opportunity list caches (called on insert/update/delete)."""
    await cache_delete_pattern("cache:opportunities:*")
    logger.info("Busted opportunities cache")
