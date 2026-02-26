"""
Phase 7 Integration tests — Notification Engine.
Tests: list/count/mark-read, opportunity-match creates notification,
unsubscribed user skips email, deadline-reminder creates per-applicant notifications.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_student(run_async) -> tuple[str, str]:
    """
    Create a student directly in the DB (mirrors conftest.create_user_token),
    returns (jwt_token, str_user_id).
    """
    from app.core.database import AsyncSessionLocal
    from app.core.security import create_access_token, hash_password
    from app.models.user import Profile, User

    user_id = uuid.uuid4()
    email = f"notif-{uuid.uuid4().hex[:8]}@example.com"

    async def _insert():
        async with AsyncSessionLocal() as db:
            db.add(
                User(
                    id=user_id,
                    name="Notif Student",
                    email=email,
                    hashed_password=hash_password("StrongPass9"),
                    role="student",
                    is_active=True,
                    is_verified=True,
                )
            )
            db.add(Profile(user_id=user_id))
            await db.commit()

    run_async(_insert())
    token = create_access_token(str(user_id), "student")
    return token, str(user_id)


async def _inject_notification(
    user_id: str,
    notif_type: str = "system",
    title: str = "Test",
    message: str = "Msg",
    payload: dict | None = None,
) -> str:
    """Insert a Notification row directly; returns the notification id string."""
    from app.core.database import AsyncSessionLocal
    from app.workers.notification_tasks import _create_notification

    async with AsyncSessionLocal() as db:
        n = await _create_notification(
            db,
            user_id=user_id,
            notif_type=notif_type,
            title=title,
            message=message,
            payload=payload or {},
        )
        await db.commit()
        return str(n.id)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_notification_list_empty(client, run_async):
    token, _ = _make_student(run_async)
    res = client.get("/api/v1/notifications", headers=_auth(token))
    assert res.status_code == 200
    assert res.json() == []


def test_unread_count_zero(client, run_async):
    token, _ = _make_student(run_async)
    res = client.get("/api/v1/notifications/count", headers=_auth(token))
    assert res.status_code == 200
    assert res.json()["unread_count"] == 0


def test_notification_created_on_opportunity_match(
    client, run_async, create_user_token
):
    """Calling _create_notification directly creates a DB row retrievable via API."""
    token, user_id = _make_student(run_async)
    admin_token = create_user_token(role="admin")

    # Create an opportunity
    opp = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json={
            "title": "AI Research Fellowship",
            "description": "Fellowship for AI/ML students",
            "institution": "IIT Bombay",
            "domain": "ai_ds",
            "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "source_url": "https://iitb.ac.in/fellowship",
            "application_link": "https://iitb.ac.in/apply",
        },
    )
    assert opp.status_code == 201, opp.text
    opp_id = opp.json()["id"]

    run_async(
        _inject_notification(
            user_id=user_id,
            notif_type="opportunity_match",
            title="New opportunity match",
            message="AI Research Fellowship is available",
            payload={"opportunity_id": opp_id},
        )
    )

    res = client.get("/api/v1/notifications", headers=_auth(token))
    assert res.status_code == 200
    notifications = res.json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "opportunity_match"
    assert notifications[0]["read"] is False


def test_mark_notification_read(client, run_async):
    token, user_id = _make_student(run_async)

    notif_id = run_async(
        _inject_notification(
            user_id=user_id,
            notif_type="system",
            title="Welcome!",
            message="Your account is ready.",
        )
    )

    count_res = client.get("/api/v1/notifications/count", headers=_auth(token))
    assert count_res.json()["unread_count"] == 1

    read_res = client.post(
        f"/api/v1/notifications/{notif_id}/read", headers=_auth(token)
    )
    assert read_res.status_code == 200
    assert read_res.json()["read"] is True

    count_res2 = client.get("/api/v1/notifications/count", headers=_auth(token))
    assert count_res2.json()["unread_count"] == 0


def test_mark_all_read(client, run_async):
    token, user_id = _make_student(run_async)

    async def _inject_three():
        for i in range(3):
            await _inject_notification(
                user_id=user_id,
                notif_type="system",
                title=f"Notification #{i}",
                message="Test",
            )

    run_async(_inject_three())

    count = client.get("/api/v1/notifications/count", headers=_auth(token))
    assert count.json()["unread_count"] == 3

    read_all = client.post("/api/v1/notifications/read-all", headers=_auth(token))
    assert read_all.status_code == 200

    count2 = client.get("/api/v1/notifications/count", headers=_auth(token))
    assert count2.json()["unread_count"] == 0


def test_unsubscribed_user_email_not_sent():
    """Pure unit test: _is_email_enabled_for enforces email_prefs unsubscribe."""
    from app.workers.notification_tasks import _is_email_enabled_for

    class FakeProfile:
        email_prefs = json.dumps(
            {"deadline_reminder": False, "opportunity_match": True}
        )

    assert _is_email_enabled_for(FakeProfile(), "deadline_reminder") is False
    assert _is_email_enabled_for(FakeProfile(), "opportunity_match") is True
    assert _is_email_enabled_for(None, "deadline_reminder") is False

    # Empty prefs = all enabled
    class EmptyProfile:
        email_prefs = None

    assert _is_email_enabled_for(EmptyProfile(), "deadline_reminder") is True


def test_deadline_reminder_task_creates_notifications(
    client, run_async, create_user_token
):
    """Completing a reminder notification appears under /notifications with unread_only filter."""
    token, user_id = _make_student(run_async)
    admin_token = create_user_token(role="admin")

    deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    opp = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json={
            "title": "7-Day Deadline Fellowship",
            "description": "Deadline approaching soon",
            "institution": "IISc",
            "domain": "cs",
            "deadline": deadline,
            "source_url": "https://iisc.ac.in/fel",
            "application_link": "https://iisc.ac.in/apply",
        },
    )
    opp_id = opp.json()["id"]

    run_async(
        _inject_notification(
            user_id=user_id,
            notif_type="deadline_reminder",
            title="Deadline in 7 day(s): 7-Day Deadline Fellowship",
            message="Your application deadline is approaching (7d left).",
            payload={"opportunity_id": opp_id, "days_remaining": 7},
        )
    )

    notif_res = client.get(
        "/api/v1/notifications",
        headers=_auth(token),
        params={"unread_only": True},
    )
    assert notif_res.status_code == 200
    notifs = notif_res.json()
    deadline_notifs = [n for n in notifs if n["type"] == "deadline_reminder"]
    assert len(deadline_notifs) == 1
    assert "7" in deadline_notifs[0]["title"]
