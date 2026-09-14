"""
Redis async client with fallback methods for caching and token management.
Guarantees high-availability even if Redis service is disconnected.
"""

import logging
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client (initialized on app startup)
redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """Initialize the Redis connection pool cleanly with fallback on error."""
    global redis_client
    try:
        client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
        await client.ping()
        redis_client = client
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.warning(
            f"Could not connect to Redis at {settings.REDIS_URL}: {e}. Operating in graceful fallback mode."
        )
        redis_client = None


async def close_redis() -> None:
    """Close the Redis connection."""
    global redis_client
    if redis_client:
        try:
            await redis_client.aclose()
        except Exception:
            pass
        redis_client = None


def get_redis() -> Optional[aioredis.Redis]:
    """FastAPI dependency: return the Redis client if available."""
    return redis_client


# ── Token revocation (JWT blocklist) ─────────────────────────────────────────


async def add_to_blocklist(jti: str, ttl_seconds: int) -> None:
    """Add a JWT ID to the revocation blocklist with TTL matching token expiry."""
    if redis_client is None:
        return
    try:
        await redis_client.setex(f"blocklist:{jti}", ttl_seconds, "1")
    except Exception as e:
        logger.warning(f"Redis add_to_blocklist failed: {e}")


async def is_token_revoked(jti: str) -> bool:
    """Return True if the token JTI has been revoked."""
    if redis_client is None:
        return False
    try:
        return bool(await redis_client.exists(f"blocklist:{jti}"))
    except Exception as e:
        logger.warning(f"Redis is_token_revoked failed: {e}")
        return False


# ── Cache helpers ─────────────────────────────────────────────────────────────


async def cache_set(key: str, value: str, ttl: int) -> None:
    """Set a JSON string value with TTL."""
    if redis_client is None:
        return
    try:
        await redis_client.setex(key, ttl, value)
    except Exception as e:
        logger.warning(f"Redis cache_set failed: {e}")


async def cache_get(key: str) -> Optional[str]:
    """Get a cached value, returns None if missing or expired."""
    if redis_client is None:
        return None
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.warning(f"Redis cache_get failed: {e}")
        return None


async def cache_delete(key: str) -> None:
    """Delete a cache key."""
    if redis_client is None:
        return
    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Redis cache_delete failed: {e}")


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern (use carefully in prod)."""
    if redis_client is None:
        return
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
    except Exception as e:
        logger.warning(f"Redis cache_delete_pattern failed: {e}")


async def health_check() -> bool:
    """Return True if Redis is reachable."""
    if redis_client is None:
        return False
    try:
        return bool(await redis_client.ping())
    except Exception:
        return False
