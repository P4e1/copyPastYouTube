import uuid

from sqlalchemy import text

from app.infrastructure import db


def _auth(client) -> dict:
    mark = uuid.uuid4().hex[:10]
    payload = {
        "email": f"channel-{mark}@example.com",
        "username": f"channel{mark}",
        "password": "secret-pass",
    }
    registered = client.post("/auth/register", json=payload)
    assert registered.status_code == 201
    login = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {
        "user_id": registered.json()["id"],
        "channel_id": registered.json()["channel_id"],
        "headers": {"Authorization": f"Bearer {token}"},
    }


def _video(client, headers, **overrides) -> str:
    payload = {"title": "Ролик", "description": "", "visibility": "public", "grant_user_ids": []}
    payload.update(overrides)
    created = client.post("/videos", json=payload, headers=headers)
    assert created.status_code == 201
    return created.json()["id"]


def _set_status(video_id: str, status: str) -> None:
    with db._engine.begin() as connection:
        connection.execute(
            text("update videos set status = :status where id = :video_id"),
            {"status": status, "video_id": video_id},
        )


def _subscription_count(subscriber_id: str, channel_id: str) -> int:
    with db._engine.connect() as connection:
        return int(
            connection.execute(
                text(
                    "select count(*) from subscriptions where subscriber_id = :subscriber_id and channel_id = :channel_id"
                ),
                {"subscriber_id": subscriber_id, "channel_id": channel_id},
            ).scalar()
        )


def test_repeat_subscribe_does_not_duplicate_and_unsubscribe_removes_row(client):
    owner = _auth(client)
    subscriber = _auth(client)

    first = client.post(f"/channels/{owner['channel_id']}/subscribe", headers=subscriber["headers"])
    second = client.post(f"/channels/{owner['channel_id']}/subscribe", headers=subscriber["headers"])

    assert first.status_code == 200
    assert second.status_code == 200
    assert _subscription_count(subscriber["user_id"], owner["channel_id"]) == 1

    removed = client.request(
        "DELETE",
        f"/channels/{owner['channel_id']}/subscribe",
        headers=subscriber["headers"],
    )
    assert removed.status_code == 200
    assert _subscription_count(subscriber["user_id"], owner["channel_id"]) == 0


def test_owner_channel_shows_unready_and_hidden_viewer_does_not(client):
    owner = _auth(client)
    viewer = _auth(client)
    uploading_id = _video(client, owner["headers"], title="Черновик")
    hidden_id = _video(client, owner["headers"], title="Скрытый")
    ready_id = _video(client, owner["headers"], title="Готовый")
    _set_status(hidden_id, "hidden")
    _set_status(ready_id, "ready")

    owner_view = client.get(f"/channels/{owner['channel_id']}", headers=owner["headers"])
    viewer_view = client.get(f"/channels/{owner['channel_id']}", headers=viewer["headers"])

    assert owner_view.status_code == 200
    assert viewer_view.status_code == 200
    owner_ids = {item["id"]: item for item in owner_view.json()["videos"]}
    viewer_ids = {item["id"] for item in viewer_view.json()["videos"]}
    assert uploading_id in owner_ids
    assert hidden_id in owner_ids
    assert owner_ids[hidden_id]["hidden_mark"] is True
    assert ready_id in owner_ids
    assert viewer_ids == {ready_id}


def test_playlist_items_follow_position(client):
    owner = _auth(client)
    first_id = _video(client, owner["headers"], title="Первый")
    second_id = _video(client, owner["headers"], title="Второй")
    _set_status(first_id, "ready")
    _set_status(second_id, "ready")
    created = client.post(
        "/playlists",
        json={"channel_id": owner["channel_id"], "title": "Подборка", "visibility": "public"},
        headers=owner["headers"],
    )
    assert created.status_code == 201
    playlist_id = created.json()["id"]

    later = client.post(
        f"/playlists/{playlist_id}/items",
        json={"video_id": second_id, "position": 2},
        headers=owner["headers"],
    )
    earlier = client.post(
        f"/playlists/{playlist_id}/items",
        json={"video_id": first_id, "position": 1},
        headers=owner["headers"],
    )
    assert later.status_code == 201
    assert earlier.status_code == 201

    listed = client.get(f"/playlists?channel_id={owner['channel_id']}", headers=owner["headers"])
    assert listed.status_code == 200
    playlist = next(item for item in listed.json()["items"] if item["id"] == playlist_id)
    assert [item["video_id"] for item in playlist["items"]] == [first_id, second_id]
    assert [item["position"] for item in playlist["items"]] == [1, 2]


def test_stranger_cannot_rename_channel_or_fill_foreign_playlist(client):
    owner = _auth(client)
    stranger = _auth(client)
    video_id = _video(client, owner["headers"], title="Чужой ролик")
    _set_status(video_id, "ready")
    created = client.post(
        "/playlists",
        json={"channel_id": owner["channel_id"], "title": "Канал владельца", "visibility": "public"},
        headers=owner["headers"],
    )
    assert created.status_code == 201
    playlist_id = created.json()["id"]

    renamed = client.request(
        "PATCH",
        f"/channels/{owner['channel_id']}",
        json={"name": "Взломанное имя"},
        headers=stranger["headers"],
    )
    added = client.post(
        f"/playlists/{playlist_id}/items",
        json={"video_id": video_id, "position": 1},
        headers=stranger["headers"],
    )

    assert renamed.status_code == 403
    assert added.status_code == 403
    channel = client.get(f"/channels/{owner['channel_id']}", headers=owner["headers"])
    assert channel.json()["name"] != "Взломанное имя"
    listed = client.get(f"/playlists?channel_id={owner['channel_id']}", headers=owner["headers"])
    playlist = next(item for item in listed.json()["items"] if item["id"] == playlist_id)
    assert playlist["items"] == []
