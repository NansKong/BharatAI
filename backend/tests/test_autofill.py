"""Integration tests for Phase 5 autofill endpoint — consent gate and rate limiting."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _opp_payload() -> dict:
    return {
        "title": "Autofill Test Opportunity",
        "description": "An opportunity to test autofill functionality end-to-end.",
        "institution": "IISc Bangalore",
        "domain": "ai_ds",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=20)).isoformat(),
        "source_url": f"https://example.com/{uuid.uuid4().hex}",
        "application_link": "https://example.com/apply",
    }


def _register_student(client, email: str | None = None) -> str:
    email = email or f"af-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Autofill User",
            "email": email,
            "password": "StudentPass1",
            "college": "IISc Bangalore",
            "degree": "M.Tech",
            "year": 1,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def _create_application(client, student_token: str, admin_token: str) -> str:
    opp = client.post(
        "/api/v1/opportunities", headers=_auth(admin_token), json=_opp_payload()
    )
    assert opp.status_code == 201
    opp_id = opp.json()["id"]

    app = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp_id},
    )
    assert app.status_code == 201
    return app.json()["id"]


def test_autofill_blocked_without_consent(client, create_user_token):
    """Autofill must return 403 if profile.consent_to_autofill = False (default)."""
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)
    app_id = _create_application(client, student_token, admin_token)

    # Default consent = False
    res = client.get(
        f"/api/v1/applications/{app_id}/autofill", headers=_auth(student_token)
    )
    assert res.status_code == 403
    assert "consent" in res.json()["detail"].lower()


def test_autofill_returns_fields_with_consent(client, create_user_token):
    """Autofill must return field suggestions when consent is true."""
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)
    app_id = _create_application(client, student_token, admin_token)

    # Grant consent
    profile_res = client.put(
        "/api/v1/profile",
        headers=_auth(student_token),
        json={"consent_to_autofill": True, "skills": ["Python", "ML"]},
    )
    assert profile_res.status_code == 200

    res = client.get(
        f"/api/v1/applications/{app_id}/autofill", headers=_auth(student_token)
    )
    assert res.status_code == 200
    body = res.json()
    assert body["consent_used"] is True
    fields = body["fields"]
    assert isinstance(fields, dict)
    assert len(fields) > 0
    # Basic fields from profile should be present
    assert "name" in fields
    assert "email" in fields


def test_autofill_rate_limit(client, create_user_token):
    """Autofill must return 429 after exceeding 20 requests/hour."""
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)
    app_id = _create_application(client, student_token, admin_token)

    # Grant consent
    client.put(
        "/api/v1/profile",
        headers=_auth(student_token),
        json={"consent_to_autofill": True},
    )

    # Patch Redis INCR to simulate being over the limit
    from app.api.v1 import applications as apps_module

    original_check = apps_module._check_autofill_rate_limit

    call_count = 0

    async def _mock_rate_limit(user_id, redis):
        nonlocal call_count
        call_count += 1
        if call_count > 20:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=429,
                detail="Autofill rate limit exceeded (20 requests/hour). Try again later.",
            )

    with patch.object(
        apps_module, "_check_autofill_rate_limit", side_effect=_mock_rate_limit
    ):
        # First 20 should succeed
        for _ in range(20):
            r = client.get(
                f"/api/v1/applications/{app_id}/autofill", headers=_auth(student_token)
            )
            assert r.status_code == 200

        # 21st should be 429
        r21 = client.get(
            f"/api/v1/applications/{app_id}/autofill", headers=_auth(student_token)
        )
        assert r21.status_code == 429
