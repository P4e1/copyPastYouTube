"""Сборка сценариев видео поверх сессии и выбранного хранилища."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.application.videos import VideoCard, create_video, list_feed, open_video, search_videos
from app.domain.storage import ObjectStorage
from app.infrastructure import db
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


def bind_create_video(storage: ObjectStorage):
    def create_video_for_channel(
        *,
        channel_id: str,
        owner_id: str,
        title: str,
        description: str,
        visibility: str,
        grant_user_ids: list[str],
    ) -> tuple[VideoCard, str]:
        with _session_scope() as session:
            return create_video(
                SqlVideoRepository(session),
                storage,
                channel_id=channel_id,
                owner_id=owner_id,
                title=title,
                description=description,
                visibility=visibility,
                grant_user_ids=grant_user_ids,
            )

    return create_video_for_channel


def video_card(video_id: str, viewer_id: str | None) -> VideoCard:
    with _session_scope() as session:
        return open_video(SqlVideoRepository(session), video_id, viewer_id)


def feed_cards() -> list[VideoCard]:
    with _session_scope() as session:
        return list_feed(SqlVideoRepository(session))


def search_cards(query: str) -> list[VideoCard]:
    with _session_scope() as session:
        return search_videos(SqlVideoRepository(session), query)
