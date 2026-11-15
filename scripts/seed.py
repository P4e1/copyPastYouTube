"""Демо-данные: администратор, модератор, два автора, ролики, лайк, комментарий и жалоба.

Повторный запуск находит тех же пользователей и ролики и не создаёт вторые копии.
Короткий mp4 собирает ffmpeg, файл кладётся в хранилище, воркер доводит ролик до ready.
"""

import subprocess
import tempfile
from pathlib import Path

from app.domain.auth import EmailTakenError, InvalidCredentialsError
from app.domain.errors import NotFoundError
from app.infrastructure.media_gateway import run_once

PASSWORD = "demo-pass"
COMMENT = "Хороший ролик"
REASON = "Проверьте этот ролик"

ACCOUNTS = (
    ("admin@demo.local", "admin", "admin"),
    ("moderator@demo.local", "moderator", "moderator"),
    ("author1@demo.local", "author-one", "user"),
    ("author2@demo.local", "author-two", "user"),
)


def apply(app) -> None:
    users = {
        email: _ensure_user(app, email, username, role)
        for email, username, role in ACCOUNTS
    }
    author = users["author1@demo.local"]
    neighbor = users["author2@demo.local"]
    clips = {
        "Утро на канале": _ensure_video(app, author, "Утро на канале", "public", [], "red"),
        "Второй ролик": _ensure_video(app, author, "Второй ролик", "public", [], "blue"),
        "Ролик соседа": _ensure_video(app, neighbor, "Ролик соседа", "public", [], "green"),
        "Закрытый ролик": _ensure_video(
            app, author, "Закрытый ролик", "private", [neighbor.id], "yellow"
        ),
    }
    owners = {
        clips["Утро на канале"]: author.id,
        clips["Второй ролик"]: author.id,
        clips["Ролик соседа"]: neighbor.id,
        clips["Закрытый ролик"]: author.id,
    }
    _wait_ready(app, owners)
    morning = clips["Утро на канале"]
    reported = clips["Ролик соседа"]
    _engage(app, morning, neighbor.id, author.id, reported)


def main() -> None:
    from app.main import create_app

    apply(create_app())


def _ensure_user(app, email: str, username: str, role: str):
    try:
        account = app.state.register_account(email, username, PASSWORD)
    except EmailTakenError:
        try:
            account, _token = app.state.login_account(email, PASSWORD)
        except InvalidCredentialsError:
            _set_password(email, PASSWORD)
            account, _token = app.state.login_account(email, PASSWORD)
    if account.role != role:
        _set_role(account.id, role)
        account, _token = app.state.login_account(email, PASSWORD)
    return account


def _set_password(email: str, password: str) -> None:
    from sqlalchemy import text

    from app.infrastructure import db
    from app.infrastructure.passwords import PwdlibHasher

    with db._engine.begin() as connection:
        connection.execute(
            text("update users set password_hash = :password_hash where email = :email"),
            {"password_hash": PwdlibHasher().hash(password), "email": email},
        )


def _set_role(user_id: str, role: str) -> None:
    from sqlalchemy import text

    from app.infrastructure import db

    with db._engine.begin() as connection:
        connection.execute(
            text("update users set role = :role where id = :user_id"),
            {"role": role, "user_id": user_id},
        )


def _ensure_video(app, owner, title: str, visibility: str, grant_user_ids: list[str], color: str) -> str:
    channel = app.state.channel_card(owner.channel_id, owner.id)
    existing = next((item.id for item in channel.videos if item.title == title), None)
    if existing:
        return existing
    card, _upload_url = app.state.create_video(
        channel_id=owner.channel_id,
        owner_id=owner.id,
        title=title,
        description="Демо-ролик",
        visibility=visibility,
        grant_user_ids=grant_user_ids,
    )
    app.state.object_storage.put_bytes(card.object_key, _mp4(color), "video/mp4")
    app.state.complete_upload(card.id, owner.id)
    return card.id


def _engage(app, morning: str, viewer_id: str, reporter_id: str, reported: str) -> None:
    try:
        if not any(item.body == COMMENT for item in app.state.comments_for_video(morning, viewer_id)):
            app.state.publish_comment(morning, viewer_id, COMMENT, None)
        app.state.register_like(morning, viewer_id, 1)
    except NotFoundError:
        return
    try:
        if not any(
            item.video_id == reported and item.reason == REASON
            for item in app.state.queue_reports("moderator")
        ):
            app.state.file_report(reported, reporter_id, REASON)
    except NotFoundError:
        return


def _wait_ready(app, owners: dict[str, str]) -> None:
    for _ in range(40):
        waiting = []
        failed = []
        for video_id, owner_id in owners.items():
            card = app.state.get_video(video_id, owner_id)
            if card.status == "failed":
                failed.append(card.title)
            elif card.status not in {"ready", "hidden"}:
                waiting.append(card.title)
        if failed:
            raise RuntimeError("Не удалось обработать: " + ", ".join(failed))
        if not waiting:
            return
        run_once(app.state.object_storage)
    raise RuntimeError("Демо-ролики не дошли до готовности")


def _mp4(color: str) -> bytes:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "clip.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=160x120:d=1",
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
        return path.read_bytes()


if __name__ == "__main__":
    main()
