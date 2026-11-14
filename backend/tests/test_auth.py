import uuid

from sqlalchemy import text

from app.infrastructure import db


def _count(sql: str, **params) -> int:
    with db._engine.connect() as connection:
        return int(connection.execute(text(sql), params).scalar())


def _registration(suffix: str | None = None) -> dict:
    mark = suffix or uuid.uuid4().hex
    return {
        "email": f"user-{mark}@example.com",
        "username": f"user{mark[:8]}",
        "password": "secret-pass",
    }


def test_register_creates_user_and_channel(client):
    payload = _registration()

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["username"] == payload["username"]
    assert body["role"] == "user"
    assert body["channel_id"]
    assert "password" not in body
    assert "password_hash" not in body
    assert _count("select count(*) from users where email = :email", email=payload["email"]) == 1
    assert _count(
        "select count(*) from channels where owner_id = :owner_id",
        owner_id=body["id"],
    ) == 1


def test_duplicate_email_does_not_create_second_user(client):
    payload = _registration()
    assert client.post("/auth/register", json=payload).status_code == 201

    duplicate = client.post("/auth/register", json={**payload, "username": "other-name"})

    assert duplicate.status_code == 409
    assert "password" not in duplicate.json()
    assert _count("select count(*) from users where email = :email", email=payload["email"]) == 1


def test_wrong_password_does_not_issue_token(client):
    payload = _registration()
    assert client.post("/auth/register", json=payload).status_code == 201

    response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "wrong-pass"},
    )

    assert response.status_code == 401
    assert "access_token" not in response.json()
    assert "password" not in response.json()


def test_me_requires_token_and_returns_user_role(client):
    payload = _registration()
    assert client.post("/auth/register", json=payload).status_code == 201
    anonymous = client.get("/auth/me")
    assert anonymous.status_code == 401

    login = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert "password" not in login.json()
    assert "password_hash" not in login.json()

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me.status_code == 200
    body = me.json()
    assert body["role"] == "user"
    assert body["email"] == payload["email"]
    assert "password" not in body
    assert "password_hash" not in body
