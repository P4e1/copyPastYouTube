import uuid

from sqlalchemy import text

from app.infrastructure import db


def _auth(client, prefix: str = "media") -> dict:
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
    return {"headers": {"Authorization": f"Bearer {login.json()['access_token']}"}}


def _create(client, headers, **overrides):
    payload = {"title": "Загрузка", "description": "", "visibility": "public", "grant_user_ids": []}
    payload.update(overrides)
    return client.post("/videos", json=payload, headers=headers)


def _job_count(video_id: str) -> int:
    with db._engine.connect() as connection:
        return connection.execute(
            text("select count(*) from media_jobs where video_id = :video_id"),
            {"video_id": video_id},
        ).scalar_one()


def test_create_returns_upload_url_and_uploading_status(client):
    owner = _auth(client)

    created = _create(client, owner["headers"])

    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "uploading"
    assert body["upload_url"] == f"https://storage.test/{body['object_key']}"


def test_stranger_cannot_complete_upload(client):
    owner = _auth(client, "owner")
    stranger = _auth(client, "stranger")
    created = _create(client, owner["headers"])
    video_id = created.json()["id"]

    response = client.post(f"/videos/{video_id}/complete", headers=stranger["headers"])

    assert response.status_code == 403
    assert client.get(f"/videos/{video_id}", headers=owner["headers"]).json()["status"] == "uploading"
    assert _job_count(video_id) == 0


def test_wrong_content_type_is_rejected_without_job(client, app):
    owner = _auth(client)
    created = _create(client, owner["headers"])
    body = created.json()
    app.state.object_storage.put_bytes(body["object_key"], b"not-a-video", "text/plain")

    response = client.post(f"/videos/{body['id']}/complete", headers=owner["headers"])

    assert response.status_code == 422
    assert client.get(f"/videos/{body['id']}", headers=owner["headers"]).json()["status"] == "uploading"
    assert _job_count(body["id"]) == 0


def test_feed_skips_video_before_ready(client):
    owner = _auth(client)
    created = _create(client, owner["headers"], title="Ещё не готово")
    video_id = created.json()["id"]

    items = client.get("/feed").json()["items"]

    assert video_id not in {item["id"] for item in items}


def test_private_without_grant_has_no_playback_url(client):
    owner = _auth(client, "owner")
    stranger = _auth(client, "stranger")
    created = _create(client, owner["headers"], visibility="private")
    video_id = created.json()["id"]
    with db._engine.begin() as connection:
        connection.execute(text("update videos set status = 'ready' where id = :video_id"), {"video_id": video_id})

    denied = client.get(f"/videos/{video_id}/playback", headers=stranger["headers"])
    allowed = client.get(f"/videos/{video_id}/playback", headers=owner["headers"])

    assert denied.status_code == 404
    assert allowed.status_code == 200
    assert allowed.json()["url"].startswith("https://storage.test/")
