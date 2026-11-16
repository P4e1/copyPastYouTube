"""Карточка канала, подписка и плейлисты."""

import uuid
from dataclasses import dataclass

from app.domain.channels import ensure_channel_owner, ensure_not_own_subscription, subscription_visible
from app.domain.errors import NotFoundError
from app.domain.videos import VideoSnapshot, VideoStatus, View, Visibility, view_access


@dataclass(frozen=True)
class ChannelVideo:
    id: str
    title: str
    status: str
    visibility: str
    hidden_mark: bool


@dataclass(frozen=True)
class ChannelCard:
    id: str
    name: str
    description: str
    subscriber_count: int
    subscribed: bool
    videos: list[ChannelVideo]


@dataclass(frozen=True)
class PlaylistItem:
    video_id: str
    position: int


@dataclass(frozen=True)
class PlaylistCard:
    id: str
    channel_id: str
    title: str
    visibility: str
    items: list[PlaylistItem]


@dataclass(frozen=True)
class ChannelRecord:
    id: str
    owner_id: str
    name: str
    description: str


@dataclass(frozen=True)
class VideoOnChannel:
    id: str
    title: str
    visibility: str
    status: str
    owner_id: str
    grant_user_ids: frozenset[str]


class ChannelRepository:
    def get(self, channel_id: str) -> ChannelRecord | None:
        raise NotImplementedError

    def rename(self, channel_id: str, name: str) -> ChannelRecord:
        raise NotImplementedError

    def subscription_exists(self, subscriber_id: str, channel_id: str) -> bool:
        raise NotImplementedError

    def add_subscription(self, subscriber_id: str, channel_id: str) -> None:
        raise NotImplementedError

    def remove_subscription(self, subscriber_id: str, channel_id: str) -> None:
        raise NotImplementedError

    def subscriber_count(self, channel_id: str) -> int:
        raise NotImplementedError

    def subscribed_channels(self, subscriber_id: str) -> list[ChannelRecord]:
        raise NotImplementedError

    def videos(self, channel_id: str) -> list[VideoOnChannel]:
        raise NotImplementedError

    def video(self, video_id: str) -> VideoOnChannel | None:
        raise NotImplementedError

    def add_playlist(self, playlist_id: str, channel_id: str, title: str, visibility: str) -> PlaylistCard:
        raise NotImplementedError

    def get_playlist(self, playlist_id: str) -> tuple[str, str] | None:
        """Вернуть (channel owner_id, playlist channel_id) или None."""

    def add_item(self, playlist_id: str, video_id: str, position: int) -> None:
        raise NotImplementedError

    def list_playlists(self, channel_id: str) -> list[PlaylistCard]:
        raise NotImplementedError


def _visible(video: VideoOnChannel, viewer_id: str | None, *, owner_channel: bool) -> ChannelVideo | None:
    snapshot = VideoSnapshot(
        visibility=Visibility(video.visibility),
        status=VideoStatus(video.status),
        owner_id=video.owner_id,
        grant_user_ids=video.grant_user_ids,
    )
    access = view_access(snapshot, viewer_id)
    if access is View.denied:
        return None
    if access is View.owner_marked and not owner_channel:
        return None
    return ChannelVideo(
        id=video.id,
        title=video.title,
        status=video.status,
        visibility=video.visibility,
        hidden_mark=access is View.owner_marked,
    )


def open_channel(channels: ChannelRepository, channel_id: str, viewer_id: str | None) -> ChannelCard:
    channel = channels.get(channel_id)
    if channel is None:
        raise NotFoundError("Не найдено")
    owner_channel = viewer_id == channel.owner_id
    videos = []
    for video in channels.videos(channel_id):
        card = _visible(video, viewer_id, owner_channel=owner_channel)
        if card is not None:
            videos.append(card)
    return ChannelCard(
        id=channel.id,
        name=channel.name,
        description=channel.description,
        subscriber_count=channels.subscriber_count(channel_id),
        subscribed=subscription_visible(
            channel.owner_id,
            viewer_id,
            bool(viewer_id) and channels.subscription_exists(viewer_id, channel_id),
        ),
        videos=videos,
    )


def list_subscriptions(channels: ChannelRepository, subscriber_id: str) -> list[ChannelRecord]:
    return [channel for channel in channels.subscribed_channels(subscriber_id) if channel.owner_id != subscriber_id]


def subscribe(channels: ChannelRepository, channel_id: str, subscriber_id: str) -> None:
    channel = channels.get(channel_id)
    if channel is None:
        raise NotFoundError("Не найдено")
    ensure_not_own_subscription(channel.owner_id, subscriber_id)
    if not channels.subscription_exists(subscriber_id, channel_id):
        channels.add_subscription(subscriber_id, channel_id)


def unsubscribe(channels: ChannelRepository, channel_id: str, subscriber_id: str) -> None:
    if channels.get(channel_id) is None:
        raise NotFoundError("Не найдено")
    channels.remove_subscription(subscriber_id, channel_id)


def rename_channel(channels: ChannelRepository, channel_id: str, actor_id: str, name: str) -> ChannelRecord:
    channel = channels.get(channel_id)
    if channel is None:
        raise NotFoundError("Не найдено")
    ensure_channel_owner(channel.owner_id, actor_id)
    return channels.rename(channel_id, name)


def create_playlist(
    channels: ChannelRepository,
    channel_id: str,
    actor_id: str,
    title: str,
    visibility: str,
) -> PlaylistCard:
    channel = channels.get(channel_id)
    if channel is None:
        raise NotFoundError("Не найдено")
    ensure_channel_owner(channel.owner_id, actor_id)
    return channels.add_playlist(str(uuid.uuid4()), channel_id, title, visibility)


def add_playlist_item(
    channels: ChannelRepository,
    playlist_id: str,
    actor_id: str,
    video_id: str,
    position: int,
) -> None:
    playlist = channels.get_playlist(playlist_id)
    if playlist is None:
        raise NotFoundError("Не найдено")
    owner_id, _channel_id = playlist
    ensure_channel_owner(owner_id, actor_id)
    video = channels.video(video_id)
    if video is None:
        raise NotFoundError("Не найдено")
    snapshot = VideoSnapshot(
        visibility=Visibility(video.visibility),
        status=VideoStatus(video.status),
        owner_id=video.owner_id,
        grant_user_ids=video.grant_user_ids,
    )
    if view_access(snapshot, actor_id) is View.denied:
        raise NotFoundError("Не найдено")
    channels.add_item(playlist_id, video_id, position)


def playlists_of(channels: ChannelRepository, channel_id: str, viewer_id: str | None) -> list[PlaylistCard]:
    channel = channels.get(channel_id)
    if channel is None:
        raise NotFoundError("Не найдено")
    cards = channels.list_playlists(channel_id)
    if viewer_id == channel.owner_id:
        return cards
    return [card for card in cards if card.visibility == Visibility.public.value]
