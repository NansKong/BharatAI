"""
Authentication API router: register, login, refresh, logout, Google OAuth.
"""
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import add_to_blocklist, cache_delete, cache_get, cache_set
from app.core.security import (create_access_token, create_refresh_token,
                               decode_token, get_current_user_payload,
                               hash_password, verify_password)
from app.models.user import Profile, User
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# ── OAuth2 setup ─────────────────────────────────────────────────────────────
oauth = OAuth()
if settings.GOOGLE_CLIENT_ID:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


# ── Request / Response Schemas ───────────────────────────────────────────────


class RegisterRequest(BaseModel):
    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    college: str | None = Field(None, max_length=300)
    degree: str | None = Field(None, max_length=200)
    year: int | None = Field(None, ge=1, le=6)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    model_config = {"extra": "forbid"}
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60


class RefreshRequest(BaseModel):
    model_config = {"extra": "forbid"}
    refresh_token: str


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _create_tokens_for_user(user: User) -> TokenResponse:
    access_token = create_access_token(str(user.id), user.role)
    refresh_token, jti = create_refresh_token(str(user.id))

    # Store refresh token JTI in Redis (valid for TTL)
    ttl = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await cache_set(f"refresh_jti:{jti}:{user.id}", "1", ttl)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
    description="Creates a new student account with email and password. Returns JWT tokens.",
    responses={
        400: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check for existing email
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    # Sanitize user input
    from app.core.sanitize import sanitize_text

    clean_name = sanitize_text(body.name) or body.name
    clean_college = sanitize_text(body.college)
    clean_degree = sanitize_text(body.degree)

    # Create user
    user = User(
        name=clean_name,
        email=body.email,
        hashed_password=hash_password(body.password),
        role="student",
        college=clean_college,
        degree=clean_degree,
        year=body.year,
    )
    db.add(user)
    await db.flush()  # Get user.id

    # Create empty profile
    profile = Profile(user_id=user.id)
    db.add(profile)

    await db.commit()  # Persist user + profile before issuing tokens
    return await _create_tokens_for_user(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description="Returns JWT access and refresh tokens on successful authentication.",
    responses={
        401: {"description": "Invalid credentials"},
    },
)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if (
        not user
        or not user.hashed_password
        or not verify_password(body.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await _create_tokens_for_user(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token + refresh token pair (rotation).",
    responses={
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    from jose import JWTError

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "refresh":
        raise credentials_exception

    user_id = payload.get("sub")
    jti = payload.get("jti")

    # Check if this refresh token is still valid in Redis
    cached = await cache_get(f"refresh_jti:{jti}:{user_id}")
    if not cached:
        raise credentials_exception

    # Revoke old refresh token
    await cache_delete(f"refresh_jti:{jti}:{user_id}")

    # Load user
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception

    return await _create_tokens_for_user(user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke current access token",
)
async def logout(payload: dict = Depends(get_current_user_payload)):
    jti = payload.get("jti")
    if jti:
        # Add to blocklist with TTL = remaining token lifetime
        exp = payload.get("exp", 0)
        remaining = max(0, int(exp - datetime.now(timezone.utc).timestamp()))
        await add_to_blocklist(jti, remaining + 60)  # +60s buffer


# ── Google OAuth2 ────────────────────────────────────────────────────────────


@router.get(
    "/google",
    summary="Initiate Google OAuth2 login",
    include_in_schema=bool(settings.GOOGLE_CLIENT_ID),
)
async def google_login(request: Request):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get(
    "/google/callback",
    response_model=TokenResponse,
    summary="Google OAuth2 callback",
    include_in_schema=bool(settings.GOOGLE_CLIENT_ID),
)
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    if not user_info:
        raise HTTPException(
            status_code=400, detail="Failed to fetch user info from Google"
        )

    google_id = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])

    # Upsert user
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        # Check if email already exists (link accounts)
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            user.google_id = google_id
        else:
            user = User(
                name=name,
                email=email,
                google_id=google_id,
                role="student",
                is_verified=True,
            )
            db.add(user)
            await db.flush()
            profile = Profile(user_id=user.id)
            db.add(profile)

    return await _create_tokens_for_user(user)
