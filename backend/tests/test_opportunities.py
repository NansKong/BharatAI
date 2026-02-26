import uuid
from datetime import datetime, timedelta, timezone


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_student(client, email: str) -> str:
    payload = {
        "name": "Student Tester",
        "email": email,
        "password": "StudentPass1",
        "college": "IIT Bombay",
        "degree": "B.Tech",
        "year": 3,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()["access_token"]


def _opportunity_payload(**overrides):
    payload = {
        "title": "AI Fellowship Program 2026",
        "description": "This fellowship provides mentorship, funding, and project opportunities.",
        "institution": "IIT Bombay",
        "domain": "ai_ds",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=45)).isoformat(),
        "source_url": f"https://example.com/opportunity/{uuid.uuid4().hex}",
        "application_link": "https://example.com/apply",
        "eligibility": "Open for final year undergraduates.",
        "is_verified": False,
    }
    payload.update(overrides)
    return payload


def test_opportunity_crud_and_soft_delete_admin_only(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(
        client, email=f"student-{uuid.uuid4().hex[:8]}@example.com"
    )

    create_forbidden = client.post(
        "/api/v1/opportunities",
        headers=_auth_header(student_token),
        json=_opportunity_payload(title="Forbidden Create"),
    )
    assert create_forbidden.status_code == 403

    create_ok = client.post(
        "/api/v1/opportunities",
        headers=_auth_header(admin_token),
        json=_opportunity_payload(title="Admin Create"),
    )
    assert create_ok.status_code == 201
    created = create_ok.json()
    opportunity_id = created["id"]

    update_ok = client.put(
        f"/api/v1/opportunities/{opportunity_id}",
        headers=_auth_header(admin_token),
        json={"title": "Admin Updated Title"},
    )
    assert update_ok.status_code == 200
    assert update_ok.json()["title"] == "Admin Updated Title"

    delete_ok = client.delete(
        f"/api/v1/opportunities/{opportunity_id}",
        headers=_auth_header(admin_token),
    )
    assert delete_ok.status_code == 204

    get_deleted = client.get(
        f"/api/v1/opportunities/{opportunity_id}",
        headers=_auth_header(student_token),
    )
    assert get_deleted.status_code == 404


def test_opportunity_filters_and_cursor_pagination(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(
        client, email=f"student-{uuid.uuid4().hex[:8]}@example.com"
    )

    first_cs = client.post(
        "/api/v1/opportunities",
        headers=_auth_header(admin_token),
        json=_opportunity_payload(
            title="CS Research Internship 2026",
            domain="cs",
            institution="IIT Delhi",
            source_url=f"https://example.com/cs/{uuid.uuid4().hex}",
        ),
    )
    assert first_cs.status_code == 201

    second_finance = client.post(
        "/api/v1/opportunities",
        headers=_auth_header(admin_token),
        json=_opportunity_payload(
            title="Finance Scholarship 2026",
            domain="finance",
            institution="IIM Ahmedabad",
            source_url=f"https://example.com/finance/{uuid.uuid4().hex}",
        ),
    )
    assert second_finance.status_code == 201

    third_cs = client.post(
        "/api/v1/opportunities",
        headers=_auth_header(admin_token),
        json=_opportunity_payload(
            title="CS Systems Fellowship 2026",
            domain="cs",
            institution="IISc Bengaluru",
            source_url=f"https://example.com/cs/{uuid.uuid4().hex}",
        ),
    )
    assert third_cs.status_code == 201

    by_domain = client.get(
        "/api/v1/opportunities",
        headers=_auth_header(student_token),
        params={"domain": "cs", "limit": 1},
    )
    assert by_domain.status_code == 200
    by_domain_body = by_domain.json()
    assert by_domain_body["total"] == 2
    assert by_domain_body["limit"] == 1
    assert len(by_domain_body["items"]) == 1
    assert by_domain_body["items"][0]["domain"] == "cs"
    assert by_domain_body["next_cursor"] is not None

    next_page = client.get(
        "/api/v1/opportunities",
        headers=_auth_header(student_token),
        params={"domain": "cs", "limit": 1, "cursor": by_domain_body["next_cursor"]},
    )
    assert next_page.status_code == 200
    next_page_body = next_page.json()
    assert next_page_body["total"] == 2
    assert len(next_page_body["items"]) == 1
    assert next_page_body["items"][0]["domain"] == "cs"
    assert next_page_body["items"][0]["id"] != by_domain_body["items"][0]["id"]
    assert next_page_body["next_cursor"] is None

    by_keyword = client.get(
        "/api/v1/opportunities",
        headers=_auth_header(student_token),
        params={"keyword": "Finance"},
    )
    assert by_keyword.status_code == 200
    keyword_body = by_keyword.json()
    assert keyword_body["total"] >= 1
    assert any("Finance" in item["title"] for item in keyword_body["items"])


def test_opportunity_invalid_cursor_rejected(client, create_user_token):
    student_token = _register_student(
        client, email=f"student-{uuid.uuid4().hex[:8]}@example.com"
    )
    response = client.get(
        "/api/v1/opportunities",
        headers=_auth_header(student_token),
        params={"cursor": "not-a-valid-cursor"},
    )
    assert response.status_code == 422
