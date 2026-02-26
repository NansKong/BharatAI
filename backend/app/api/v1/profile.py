"""Profile and resume endpoints for personalization."""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from app.ai.resume_parser import parse_resume, sanitize_skills
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import cache_delete_pattern
from app.core.security import get_current_user
from app.core.storage import store_resume_pdf
from app.models.user import Profile
from app.workers.ai_tasks import generate_embeddings
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    bio: Optional[str] = Field(default=None, max_length=5000)
    skills: Optional[list[str]] = None
    interests: Optional[list[str]] = None
    github_url: Optional[str] = Field(default=None, max_length=300)
    linkedin_url: Optional[str] = Field(default=None, max_length=300)
    consent_to_autofill: Optional[bool] = None
    college: Optional[str] = Field(default=None, max_length=300)
    degree: Optional[str] = Field(default=None, max_length=200)
    year: Optional[int] = Field(default=None, ge=1, le=6)


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    bio: Optional[str]
    skills: list[str]
    interests: list[str]
    resume_path: Optional[str]
    github_url: Optional[str]
    linkedin_url: Optional[str]
    consent_to_autofill: bool
    embedding_ready: bool


class ProfileMeResponse(BaseModel):
    user_id: UUID
    name: str
    email: str
    college: Optional[str]
    degree: Optional[str]
    year: Optional[int]
    profile: ProfileResponse


class ResumeUploadResponse(BaseModel):
    message: str
    resume_path: str
    extracted_skills_count: int
    embedding_task_queued: bool


async def _get_or_create_profile(db: AsyncSession, user_id: UUID) -> Profile:
    profile = (
        await db.execute(select(Profile).where(Profile.user_id == user_id))
    ).scalar_one_or_none()
    if profile:
        return profile

    profile = Profile(user_id=user_id)
    db.add(profile)
    await db.flush()
    return profile


def _to_profile_response(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        bio=profile.bio,
        skills=profile.skills or [],
        interests=profile.interests or [],
        resume_path=profile.resume_path,
        github_url=profile.github_url,
        linkedin_url=profile.linkedin_url,
        consent_to_autofill=bool(profile.consent_to_autofill),
        embedding_ready=bool(profile.embedding_vector),
    )


@router.get(
    "/me",
    response_model=ProfileMeResponse,
    summary="Get full profile with embedding status",
)
async def get_my_profile(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user.id)
    return ProfileMeResponse(
        user_id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        college=current_user.college,
        degree=current_user.degree,
        year=current_user.year,
        profile=_to_profile_response(profile),
    )


@router.put("", response_model=ProfileResponse, summary="Update profile manually")
async def update_profile(
    body: ProfileUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user.id)
    updates = body.model_dump(exclude_unset=True)

    if "skills" in updates and updates["skills"] is not None:
        updates["skills"] = sanitize_skills(updates["skills"], max_skills=30)
    if "interests" in updates and updates["interests"] is not None:
        updates["interests"] = sanitize_skills(updates["interests"], max_skills=30)

    for field in (
        "bio",
        "skills",
        "interests",
        "github_url",
        "linkedin_url",
        "consent_to_autofill",
    ):
        if field in updates:
            setattr(profile, field, updates[field])

    for user_field in ("college", "degree", "year"):
        if user_field in updates:
            setattr(current_user, user_field, updates[user_field])

    await db.flush()

    try:
        generate_embeddings.delay(str(current_user.id))
    except Exception:
        logger.warning(
            "Failed to queue embedding generation after profile update", exc_info=True
        )

    try:
        await cache_delete_pattern(f"feed:{current_user.id}:*")
    except Exception:
        logger.warning(
            "Failed to invalidate personalized feed cache after profile update",
            exc_info=True,
        )

    return _to_profile_response(profile)


@router.post(
    "/resume",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload resume PDF (max 5MB)",
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=422, detail="Only PDF files are accepted")

    max_size_bytes = settings.MAX_RESUME_SIZE_MB * 1024 * 1024
    content = await file.read(max_size_bytes + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=422,
            detail=f"File size exceeds {settings.MAX_RESUME_SIZE_MB}MB limit",
        )

    profile = await _get_or_create_profile(db, current_user.id)
    resume_path = store_resume_pdf(
        str(current_user.id), file.filename or "resume.pdf", content
    )
    parsed = parse_resume(content)

    profile.resume_path = resume_path
    extracted_skills = sanitize_skills(parsed.get("skills", []), max_skills=30)
    if extracted_skills:
        merged_skills = sanitize_skills(
            (profile.skills or []) + extracted_skills, max_skills=30
        )
        profile.skills = merged_skills

    parsed_college = parsed.get("college")
    parsed_degree = parsed.get("degree")
    parsed_year = parsed.get("graduation_year")
    if isinstance(parsed_college, str) and parsed_college and not current_user.college:
        current_user.college = parsed_college
    if isinstance(parsed_degree, str) and parsed_degree and not current_user.degree:
        current_user.degree = parsed_degree
    if isinstance(parsed_year, int) and 1 <= parsed_year <= 6 and not current_user.year:
        current_user.year = parsed_year

    await db.flush()

    task_queued = True
    try:
        generate_embeddings.delay(str(current_user.id))
    except Exception:
        task_queued = False
        logger.warning(
            "Failed to queue embedding generation after resume upload", exc_info=True
        )

    try:
        await cache_delete_pattern(f"feed:{current_user.id}:*")
    except Exception:
        logger.warning(
            "Failed to invalidate personalized feed cache after resume upload",
            exc_info=True,
        )

    return ResumeUploadResponse(
        message="Resume processed and profile enrichment queued.",
        resume_path=resume_path,
        extracted_skills_count=len(extracted_skills),
        embedding_task_queued=task_queued,
    )
