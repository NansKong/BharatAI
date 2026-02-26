from app.api.v1 import auth as auth_module
from fastapi.responses import RedirectResponse


def _register_user(
    client, email: str = "student1@example.com", password: str = "StudentPass1"
):
    payload = {
        "name": "Student One",
        "email": email,
        "password": password,
        "college": "IIT Bombay",
        "degree": "B.Tech CSE",
        "year": 3,
    }
    return client.post("/api/v1/auth/register", json=payload)


def _login_user(
    client, email: str = "student1@example.com", password: str = "StudentPass1"
):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )


def test_register_login_refresh_logout_flow(client):
    register_res = _register_user(client)
    assert register_res.status_code == 201
    register_body = register_res.json()
    assert "access_token" in register_body
    assert "refresh_token" in register_body

    login_res = _login_user(client)
    assert login_res.status_code == 200
    login_body = login_res.json()
    access_token = login_body["access_token"]
    refresh_token = login_body["refresh_token"]

    # Refresh should rotate token and invalidate old refresh JTI
    refresh_res = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_res.status_code == 200
    rotated = refresh_res.json()
    assert rotated["refresh_token"] != refresh_token

    stale_refresh_res = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert stale_refresh_res.status_code == 401

    protected_before_logout = client.get(
        "/api/v1/opportunities",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert protected_before_logout.status_code == 200

    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_res.status_code == 204

    protected_after_logout = client.get(
        "/api/v1/opportunities",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert protected_after_logout.status_code == 401


def test_google_oauth_mock_flow(client, monkeypatch):
    class DummyGoogleOAuth:
        async def authorize_redirect(self, request, redirect_uri):
            return RedirectResponse(
                url="https://accounts.google.com/o/oauth2/auth?state=test"
            )

        async def authorize_access_token(self, request):
            return {
                "userinfo": {
                    "sub": "google-sub-001",
                    "email": "google.user@example.com",
                    "name": "Google User",
                }
            }

    monkeypatch.setattr(
        auth_module.settings,
        "GOOGLE_CLIENT_ID",
        "dummy-google-client-id",
        raising=False,
    )
    monkeypatch.setattr(
        auth_module.settings,
        "GOOGLE_CLIENT_SECRET",
        "dummy-google-client-secret",
        raising=False,
    )
    monkeypatch.setattr(
        auth_module.settings,
        "GOOGLE_REDIRECT_URI",
        "http://testserver/api/v1/auth/google/callback",
        raising=False,
    )
    monkeypatch.setattr(auth_module.oauth, "google", DummyGoogleOAuth(), raising=False)

    start_res = client.get("/api/v1/auth/google", follow_redirects=False)
    assert start_res.status_code in (302, 307)

    callback_res = client.get("/api/v1/auth/google/callback")
    assert callback_res.status_code == 200
    body = callback_res.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_admin_endpoint_forbidden_for_student_token(client):
    register_res = _register_user(client, email="student-rbac@example.com")
    assert register_res.status_code == 201
    student_token = register_res.json()["access_token"]

    admin_res = client.get(
        "/api/v1/admin/sources",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert admin_res.status_code == 403
