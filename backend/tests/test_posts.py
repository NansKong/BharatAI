"""Integration tests for Phase 6 Posts: CRUD, like toggle, spam, report auto-flag, comments."""

from __future__ import annotations

import uuid


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_student(client, email: str | None = None) -> str:
    email = email or f"post-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Post User",
            "email": email,
            "password": "StudentPass1",
            "college": "BITS Pilani",
            "degree": "B.E.",
            "year": 3,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def test_create_post(client, create_user_token):
    token = _register_student(client)
    res = client.post(
        "/api/v1/community/posts",
        headers=_auth(token),
        json={"content": "Hello BharatAI community! Excited to be here."},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["content"] == "Hello BharatAI community! Excited to be here."
    assert body["likes_count"] == 0


def test_post_spam_url_limit(client, create_user_token):
    token = _register_student(client)
    urls = " ".join([f"https://example.com/{i}" for i in range(6)])
    res = client.post(
        "/api/v1/community/posts",
        headers=_auth(token),
        json={"content": f"Check these out: {urls}"},
    )
    assert res.status_code == 422
    assert "url" in res.json()["detail"].lower()


def test_like_toggle_idempotent(client, create_user_token):
    token = _register_student(client)

    # Create post
    post = client.post(
        "/api/v1/community/posts",
        headers=_auth(token),
        json={"content": "Like toggle test post, please interact!"},
    )
    assert post.status_code == 201
    post_id = post.json()["id"]

    # Like it
    r1 = client.post(f"/api/v1/community/posts/{post_id}/like", headers=_auth(token))
    assert r1.status_code == 200
    assert r1.json()["liked"] is True
    assert r1.json()["likes_count"] == 1

    # Like again — should unlike
    r2 = client.post(f"/api/v1/community/posts/{post_id}/like", headers=_auth(token))
    assert r2.status_code == 200
    assert r2.json()["liked"] is False
    assert r2.json()["likes_count"] == 0


def test_report_auto_flag_at_3(client, create_user_token):
    author_token = _register_student(client)
    reporter1_token = _register_student(client)
    reporter2_token = _register_student(client)
    reporter3_token = _register_student(client)

    # Author creates post
    post = client.post(
        "/api/v1/community/posts",
        headers=_auth(author_token),
        json={"content": "This is a controversial post that will be reported."},
    )
    post_id = post.json()["id"]

    # Three different users report it
    for reporter_token in [reporter1_token, reporter2_token, reporter3_token]:
        client.post(
            f"/api/v1/community/posts/{post_id}/report", headers=_auth(reporter_token)
        )

    # Post should be hidden from feed
    feed = client.get("/api/v1/community/posts", headers=_auth(author_token))
    assert feed.status_code == 200
    ids_in_feed = [p["id"] for p in feed.json()]
    assert post_id not in ids_in_feed


def test_add_and_list_comments(client, create_user_token):
    token = _register_student(client)

    post = client.post(
        "/api/v1/community/posts",
        headers=_auth(token),
        json={"content": "Post to test comment functionality end to end."},
    )
    post_id = post.json()["id"]

    c1 = client.post(
        f"/api/v1/community/posts/{post_id}/comments",
        headers=_auth(token),
        json={"content": "Great post!"},
    )
    assert c1.status_code == 201
    assert c1.json()["content"] == "Great post!"

    comments = client.get(
        f"/api/v1/community/posts/{post_id}/comments", headers=_auth(token)
    )
    assert comments.status_code == 200
    assert len(comments.json()) == 1
    assert comments.json()[0]["content"] == "Great post!"
