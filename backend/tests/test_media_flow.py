"""PostgreSQL и MinIO: один проход воркера и сценарий приёмки API."""

import os
import subprocess
import uuid
from pathlib import Path

import anyio
import httpx
from httpx import ASGITransport, AsyncClient

from app.infrastructure.media_gateway import run_once


def _client(app):
    class SyncClient:
        def request(self, method, path, json=None, headers=None):
            async def _call():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as http:
                    return await http.request(method, path, json=json, headers=headers)

            return anyio.run(_call)

        def get(self, path, headers=None):
            return self.request("GET", path, headers=headers)

        def post(self, path, json=None, headers=None):
            return self.request("POST", path, json=json, headers=headers)

    return SyncClient()


def _app():
    os.environ["MINIO_ENDPOINT"] = "http://127.0.0.1:9000"
    os.environ["MINIO_PUBLIC_ENDPOINT"] = "http://127.0.0.1:9000"
    os.environ["MINIO_ROOT_USER"] = "minio"
    os.environ["MINIO_ROOT_PASSWORD"] = "change-me-minio"
    os.environ["MINIO_BUCKET"] = "videos"
    os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
    from app.main import create_app

    return create_app()


def _register(client) -> dict:
    mark = uuid.uuid4().hex[:10]
    payload = {
        "email": f"accept-{mark}@example.com",
        "username": f"accept{mark}",
        "password": "secret-pass",
    }
    assert client.post("/auth/register", json=payload).status_code == 201
    login = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    return {"headers": {"Authorization": f"Bearer {login.json()['access_token']}"}}


def _mp4(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=160x120:d=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-t",
            "1",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def _upload_ready(client, headers, title: str) -> str:
    created = client.post(
        "/videos",
        json={"title": title, "description": "", "visibility": "public", "grant_user_ids": []},
        headers=headers,
    )
    assert created.status_code == 201
    body = created.json()
    folder = Path(os.environ.get("TEMP", "."))
    video_path = folder / f"{body['id']}.mp4"
    _mp4(video_path)
    put = httpx.put(body["upload_url"], content=video_path.read_bytes(), headers={"Content-Type": "video/mp4"})
    assert put.status_code in {200, 204}
    assert client.post(f"/videos/{body['id']}/complete", headers=headers).status_code == 200
    assert run_once() is True
    return body["id"]


def test_worker_marks_ready_and_owner_gets_playback():
    client = _client(_app())
    owner = _register(client)
    video_id = _upload_ready(client, owner["headers"], "Превью")

    card = client.get(f"/videos/{video_id}", headers=owner["headers"])
    assert card.status_code == 200
    assert card.json()["status"] == "ready"
    playback = client.get(f"/videos/{video_id}/playback", headers=owner["headers"])
    assert playback.status_code == 200
    assert playback.json()["url"].startswith("http://127.0.0.1:9000/")
    from app.infrastructure.storage_factory import build_storage

    thumbnail = build_storage().inspect(f"videos/{video_id}/thumbnail.jpg")
    assert thumbnail is not None
    assert thumbnail.size > 0


def test_acceptance_register_upload_view_like_comment():
    client = _client(_app())
    viewer = _register(client)
    video_id = _upload_ready(client, viewer["headers"], "Приёмка")

    watched = client.post(f"/videos/{video_id}/view", headers=viewer["headers"])
    assert watched.status_code == 200
    assert watched.json()["view_count"] >= 1
    liked = client.post("/videos/" + video_id + "/like", json={"value": 1}, headers=viewer["headers"])
    assert liked.status_code == 200
    commented = client.post(
        f"/videos/{video_id}/comments",
        json={"body": "Первый комментарий", "parent_id": None},
        headers=viewer["headers"],
    )
    assert commented.status_code == 201
    listed = client.get(f"/videos/{video_id}/comments", headers=viewer["headers"])
    assert "Первый комментарий" in {item["body"] for item in listed.json()["items"]}
