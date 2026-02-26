import uuid

import fitz


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_student(client, email: str) -> str:
    payload = {
        "name": "Resume Student",
        "email": email,
        "password": "StudentPass1",
        "college": "IIT Bombay",
        "degree": "B.Tech",
        "year": 2,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()["access_token"]


def _build_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_resume_upload_accepts_valid_pdf(client):
    student_token = _register_student(
        client, f"resume-{uuid.uuid4().hex[:8]}@example.com"
    )
    pdf_bytes = _build_pdf_bytes("IIT Bombay B.Tech 2027 Python ML")

    response = client.post(
        "/api/v1/profile/resume",
        headers=_auth_header(student_token),
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["resume_path"]
    assert body["extracted_skills_count"] >= 1


def test_resume_upload_rejects_non_pdf(client):
    student_token = _register_student(
        client, f"resume-{uuid.uuid4().hex[:8]}@example.com"
    )

    response = client.post(
        "/api/v1/profile/resume",
        headers=_auth_header(student_token),
        files={"file": ("resume.txt", b"plain text", "text/plain")},
    )

    assert response.status_code == 422
