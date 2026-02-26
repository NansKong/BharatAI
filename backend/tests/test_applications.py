"""Integration tests for Phase 5 Application CRUD and status state machine."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _opp_payload(title: str = "Test Opportunity") -> dict:
    return {
        "title": title,
        "description": "A detailed description of this test opportunity for students.",
        "institution": "IIT Bombay",
        "domain": "cs",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "source_url": f"https://example.com/{uuid.uuid4().hex}",
        "application_link": "https://example.com/apply",
        "eligibility": "Resume required. Minimum CGPA 7.0. Submit statement of purpose.",
    }


def _register_student(client, email: str | None = None) -> str:
    email = email or f"student-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Student",
            "email": email,
            "password": "StudentPass1",
            "college": "IIT Bombay",
            "degree": "B.Tech",
            "year": 2,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def test_create_application(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    opp = client.post(
        "/api/v1/opportunities", headers=_auth(admin_token), json=_opp_payload()
    )
    assert opp.status_code == 201
    opp_id = opp.json()["id"]

    res = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp_id},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "draft"
    assert body["opportunity_id"] == opp_id
    assert body["opportunity_title"] == "Test Opportunity"


def test_duplicate_application_rejected(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    opp = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json=_opp_payload("Dup Opp"),
    )
    opp_id = opp.json()["id"]

    first = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp_id},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp_id},
    )
    assert second.status_code == 409


def test_list_applications_with_status_filter(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    opp1 = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json=_opp_payload("List Opp 1"),
    )
    opp2 = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json=_opp_payload("List Opp 2"),
    )
    opp1_id = opp1.json()["id"]
    opp2_id = opp2.json()["id"]

    app1 = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp1_id},
    )
    app2 = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp2_id},
    )
    app1_id = app1.json()["id"]

    # advance app1 to submitted
    client.put(
        f"/api/v1/applications/{app1_id}/status",
        headers=_auth(student_token),
        json={"status": "submitted"},
    )

    draft_res = client.get(
        "/api/v1/applications?status=draft", headers=_auth(student_token)
    )
    assert draft_res.status_code == 200
    ids = [i["id"] for i in draft_res.json()["items"]]
    assert app2.json()["id"] in ids
    assert app1_id not in ids

    submitted_res = client.get(
        "/api/v1/applications?status=submitted", headers=_auth(student_token)
    )
    assert submitted_res.status_code == 200
    assert any(i["id"] == app1_id for i in submitted_res.json()["items"])


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------


def test_status_transition_valid_draft_to_submitted(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    opp = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json=_opp_payload("Transition Opp"),
    )
    app = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp.json()["id"]},
    )
    app_id = app.json()["id"]

    res = client.put(
        f"/api/v1/applications/{app_id}/status",
        headers=_auth(student_token),
        json={"status": "submitted"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "submitted"
    assert res.json()["applied_at"] is not None


def test_status_transition_invalid_backward_jump(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    opp = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json=_opp_payload("Invalid Trans"),
    )
    app = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp.json()["id"]},
    )
    app_id = app.json()["id"]

    # advance to submitted
    client.put(
        f"/api/v1/applications/{app_id}/status",
        headers=_auth(student_token),
        json={"status": "submitted"},
    )

    # try to go back to draft — must fail
    res = client.put(
        f"/api/v1/applications/{app_id}/status",
        headers=_auth(student_token),
        json={"status": "draft"},
    )
    assert res.status_code == 422


def test_student_cannot_see_other_users_application(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student1_token = _register_student(client)
    student2_token = _register_student(client)

    opp = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json=_opp_payload("Private Opp"),
    )
    app = client.post(
        "/api/v1/applications",
        headers=_auth(student1_token),
        json={"opportunity_id": opp.json()["id"]},
    )
    app_id = app.json()["id"]

    # student2 cannot access student1's application
    res = client.put(
        f"/api/v1/applications/{app_id}/status",
        headers=_auth(student2_token),
        json={"status": "submitted"},
    )
    assert res.status_code == 404


def test_admin_can_update_any_application_status(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    opp = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json=_opp_payload("Admin Update Opp"),
    )
    app = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp.json()["id"]},
    )
    app_id = app.json()["id"]

    # Admin submits the application on behalf
    res = client.put(
        f"/api/v1/applications/{app_id}/status",
        headers=_auth(admin_token),
        json={"status": "submitted"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "submitted"

    # Admin marks as accepted
    res2 = client.put(
        f"/api/v1/applications/{app_id}/status",
        headers=_auth(admin_token),
        json={"status": "accepted"},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "accepted"
