"""AI Celery tasks for classification and personalization pipelines."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import redis.asyncio as aioredis
from app.ai.classifier import get_domain_classifier
from app.ai.embeddings import (build_opportunity_text, build_profile_text,
                               generate_embedding)
from app.core.config import settings
from app.core.database import AsyncSessionLocal, close_database
from app.models.opportunity import Opportunity
from app.models.user import Profile, User
from app.workers.celery_app import celery_app
from celery.exceptions import MaxRetriesExceededError, Retry
from prometheus_client import Histogram
from sqlalchemy import select

logger = logging.getLogger(__name__)

CLASSIFICATION_LATENCY_SECONDS = Histogram(
    "classification_latency_seconds",
    "Latency of opportunity domain classification task",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)


def _backoff_seconds(retries: int) -> int:
    return min(2 ** max(1, retries + 1), 8)


async def _run_with_db_cleanup(coro):
    try:
        return await coro
    finally:
        await close_database()


async def _invalidate_feed_cache(user_id: str | None = None) -> None:
    redis = await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        if user_id:
            keys = await redis.keys(f"feed:{user_id}:*")
            if keys:
                await redis.delete(*keys)
            return

        keys = await redis.keys("feed:*")
        if keys:
            await redis.delete(*keys)
    finally:
        await redis.aclose()


async def _classify_opportunity_async(opportunity_id: str) -> dict:
    try:
        parsed_id = UUID(opportunity_id)
    except ValueError:
        return {"status": "invalid_id", "opportunity_id": opportunity_id}

    classifier = get_domain_classifier()

    async with AsyncSessionLocal() as db:
        opportunity = (
            await db.execute(
                select(Opportunity).where(
                    Opportunity.id == parsed_id,
                    Opportunity.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not opportunity:
            return {"status": "not_found", "opportunity_id": opportunity_id}

        text = build_opportunity_text(
            title=opportunity.title,
            description=opportunity.description,
            domain=opportunity.domain,
            institution=opportunity.institution,
        )
        result = classifier.classify(text)

        opportunity.domain = result.primary_domain
        opportunity.secondary_domain = result.secondary_domain
        opportunity.classification_confidence = result.confidence
        if not opportunity.embedding_vector:
            opportunity.embedding_vector = generate_embedding(text)

        await db.commit()

    await _invalidate_feed_cache()
    return {
        "status": "classified",
        "opportunity_id": opportunity_id,
        "domain": result.primary_domain,
        "secondary_domain": result.secondary_domain,
        "confidence": result.confidence,
    }


async def _generate_user_embedding_async(user_id: str) -> dict:
    try:
        parsed_id = UUID(user_id)
    except ValueError:
        return {"status": "invalid_id", "user_id": user_id}

    async with AsyncSessionLocal() as db:
        user = (
            await db.execute(select(User).where(User.id == parsed_id))
        ).scalar_one_or_none()
        if not user:
            return {"status": "not_found", "user_id": user_id}

        profile = (
            await db.execute(select(Profile).where(Profile.user_id == parsed_id))
        ).scalar_one_or_none()
        if not profile:
            profile = Profile(user_id=parsed_id)
            db.add(profile)
            await db.flush()

        profile_text = build_profile_text(
            bio=profile.bio,
            skills=profile.skills or [],
            interests=profile.interests or [],
        )
        if not profile_text:
            return {"status": "skipped_no_text", "user_id": user_id}

        profile.embedding_vector = generate_embedding(profile_text)
        profile.embedding_updated_at = datetime.now(timezone.utc)
        await db.commit()

    await _invalidate_feed_cache(user_id=user_id)
    return {"status": "updated", "user_id": user_id}


async def _rebuild_faiss_index_async() -> dict:
    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(Profile.user_id, Profile.embedding_vector).where(
                    Profile.embedding_vector.is_not(None)
                )
            )
        ).all()

    vectors = [(str(user_id), vector) for user_id, vector in rows if vector]
    if not vectors:
        return {"status": "skipped", "reason": "no_vectors"}

    try:
        import faiss  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return {"status": "skipped", "reason": "faiss_unavailable"}

    dim = len(vectors[0][1])
    matrix = np.array([vector for _, vector in vectors], dtype="float32")
    faiss.normalize_L2(matrix)

    index = faiss.IndexFlatIP(dim)
    index.add(matrix)

    index_path = Path(settings.FAISS_INDEX_PATH)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))

    metadata_path = index_path.with_suffix(index_path.suffix + ".meta.json")
    metadata_path.write_text(
        json.dumps({"user_ids": [user_id for user_id, _ in vectors]}), encoding="utf-8"
    )

    return {"status": "rebuilt", "vectors": len(vectors), "index_path": str(index_path)}


@celery_app.task(
    name="app.workers.ai_tasks.classify_opportunity", bind=True, max_retries=3
)
def classify_opportunity(self, opportunity_id: str):
    timer = CLASSIFICATION_LATENCY_SECONDS.time()
    try:
        result = asyncio.run(
            _run_with_db_cleanup(_classify_opportunity_async(opportunity_id))
        )
        timer.observe_duration()
        return result
    except Retry:
        raise
    except Exception as exc:
        timer.observe_duration()
        countdown = _backoff_seconds(self.request.retries)
        logger.exception(
            "Failed to classify opportunity", extra={"opportunity_id": opportunity_id}
        )
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            return {
                "status": "failed",
                "opportunity_id": opportunity_id,
                "error": str(exc),
            }


@celery_app.task(
    name="app.workers.ai_tasks.generate_embeddings", bind=True, max_retries=3
)
def generate_embeddings(self, user_id: str):
    try:
        return asyncio.run(
            _run_with_db_cleanup(_generate_user_embedding_async(user_id))
        )
    except Retry:
        raise
    except Exception as exc:
        countdown = _backoff_seconds(self.request.retries)
        logger.exception("Failed to generate embeddings", extra={"user_id": user_id})
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            return {"status": "failed", "user_id": user_id, "error": str(exc)}


@celery_app.task(
    name="app.workers.ai_tasks.rebuild_faiss_index", bind=True, max_retries=1
)
def rebuild_faiss_index(self):
    try:
        return asyncio.run(_run_with_db_cleanup(_rebuild_faiss_index_async()))
    except Exception as exc:
        logger.exception("Failed to rebuild FAISS index")
        if self.request.retries >= self.max_retries:
            return {"status": "failed", "error": str(exc)}
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.workers.ai_tasks.update_incoscore", bind=True)
def update_incoscore(self, user_id: str):
    logger.info(
        "InCoScore update task is scheduled for Phase 6", extra={"user_id": user_id}
    )
    return {"status": "deferred_phase_6", "user_id": user_id}
