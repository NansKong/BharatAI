"""
Applications API — CRUD, status state machine, checklist, autofill.
Phase 5: Application Assistance Engine
"""
from __future__ import annotations

import json
import logging
from typing import Optional
from uuid import UUID

from app.ai.application_ai import generate_autofill, generate_checklist
from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import get_current_user
from app.models.application import Application
from app.models.autofill_log import AutofillLog
from app.models.opportunity import Opportunity
from app.models.user import Profile
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# State machine — allowed transitions
# ---------------------------------------------------------------------------
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"submitted", "withdrawn"},
    "submitted": {"accepted", "rejected", "withdrawn"},
    "accepted": set(),
    "rejected": set(),
    "withdrawn": set(),
}

AUTOFILL_RATE_LIMIT = 20  # max requests per hour per user
AUTOFILL_RL_TTL = 3600  # seconds (1 hour)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class ApplicationCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    opportunity_id: UUID
    notes: Optional[str] = Field(default=None, max_length=2000)


class ApplicationStatusUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    status: str = Field(..., description="New status for the application")


class ApplicationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    opportunity_id: UUID
    status: str
    notes: Optional[str]
    applied_at: Optional[str]
    created_at: str
    opportunity_title: Optional[str] = None

    @classmethod
    def from_orm_with_title(
        cls, app: Application, title: Optional[str] = None
    ) -> "ApplicationResponse":
        return cls(
            id=app.id,
            user_id=app.user_id,
            opportunity_id=app.opportunity_id,
            status=app.status,
            notes=app.notes,
            applied_at=app.applied_at.isoformat() if app.applied_at else None,
            created_at=app.created_at.isoformat(),
            opportunity_title=title,
        )


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int
    limit: int
    offset: int


class ChecklistResponse(BaseModel):
    items: list[str]


