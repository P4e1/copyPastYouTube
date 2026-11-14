"""Репозиторий роликов и списка доступа."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.videos import StoredVideo
from app.domain.videos import VideoStatus, Visibility
from app.infrastructure.auth_models import ChannelRow
from app.infrastructure.video_models import VideoGrantRow, VideoRow


class SqlVideoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        video_id: str,
        channel_id: str,
        title: str,
        description: str,
        visibility: str,
        status: str,
        object_key: str,
        grant_user_ids: list[str],
    ) -> StoredVideo:
        self._session.add(
            VideoRow(
                id=video_id,
                channel_id=channel_id,
                title=title,
                description=description,
                visibility=visibility,
                status=status,
                object_key=object_key,
                duration_sec=0,
                view_count=0,
                created_at=datetime.now(timezone.utc),
            )
        )
        self._session.flush()
        for user_id in grant_user_ids:
            self._session.add(VideoGrantRow(video_id=video_id, user_id=user_id))
        if grant_user_ids:
            self._session.flush()
        owner_id = self._owner_id(channel_id)
        return StoredVideo(
            id=video_id,
            channel_id=channel_id,
            owner_id=owner_id,
            title=title,
            description=description,
            visibility=visibility,
            status=status,
            object_key=object_key,
            grant_user_ids=frozenset(grant_user_ids),
        )

    def get(self, video_id: str) -> StoredVideo | None:
        row = self._session.get(VideoRow, video_id)
        if row is None:
            return None
        return self._to_stored(row)

    def feed(self) -> list[StoredVideo]:
        rows = self._session.scalars(
            select(VideoRow)
            .where(VideoRow.visibility == Visibility.public.value, VideoRow.status == VideoStatus.ready.value)
            .order_by(VideoRow.created_at.desc())
        )
        return [self._to_stored(row) for row in rows]

    def search(self, query: str) -> list[StoredVideo]:
        pattern = f"%{query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')}%"
        rows = self._session.scalars(
            select(VideoRow)
            .where(
                VideoRow.visibility == Visibility.public.value,
                VideoRow.status == VideoStatus.ready.value,
                VideoRow.title.ilike(pattern, escape="\\"),
            )
            .order_by(VideoRow.created_at.desc())
        )
        return [self._to_stored(row) for row in rows]

    def _to_stored(self, row: VideoRow) -> StoredVideo:
        grants = self._session.scalars(select(VideoGrantRow.user_id).where(VideoGrantRow.video_id == row.id))
        return StoredVideo(
            id=row.id,
            channel_id=row.channel_id,
            owner_id=self._owner_id(row.channel_id),
            title=row.title,
            description=row.description,
            visibility=row.visibility,
            status=row.status,
            object_key=row.object_key,
            grant_user_ids=frozenset(grants),
            view_count=row.view_count,
            duration_sec=row.duration_sec,
            created_at=row.created_at.isoformat(),
            channel_name=self._channel_name(row.channel_id),
            thumbnail_key=row.thumbnail_key,
        )

    def _channel_name(self, channel_id: str) -> str:
        name = self._session.scalar(select(ChannelRow.name).where(ChannelRow.id == channel_id))
        return name or ""

    def _owner_id(self, channel_id: str) -> str:
        owner_id = self._session.scalar(select(ChannelRow.owner_id).where(ChannelRow.id == channel_id))
        if owner_id is None:
            raise RuntimeError("Канал ролика не найден")
        return owner_id
