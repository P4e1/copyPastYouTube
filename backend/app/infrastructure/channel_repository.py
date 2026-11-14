"""Репозиторий каналов, подписок и плейлистов."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.channels import ChannelRecord, PlaylistCard, PlaylistItem, VideoOnChannel
from app.infrastructure.auth_models import ChannelRow
from app.infrastructure.channel_models import PlaylistItemRow, PlaylistRow, SubscriptionRow
from app.infrastructure.video_models import VideoGrantRow, VideoRow


class SqlChannelRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, channel_id: str) -> ChannelRecord | None:
        row = self._session.get(ChannelRow, channel_id)
        if row is None:
            return None
        return ChannelRecord(id=row.id, owner_id=row.owner_id, name=row.name, description=row.description)

    def rename(self, channel_id: str, name: str) -> ChannelRecord:
        row = self._session.get(ChannelRow, channel_id)
        if row is None:
            raise RuntimeError("Канал не найден")
        row.name = name
        self._session.flush()
        return ChannelRecord(id=row.id, owner_id=row.owner_id, name=row.name, description=row.description)

    def subscription_exists(self, subscriber_id: str, channel_id: str) -> bool:
        row = self._session.get(SubscriptionRow, {"subscriber_id": subscriber_id, "channel_id": channel_id})
        return row is not None

    def add_subscription(self, subscriber_id: str, channel_id: str) -> None:
        self._session.add(SubscriptionRow(subscriber_id=subscriber_id, channel_id=channel_id))
        self._session.flush()

    def remove_subscription(self, subscriber_id: str, channel_id: str) -> None:
        row = self._session.get(SubscriptionRow, {"subscriber_id": subscriber_id, "channel_id": channel_id})
        if row is not None:
            self._session.delete(row)
            self._session.flush()

    def subscriber_count(self, channel_id: str) -> int:
        return int(
            self._session.scalar(
                select(func.count()).select_from(SubscriptionRow).where(SubscriptionRow.channel_id == channel_id)
            )
            or 0
        )

    def videos(self, channel_id: str) -> list[VideoOnChannel]:
        rows = self._session.scalars(select(VideoRow).where(VideoRow.channel_id == channel_id))
        return [self._video(row) for row in rows]

    def video(self, video_id: str) -> VideoOnChannel | None:
        row = self._session.get(VideoRow, video_id)
        if row is None:
            return None
        return self._video(row)

    def add_playlist(self, playlist_id: str, channel_id: str, title: str, visibility: str) -> PlaylistCard:
        self._session.add(PlaylistRow(id=playlist_id, channel_id=channel_id, title=title, visibility=visibility))
        self._session.flush()
        return PlaylistCard(id=playlist_id, channel_id=channel_id, title=title, visibility=visibility, items=[])

    def get_playlist(self, playlist_id: str) -> tuple[str, str] | None:
        row = self._session.get(PlaylistRow, playlist_id)
        if row is None:
            return None
        owner_id = self._session.scalar(select(ChannelRow.owner_id).where(ChannelRow.id == row.channel_id))
        if owner_id is None:
            return None
        return owner_id, row.channel_id

    def add_item(self, playlist_id: str, video_id: str, position: int) -> None:
        row = self._session.get(PlaylistItemRow, {"playlist_id": playlist_id, "video_id": video_id})
        if row is None:
            self._session.add(PlaylistItemRow(playlist_id=playlist_id, video_id=video_id, position=position))
        else:
            row.position = position
        self._session.flush()

    def list_playlists(self, channel_id: str) -> list[PlaylistCard]:
        rows = self._session.scalars(select(PlaylistRow).where(PlaylistRow.channel_id == channel_id))
        return [self._playlist(row) for row in rows]

    def _playlist(self, row: PlaylistRow) -> PlaylistCard:
        items = self._session.scalars(
            select(PlaylistItemRow).where(PlaylistItemRow.playlist_id == row.id).order_by(PlaylistItemRow.position.asc())
        )
        return PlaylistCard(
            id=row.id,
            channel_id=row.channel_id,
            title=row.title,
            visibility=row.visibility,
            items=[PlaylistItem(video_id=item.video_id, position=item.position) for item in items],
        )

    def _video(self, row: VideoRow) -> VideoOnChannel:
        grants = self._session.scalars(select(VideoGrantRow.user_id).where(VideoGrantRow.video_id == row.id))
        owner_id = self._session.scalar(select(ChannelRow.owner_id).where(ChannelRow.id == row.channel_id))
        return VideoOnChannel(
            id=row.id,
            title=row.title,
            visibility=row.visibility,
            status=row.status,
            owner_id=owner_id or "",
            grant_user_ids=frozenset(grants),
        )
