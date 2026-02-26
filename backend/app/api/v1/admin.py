"""Admin API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import require_admin
from app.models.opportunity import MonitoredSource, Opportunity
from app.workers.scrape_tasks import scrape_single_source
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import AnyHttpUrl, BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class MonitoredSourceCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=3, max_length=300)
    url: AnyHttpUrl
    type: str = Field(default="static")
    interval_minutes: int = Field(default=30, ge=15)
    active: bool = True

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"static", "dynamic"}:
            raise ValueError("type must be either 'static' or 'dynamic'")
        return normalized


class MonitoredSourceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    url: str
    type: str
    interval_minutes: int
    active: bool
    failure_count: int
    last_error: Optional[str]


class MonitoredSourceListResponse(BaseModel):
    items: list[MonitoredSourceResponse]
    total: int
    page: int
    page_size: int


class SourceTriggerResponse(BaseModel):
    status: str
    source_id: UUID
    task_id: str


class UnclassifiedOpportunityResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    title: str
    institution: Optional[str]
    source_url: str
    classification_confidence: Optional[float]
    created_at: datetime


class UnclassifiedOpportunityListResponse(BaseModel):
    items: list[UnclassifiedOpportunityResponse]
    total: int
    page: int
    page_size: int


def queue_scrape_single_source(source_id: str):
    """
    Queue source scraping task.
    Kept as a plain helper so tests can patch this function directly
    without relying on Celery Task method monkeypatch behavior.
    """
    return scrape_single_source.delay(source_id)


@router.get(
    "/sources",
    response_model=MonitoredSourceListResponse,
    summary="List monitored sources (admin only)",
)
async def list_sources(
    active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del admin

    filters = []
    if active is not None:
        filters.append(MonitoredSource.active.is_(active))

    count_stmt = select(func.count(MonitoredSource.id))
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = int((await db.execute(count_stmt)).scalar_one() or 0)

    stmt = (
        select(MonitoredSource)
        .order_by(MonitoredSource.active.desc(), MonitoredSource.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if filters:
        stmt = stmt.where(*filters)

    rows = (await db.execute(stmt)).scalars().all()
    items = [MonitoredSourceResponse.model_validate(row) for row in rows]
    return MonitoredSourceListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post(
    "/sources",
    response_model=MonitoredSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create monitored source (admin only)",
)
async def create_source(
    body: MonitoredSourceCreateRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del admin

    source = MonitoredSource(
        name=body.name.strip(),
        url=str(body.url),
        type=body.type,
        interval_minutes=body.interval_minutes,
        active=body.active,
        failure_count=0,
    )
    db.add(source)

    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A source with this URL already exists",
        )

    return MonitoredSourceResponse.model_validate(source)


@router.post(
    "/sources/{source_id}/trigger",
    response_model=SourceTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger source scrape manually (admin only)",
)
async def trigger_source_scrape(
    source_id: UUID,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del admin

    source = (
        await db.execute(select(MonitoredSource).where(MonitoredSource.id == source_id))
    ).scalar_one_or_none()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source not found"
        )

    try:
        task = queue_scrape_single_source(str(source.id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to queue scrape task",
        )
    return SourceTriggerResponse(status="queued", source_id=source.id, task_id=task.id)


@router.get(
    "/opportunities/unclassified",
    response_model=UnclassifiedOpportunityListResponse,
    summary="List unclassified opportunities (admin review queue)",
)
async def list_unclassified_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del admin

    filters = [Opportunity.is_active.is_(True), Opportunity.domain == "unclassified"]

    total_stmt = select(func.count(Opportunity.id)).where(*filters)
    total = int((await db.execute(total_stmt)).scalar_one() or 0)

    rows = (
        (
            await db.execute(
                select(Opportunity)
                .where(*filters)
                .order_by(Opportunity.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )

    items = [UnclassifiedOpportunityResponse.model_validate(row) for row in rows]
    return UnclassifiedOpportunityListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/reports", summary="Content moderation queue (admin only)")
async def list_reports(admin=Depends(require_admin)):
    del admin
    return {"items": [], "message": "Full implementation in Phase 6"}
