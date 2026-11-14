"""Репозиторий жалоб, скрытия и ролей."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.moderation import Report
from app.domain.errors import NotFoundError
from app.domain.moderation import ReportStatus
from app.infrastructure.auth_models import UserRow
from app.infrastructure.moderation_models import ReportRow
from app.infrastructure.video_models import VideoRow


class SqlModerationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_report(self, report_id: str, reporter_id: str, video_id: str, reason: str) -> Report:
        self._session.add(
            ReportRow(
                id=report_id,
                reporter_id=reporter_id,
                video_id=video_id,
                reason=reason,
                status=ReportStatus.open.value,
                created_at=datetime.now(timezone.utc),
            )
        )
        self._session.flush()
        return Report(
            id=report_id,
            reporter_id=reporter_id,
            video_id=video_id,
            reason=reason,
            status=ReportStatus.open.value,
        )

    def list_open(self) -> list[Report]:
        rows = self._session.execute(
            select(ReportRow, UserRow.username, VideoRow.title)
            .join(UserRow, UserRow.id == ReportRow.reporter_id)
            .join(VideoRow, VideoRow.id == ReportRow.video_id)
            .where(ReportRow.status == ReportStatus.open.value)
            .order_by(ReportRow.created_at.asc())
        )
        return [
            Report(
                id=report.id,
                reporter_id=report.reporter_id,
                video_id=report.video_id,
                reason=report.reason,
                status=report.status,
                reporter_username=username,
                video_title=title,
            )
            for report, username, title in rows
        ]

    def resolve_open(self, video_id: str, resolved_by: str) -> None:
        rows = self._session.scalars(
            select(ReportRow).where(
                ReportRow.video_id == video_id,
                ReportRow.status == ReportStatus.open.value,
            )
        )
        for row in rows:
            row.status = ReportStatus.resolved.value
            row.resolved_by = resolved_by
        self._session.flush()

    def set_video_status(self, video_id: str, status: str) -> None:
        row = self._session.get(VideoRow, video_id)
        if row is None:
            raise NotFoundError("Не найдено")
        row.status = status
        self._session.flush()

    def set_user_role(self, user_id: str, role: str) -> str:
        row = self._session.get(UserRow, user_id)
        if row is None:
            raise NotFoundError("Не найдено")
        row.role = role
        self._session.flush()
        return row.role
