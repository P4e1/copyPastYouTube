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
