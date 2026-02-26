"""
Feature Flag evaluation service.

Provides `is_enabled(flag_name, user_id)` with:
  1. Redis cache (TTL 60s) for fast lookups
  2. DB fallback for cache misses
  3. Percentage-based rollout using consistent hashing
  4. User whitelist targeting
  5. Evaluation logging for analytics
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Optional

from app.core.redis import cache_get, cache_set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

FLAG_CACHE_TTL = 60  # 1 minute
FLAGS_CACHE_KEY = "feature_flags:all"


def _consistent_hash_percentage(flag_name: str, user_id: str) -> float:
    """
    Deterministic percentage check: same user always gets the same result
    for the same flag, avoiding flip-flopping between requests.
    """
    h = hashlib.md5(f"{flag_name}:{user_id}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF  # 0.0 to 1.0


async def get_all_flags(db: AsyncSession) -> dict:
    """Return all flags as a dict keyed by name, with Redis caching."""
    # Try cache first
    cached = await cache_get(FLAGS_CACHE_KEY)
    if cached:
        return json.loads(cached)

    from app.models.feature_flag import FeatureFlag

    result = await db.execute(select(FeatureFlag))
    flags = result.scalars().all()

    flags_dict = {}
    for f in flags:
        flags_dict[f.name] = {
            "id": str(f.id),
            "is_enabled": f.is_enabled,
            "rollout_percentage": f.rollout_percentage,
            "target_user_ids": f.target_user_ids or [],
        }

    await cache_set(FLAGS_CACHE_KEY, json.dumps(flags_dict), FLAG_CACHE_TTL)
    return flags_dict


async def is_enabled(
    flag_name: str,
    db: AsyncSession,
    user_id: Optional[str] = None,
    log_evaluation: bool = True,
) -> bool:
    """
    Evaluate a feature flag for a specific user.

    Resolution order:
      1. If flag doesn't exist → False
      2. If flag is globally disabled → False
      3. If user is in target_user_ids whitelist → True
      4. If rollout_percentage > 0 → consistent hash check
      5. If flag is_enabled with rollout_percentage == 0 → True (fully on)
    """
    flags = await get_all_flags(db)
    flag_data = flags.get(flag_name)

    if not flag_data:
        return False

    result = False

    if not flag_data["is_enabled"]:
        result = False
    elif user_id and str(user_id) in [
        str(uid) for uid in flag_data.get("target_user_ids", [])
    ]:
        # Whitelisted user
        result = True
    elif flag_data["rollout_percentage"] > 0 and user_id:
        # Percentage rollout
        user_pct = _consistent_hash_percentage(flag_name, str(user_id))
        result = user_pct <= flag_data["rollout_percentage"]
    elif flag_data["rollout_percentage"] == 0 and flag_data["is_enabled"]:
        # Fully enabled (no rollout constraint)
        result = True

    # Log evaluation (fire-and-forget, don't block the request)
    if log_evaluation and flag_data.get("id"):
        try:
            await _log_evaluation(db, flag_data["id"], flag_name, user_id, result)
        except Exception:
            logger.warning("Failed to log flag evaluation for %s", flag_name)

    return result


async def _log_evaluation(
    db: AsyncSession,
    flag_id: str,
    flag_name: str,
    user_id: Optional[str],
    result: bool,
) -> None:
    """Insert a flag evaluation log entry."""
    from app.models.feature_flag import FlagEvaluation

    evaluation = FlagEvaluation(
        flag_id=flag_id,
        flag_name=flag_name,
        user_id=user_id,
        result=result,
    )
    db.add(evaluation)
    # Don't commit — let the request's session handle it


async def invalidate_flags_cache() -> None:
    """Clear the flags cache (call after any flag update)."""
    from app.core.redis import cache_delete

    await cache_delete(FLAGS_CACHE_KEY)
