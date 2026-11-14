"""Сборка сценариев модерации и ролей."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.application.moderation import Report, assign_role, create_report, hide_video, open_reports, restore_video
from app.infrastructure import db
from app.infrastructure.moderation_repository import SqlModerationRepository
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


def file_report(video_id: str, reporter_id: str, reason: str) -> Report:
    with _session_scope() as session:
        return create_report(SqlVideoRepository(session), SqlModerationRepository(session), video_id, reporter_id, reason)


def queue_reports(actor_role: str) -> list[Report]:
    with _session_scope() as session:
        return open_reports(SqlModerationRepository(session), actor_role)


def hide_reported_video(video_id: str, actor_id: str, actor_role: str) -> None:
    with _session_scope() as session:
        hide_video(SqlVideoRepository(session), SqlModerationRepository(session), video_id, actor_id, actor_role)


def restore_hidden_video(video_id: str, actor_role: str) -> None:
    with _session_scope() as session:
        restore_video(SqlVideoRepository(session), SqlModerationRepository(session), video_id, actor_role)


def change_user_role(actor_role: str, user_id: str, new_role: str) -> str:
    with _session_scope() as session:
        return assign_role(SqlModerationRepository(session), actor_role, user_id, new_role)
