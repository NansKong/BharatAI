"""Integration tests for Phase 6 anti-gaming: velocity check and duplicate detection."""

from __future__ import annotations

import uuid


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_student(client, email: str | None = None) -> str:
    email = email or f"ag-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Anti-Gaming User",
            "email": email,
            "password": "StudentPass1",
            "college": "IIT Madras",
            "degree": "B.Tech",
            "year": 2,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def _achievement_payload(
    title: str = "My Achievement", event_date: str | None = None
) -> dict:
    payload = {
        "type": "hackathon",
        "title": title,
        "description": "Won 1st place",
    }
    if event_date:
        payload["event_date"] = event_date
    return payload


def test_velocity_check_blocks_6th_submission_in_24h(client, create_user_token):
    student_token = _register_student(client)

    # Submit 5 — all should succeed
    for i in range(5):
        res = client.post(
            "/api/v1/community/achievements",
            headers=_auth(student_token),
            json=_achievement_payload(title=f"Hackathon #{i}"),
        )
        assert (
            res.status_code == 201
        ), f"Expected 201 on submission {i+1}, got {res.status_code}: {res.text}"

    # 6th submission should be blocked
    res6 = client.post(
        "/api/v1/community/achievements",
        headers=_auth(student_token),
        json=_achievement_payload(title="Hackathon #5"),
    )
    assert res6.status_code == 429
    assert "too many" in res6.json()["detail"].lower()


def test_duplicate_title_date_rejected(client, create_user_token):
    student_token = _register_student(client)

    event_date = "2025-08-15T00:00:00Z"

    first = client.post(
        "/api/v1/community/achievements",
        headers=_auth(student_token),
        json={
            **_achievement_payload(title="Smart India Hackathon"),
            "event_date": event_date,
        },
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/api/v1/community/achievements",
        headers=_auth(student_token),
        json={
            **_achievement_payload(title="Smart India Hackathon"),
            "event_date": event_date,
        },
    )
    assert duplicate.status_code == 409
    assert "duplicate" in duplicate.json()["detail"].lower()
