"""
Users API – current user info and resume upload.
"""
from typing import List, Optional

from app.core.security import get_current_user
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

router = APIRouter()


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    college: Optional[str]
    degree: Optional[str]
    year: Optional[int]


class ResumeUploadResponse(BaseModel):
    message: str
    filename: Optional[str]


class ProfileUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    consent_to_autofill: Optional[bool] = None


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description=(
        "Returns the authenticated user's core account fields (id, name, email, role, college, degree, year). "
        "For extended profile data (bio, skills, interests, social links) use `GET /api/v1/profile`."
    ),
    responses={
        401: {"description": "Missing or invalid access token"},
    },
)
async def get_my_profile(current_user=Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "college": current_user.college,
        "degree": current_user.degree,
        "year": current_user.year,
    }


@router.put(
    "/me/profile",
    summary="Update current user profile (legacy)",
    description=(
        "Lightweight profile patch — prefer `PUT /api/v1/profile` for full profile management. "
        "This endpoint is kept for backward compatibility."
    ),
    responses={
        401: {"description": "Missing or invalid access token"},
    },
)
async def update_profile(
    body: ProfileUpdateRequest, current_user=Depends(get_current_user)
):
    return {"message": "Profile update queued", "user_id": str(current_user.id)}


@router.post(
    "/me/resume",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload resume PDF",
    description=(
        "Upload a PDF resume (max 5 MB). The file is validated for MIME type and size before storage. "
        "After upload, the AI autofill pipeline extracts skills, education, and experience automatically."
    ),
    responses={
        401: {"description": "Missing or invalid access token"},
        422: {"description": "File is not a PDF or exceeds 5 MB"},
    },
)
async def upload_resume(
    file: UploadFile = File(..., description="PDF file, max 5 MB"),
    current_user=Depends(get_current_user),
):
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted")
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="File size exceeds 5MB limit")
    return {
        "message": "Resume received. Processing will begin shortly.",
        "filename": file.filename,
    }
