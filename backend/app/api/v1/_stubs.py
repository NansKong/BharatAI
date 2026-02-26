"""Stub routers for applications, community, incoscore, notifications."""
from app.core.security import get_current_user, require_admin
from fastapi import APIRouter, Depends

# ── Applications ──────────────────────────────────────────────────────────────
applications_router = APIRouter()


@applications_router.get("", summary="List my applications")
async def list_applications(current_user=Depends(get_current_user)):
    return {"items": [], "message": "Full implementation in Phase 5"}


@applications_router.post("", status_code=201, summary="Create application")
async def create_application(current_user=Depends(get_current_user)):
    return {"message": "Phase 5"}


# ── Community ─────────────────────────────────────────────────────────────────
community_router = APIRouter()


@community_router.get("/posts", summary="List posts")
async def list_posts(current_user=Depends(get_current_user)):
    return {"items": [], "message": "Full implementation in Phase 6"}


@community_router.get("/groups", summary="List groups")
async def list_groups(current_user=Depends(get_current_user)):
    return {"items": [], "message": "Phase 6"}


# ── InCoScore ─────────────────────────────────────────────────────────────────
incoscore_router = APIRouter()


@incoscore_router.get("/leaderboard/overall", summary="Overall leaderboard")
async def overall_leaderboard(current_user=Depends(get_current_user)):
    return {"items": [], "message": "Full implementation in Phase 6"}


@incoscore_router.get("/me", summary="My InCoScore")
async def my_score(current_user=Depends(get_current_user)):
    return {"score": 0, "rank": None, "message": "Phase 6"}


# ── Notifications ─────────────────────────────────────────────────────────────
notifications_router = APIRouter()


@notifications_router.get("", summary="List my notifications")
async def list_notifications(current_user=Depends(get_current_user)):
    return {"items": [], "unread_count": 0, "message": "Full implementation in Phase 7"}


@notifications_router.post(
    "/{notification_id}/read", summary="Mark notification as read"
)
async def mark_read(notification_id: str, current_user=Depends(get_current_user)):
    return {"message": "Phase 7"}


# ── Admin ─────────────────────────────────────────────────────────────────────
admin_router = APIRouter()


@admin_router.get("/sources", summary="List monitored sources (admin only)")
async def list_sources(admin=Depends(require_admin)):
    return {"items": [], "message": "Full implementation in Phase 3"}


@admin_router.get("/reports", summary="Content moderation queue (admin only)")
async def list_reports(admin=Depends(require_admin)):
    return {"items": [], "message": "Full implementation in Phase 6"}
