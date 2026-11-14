"""Очередь media_jobs и смена статуса ролика."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.media import ClaimedJob
from app.domain.errors import NotFoundError
from app.domain.videos import VideoStatus
from app.infrastructure.media_models import MediaJobRow
from app.infrastructure.video_models import VideoRow


class SqlMediaJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def enqueue(self, video_id: str) -> None:
        video = self._session.get(VideoRow, video_id)
        if video is None:
            raise NotFoundError("Не найдено")
        video.status = VideoStatus.processing.value
        self._session.add(
            MediaJobRow(
                id=str(uuid.uuid4()),
                video_id=video_id,
                kind="finalize",
                status="pending",
                created_at=datetime.now(timezone.utc),
            )
        )
        self._session.flush()

    def claim_next(self) -> ClaimedJob | None:
        row = self._session.scalars(
            select(MediaJobRow)
            .where(MediaJobRow.status == "pending")
            .order_by(MediaJobRow.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        ).first()
        if row is None:
            return None
        video = self._session.get(VideoRow, row.video_id)
        if video is None:
            raise NotFoundError("Не найдено")
        row.status = "running"
        self._session.flush()
        return ClaimedJob(id=row.id, video_id=row.video_id, object_key=video.object_key)

    def finish(self, job_id: str, video_id: str, thumbnail_key: str, duration_sec: int) -> None:
        job = self._session.get(MediaJobRow, job_id)
        video = self._session.get(VideoRow, video_id)
        if job is None or video is None:
            raise NotFoundError("Не найдено")
        job.status = "done"
        job.error = None
        video.status = VideoStatus.ready.value
        video.thumbnail_key = thumbnail_key
        video.duration_sec = duration_sec
        self._session.flush()

    def fail(self, job_id: str, video_id: str, error: str) -> None:
        job = self._session.get(MediaJobRow, job_id)
        video = self._session.get(VideoRow, video_id)
        if job is None or video is None:
            raise NotFoundError("Не найдено")
        job.status = "failed"
        job.error = error
        video.status = VideoStatus.failed.value
        self._session.flush()
