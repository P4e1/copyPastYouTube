import uuid

from sqlalchemy import text

from app.infrastructure import db


def _auth(client) -> dict:
    mark = uuid.uuid4().hex[:10]
    payload = {
        "email": f"video-{mark}@example.com",
        "username": f"video{mark}",
        "password": "secret-pass",
    }
    assert client.post("/auth/register", json=payload).status_code == 201
    login = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    body = login.json()
    return {
        "token": body["access_token"],
        "user_id": body["user"]["id"],
        "headers": {"Authorization": f"Bearer {body['access_token']}"},
    }


def _create(client, headers, **overrides):
    payload = {
        "title": "Море",
        "description": "описание",
        "visibility": "public",
        "grant_user_ids": [],
    }
    payload.update(overrides)
    return client.post("/videos", json=payload, headers=headers)


def _set_status(video_id: str, status: str, visibility: str | None = None) -> None:
    sql = "update videos set status = :status"
    params = {"status": status, "video_id": video_id}
    if visibility is not None:
        sql += ", visibility = :visibility"
        params["visibility"] = visibility
    sql += " where id = :video_id"
    with db._engine.begin() as connection:
        connection.execute(text(sql), params)


def test_create_video_is_uploading_and_rejects_client_object_key(client):
    owner = _auth(client)

    created = _create(client, owner["headers"])

    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "uploading"
    assert body["object_key"].startswith("videos/")
    assert body["upload_url"] == f"https://storage.test/{body['object_key']}"

    rejected = _create(client, owner["headers"], object_key="client/picked.mp4")
    assert rejected.status_code == 422


def test_feed_hides_video_until_public_and_ready(client):
    owner = _auth(client)
    created = _create(client, owner["headers"], title="Лента")
    assert created.status_code == 201
    video_id = created.json()["id"]

    before = client.get("/feed").json()["items"]
    assert video_id not in {item["id"] for item in before}

    _set_status(video_id, "ready")
    after = client.get("/feed").json()["items"]
    assert video_id in {item["id"] for item in after}

    _set_status(video_id, "ready", "unlisted")
    hidden = client.get("/feed").json()["items"]
    assert video_id not in {item["id"] for item in hidden}


def test_search_matches_title_case_and_skips_unlisted_and_private(client):
    owner = _auth(client)
    stranger = _auth(client)
    mark = uuid.uuid4().hex[:8]
    public = _create(client, owner["headers"], title=f"Blue {mark} Sea", visibility="public")
    unlisted = _create(client, owner["headers"], title=f"Blue {mark} Link", visibility="unlisted")
    private = _create(
        client,
        owner["headers"],
        title=f"Blue {mark} Closed",
        visibility="private",
        grant_user_ids=[stranger["user_id"]],
    )
    assert public.status_code == 201
    assert unlisted.status_code == 201
    assert private.status_code == 201
    public_id = public.json()["id"]
    unlisted_id = unlisted.json()["id"]
    private_id = private.json()["id"]
    _set_status(public_id, "ready")
    _set_status(unlisted_id, "ready")
    _set_status(private_id, "ready")

    found = client.get(f"/search?q=blue {mark}").json()["items"]
    ids = {item["id"] for item in found}

    assert ids == {public_id}


def test_private_card_is_not_found_for_stranger(client):
    owner = _auth(client)
    stranger = _auth(client)
    grantee = _auth(client)
    created = _create(
        client,
        owner["headers"],
        title="Закрытое",
        visibility="private",
        grant_user_ids=[grantee["user_id"]],
    )
    assert created.status_code == 201
    video_id = created.json()["id"]
    _set_status(video_id, "ready")

    missing = client.get(f"/videos/{video_id}", headers=stranger["headers"])
    assert missing.status_code == 404

    allowed = client.get(f"/videos/{video_id}", headers=grantee["headers"])
    assert allowed.status_code == 200
    assert allowed.json()["id"] == video_id
