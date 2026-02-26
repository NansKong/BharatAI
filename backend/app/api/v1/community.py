"""
Community API — Posts, Groups, Moderation, Achievements, Peer Endorsements.
Phase 6: Community & InCoScore Engine
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.application import Achievement
from app.models.community import Comment, Group, GroupMember, Post
from app.models.post_like import PostLike
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"https?://\S+", re.I)
REPORT_AUTO_FLAG_THRESHOLD = 3
ACHIEVEMENT_VELOCITY_LIMIT = 5  # max submissions per 24h per user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _check_spam(content: str) -> None:
    urls = _URL_RE.findall(content)
    if len(urls) > 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Post contains too many URLs (max 5). Spam prevention.",
        )


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class PostCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    content: str = Field(..., min_length=1, max_length=2000)
    group_id: Optional[UUID] = None
    image_url: Optional[str] = Field(None, max_length=2048)


class PostResponse(BaseModel):
    id: UUID
    user_id: UUID
    group_id: Optional[UUID]
    content: str
    image_url: Optional[str]
    likes_count: int
    comments_count: int
    is_flagged: bool
    created_at: str

    @classmethod
    def from_orm(cls, p: Post) -> "PostResponse":
        return cls(
            id=p.id,
            user_id=p.user_id,
            group_id=p.group_id,
            content=p.content,
            image_url=p.image_url,
            likes_count=p.likes_count,
            comments_count=p.comments_count,
            is_flagged=p.is_flagged,
            created_at=p.created_at.isoformat(),
        )


class CommentCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    content: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    user_id: UUID
    content: str
    created_at: str

    @classmethod
    def from_orm(cls, c: Comment) -> "CommentResponse":
        return cls(
            id=c.id,
            post_id=c.post_id,
            user_id=c.user_id,
            content=c.content,
            created_at=c.created_at.isoformat(),
        )


class GroupCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    name: str = Field(..., min_length=3, max_length=300)
    type: str = Field(default="general")
    description: Optional[str] = Field(None, max_length=1000)
    domain: Optional[str] = None
    college: Optional[str] = Field(None, max_length=300)


class GroupResponse(BaseModel):
    id: UUID
    name: str
    type: str
    description: Optional[str]
    domain: Optional[str]
    college: Optional[str]
    member_count: int

    @classmethod
    def from_orm(cls, g: Group) -> "GroupResponse":
        return cls(
            id=g.id,
            name=g.name,
            type=g.type,
            description=g.description,
            domain=g.domain,
            college=g.college,
            member_count=g.member_count,
        )


class AchievementCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    type: str = Field(
        ...,
        description="hackathon | internship | publication | competition | certification | coding | community | other",
    )
    title: str = Field(..., min_length=3, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    proof_url: Optional[str] = Field(None, max_length=2048)
    event_date: Optional[datetime] = None
    points_claimed: Optional[int] = Field(None, ge=0, le=100)


class AchievementResponse(BaseModel):
    id: UUID
    type: str
    title: str
    description: Optional[str]
    proof_url: Optional[str]
    verified: bool
    created_at: str

    @classmethod
    def from_orm(cls, a: Achievement) -> "AchievementResponse":
        return cls(
            id=a.id,
            type=a.type,
            title=a.title,
            description=a.description,
            proof_url=a.proof_url,
            verified=a.verified,
            created_at=a.created_at.isoformat(),
        )


class AchievementVerifyRequest(BaseModel):
    model_config = {"extra": "forbid"}
    verified: bool
    rejection_reason: Optional[str] = Field(None, max_length=500)


# ---------------------------------------------------------------------------
# Post Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/posts", response_model=PostResponse, status_code=201, summary="Create post"
)
async def create_post(
    body: PostCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = _strip_html(body.content)
    _check_spam(content)

    if body.group_id:
        grp = (
            await db.execute(
                select(Group).where(
                    Group.id == body.group_id, Group.is_active.is_(True)
                )
            )
        ).scalar_one_or_none()
        if not grp:
            raise HTTPException(status_code=404, detail="Group not found")

    post = Post(
        user_id=current_user.id,
        group_id=body.group_id,
        content=content,
        image_url=body.image_url,
    )
    db.add(post)
    await db.flush()
    return PostResponse.from_orm(post)


@router.get(
    "/posts",
    response_model=list[PostResponse],
    summary="Paginated global/group post feed",
)
async def list_posts(
    group_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [Post.is_hidden.is_(False)]
    if group_id:
        filters.append(Post.group_id == group_id)

    rows = (
        (
            await db.execute(
                select(Post)
                .where(and_(*filters))
                .order_by(Post.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return [PostResponse.from_orm(p) for p in rows]


@router.post("/posts/{post_id}/like", summary="Toggle like on a post (idempotent)")
async def toggle_like(
    post_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post = (
        await db.execute(select(Post).where(Post.id == post_id))
    ).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = (
        await db.execute(
            select(PostLike).where(
                PostLike.user_id == current_user.id, PostLike.post_id == post_id
            )
        )
    ).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        post.likes_count = max(0, post.likes_count - 1)
        liked = False
    else:
        db.add(PostLike(user_id=current_user.id, post_id=post_id))
        post.likes_count += 1
        liked = True

    await db.flush()
    return {"liked": liked, "likes_count": post.likes_count}


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=201,
    summary="Add comment",
)
async def add_comment(
    post_id: UUID,
    body: CommentCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post = (
        await db.execute(select(Post).where(Post.id == post_id))
    ).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = Comment(
        post_id=post_id, user_id=current_user.id, content=_strip_html(body.content)
    )
    db.add(comment)
    post.comments_count += 1
    await db.flush()
    return CommentResponse.from_orm(comment)


@router.get(
    "/posts/{post_id}/comments",
    response_model=list[CommentResponse],
    summary="List comments on a post",
)
async def list_comments(
    post_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        (
            await db.execute(
                select(Comment)
                .where(Comment.post_id == post_id, Comment.is_flagged.is_(False))
                .order_by(Comment.created_at.asc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return [CommentResponse.from_orm(c) for c in rows]


@router.post("/posts/{post_id}/report", summary="Report a post")
async def report_post(
    post_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post = (
        await db.execute(select(Post).where(Post.id == post_id))
    ).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.report_count += 1
    if post.report_count >= REPORT_AUTO_FLAG_THRESHOLD:
        post.is_flagged = True
        post.is_hidden = True
    await db.flush()
    return {"report_count": post.report_count, "is_flagged": post.is_flagged}


@router.post("/comments/{comment_id}/report", summary="Report a comment")
async def report_comment(
    comment_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comment = (
        await db.execute(select(Comment).where(Comment.id == comment_id))
    ).scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment.is_flagged = True
    await db.flush()
    return {"is_flagged": True}


# ---------------------------------------------------------------------------
# Group Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/groups",
    response_model=GroupResponse,
    status_code=201,
    summary="Create group (admin only)",
)
async def create_group(
    body: GroupCreateRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    valid_types = {"domain", "college", "general"}
    if body.type not in valid_types:
        raise HTTPException(
            status_code=422,
            detail=f"type must be one of: {', '.join(sorted(valid_types))}",
        )
    group = Group(
        name=body.name,
        type=body.type,
        description=body.description,
        domain=body.domain,
        college=body.college,
    )
    db.add(group)
    await db.flush()
    return GroupResponse.from_orm(group)


@router.get("/groups", response_model=list[GroupResponse], summary="List groups")
async def list_groups(
    type_filter: Optional[str] = Query(None, alias="type"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [Group.is_active.is_(True)]
    if type_filter:
        filters.append(Group.type == type_filter)
    rows = (
        (await db.execute(select(Group).where(and_(*filters)).order_by(Group.name)))
        .scalars()
        .all()
    )
    return [GroupResponse.from_orm(g) for g in rows]


@router.post("/groups/{group_id}/join", summary="Join a group")
async def join_group(
    group_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = (
        await db.execute(
            select(Group).where(Group.id == group_id, Group.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    member = GroupMember(group_id=group_id, user_id=current_user.id)
    db.add(member)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=409, detail="You are already a member of this group"
        )

    group.member_count += 1
    await db.flush()
    return {
        "message": "Joined group",
        "group_id": str(group_id),
        "member_count": group.member_count,
    }


@router.get(
    "/groups/{group_id}/feed",
    response_model=list[PostResponse],
    summary="Group-scoped post feed",
)
async def group_feed(
    group_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        (
            await db.execute(
                select(Post)
                .where(Post.group_id == group_id, Post.is_hidden.is_(False))
                .order_by(Post.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return [PostResponse.from_orm(p) for p in rows]


# ---------------------------------------------------------------------------
# Achievement Endpoints
# ---------------------------------------------------------------------------

VALID_ACHIEVEMENT_TYPES = {
    "hackathon",
    "internship",
    "publication",
    "competition",
    "certification",
    "coding",
    "community",
    "other",
}


@router.post(
    "/achievements",
    response_model=AchievementResponse,
    status_code=201,
    summary="Submit achievement",
)
async def submit_achievement(
    body: AchievementCreateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.type not in VALID_ACHIEVEMENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid type. Allowed: {', '.join(sorted(VALID_ACHIEVEMENT_TYPES))}",
        )

    # Anti-gaming: velocity check — max 5 submissions per 24h
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_count = int(
        (
            await db.execute(
                select(func.count(Achievement.id)).where(
                    Achievement.user_id == current_user.id,
                    Achievement.created_at >= cutoff,
                )
            )
        ).scalar_one()
        or 0
    )
    if recent_count >= ACHIEVEMENT_VELOCITY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many achievement submissions in 24 hours (max 5). Try again tomorrow.",
        )

    # Duplicate detection: same title + same event_date
    if body.event_date:
        dup = (
            await db.execute(
                select(Achievement).where(
                    Achievement.user_id == current_user.id,
                    Achievement.title == body.title.strip(),
                    Achievement.event_date == body.event_date,
                )
            )
        ).scalar_one_or_none()
        if dup:
            raise HTTPException(
                status_code=409,
                detail="Duplicate achievement: same title and date already submitted.",
            )

    ach = Achievement(
        user_id=current_user.id,
        type=body.type,
        title=body.title.strip(),
        description=body.description,
        proof_url=body.proof_url,
        event_date=body.event_date,
        points_claimed=body.points_claimed,
        verified=False,
    )
    db.add(ach)
    await db.flush()
    return AchievementResponse.from_orm(ach)


@router.get(
    "/achievements",
    response_model=list[AchievementResponse],
    summary="List my achievements",
)
async def list_achievements(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        (
            await db.execute(
                select(Achievement)
                .where(Achievement.user_id == current_user.id)
                .order_by(Achievement.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [AchievementResponse.from_orm(a) for a in rows]


@router.put(
    "/achievements/{achievement_id}/verify",
    response_model=AchievementResponse,
    summary="Verify or reject achievement (admin only)",
)
async def verify_achievement(
    achievement_id: UUID,
    body: AchievementVerifyRequest,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    ach = (
        await db.execute(select(Achievement).where(Achievement.id == achievement_id))
    ).scalar_one_or_none()
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found")

    ach.verified = body.verified
    ach.verified_by = admin.id
    ach.verified_at = datetime.now(timezone.utc)
    if not body.verified:
        ach.rejection_reason = body.rejection_reason
    await db.flush()

    if body.verified:
        try:
            from app.workers.incoscore_tasks import update_incoscore

            update_incoscore.delay(str(ach.user_id))
        except Exception:
            logger.warning(
                "Failed to queue update_incoscore after verification", exc_info=True
            )

    return AchievementResponse.from_orm(ach)


# ---------------------------------------------------------------------------
# Peer Endorsements
# ---------------------------------------------------------------------------


@router.post(
    "/users/{user_id}/endorse/{skill}", summary="Endorse a peer's skill (idempotent)"
)
async def endorse_skill(
    user_id: UUID,
    skill: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot endorse yourself")

    from app.models.user import User

    target = (
        await db.execute(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Idempotent: just return OK if already endorsed (no separate table in this phase)
    return {
        "message": f"Endorsed '{skill}' for user {user_id}",
        "endorser": str(current_user.id),
    }
