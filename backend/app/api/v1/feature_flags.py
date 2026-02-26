"""
Feature Flags API — admin CRUD + public evaluation endpoint.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.feature_flags import (get_all_flags, invalidate_flags_cache,
                                    is_enabled)
from app.core.security import get_current_user, require_admin
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────


class FlagCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field("", max_length=500)
    is_enabled: bool = False
    rollout_percentage: float = Field(0.0, ge=0.0, le=1.0)
    target_user_ids: list[str] = []


class FlagUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    description: Optional[str] = Field(None, max_length=500)
    is_enabled: Optional[bool] = None
    rollout_percentage: Optional[float] = Field(None, ge=0.0, le=1.0)
    target_user_ids: Optional[list[str]] = None


class FlagResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    name: str
    description: str
    is_enabled: bool
    rollout_percentage: float
    target_user_ids: list
    created_at: datetime
    updated_at: datetime


class FlagEvaluationResponse(BaseModel):
    flag_name: str
    result: bool


class FlagAnalyticsResponse(BaseModel):
    flag_name: str
    total_evaluations: int
    true_count: int
    false_count: int
    true_percentage: float


# ── Admin Endpoints ──────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=list[FlagResponse],
    summary="List all feature flags",
)
async def list_flags(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.feature_flag import FeatureFlag

    result = await db.execute(select(FeatureFlag).order_by(FeatureFlag.name))
    return result.scalars().all()


@router.post(
    "",
    response_model=FlagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a feature flag",
)
async def create_flag(
    body: FlagCreateRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.feature_flag import FeatureFlag

    existing = await db.execute(
        select(FeatureFlag).where(FeatureFlag.name == body.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail=f"Flag '{body.name}' already exists"
        )

    flag = FeatureFlag(
        name=body.name,
        description=body.description,
        is_enabled=body.is_enabled,
        rollout_percentage=body.rollout_percentage,
        target_user_ids=body.target_user_ids,
    )
    db.add(flag)
    await db.flush()
    await invalidate_flags_cache()
    return flag


@router.patch(
    "/{flag_name}",
    response_model=FlagResponse,
    summary="Update a feature flag",
)
async def update_flag(
    flag_name: str,
    body: FlagUpdateRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.feature_flag import FeatureFlag

    result = await db.execute(select(FeatureFlag).where(FeatureFlag.name == flag_name))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(flag, field, value)

    await db.flush()
    await invalidate_flags_cache()
    return flag


@router.delete(
    "/{flag_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a feature flag",
)
async def delete_flag(
    flag_name: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.feature_flag import FeatureFlag

    result = await db.execute(select(FeatureFlag).where(FeatureFlag.name == flag_name))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")

    await db.delete(flag)
    await invalidate_flags_cache()


# ── Evaluation Endpoint (for frontend) ──────────────────────────────────────


@router.get(
    "/evaluate/{flag_name}",
    response_model=FlagEvaluationResponse,
    summary="Evaluate a flag for the current user",
)
async def evaluate_flag(
    flag_name: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await is_enabled(flag_name, db, user_id=str(current_user.id))
    return FlagEvaluationResponse(flag_name=flag_name, result=result)


@router.get(
    "/evaluate",
    response_model=dict[str, bool],
    summary="Evaluate all flags for the current user",
)
async def evaluate_all_flags(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    all_flags = await get_all_flags(db)
    results = {}
    for name in all_flags:
        results[name] = await is_enabled(
            name, db, user_id=str(current_user.id), log_evaluation=False
        )
    return results


# ── Analytics Endpoint ───────────────────────────────────────────────────────


@router.get(
    "/{flag_name}/analytics",
    response_model=FlagAnalyticsResponse,
    summary="Get flag evaluation analytics",
)
async def flag_analytics(
    flag_name: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.feature_flag import FlagEvaluation

    total_stmt = select(func.count(FlagEvaluation.id)).where(
        FlagEvaluation.flag_name == flag_name
    )
    total = int((await db.execute(total_stmt)).scalar_one() or 0)

    true_stmt = select(func.count(FlagEvaluation.id)).where(
        FlagEvaluation.flag_name == flag_name,
        FlagEvaluation.result == True,
    )
    true_count = int((await db.execute(true_stmt)).scalar_one() or 0)

    false_count = total - true_count
    true_pct = (true_count / total * 100) if total > 0 else 0.0

    return FlagAnalyticsResponse(
        flag_name=flag_name,
        total_evaluations=total,
        true_count=true_count,
        false_count=false_count,
        true_percentage=round(true_pct, 2),
    )
