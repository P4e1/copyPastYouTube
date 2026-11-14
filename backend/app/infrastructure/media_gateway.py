"""Сборка complete, playback и одного прохода воркера."""

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.application.media import process_next
from app.domain.storage import ObjectStorage
from app.infrastructure import db
from app.infrastructure.ffmpeg import FfmpegExtractor
from app.infrastructure.media_repository import SqlMediaJobRepository
from app.infrastructure.storage_factory import build_storage
from app.infrastructure.video_repository import SqlVideoRepository


@contextmanager
def _session_scope() -> Iterator[Session]:
    if db.SessionLocal is None:
        raise RuntimeError("Подключение к базе не настроено")
    session = db.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def complete_for_owner(storage: ObjectStorage, video_id: str, owner_id: str) -> None:
    limit = int(os.environ.get("MAX_UPLOAD_BYTES", "2147483648"))
    with _session_scope() as session:
        from app.application.media import complete_upload

        complete_upload(
            SqlVideoRepository(session),
            SqlMediaJobRepository(session),
            storage,
            video_id,
            owner_id,
            limit,
        )


def playback_for_viewer(storage: ObjectStorage, video_id: str, viewer_id: str | None) -> str:
    with _session_scope() as session:
        from app.application.media import playback_url

        return playback_url(SqlVideoRepository(session), storage, video_id, viewer_id)


def run_once(storage: ObjectStorage | None = None) -> bool:
    if db.SessionLocal is None:
        db.init_engine(os.environ["DATABASE_URL"])
    active = storage if storage is not None else build_storage()
    with _session_scope() as session:
        return process_next(SqlMediaJobRepository(session), active, FfmpegExtractor())
