import uuid

from sqlalchemy import text

from app.infrastructure import db


def _auth(client) -> dict:
    mark = uuid.uuid4().hex[:10]
    payload = {
        "email": f"watch-{mark}@example.com",
        "username": f"watch{mark}",
        "password": "secret-pass",
    }
    assert client.post("/auth/register", json=payload).status_code == 201
    login = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    body = login.json()
    return {
        "user_id": body["user"]["id"],
        "headers": {"Authorization": f"Bearer {body['access_token']}"},
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


def _view_count(video_id: str) -> int:
    with db._engine.connect() as connection:
        return int(
            connection.execute(
                text("select view_count from videos where id = :video_id"),
                {"video_id": video_id},
            ).scalar()
        )


def _like_rows(video_id: str, user_id: str) -> list[int]:
    with db._engine.connect() as connection:
        return list(
            connection.execute(
                text("select value from likes where video_id = :video_id and user_id = :user_id"),
                {"video_id": video_id, "user_id": user_id},
            ).scalars()
        )


def test_view_of_ready_video_increments_counter(client):
    owner = _auth(client)
    video_id = _video(client, owner["headers"])
    _set_status(video_id, "ready")

    response = client.post(f"/videos/{video_id}/view", headers=owner["headers"])

    assert response.status_code == 200
    assert response.json()["view_count"] == 1
    assert _view_count(video_id) == 1


def test_view_of_closed_video_is_404_and_does_not_change_counter(client):
    owner = _auth(client)
    stranger = _auth(client)
    private_id = _video(client, owner["headers"], visibility="private")
    hidden_id = _video(client, owner["headers"], title="Скрытый")
    _set_status(private_id, "ready")
    _set_status(hidden_id, "hidden")

    private_view = client.post(f"/videos/{private_id}/view", headers=stranger["headers"])
    hidden_view = client.post(f"/videos/{hidden_id}/view", headers=stranger["headers"])

    assert private_view.status_code == 404
    assert hidden_view.status_code == 404
    assert _view_count(private_id) == 0
    assert _view_count(hidden_id) == 0


def test_repeat_like_updates_value_without_second_row(client):
    owner = _auth(client)
    video_id = _video(client, owner["headers"])
    _set_status(video_id, "ready")

    first = client.post(f"/videos/{video_id}/like", json={"value": 1}, headers=owner["headers"])
    second = client.post(f"/videos/{video_id}/like", json={"value": -1}, headers=owner["headers"])

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["value"] == -1
    assert _like_rows(video_id, owner["user_id"]) == [-1]


def test_guest_reads_public_comments_and_not_private(client):
    owner = _auth(client)
    public_id = _video(client, owner["headers"])
    private_id = _video(client, owner["headers"], visibility="private", title="Закрытый")
    _set_status(public_id, "ready")
    _set_status(private_id, "ready")
    created = client.post(
        f"/videos/{public_id}/comments",
        json={"body": "Видно всем"},
        headers=owner["headers"],
    )
    assert created.status_code == 201
    private_comment = client.post(
        f"/videos/{private_id}/comments",
        json={"body": "Секрет"},
        headers=owner["headers"],
    )
    assert private_comment.status_code == 201

    public_list = client.get(f"/videos/{public_id}/comments")
    private_list = client.get(f"/videos/{private_id}/comments")

    assert public_list.status_code == 200
    assert public_list.json()["items"][0]["body"] == "Видно всем"
    assert private_list.status_code == 404


def test_comment_is_listed_and_reply_keeps_parent(client):
    owner = _auth(client)
    video_id = _video(client, owner["headers"])
    _set_status(video_id, "ready")

    created = client.post(
        f"/videos/{video_id}/comments",
        json={"body": "Первый"},
        headers=owner["headers"],
    )
    assert created.status_code == 201
    comment_id = created.json()["id"]

    reply = client.post(
        f"/videos/{video_id}/comments",
        json={"body": "Ответ", "parent_id": comment_id},
        headers=owner["headers"],
    )
    assert reply.status_code == 201
    assert reply.json()["parent_id"] == comment_id

    listed = client.get(f"/videos/{video_id}/comments", headers=owner["headers"])
    assert listed.status_code == 200
    by_id = {item["id"]: item for item in listed.json()["items"]}
    assert by_id[comment_id]["body"] == "Первый"
    assert by_id[reply.json()["id"]]["parent_id"] == comment_id


def _set_visibility(video_id: str, visibility: str) -> None:
    with db._engine.begin() as connection:
        connection.execute(
            text("update videos set visibility = :visibility where id = :video_id"),
            {"visibility": visibility, "video_id": video_id},
        )


def test_history_keeps_each_watched_video_once_and_newest_first(client):
    owner = _auth(client)
    viewer = _auth(client)
    first = _video(client, owner["headers"], title="Первый")
    second = _video(client, owner["headers"], title="Второй")
    _set_status(first, "ready")
    _set_status(second, "ready")

    guest = client.get("/history")
    empty = client.get("/history", headers=viewer["headers"])
    client.post(f"/videos/{first}/view", headers=viewer["headers"])
    client.post(f"/videos/{second}/view", headers=viewer["headers"])
    listed = client.get("/history", headers=viewer["headers"])
    client.post(f"/videos/{first}/view", headers=viewer["headers"])
    repeated = client.get("/history", headers=viewer["headers"])
    _set_visibility(first, "private")
    closed = client.get("/history", headers=viewer["headers"])

    assert guest.status_code == 401
    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert [item["id"] for item in listed.json()["items"]] == [second, first]
    assert listed.json()["items"][0]["title"] == "Второй"
    assert [item["id"] for item in repeated.json()["items"]] == [first, second]
    assert [item["id"] for item in closed.json()["items"]] == [second]
    assert _view_count(first) == 2


def test_stranger_cannot_delete_someone_elses_comment(client):
    owner = _auth(client)
    stranger = _auth(client)
    video_id = _video(client, owner["headers"])
    _set_status(video_id, "ready")
    created = client.post(
        f"/videos/{video_id}/comments",
        json={"body": "Мой комментарий"},
        headers=owner["headers"],
    )
    assert created.status_code == 201
    comment_id = created.json()["id"]

    denied = client.request(
        "DELETE",
        f"/videos/{video_id}/comments/{comment_id}",
        headers=stranger["headers"],
    )

    assert denied.status_code == 403
    listed = client.get(f"/videos/{video_id}/comments", headers=owner["headers"])
    assert comment_id in {item["id"] for item in listed.json()["items"]}
