"""Повторный сид не создаёт вторые демо-учётки и ролики."""

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PUBLIC_TITLES = ("Утро на канале", "Второй ролик", "Ролик соседа")
PRIVATE_TITLE = "Закрытый ролик"
COMMENT = "Хороший ролик"
REASON = "Проверьте этот ролик"


def _ensure_ffmpeg():
    bundled = Path(os.environ.get("LOCALAPPDATA", "")) / "cpyt-ffmpeg" / "ffmpeg-9.0.2-essentials_build" / "bin"
    if bundled.exists():
        os.environ["PATH"] = str(bundled) + os.pathsep + os.environ.get("PATH", "")
    assert shutil.which("ffmpeg"), "Для сида нужен ffmpeg в PATH"


def test_backend_root_finds_app_package(tmp_path):
    from scripts.seed import backend_root

    repo = tmp_path / "backend"
    (repo / "app").mkdir(parents=True)
    container = tmp_path / "container"
    (container / "app").mkdir(parents=True)
    assert backend_root([repo, container]) == repo
    assert backend_root([tmp_path / "missing", container]) == container


def test_seed_restores_demo_file_when_object_is_missing(client, app):
    _ensure_ffmpeg()
    from scripts.seed import _ensure_user, _ensure_video

    owner = _ensure_user(app, "author1@demo.local", "author-one", "user")
    video_id = _ensure_video(app, owner, "Утро на канале", "public", [], "red")
    login = client.post("/auth/login", json={"email": "author1@demo.local", "password": "demo-pass"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    card = client.get(f"/videos/{video_id}", headers=headers).json()
    app.state.object_storage._objects.pop(card["object_key"], None)

    _ensure_video(app, owner, "Утро на канале", "public", [], "red")

    assert app.state.object_storage.inspect(card["object_key"]) is not None


def test_seed_rewrites_demo_password(client, app):
    from sqlalchemy import text

    from app.infrastructure import db
    from app.infrastructure.passwords import PwdlibHasher
    from scripts.seed import _ensure_user

    email = "admin@demo.local"
    created = client.post(
        "/auth/register",
        json={"email": email, "username": "admin", "password": "old-pass"},
    )
    assert created.status_code in {201, 409}
    hashed = PwdlibHasher().hash("old-pass")
    with db._engine.begin() as connection:
        connection.execute(
            text("update users set password_hash = :password_hash where email = :email"),
            {"password_hash": hashed, "email": email},
        )

    stale = client.post("/auth/login", json={"email": email, "password": "old-pass"})
    assert stale.status_code == 200

    _ensure_user(app, email, "admin", "admin")

    rejected = client.post("/auth/login", json={"email": email, "password": "old-pass"})
    accepted = client.post("/auth/login", json={"email": email, "password": "demo-pass"})
    assert rejected.status_code == 401
    assert accepted.status_code == 200
    assert accepted.json()["user"]["role"] == "admin"


def test_seed_twice_keeps_one_copy_of_demo_data(client, app):
    _ensure_ffmpeg()
    from scripts.seed import apply

    apply(app)
    apply(app)

    feed = client.get("/feed").json()["items"]
    titles = [item["title"] for item in feed]
    for title in PUBLIC_TITLES:
        assert titles.count(title) == 1
    assert PRIVATE_TITLE not in titles

    admin = client.post("/auth/login", json={"email": "admin@demo.local", "password": "demo-pass"})
    assert admin.status_code == 200
    assert admin.json()["user"]["role"] == "admin"

    moderator = client.post("/auth/login", json={"email": "moderator@demo.local", "password": "demo-pass"})
    assert moderator.status_code == 200
    assert moderator.json()["user"]["role"] == "moderator"
    reports = client.get("/moderation/reports", headers={"Authorization": f"Bearer {moderator.json()['access_token']}"})
    assert reports.status_code == 200
    assert sum(1 for item in reports.json()["items"] if item["reason"] == REASON and item["video_title"] == "Ролик соседа") == 1

    author = client.post("/auth/login", json={"email": "author1@demo.local", "password": "demo-pass"})
    guest = client.post("/auth/login", json={"email": "author2@demo.local", "password": "demo-pass"})
    author_headers = {"Authorization": f"Bearer {author.json()['access_token']}"}
    guest_headers = {"Authorization": f"Bearer {guest.json()['access_token']}"}
    channel = client.get(f"/channels/{author.json()['user']['channel_id']}", headers=author_headers)
    videos = channel.json()["videos"]
    private = next(item for item in videos if item["title"] == PRIVATE_TITLE)
    morning = next(item for item in videos if item["title"] == "Утро на канале")

    assert client.get(f"/videos/{private['id']}", headers=guest_headers).status_code == 200
    assert client.get(f"/videos/{private['id']}", headers={"Authorization": f"Bearer {moderator.json()['access_token']}"}).status_code == 404
    comments = client.get(f"/videos/{morning['id']}/comments", headers=guest_headers)
    assert sum(1 for item in comments.json()["items"] if item["body"] == COMMENT) == 1

    hidden = client.post(
        f"/moderation/videos/{next(item['video_id'] for item in reports.json()['items'] if item['reason'] == REASON)}/hide",
        headers={"Authorization": f"Bearer {moderator.json()['access_token']}"},
    )
    assert hidden.status_code == 200
    apply(app)
    titles_after = [item["title"] for item in client.get("/feed").json()["items"]]
    assert titles_after.count("Утро на канале") == 1
    assert "Ролик соседа" not in titles_after
