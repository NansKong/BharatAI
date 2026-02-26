import uuid
from datetime import datetime, timedelta, timezone


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_student(client, email: str) -> str:
    payload = {
        "name": "Feed Student",
        "email": email,
        "password": "StudentPass1",
        "college": "IIT Bombay",
        "degree": "B.Tech",
        "year": 3,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()["access_token"]


def _opportunity_payload(title: str, description: str, domain: str):
    return {
        "title": title,
        "description": description,
        "institution": "IIT Bombay",
        "domain": domain,
        "deadline": (datetime.now(timezone.utc) + timedelta(days=21)).isoformat(),
        "source_url": f"https://example.com/opportunity/{uuid.uuid4().hex}",
        "application_link": "https://example.com/apply",
    }


def test_personalized_feed_reorders_after_profile_update(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(
        client, f"feed-{uuid.uuid4().hex[:8]}@example.com"
    )

    finance_create = client.post(
        "/api/v1/opportunities",
        headers=_auth_header(admin_token),
        json=_opportunity_payload(
            "Finance Fellowship",
            "Equity valuation and financial modeling internship for students.",
            "finance",
        ),
    )
    assert finance_create.status_code == 201

    ai_create = client.post(
        "/api/v1/opportunities",
        headers=_auth_header(admin_token),
        json=_opportunity_payload(
            "AI Research Internship",
            "Machine learning and deep learning project with Python.",
            "ai_ds",
        ),
    )
    assert ai_create.status_code == 201

    finance_profile = client.put(
        "/api/v1/profile",
        headers=_auth_header(student_token),
        json={"skills": ["finance", "valuation"], "interests": ["finance"]},
    )
    assert finance_profile.status_code == 200

    first_feed = client.get("/api/v1/feed", headers=_auth_header(student_token))
    assert first_feed.status_code == 200
    first_items = first_feed.json()["items"]
    assert len(first_items) >= 2
    assert first_items[0]["domain"] == "finance"

    ai_profile = client.put(
        "/api/v1/profile",
        headers=_auth_header(student_token),
        json={"skills": ["machine learning", "python"], "interests": ["ai", "ml"]},
    )
    assert ai_profile.status_code == 200

    second_feed = client.get("/api/v1/feed", headers=_auth_header(student_token))
    assert second_feed.status_code == 200
    second_items = second_feed.json()["items"]
    assert len(second_items) >= 2
    assert second_items[0]["domain"] == "ai_ds"


def test_cold_start_feed_returns_opportunities(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(
        client, f"cold-{uuid.uuid4().hex[:8]}@example.com"
    )

    created = client.post(
        "/api/v1/opportunities",
        headers=_auth_header(admin_token),
        json=_opportunity_payload(
            "Open Innovation Program",
            "General innovation opportunity with upcoming deadline.",
            "management",
        ),
    )
    assert created.status_code == 201

    feed_res = client.get("/api/v1/feed", headers=_auth_header(student_token))
    assert feed_res.status_code == 200
    body = feed_res.json()
    assert body["cold_start"] is True
    assert len(body["items"]) >= 1
