"""Personalized opportunity feed endpoint — works with or without authentication."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.ai.embeddings import build_opportunity_text
from app.ai.personalization import (compute_relevance_score,
                                    deadline_urgency_score,
                                    interest_match_score,
                                    skill_similarity_score)
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import cache_get, cache_set
from app.core.security import get_optional_user
from app.models.application import Application
from app.models.opportunity import Opportunity
from app.models.user import Profile
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class FeedItemResponse(BaseModel):
    opportunity_id: UUID
    title: str
    institution: Optional[str]
    domain: str
    deadline: Optional[datetime]
    source_url: Optional[str] = None
    application_link: Optional[str] = None
    eligibility: Optional[str] = None
    description: Optional[str] = None
    relevance_score: float
    is_authenticated: bool = False


class FeedResponse(BaseModel):
    items: list[FeedItemResponse]
    cached: bool = False
    cold_start: bool = False
    is_authenticated: bool = False


async def _engagement_score(
    db: AsyncSession, user_id: UUID, opportunity_domain: str
) -> float:
    total_stmt = select(func.count(Application.id)).where(
        Application.user_id == user_id
    )
    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    if total == 0:
        return 0.0

    matched_stmt = (
        select(func.count(Application.id))
        .join(Opportunity, Opportunity.id == Application.opportunity_id)
        .where(
            Application.user_id == user_id,
            Opportunity.domain == opportunity_domain,
        )
    )
    matched = int((await db.execute(matched_stmt)).scalar_one() or 0)
    return min(1.0, matched / max(1, total))


def _serialize_items(items: list[FeedItemResponse]) -> list[dict]:
    return [
        {
            "opportunity_id": str(item.opportunity_id),
            "title": item.title,
            "institution": item.institution,
            "domain": item.domain,
            "deadline": item.deadline.isoformat() if item.deadline else None,
            "source_url": item.source_url,
            "application_link": item.application_link,
            "eligibility": item.eligibility,
            "description": item.description,
            "relevance_score": item.relevance_score,
            "is_authenticated": item.is_authenticated,
        }
        for item in items
    ]


@router.get(
    "",
    response_model=FeedResponse,
    summary="Get opportunity feed (public or personalized)",
    description=(
        "Returns opportunities. **Authentication is optional.**\n\n"
        "- **Unauthenticated**: Returns recent active opportunities, sorted by deadline. "
        "Full details (description, links) included; applying requires login.\n"
        "- **Authenticated**: Returns AI-personalized feed ranked by user profile match.\n\n"
        "**Caching**: Results cached in Redis for 5 minutes per user/anonymous key."
    ),
)
async def get_feed(
    limit: int = Query(20, ge=1, le=100, description="Max opportunities to return"),
    domain: Optional[str] = Query(
        None, description="Filter by domain code (e.g. cs, ai_ds)"
    ),
    current_user=Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    is_authenticated = current_user is not None

    # Cache key: per-user if logged in, shared public key otherwise
    cache_key = f"feed:{'user:' + str(current_user.id) if is_authenticated else 'public'}:{limit}:{domain or 'all'}"
    cached_payload = await cache_get(cache_key)
    if cached_payload:
        payload = json.loads(cached_payload)
        items = [FeedItemResponse(**item) for item in payload.get("items", [])]
        return FeedResponse(
            items=items,
            cached=True,
            cold_start=bool(payload.get("cold_start", False)),
            is_authenticated=is_authenticated,
        )

    # Build base query with optional domain filter
    stmt = (
        select(Opportunity)
        .where(Opportunity.is_active.is_(True))
        .order_by(
            Opportunity.deadline.is_(None),
            Opportunity.deadline.asc(),
            Opportunity.created_at.desc(),
        )
        .limit(max(100, limit * 4))
    )
    if domain:
        stmt = stmt.where(Opportunity.domain == domain)

    opportunities = (await db.execute(stmt)).scalars().all()

    cold_start = True
    items: list[FeedItemResponse] = []

    if not is_authenticated:
        # Public / anonymous: serve recent opportunities, cold-start style
        for opp in opportunities[:limit]:
            items.append(_make_item(opp, 0.0, is_authenticated=False))
    else:
        # Authenticated: try to personalise
        profile = (
            await db.execute(select(Profile).where(Profile.user_id == current_user.id))
        ).scalar_one_or_none()

        cold_start = not profile or (
            not (profile.skills or [])
            and not (profile.interests or [])
            and not (profile.embedding_vector or [])
        )

        if cold_start:
            for opp in opportunities[:limit]:
                items.append(_make_item(opp, 0.0, is_authenticated=True))
        else:
            scored: list[tuple[float, Opportunity]] = []
            for opp in opportunities:
                opp_text = build_opportunity_text(
                    title=opp.title,
                    description=opp.description,
                    domain=opp.domain,
                    institution=opp.institution,
                )
                interest = interest_match_score(
                    profile_embedding=profile.embedding_vector or [],
                    opportunity_embedding=opp.embedding_vector or [],
                    interests=profile.interests or [],
                    opportunity_text=opp_text,
                )
                skills = skill_similarity_score(profile.skills or [], opp_text)
                engagement = await _engagement_score(db, current_user.id, opp.domain)
                urgency = deadline_urgency_score(opp.deadline)
                score = compute_relevance_score(
                    interest_match=interest,
                    skill_similarity=skills,
                    engagement=engagement,
                    deadline_urgency=urgency,
                )
                scored.append((score, opp))

            scored.sort(key=lambda x: x[0], reverse=True)
            for score, opp in scored[:limit]:
                items.append(_make_item(opp, score, is_authenticated=True))

    ttl = settings.REDIS_CACHE_TTL_FEED if is_authenticated else 300  # 5 min for public
    await cache_set(
        cache_key,
        json.dumps({"items": _serialize_items(items), "cold_start": cold_start}),
        ttl,
    )
    return FeedResponse(
        items=items,
        cached=False,
        cold_start=cold_start,
        is_authenticated=is_authenticated,
    )


def _make_item(
    opp: Opportunity, score: float, *, is_authenticated: bool
) -> FeedItemResponse:
    return FeedItemResponse(
        opportunity_id=opp.id,
        title=opp.title,
        institution=opp.institution,
        domain=opp.domain,
        deadline=opp.deadline,
        source_url=opp.source_url,
        application_link=opp.application_link,
        eligibility=opp.eligibility,
        description=opp.description,
        relevance_score=score,
        is_authenticated=is_authenticated,
    )
