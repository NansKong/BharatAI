"""
Opportunities API - CRUD + search + filter.
"""
import base64
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.redis import cache_delete_pattern
from app.core.security import get_current_user, require_admin
from app.models.opportunity import Opportunity
from app.workers.ai_tasks import classify_opportunity
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import AnyHttpUrl, BaseModel, Field, field_validator
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)

VALID_DOMAINS = {
    "ai_ds",
    "cs",
    "ece",
    "me",
    "civil",
    "biotech",
    "law",
    "management",
    "finance",
    "humanities",
    "govt",
    "unclassified",
}
CURSOR_DEADLINE_MAX = datetime(9999, 12, 31, tzinfo=timezone.utc)


def _normalize_domain(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized not in VALID_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid domain '{value}'. Allowed: {', '.join(sorted(VALID_DOMAINS))}",
        )
    return normalized


class OpportunityCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    title: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=20)
    institution: Optional[str] = Field(None, max_length=300)
    domain: str = Field(default="unclassified")
    secondary_domain: Optional[str] = Field(None)
    classification_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    deadline: Optional[datetime] = None
    source_url: AnyHttpUrl
    application_link: Optional[AnyHttpUrl] = None
    eligibility: Optional[str] = Field(None, max_length=5000)
    is_verified: bool = False

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain. Allowed: {', '.join(sorted(VALID_DOMAINS))}"
            )
        return normalized

    @field_validator("secondary_domain")
    @classmethod
    def validate_secondary_domain(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in VALID_DOMAINS:
            raise ValueError(
                f"Invalid secondary_domain. Allowed: {', '.join(sorted(VALID_DOMAINS))}"
            )
        return normalized


class OpportunityUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    title: Optional[str] = Field(None, min_length=5, max_length=500)
    description: Optional[str] = Field(None, min_length=20)
    institution: Optional[str] = Field(None, max_length=300)
    domain: Optional[str] = Field(None)
    secondary_domain: Optional[str] = Field(None)
    classification_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    deadline: Optional[datetime] = None
    source_url: Optional[AnyHttpUrl] = None
    application_link: Optional[AnyHttpUrl] = None
    eligibility: Optional[str] = Field(None, max_length=5000)
    is_verified: Optional[bool] = None

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain. Allowed: {', '.join(sorted(VALID_DOMAINS))}"
            )
        return normalized

    @field_validator("secondary_domain")
    @classmethod
    def validate_secondary_domain(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in VALID_DOMAINS:
            raise ValueError(
                f"Invalid secondary_domain. Allowed: {', '.join(sorted(VALID_DOMAINS))}"
            )
        return normalized


class OpportunityResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    title: str
    description: str
    institution: Optional[str]
    domain: str
    secondary_domain: Optional[str]
    classification_confidence: Optional[float]
    deadline: Optional[datetime]
    source_url: str
    application_link: Optional[str]
    eligibility: Optional[str]
    is_active: bool
    is_verified: bool
    source_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class OpportunityListResponse(BaseModel):
    items: list[OpportunityResponse]
    total: int
    limit: int
    next_cursor: Optional[str]


def _encode_cursor(
    deadline_sort: datetime, created_at: datetime, opportunity_id: UUID
) -> str:
    payload = "|".join(
        [
            deadline_sort.isoformat(),
            created_at.isoformat(),
            str(opportunity_id),
        ]
    )
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[datetime, datetime, UUID]:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        deadline_raw, created_raw, opportunity_id_raw = decoded.split("|", 2)
        deadline_sort = datetime.fromisoformat(deadline_raw)
        created_at = datetime.fromisoformat(created_raw)
        opportunity_id = UUID(opportunity_id_raw)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid cursor",
        )

    if deadline_sort.tzinfo is None:
        deadline_sort = deadline_sort.replace(tzinfo=timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return deadline_sort, created_at, opportunity_id


@router.get(
    "",
    response_model=OpportunityListResponse,
    summary="List opportunities",
    description=(
        "Cursor-paginated, filterable list of opportunities. Supports domain, deadline, institution, and keyword filters."
    ),
)
async def list_opportunities(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    institution: Optional[str] = Query(None, description="Filter by institution name"),
    before_deadline: Optional[datetime] = Query(
        None, description="Opportunities with deadline before this date"
    ),
    keyword: Optional[str] = Query(
        None,
        max_length=200,
        description="Keyword search in title/description/institution",
    ),
    cursor: Optional[str] = Query(
        None, description="Opaque cursor from previous response"
    ),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    del current_user

    base_filters = [Opportunity.is_active.is_(True)]

    normalized_domain = _normalize_domain(domain)
    if normalized_domain:
        base_filters.append(Opportunity.domain == normalized_domain)

    if institution:
        base_filters.append(Opportunity.institution.ilike(f"%{institution.strip()}%"))

    if before_deadline:
        base_filters.append(Opportunity.deadline.is_not(None))
        base_filters.append(Opportunity.deadline <= before_deadline)

    if keyword:
        term = f"%{keyword.strip()}%"
        base_filters.append(
            or_(
                Opportunity.title.ilike(term),
                Opportunity.description.ilike(term),
                Opportunity.institution.ilike(term),
            )
        )

    deadline_sort_col = func.coalesce(Opportunity.deadline, CURSOR_DEADLINE_MAX)
    cursor_filter = None
    if cursor:
        cursor_deadline, cursor_created_at, cursor_opportunity_id = _decode_cursor(
            cursor
        )
        cursor_filter = or_(
            deadline_sort_col > cursor_deadline,
            and_(
                deadline_sort_col == cursor_deadline,
                Opportunity.created_at < cursor_created_at,
            ),
            and_(
                deadline_sort_col == cursor_deadline,
                Opportunity.created_at == cursor_created_at,
                Opportunity.id < cursor_opportunity_id,
            ),
        )

    total_where_clause = and_(*base_filters)
    filters = list(base_filters)
    if cursor_filter is not None:
        filters.append(cursor_filter)
    where_clause = and_(*filters)

    total_stmt = select(func.count(Opportunity.id)).where(total_where_clause)
    total = int((await db.execute(total_stmt)).scalar_one() or 0)

    stmt = (
        select(Opportunity)
        .where(where_clause)
        .order_by(
            deadline_sort_col.asc(),
            Opportunity.created_at.desc(),
            Opportunity.id.desc(),
        )
        .limit(limit + 1)
    )

    rows = (await db.execute(stmt)).scalars().all()
    has_more = len(rows) > limit
    page_rows = rows[:limit]

    next_cursor = None
    if has_more and page_rows:
        last = page_rows[-1]
        next_cursor = _encode_cursor(
            deadline_sort=last.deadline or CURSOR_DEADLINE_MAX,
            created_at=last.created_at,
            opportunity_id=last.id,
        )

    items = [OpportunityResponse.model_validate(row) for row in page_rows]
    return OpportunityListResponse(
        items=items, total=total, limit=limit, next_cursor=next_cursor
    )


@router.get(
    "/{opportunity_id}",
    response_model=OpportunityResponse,
    summary="Get opportunity details",
)
async def get_opportunity(
    opportunity_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    del current_user

    stmt = select(Opportunity).where(
        Opportunity.id == opportunity_id,
        Opportunity.is_active.is_(True),
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return OpportunityResponse.model_validate(row)


@router.post(
    "",
    response_model=OpportunityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create opportunity (admin only)",
)
async def create_opportunity(
    body: OpportunityCreateRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del admin

    if body.deadline and body.deadline <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Deadline must be in the future",
        )

    hash_seed = "|".join(
        [
            body.title.strip().lower(),
            body.description.strip().lower(),
            str(body.source_url).strip().lower(),
            (body.institution or "").strip().lower(),
            body.domain,
        ]
    )
    content_hash = hashlib.sha256(hash_seed.encode("utf-8")).hexdigest()

    opportunity = Opportunity(
        title=body.title.strip(),
        description=body.description.strip(),
        institution=body.institution.strip() if body.institution else None,
        domain=body.domain,
        secondary_domain=body.secondary_domain,
        classification_confidence=body.classification_confidence,
        deadline=body.deadline,
        source_url=str(body.source_url),
        application_link=str(body.application_link) if body.application_link else None,
        eligibility=body.eligibility.strip() if body.eligibility else None,
        content_hash=content_hash,
        is_active=True,
        is_verified=body.is_verified,
    )

    db.add(opportunity)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Opportunity already exists or violates a uniqueness constraint",
        )

    try:
        classify_opportunity.delay(str(opportunity.id))
    except Exception:
        logger.warning("Failed to queue classify_opportunity task", exc_info=True)

    try:
        await cache_delete_pattern("feed:*")
    except Exception:
        logger.warning(
            "Failed to invalidate feed cache after opportunity creation", exc_info=True
        )

    return OpportunityResponse.model_validate(opportunity)


@router.put(
    "/{opportunity_id}",
    response_model=OpportunityResponse,
    summary="Update opportunity (admin only)",
)
async def update_opportunity(
    opportunity_id: UUID,
    body: OpportunityUpdateRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del admin

    opportunity = (
        await db.execute(
            select(Opportunity).where(
                Opportunity.id == opportunity_id,
                Opportunity.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )

    updates = body.model_dump(exclude_unset=True)
    if (
        "deadline" in updates
        and updates["deadline"]
        and updates["deadline"] <= datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Deadline must be in the future",
        )

    for key, value in updates.items():
        if key in {"source_url", "application_link"} and value is not None:
            setattr(opportunity, key, str(value))
            continue
        if isinstance(value, str):
            setattr(opportunity, key, value.strip())
            continue
        setattr(opportunity, key, value)

    hash_seed = "|".join(
        [
            (opportunity.title or "").strip().lower(),
            (opportunity.description or "").strip().lower(),
            (opportunity.source_url or "").strip().lower(),
            (opportunity.institution or "").strip().lower(),
            (opportunity.domain or "").strip().lower(),
        ]
    )
    opportunity.content_hash = hashlib.sha256(hash_seed.encode("utf-8")).hexdigest()

    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Opportunity update violates uniqueness constraints",
        )

    try:
        await cache_delete_pattern("feed:*")
    except Exception:
        logger.warning(
            "Failed to invalidate feed cache after opportunity update", exc_info=True
        )

    return OpportunityResponse.model_validate(opportunity)


@router.delete(
    "/{opportunity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete opportunity (admin only)",
)
async def delete_opportunity(
    opportunity_id: UUID,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    del admin

    opportunity = (
        await db.execute(
            select(Opportunity).where(
                Opportunity.id == opportunity_id,
                Opportunity.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )

    opportunity.is_active = False
    await db.flush()
    try:
        await cache_delete_pattern("feed:*")
    except Exception:
        logger.warning(
            "Failed to invalidate feed cache after opportunity delete", exc_info=True
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
