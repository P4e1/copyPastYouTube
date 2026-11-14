import uuid

from sqlalchemy import text

from app.infrastructure import db


def _auth(client, prefix: str = "mod") -> dict:
    mark = uuid.uuid4().hex[:10]
    payload = {
        "email": f"{prefix}-{mark}@example.com",
        "username": f"{prefix}{mark}",
        "password": "secret-pass",
    }
    registered = client.post("/auth/register", json=payload)
    assert registered.status_code == 201
    login = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    return {
        "user_id": registered.json()["id"],
        "username": payload["username"],
        "headers": {"Authorization": f"Bearer {login.json()['access_token']}"},
    }


def _promote(user_id: str, role: str) -> None:
    with db._engine.begin() as connection:
        connection.execute(
            text("update users set role = :role where id = :user_id"),
            {"role": role, "user_id": user_id},
        )


def _ready_public(client, headers) -> str:
    created = client.post(
        "/videos",
        json={"title": "На проверке", "description": "", "visibility": "public", "grant_user_ids": []},
        headers=headers,
    )
    assert created.status_code == 201
    video_id = created.json()["id"]
    with db._engine.begin() as connection:
        connection.execute(
            text("update videos set status = 'ready' where id = :video_id"),
            {"video_id": video_id},
        )
    return video_id


def test_user_report_is_visible_to_moderator(client):
    author = _auth(client, "author")
    reporter = _auth(client, "reporter")
    moderator = _auth(client, "moderator")
    _promote(moderator["user_id"], "moderator")
    video_id = _ready_public(client, author["headers"])

    created = client.post(
        "/reports",
        json={"video_id": video_id, "reason": "спам"},
        headers=reporter["headers"],
    )
    assert created.status_code == 201

    listed = client.get("/moderation/reports", headers=moderator["headers"])
    assert listed.status_code == 200
    item = next(row for row in listed.json()["items"] if row["video_id"] == video_id)
    assert item["status"] == "open"
    assert item["reason"] == "спам"
    assert item["video_title"] == "На проверке"
    assert item["reporter_username"] == reporter["username"]


def test_hide_removes_video_from_feed_and_marks_owner_card(client):
    author = _auth(client, "author")
    viewer = _auth(client, "viewer")
    moderator = _auth(client, "moderator")
    _promote(moderator["user_id"], "moderator")
    video_id = _ready_public(client, author["headers"])
    assert client.post(
        "/reports",
        json={"video_id": video_id, "reason": "нарушение"},
        headers=viewer["headers"],
    ).status_code == 201
    assert video_id in {item["id"] for item in client.get("/feed").json()["items"]}

    hidden = client.post(f"/moderation/videos/{video_id}/hide", headers=moderator["headers"])

    assert hidden.status_code == 200
    assert video_id not in {item["id"] for item in client.get("/feed").json()["items"]}
    assert client.get(f"/videos/{video_id}", headers=viewer["headers"]).status_code == 404
    owner_card = client.get(f"/videos/{video_id}", headers=author["headers"])
    assert owner_card.status_code == 200
    assert owner_card.json()["hidden_mark"] is True


def test_user_cannot_open_moderation_queue(client):
    user = _auth(client, "user")

    response = client.get("/moderation/reports", headers=user["headers"])

    assert response.status_code == 403


def test_admin_assigns_moderator(client):
    admin = _auth(client, "admin")
    target = _auth(client, "target")
    _promote(admin["user_id"], "admin")

    response = client.request(
        "PATCH",
        f"/admin/users/{target['user_id']}/role",
        json={"role": "moderator"},
        headers=admin["headers"],
    )

    assert response.status_code == 200
    assert response.json()["role"] == "moderator"
    me = client.get("/auth/me", headers=target["headers"])
    assert me.json()["role"] == "moderator"


def test_moderator_cannot_assign_admin(client):
    moderator = _auth(client, "moderator")
    target = _auth(client, "target")
    _promote(moderator["user_id"], "moderator")

    response = client.request(
        "PATCH",
        f"/admin/users/{target['user_id']}/role",
        json={"role": "admin"},
        headers=moderator["headers"],
    )

    assert response.status_code == 403
    assert client.get("/auth/me", headers=target["headers"]).json()["role"] == "user"
