"""
Redis async client with helper methods for caching and token management.
"""
from typing import Optional

import redis.asyncio as aioredis
from app.core.config import settings

# Global Redis client (initialized on app startup)
redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """Initialize the Redis connection pool."""
    global redis_client
    redis_client = await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
    )


async def close_redis() -> None:
    """Close the Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


def get_redis() -> aioredis.Redis:
    """FastAPI dependency: return the Redis client."""
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client


# ── Token revocation (JWT blocklist) ─────────────────────────────────────────


async def add_to_blocklist(jti: str, ttl_seconds: int) -> None:
    """Add a JWT ID to the revocation blocklist with TTL matching token expiry."""
    await redis_client.setex(f"blocklist:{jti}", ttl_seconds, "1")


async def is_token_revoked(jti: str) -> bool:
    """Return True if the token JTI has been revoked."""
    return bool(await redis_client.exists(f"blocklist:{jti}"))


# ── Cache helpers ─────────────────────────────────────────────────────────────


async def cache_set(key: str, value: str, ttl: int) -> None:
    """Set a JSON string value with TTL."""
    await redis_client.setex(key, ttl, value)


async def cache_get(key: str) -> Optional[str]:
    """Get a cached value, returns None if missing or expired."""
    return await redis_client.get(key)


async def cache_delete(key: str) -> None:
    """Delete a cache key."""
    await redis_client.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern (use carefully in prod)."""
    keys = await redis_client.keys(pattern)
    if keys:
        await redis_client.delete(*keys)


async def health_check() -> bool:
    """Return True if Redis is reachable."""
    try:
        return await redis_client.ping()
    except Exception:
        return False
