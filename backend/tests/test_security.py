from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.security import (create_access_token, create_refresh_token,
                               decode_token, hash_password, verify_password)


def test_password_hash_roundtrip():
    password = "StrongPass9"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPass9", hashed) is False


def test_access_token_encode_decode_contains_claims():
    token = create_access_token(
        user_id="123e4567-e89b-12d3-a456-426614174000", role="student"
    )
    payload = decode_token(token)

    assert payload["sub"] == "123e4567-e89b-12d3-a456-426614174000"
    assert payload["role"] == "student"
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload


def test_access_token_expiry_window():
    now = datetime.now(timezone.utc)
    token = create_access_token(user_id="u1", role="student")
    payload = decode_token(token)
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    min_exp = now + timedelta(
        minutes=max(1, settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES - 1)
    )
    max_exp = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES + 1)
    assert min_exp <= exp <= max_exp


def test_refresh_token_structure_and_type():
    token, jti = create_refresh_token("user-xyz")
    payload = decode_token(token)

    assert isinstance(jti, str) and len(jti) > 10
    assert payload["sub"] == "user-xyz"
    assert payload["type"] == "refresh"
    assert payload["jti"] == jti
