import uuid

from app.api.v1 import admin as admin_module


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_student(client, email: str) -> str:
    payload = {
        "name": "Student Source Tester",
        "email": email,
        "password": "StudentPass1",
        "college": "IIT Bombay",
        "degree": "B.Tech",
        "year": 2,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()["access_token"]


def _source_payload(**overrides):
    payload = {
        "name": "IIT Bombay Events",
        "url": f"https://example.com/source/{uuid.uuid4().hex}",
        "type": "static",
        "interval_minutes": 30,
        "active": True,
    }
    payload.update(overrides)
    return payload


def test_admin_source_management(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(
        client, email=f"student-{uuid.uuid4().hex[:8]}@example.com"
    )

    forbidden = client.get("/api/v1/admin/sources", headers=_auth_header(student_token))
    assert forbidden.status_code == 403

    created = client.post(
        "/api/v1/admin/sources",
        headers=_auth_header(admin_token),
        json=_source_payload(name="AICTE Scholarships"),
    )
    assert created.status_code == 201
    created_body = created.json()
    assert created_body["name"] == "AICTE Scholarships"

    invalid_interval = client.post(
        "/api/v1/admin/sources",
        headers=_auth_header(admin_token),
        json=_source_payload(interval_minutes=10),
    )
    assert invalid_interval.status_code == 422

    listed = client.get("/api/v1/admin/sources", headers=_auth_header(admin_token))
    assert listed.status_code == 200
    listed_body = listed.json()
    assert listed_body["total"] >= 1
    assert len(listed_body["items"]) >= 1


def test_admin_manual_source_trigger(client, create_user_token, monkeypatch):
    admin_token = create_user_token(role="admin")

    created = client.post(
        "/api/v1/admin/sources",
        headers=_auth_header(admin_token),
        json=_source_payload(name="Manual Trigger Source"),
    )
    assert created.status_code == 201
    source_id = created.json()["id"]

    calls: dict[str, str] = {}

    class DummyTask:
        id = "task-123"

    def fake_enqueue(source_id_value: str):
        calls["source_id"] = source_id_value
        return DummyTask()

    monkeypatch.setattr(admin_module, "queue_scrape_single_source", fake_enqueue)

    triggered = client.post(
        f"/api/v1/admin/sources/{source_id}/trigger",
        headers=_auth_header(admin_token),
    )
    assert triggered.status_code == 202
    body = triggered.json()
    assert body["status"] == "queued"
    assert body["task_id"] == "task-123"
    assert calls["source_id"] == source_id
