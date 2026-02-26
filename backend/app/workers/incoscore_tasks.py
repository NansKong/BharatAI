"""Celery tasks for InCoScore computation."""
from __future__ import annotations

import json
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="incoscore.update", bind=True, max_retries=3)
def update_incoscore(self, user_id: str) -> dict:
    """
    Recompute InCoScore for a user after an achievement is verified.
    Loads verified achievements, runs compute_incoscore, stores snapshot.
    """
    import asyncio

    from app.ai.incoscore import assign_badges, compute_incoscore
    from app.core.database import AsyncSessionLocal
    from app.models.application import Achievement
    from app.models.community import Post
    from app.models.incoscore import IncoScoreHistory
    from app.models.user import User
    from sqlalchemy import func, select

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

            domain = (
                user.college or "unclassified"
            ).lower()  # use preferred_domain when available
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
