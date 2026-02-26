"""Integration tests for Phase 6 Achievements: submission and admin verification."""

from __future__ import annotations

import uuid


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_student(client, email: str | None = None) -> str:
    email = email or f"ach-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Achiever User",
            "email": email,
            "password": "StudentPass1",
            "college": "IIT Kharagpur",
            "degree": "M.Tech",
            "year": 1,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def test_submit_achievement_starts_unverified(client, create_user_token):
    student_token = _register_student(client)

    res = client.post(
        "/api/v1/community/achievements",
        headers=_auth(student_token),
        json={
            "type": "hackathon",
            "title": "National Coding Hackathon 2025",
            "description": "Won 1st place in national hackathon",
            "proof_url": "https://devfolio.co/submissions/my-project",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["verified"] is False
    assert body["title"] == "National Coding Hackathon 2025"


def test_list_own_achievements(client, create_user_token):
    student_token = _register_student(client)

    client.post(
        "/api/v1/community/achievements",
        headers=_auth(student_token),
        json={
            "type": "certification",
            "title": "AWS Solutions Architect",
            "description": "AWS industry certification",
        },
    )

    res = client.get("/api/v1/community/achievements", headers=_auth(student_token))
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["verified"] is False


def test_admin_verify_achievement(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    # Submit
    ach = client.post(
        "/api/v1/community/achievements",
        headers=_auth(student_token),
        json={
            "type": "publication",
            "title": "IEEE Paper on ML 2025",
            "description": "peer-reviewed IEEE conference",
        },
    )
    assert ach.status_code == 201
    ach_id = ach.json()["id"]

    # Admin verifies
    verify_res = client.put(
        f"/api/v1/community/achievements/{ach_id}/verify",
        headers=_auth(admin_token),
        json={"verified": True},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True


def test_admin_reject_achievement(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    ach = client.post(
        "/api/v1/community/achievements",
        headers=_auth(student_token),
        json={
            "type": "competition",
            "title": "Suspicious Award",
            "description": "national competition winner",
        },
    )
    ach_id = ach.json()["id"]

    reject_res = client.put(
        f"/api/v1/community/achievements/{ach_id}/verify",
        headers=_auth(admin_token),
        json={"verified": False, "rejection_reason": "Proof URL not verifiable"},
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["verified"] is False