class AutofillResponse(BaseModel):
    fields: dict[str, str]
    consent_used: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_application_owned(
    application_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> Application:
    """Return application if it belongs to user, else 404."""
    app = (
        await db.execute(
            select(Application).where(
                Application.id == application_id,
                Application.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    return app


async def _get_opportunity_or_404(
    opportunity_id: UUID, db: AsyncSession
) -> Opportunity:
    opp = (
        await db.execute(
            select(Opportunity).where(
                Opportunity.id == opportunity_id,
                Opportunity.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return opp


async def _check_autofill_rate_limit(user_id: str, redis) -> None:
    """Raise 429 if user has exceeded 20 autofill requests in the last hour."""
    key = f"autofill_rl:{user_id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, AUTOFILL_RL_TTL)
    if count > AUTOFILL_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Autofill rate limit exceeded ({AUTOFILL_RATE_LIMIT} requests/hour). Try again later.",
            headers={"Retry-After": str(AUTOFILL_RL_TTL)},
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create application",
    description="Create a new application for an opportunity. Students only. One application per opportunity.",
    tags=["applications"],
)
async def create_application(
    body: ApplicationCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify opportunity exists
    opp = await _get_opportunity_or_404(body.opportunity_id, db)

    app = Application(
        user_id=current_user.id,
        opportunity_id=body.opportunity_id,
        status="draft",
        notes=body.notes,
    )
    db.add(app)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this opportunity.",
        )

    return ApplicationResponse.from_orm_with_title(app, title=opp.title)


@router.get(
    "",
    response_model=ApplicationListResponse,
    summary="List my applications",
    description="List the current user's applications, optionally filtered by status.",
    tags=["applications"],
)
async def list_applications(
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [Application.user_id == current_user.id]
    if status_filter:
        allowed = {"draft", "submitted", "accepted", "rejected", "withdrawn"}
        if status_filter not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status. Allowed: {', '.join(sorted(allowed))}",
            )
        filters.append(Application.status == status_filter)

    from sqlalchemy import and_, func

    total = int(
        (
            await db.execute(select(func.count(Application.id)).where(and_(*filters)))
        ).scalar_one()
        or 0
    )

    rows = (
        (
            await db.execute(
                select(Application)
                .where(and_(*filters))
                .order_by(Application.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )

    # Bulk fetch opportunity titles
    opp_ids = list({r.opportunity_id for r in rows})
    opp_map: dict[UUID, str] = {}
    if opp_ids:
        opp_rows = (
            await db.execute(
                select(Opportunity.id, Opportunity.title).where(
                    Opportunity.id.in_(opp_ids)
                )
            )
        ).all()
        opp_map = {row.id: row.title for row in opp_rows}

    items = [
        ApplicationResponse.from_orm_with_title(r, title=opp_map.get(r.opportunity_id))
        for r in rows
    ]
    return ApplicationListResponse(items=items, total=total, limit=limit, offset=offset)


@router.put(
    "/{application_id}/status",
    response_model=ApplicationResponse,
    summary="Update application status",
    description=(
        "Update the status of an application. Enforces a valid state machine: "
        "draft→submitted, submitted→accepted/rejected, draft/submitted→withdrawn. "
        "Admin can update any application; students can only update their own."
    ),
    tags=["applications"],
)
async def update_application_status(
    application_id: UUID,
    body: ApplicationStatusUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone

    new_status = body.status.strip().lower()
    if new_status not in _ALLOWED_TRANSITIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{new_status}'. Allowed: {', '.join(_ALLOWED_TRANSITIONS)}",
        )

    # Admins can update any application; students only their own
    if current_user.role == "admin":
        app = (
            await db.execute(
                select(Application).where(Application.id == application_id)
            )
        ).scalar_one_or_none()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )
    else:
        app = await _get_application_owned(application_id, current_user.id, db)

    # Validate state machine transition
    allowed_next = _ALLOWED_TRANSITIONS.get(app.status, set())
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid status transition: '{app.status}' → '{new_status}'. "
                f"Allowed next states: {', '.join(sorted(allowed_next)) or 'none'}"
            ),
        )

    app.status = new_status
    if new_status == "submitted":
        app.applied_at = datetime.now(timezone.utc)
    await db.flush()

    opp = (
        await db.execute(
            select(Opportunity).where(Opportunity.id == app.opportunity_id)
        )
    ).scalar_one_or_none()
    return ApplicationResponse.from_orm_with_title(
        app, title=opp.title if opp else None
    )


@router.get(
    "/{application_id}/checklist",
    response_model=ChecklistResponse,
    summary="Get AI-generated application checklist",
    description="Returns a checklist of preparation steps based on the opportunity's eligibility text.",
    tags=["applications"],
)
async def get_checklist(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app = await _get_application_owned(application_id, current_user.id, db)
    opp = await _get_opportunity_or_404(app.opportunity_id, db)

    items = generate_checklist(opp.eligibility)
    return ChecklistResponse(items=items)


@router.get(
    "/{application_id}/autofill",
    response_model=AutofillResponse,
    summary="Get autofill suggestions from profile",
    description=(
        "Returns form field suggestions from the user's profile. "
        "Requires consent_to_autofill=true on profile. Rate-limited to 20 requests/hour."
    ),
    tags=["applications"],
)
async def get_autofill(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    app = await _get_application_owned(application_id, current_user.id, db)
    opp = await _get_opportunity_or_404(app.opportunity_id, db)

    # Consent gate
    profile = (
        await db.execute(select(Profile).where(Profile.user_id == current_user.id))
    ).scalar_one_or_none()

    if not profile or not profile.consent_to_autofill:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Autofill requires your explicit consent. "
                "Set consent_to_autofill=true in your profile settings first."
            ),
        )

    # Rate limit check
    await _check_autofill_rate_limit(str(current_user.id), redis)

    # Generate suggestions
    fields = generate_autofill(current_user, profile)

    # Compliance log
    log = AutofillLog(
        user_id=current_user.id,
        opportunity_id=opp.id,
        fields_suggested=json.dumps(list(fields.keys())),
    )
    db.add(log)
    await db.flush()

    return AutofillResponse(fields=fields, consent_used=True)
