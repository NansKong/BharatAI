"""Unit + integration tests for Phase 5 checklist generation."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.ai.application_ai import generate_checklist

# ---------------------------------------------------------------------------
# Unit tests — pure function, no DB needed
# ---------------------------------------------------------------------------


def test_checklist_generated_from_eligibility_text():
    """generate_checklist extracts relevant items from eligibility text."""
    eligibility = (
        "Applicants must submit a resume, statement of purpose, and two recommendation letters. "
        "Minimum CGPA 7.5. Final year students only. "
        "Shortlisted candidates will be invited for an interview."
    )
    items = generate_checklist(eligibility)
    assert isinstance(items, list)
    assert len(items) >= 3

    text = " ".join(items).lower()
    assert "resume" in text or "cv" in text
    assert "statement of purpose" in text or "sop" in text
    assert "recommendation" in text or "reference" in text
    assert "interview" in text


def test_checklist_fallback_for_empty_eligibility():
    """generate_checklist returns generic items when eligibility text is empty."""
    items = generate_checklist("")
    assert isinstance(items, list)
    assert len(items) > 0  # must return at least generic items

    items_none = generate_checklist(None)
    assert isinstance(items_none, list)
    assert len(items_none) > 0


def test_checklist_no_duplicate_items():
    """Checklist items must be unique even when text triggers multiple patterns."""
    eligibility = "Resume required. Please attach your CV. A statement of purpose is mandatory. SOP should be 500 words."
    items = generate_checklist(eligibility)
    assert len(items) == len(set(items)), "Checklist contains duplicate items"


# ---------------------------------------------------------------------------
# Integration test — via API
# ---------------------------------------------------------------------------


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_student(client, email: str | None = None) -> str:
    email = email or f"cl-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Checklist Student",
            "email": email,
            "password": "StudentPass1",
            "college": "IIT Delhi",
            "degree": "B.Tech",
            "year": 3,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def test_checklist_endpoint_returns_items(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    opp = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json={
            "title": "Checklist Opportunity",
            "description": "An opportunity to test the checklist endpoint for applications.",
            "institution": "IIT Delhi",
            "domain": "cs",
            "deadline": (datetime.now(timezone.utc) + timedelta(days=25)).isoformat(),
            "source_url": f"https://example.com/{uuid.uuid4().hex}",
            "application_link": "https://example.com/apply",
            "eligibility": "Submit resume and transcript. Interview required.",
        },
    )
    assert opp.status_code == 201
    opp_id = opp.json()["id"]

    app = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp_id},
    )
    assert app.status_code == 201
    app_id = app.json()["id"]

    res = client.get(
        f"/api/v1/applications/{app_id}/checklist", headers=_auth(student_token)
    )
    assert res.status_code == 200
    body = res.json()
    assert "items" in body
    assert isinstance(body["items"], list)
    assert len(body["items"]) >= 1
    # Should detect resume and interview from eligibility
    combined = " ".join(body["items"]).lower()
    assert "resume" in combined or "cv" in combined


def test_checklist_endpoint_for_no_eligibility(client, create_user_token):
    admin_token = create_user_token(role="admin")
    student_token = _register_student(client)

    opp = client.post(
        "/api/v1/opportunities",
        headers=_auth(admin_token),
        json={
            "title": "No Eligibility Opp",
            "description": "An opportunity with no eligibility text to test fallback checklist.",
            "institution": "BITS Pilani",
            "domain": "management",
            "deadline": (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),
            "source_url": f"https://example.com/{uuid.uuid4().hex}",
            "application_link": "https://example.com/apply",
        },
    )
    assert opp.status_code == 201
    opp_id = opp.json()["id"]

    app = client.post(
        "/api/v1/applications",
        headers=_auth(student_token),
        json={"opportunity_id": opp_id},
    )
    app_id = app.json()["id"]

    res = client.get(
        f"/api/v1/applications/{app_id}/checklist", headers=_auth(student_token)
    )
    assert res.status_code == 200
    body = res.json()
    # Should return generic items, not empty
    assert len(body["items"]) >= 1
