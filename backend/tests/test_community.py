"""Integration tests for Phase 6 Community: groups, group feed, peer endorsement."""

from __future__ import annotations

import uuid


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_student(client, email: str | None = None) -> str:
    email = email or f"comm-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Community User",
            "email": email,
            "password": "StudentPass1",
            "college": "NIT Trichy",
            "degree": "B.Tech",
            "year": 2,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def test_create_group_admin_only(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    # Student should get 403
    res_student = client.post(
        "/api/v1/community/groups",
        headers=_auth(student_token),
        json={"name": "CS Students", "type": "domain", "domain": "cs"},
    )
    assert res_student.status_code == 403

    # Admin should succeed
    res_admin = client.post(
        "/api/v1/community/groups",
        headers=_auth(admin_token),
        json={"name": "CS Students", "type": "domain", "domain": "cs"},
    )
    assert res_admin.status_code == 201
    assert res_admin.json()["name"] == "CS Students"


def test_join_group(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    group = client.post(
        "/api/v1/community/groups",
        headers=_auth(admin_token),
        json={"name": "AI Enthusiasts", "type": "domain", "domain": "ai_ds"},
    )
    group_id = group.json()["id"]

    # First join — should succeed
    join1 = client.post(
        f"/api/v1/community/groups/{group_id}/join", headers=_auth(student_token)
    )
    assert join1.status_code == 200
    assert join1.json()["member_count"] == 1

    # Duplicate join — should return 409
    join2 = client.post(
        f"/api/v1/community/groups/{group_id}/join", headers=_auth(student_token)
    )
    assert join2.status_code == 409


def test_group_feed_scoped(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    # Create two groups
    g1 = client.post(
        "/api/v1/community/groups",
        headers=_auth(admin_token),
        json={"name": "Finance Club", "type": "domain", "domain": "finance"},
    ).json()["id"]
    g2 = client.post(
        "/api/v1/community/groups",
        headers=_auth(admin_token),
        json={"name": "Law Circle", "type": "domain", "domain": "law"},
    ).json()["id"]

    # Post in group 1
    p1 = client.post(
        "/api/v1/community/posts",
        headers=_auth(student_token),
        json={"content": "Group 1 finance post here!", "group_id": g1},
    )
    assert p1.status_code == 201
    p1_id = p1.json()["id"]

    # Group 1 feed should have the post
    feed_g1 = client.get(
        f"/api/v1/community/groups/{g1}/feed", headers=_auth(student_token)
    )
    assert feed_g1.status_code == 200
    assert any(p["id"] == p1_id for p in feed_g1.json())

    # Group 2 feed should NOT have it
    feed_g2 = client.get(
        f"/api/v1/community/groups/{g2}/feed", headers=_auth(student_token)
    )
    assert feed_g2.status_code == 200
    assert all(p["id"] != p1_id for p in feed_g2.json())
