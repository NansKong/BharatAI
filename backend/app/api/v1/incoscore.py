"""
InCoScore API — leaderboards, personal score, badges.
Phase 6: Community & InCoScore Engine
"""
from __future__ import annotations

import json
import logging
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)

LEADERBOARD_CACHE_TTL = 600  # 10 minutes


class ScoreResponse(BaseModel):
    user_id: UUID
    total_score: float
    domain: Optional[str]
    components: dict
    badges: list[str]
    computed_at: str


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    name: str
    college: Optional[str]
    total_score: float
    badges: list[str]


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    total: int
    limit: int
    offset: int


async def _get_latest_score(user_id, db: AsyncSession):
    from app.models.incoscore import IncoScoreHistory

    return (
        await db.execute(
            select(IncoScoreHistory)
            .where(IncoScoreHistory.user_id == user_id)
            .order_by(IncoScoreHistory.computed_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def _leaderboard_query(
    db: AsyncSession,
    domain_filter: Optional[str],
    college_filter: Optional[str],
    limit: int,
    offset: int,
) -> LeaderboardResponse:
    from app.models.incoscore import IncoScoreHistory
    from app.models.user import User
    from sqlalchemy import and_

    # Sub-query: latest score per user
    latest_sub = (
        select(
            IncoScoreHistory.user_id,
            func.max(IncoScoreHistory.computed_at).label("latest_at"),
        )
        .group_by(IncoScoreHistory.user_id)
        .subquery()
    )

    filters = []
    if domain_filter:
        filters.append(IncoScoreHistory.domain == domain_filter)

    stmt = (
        select(IncoScoreHistory, User.name, User.college)
        .join(
            latest_sub,
            and_(
                IncoScoreHistory.user_id == latest_sub.c.user_id,
                IncoScoreHistory.computed_at == latest_sub.c.latest_at,
            ),
        )
        .join(User, User.id == IncoScoreHistory.user_id)
        .where(and_(*filters) if filters else True)
    )

    if college_filter:
        stmt = stmt.where(User.college.ilike(f"%{college_filter}%"))

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = int((await db.execute(total_stmt)).scalar_one() or 0)

    rows = (
        await db.execute(
            stmt.order_by(IncoScoreHistory.total_score.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()

    entries = []
    for rank_offset, row in enumerate(rows):
        history, name, college = row[0], row[1], row[2]
        components = json.loads(history.components_json or "{}")
        badges = components.pop("badges", [])
        entries.append(
            LeaderboardEntry(
                rank=offset + rank_offset + 1,
                user_id=history.user_id,
                name=name,
                college=college,
                total_score=history.total_score,
                badges=badges,
            )
        )

    return LeaderboardResponse(entries=entries, total=total, limit=limit, offset=offset)


@router.get("/me", response_model=ScoreResponse, summary="My current InCoScore")
async def get_my_score(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    history = await _get_latest_score(current_user.id, db)
    if not history:
        # No score yet — return zero
        return ScoreResponse(
            user_id=current_user.id,
            total_score=0.0,
            domain=None,
            components={},
            badges=[],
            computed_at="",
        )
    components = json.loads(history.components_json or "{}")
    badges = components.pop("badges", [])
    return ScoreResponse(
        user_id=current_user.id,
        total_score=history.total_score,
        domain=history.domain,
        components=components,
        badges=badges,
        computed_at=history.computed_at.isoformat(),
    )


@router.get(
    "/leaderboard/overall",
    response_model=LeaderboardResponse,
    summary="Overall leaderboard (top 100)",
)
async def overall_leaderboard(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _leaderboard_query(
        db, domain_filter=None, college_filter=None, limit=limit, offset=offset
    )


@router.get(
    "/leaderboard/domain/{domain}",
    response_model=LeaderboardResponse,
    summary="Domain-specific leaderboard",
)
async def domain_leaderboard(
    domain: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _leaderboard_query(
        db, domain_filter=domain, college_filter=None, limit=limit, offset=offset
    )


@router.get(
    "/leaderboard/college/{college}",
    response_model=LeaderboardResponse,
    summary="College-scoped leaderboard",
)
async def college_leaderboard(
    college: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _leaderboard_query(
        db, domain_filter=None, college_filter=college, limit=limit, offset=offset
    )
