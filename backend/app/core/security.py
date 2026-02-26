"""
JWT Security: token creation, verification, password hashing, RBAC dependencies.
Uses RS256 (asymmetric RSA) for production-grade security.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis, is_token_revoked
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

# Password hashing context (bcrypt, cost factor 12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# Bearer token extractor
bearer_scheme = HTTPBearer()


# ── Password Utilities ────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Token Creation ────────────────────────────────────────────────────────


def create_access_token(user_id: str, role: str) -> str:
    """Create a short-lived JWT access token (RS256)."""
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "jti": jti,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(
        payload, settings.jwt_private_key, algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """
    Create a long-lived JWT refresh token (RS256).
    Returns (encoded_token, jti) so the JTI can be stored in Redis.
    """
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    token = jwt.encode(
        payload, settings.jwt_private_key, algorithm=settings.JWT_ALGORITHM
    )
    return token, jti


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT with key-rotation support.
    Tries V2 public key first (if configured), falls back to primary key.
    Raises JWTError on failure.
    """
    # Try V2 key first (key rotation)
    v2_path = getattr(settings, "JWT_PUBLIC_KEY_V2_PATH", None)
    if v2_path:
        try:
            from pathlib import Path

            v2_key = Path(v2_path).read_text()
            return jwt.decode(token, v2_key, algorithms=[settings.JWT_ALGORITHM])
        except (JWTError, FileNotFoundError, OSError):
            pass  # Fall through to primary key

    return jwt.decode(
        token,
        settings.jwt_public_key,
        algorithms=[settings.JWT_ALGORITHM],
    )


def verify_access_token(token: str) -> dict:
    """Verify an access token (used by WebSocket auth). Raises on failure."""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Not an access token")
    return payload


# ── FastAPI Dependencies ──────────────────────────────────────────────────────


async def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    redis=Depends(get_redis),
) -> dict:
    """
    FastAPI dependency: validates the Bearer token, checks revocation list.
    Returns the decoded token payload.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    # Check token revocation
    jti = payload.get("jti")
    if jti and await is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency: returns the current authenticated User ORM object.
    Imported here lazily to avoid circular imports with models.
    """
    from app.models.user import User
    from sqlalchemy import select

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def require_admin(current_user=Depends(get_current_user)):
    """FastAPI dependency: require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_student(current_user=Depends(get_current_user)):
    """FastAPI dependency: require student or admin role."""
    if current_user.role not in ("student", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return current_user


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
):
    """
    FastAPI dependency: returns the authenticated User if a valid Bearer token
    is present, otherwise returns None (unauthenticated / public access).
    """
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        return None

    if payload.get("type") != "access":
        return None

    jti = payload.get("jti")
    if jti and await is_token_revoked(jti):
        return None

    from app.models.user import User
    from sqlalchemy import select

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    return result.scalar_one_or_none()
