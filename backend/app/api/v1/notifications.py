"""
Notifications API — in-app notification inbox + mark-read.
Phase 7: Notification Engine
"""
from __future__ import annotations

import logging
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    message: str
    payload: dict
    read: bool
    created_at: str

    @classmethod
    def from_orm(cls, n) -> "NotificationResponse":
        import json

        return cls(
            id=n.id,
            type=n.type,
            title=n.title,
            message=n.message,
            payload=json.loads(n.payload_json or "{}"),
            read=n.read,
            created_at=n.created_at.isoformat(),
        )


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="List notifications",
    description=(
        "Returns the current user's notifications, newest first. "
        "Use `unread_only=true` to show only unread items. "
        "Supports `limit`/`offset` pagination."
    ),
    responses={401: {"description": "Missing or invalid access token"}},
)
async def list_notifications(
    unread_only: bool = Query(
        False, description="If true, return only unread notifications"
    ),
    limit: int = Query(20, ge=1, le=100, description="Max results (1–100)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.incoscore import Notification

    filters = [Notification.user_id == current_user.id]
    if unread_only:
        filters.append(Notification.read.is_(False))
    from sqlalchemy import and_

    rows = (
        (
            await db.execute(
                select(Notification)
                .where(and_(*filters))
                .order_by(Notification.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return [NotificationResponse.from_orm(n) for n in rows]


@router.get(
    "/count",
    summary="Unread notification count",
    description="Returns the number of unread notifications for the notification bell badge.",
    responses={401: {"description": "Missing or invalid access token"}},
)
async def unread_count(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.incoscore import Notification
    from sqlalchemy import func

    count = int(
        (
            await db.execute(
                select(func.count(Notification.id)).where(
                    Notification.user_id == current_user.id,
                    Notification.read.is_(False),
                )
            )
        ).scalar_one()
        or 0
    )
    return {"unread_count": count}


@router.post(
    "/{notification_id}/read",
    summary="Mark notification as read",
    description="Marks a single notification as read. Returns 404 if the notification does not belong to the current user.",
    responses={
        401: {"description": "Missing or invalid access token"},
        404: {"description": "Notification not found"},
    },
)
async def mark_read(
    notification_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.incoscore import Notification

    notif = (
        await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read = True
    await db.commit()
    return {"id": str(notification_id), "read": True}


@router.post(
    "/read-all",
    summary="Mark all notifications as read",
    description="Bulk-marks every unread notification for the current user as read in a single operation.",
    responses={401: {"description": "Missing or invalid access token"}},
)
async def mark_all_read(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.incoscore import Notification

    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.read.is_(False))
        .values(read=True)
    )
    await db.commit()
    return {"message": "All notifications marked as read"}
