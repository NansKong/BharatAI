"""Celery tasks for InCoScore computation."""
from __future__ import annotations

import json
import logging
import re

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


# Keyword -> canonical domain key. Multi-word entries are matched as phrases;
# single-word entries are matched against whole words only, never as substrings
# ("me" must not match "manage*me*nt", "cs" must not match "economi*cs*").
DOMAIN_KEY_MAP = {
    "ai": "ai_ds",
    "ds": "ai_ds",
    "data science": "ai_ds",
    "machine learning": "ai_ds",
    "artificial intelligence": "ai_ds",
    "cs": "cs",
    "computer science": "cs",
    "it": "cs",
    "information technology": "cs",
    "software": "cs",
    "ece": "ece",
    "electronics": "ece",
    "electrical": "ece",
    "me": "me",
    "mechanical": "me",
    "civil": "civil",
    "biotech": "biotech",
    "biotechnology": "biotech",
    "law": "law",
    "legal": "law",
    "management": "management",
    "mba": "management",
    "bba": "management",
    "business": "management",
    "finance": "finance",
    "financial": "finance",
    "economics": "finance",
    "humanities": "humanities",
    "arts": "humanities",
    "govt": "govt",
    "government": "govt",
    "policy": "govt",
}


def _match_domain(text: str) -> str | None:
    """Return the domain key for ``text``, matching phrases before single words."""
    lowered = text.lower()
    for kw, key in DOMAIN_KEY_MAP.items():
        if " " in kw and kw in lowered:
            return key
    words = set(re.findall(r"[a-z]+", lowered))
    for kw, key in DOMAIN_KEY_MAP.items():
        if " " not in kw and kw in words:
            return key
    return None


def _resolve_user_domain(user, profile=None) -> str:
    """
    Infer user's academic domain from degree, profile interests, or skills.
    Returns a canonical domain key (e.g., 'ai_ds', 'cs', 'management', 'finance')
    or 'unclassified' if undetermined.
    """
    if user and user.degree:
        matched = _match_domain(user.degree)
        if matched:
            return matched

    if profile:
        for value in (profile.interests or []) + (profile.skills or []):
            matched = _match_domain(str(value))
            if matched:
                return matched

    return "unclassified"


@celery_app.task(name="incoscore.update", bind=True, max_retries=3)
def update_incoscore(self, user_id: str) -> dict:
    """
    Recompute InCoScore for a user after an achievement is verified.
    Loads verified achievements, runs compute_incoscore, stores snapshot.
    """
    import asyncio

    from sqlalchemy import func, select

    from app.ai.incoscore import assign_badges, compute_incoscore
    from app.core.database import AsyncSessionLocal
    from app.models.application import Achievement
    from app.models.community import Post
    from app.models.incoscore import IncoScoreHistory
    from app.models.user import User

    async def _run():
        async with AsyncSessionLocal() as db:
            user = (
                await db.execute(select(User).where(User.id == user_id))
            ).scalar_one_or_none()
            if not user:
                logger.warning("update_incoscore: user not found %s", user_id)
                return {"status": "user_not_found"}

            achievements = (
                (
                    await db.execute(
                        select(Achievement).where(
                            Achievement.user_id == user_id,
                            Achievement.verified.is_(True),
                        )
                    )
                )
                .scalars()
                .all()
            )

            post_count = int(
                (
                    await db.execute(
                        select(func.count(Post.id)).where(Post.user_id == user_id)
                    )
                ).scalar_one()
                or 0
            )

            from app.models.user import Profile

            profile = (
                await db.execute(select(Profile).where(Profile.user_id == user_id))
            ).scalar_one_or_none()

            domain = _resolve_user_domain(user, profile)
            sc = compute_incoscore(
                list(achievements), domain=domain, community_post_count=post_count
            )
            badges = assign_badges(sc.total, list(achievements))

            history = IncoScoreHistory(
                user_id=user_id,
                total_score=sc.total,
                domain=domain,
                components_json=json.dumps({**sc.to_dict(), "badges": badges}),
            )
            db.add(history)
            await db.commit()
            logger.info("InCoScore updated: user=%s score=%.1f", user_id, sc.total)
            return {"status": "ok", "score": sc.total, "badges": badges}

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        logger.error("update_incoscore failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=2**self.request.retries)
