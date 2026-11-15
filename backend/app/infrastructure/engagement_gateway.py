"""Сборка сценариев просмотра, лайка и комментариев."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.application.engagement import (
    Comment,
    add_comment,
    list_comments,
    reaction_counts,
    record_view,
    remove_comment,
    set_like,
)
from app.infrastructure import db
from app.infrastructure.engagement_repository import SqlEngagementRepository
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


def register_view(video_id: str, viewer_id: str) -> int:
    with _session_scope() as session:
        return record_view(SqlVideoRepository(session), SqlEngagementRepository(session), video_id, viewer_id)


def reactions_for(video_id: str, viewer_id: str | None) -> tuple[int, int, int]:
    with _session_scope() as session:
        return reaction_counts(SqlEngagementRepository(session), video_id, viewer_id)


def register_like(video_id: str, user_id: str, value: int) -> int:
    with _session_scope() as session:
        return set_like(SqlVideoRepository(session), SqlEngagementRepository(session), video_id, user_id, value)


def publish_comment(video_id: str, user_id: str, body: str, parent_id: str | None) -> Comment:
    with _session_scope() as session:
        return add_comment(
            SqlVideoRepository(session),
            SqlEngagementRepository(session),
            video_id,
            user_id,
            body,
            parent_id,
        )


def comments_for_video(video_id: str, viewer_id: str | None) -> list[Comment]:
    with _session_scope() as session:
        return list_comments(SqlVideoRepository(session), SqlEngagementRepository(session), video_id, viewer_id)


def delete_own_comment(video_id: str, comment_id: str, actor_id: str) -> None:
    with _session_scope() as session:
        remove_comment(
            SqlVideoRepository(session),
            SqlEngagementRepository(session),
            video_id,
            comment_id,
            actor_id,
        )
