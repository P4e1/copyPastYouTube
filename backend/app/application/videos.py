"""Создание ролика, карточка, лента и поиск."""

import uuid
from dataclasses import dataclass

from app.domain.errors import NotFoundError
from app.domain.storage import ObjectStorage
from app.domain.videos import VideoSnapshot, VideoStatus, View, Visibility, in_feed, view_access


@dataclass(frozen=True)
class VideoCard:
    id: str
    title: str
    description: str
    visibility: str
    status: str
    object_key: str
    channel_id: str
    hidden_mark: bool
    view_count: int = 0
    duration_sec: int = 0
    created_at: str = ""
    channel_name: str = ""
    thumbnail_key: str | None = None
    thumbnail_url: str | None = None


@dataclass(frozen=True)
class StoredVideo:
    id: str
    channel_id: str
    owner_id: str
    title: str
    description: str
    visibility: str
    status: str
    object_key: str
    grant_user_ids: frozenset[str]
    view_count: int = 0
    duration_sec: int = 0
    created_at: str = ""
    channel_name: str = ""
    thumbnail_key: str | None = None


class VideoRepository:
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
        raise NotImplementedError

    def get(self, video_id: str) -> StoredVideo | None:
        raise NotImplementedError

    def feed(self) -> list[StoredVideo]:
        raise NotImplementedError

    def search(self, query: str) -> list[StoredVideo]:
        raise NotImplementedError


def _snapshot(stored: StoredVideo) -> VideoSnapshot:
    return VideoSnapshot(
        visibility=Visibility(stored.visibility),
        status=VideoStatus(stored.status),
        owner_id=stored.owner_id,
        grant_user_ids=stored.grant_user_ids,
    )


def _card(stored: StoredVideo, hidden_mark: bool) -> VideoCard:
    return VideoCard(
        id=stored.id,
        title=stored.title,
        description=stored.description,
        visibility=stored.visibility,
        status=stored.status,
        object_key=stored.object_key,
        channel_id=stored.channel_id,
        hidden_mark=hidden_mark,
        view_count=stored.view_count,
        duration_sec=stored.duration_sec,
        created_at=stored.created_at,
        channel_name=stored.channel_name,
        thumbnail_key=stored.thumbnail_key,
    )


def create_video(
    videos: VideoRepository,
    storage: ObjectStorage,
    *,
    channel_id: str,
    owner_id: str,
    title: str,
    description: str,
    visibility: str,
    grant_user_ids: list[str],
) -> tuple[VideoCard, str]:
    video_id = str(uuid.uuid4())
    object_key, upload_url = storage.allocate_upload(video_id)
    grants = grant_user_ids if visibility == Visibility.private.value else []
    stored = videos.add(
        video_id=video_id,
        channel_id=channel_id,
        title=title,
        description=description,
        visibility=visibility,
        status=VideoStatus.uploading.value,
        object_key=object_key,
        grant_user_ids=grants,
    )
    return _card(stored, hidden_mark=False), upload_url


def open_video(videos: VideoRepository, video_id: str, viewer_id: str | None) -> VideoCard:
    stored = videos.get(video_id)
    if stored is None:
        raise NotFoundError("Не найдено")
    access = view_access(_snapshot(stored), viewer_id)
    if access is View.denied:
        raise NotFoundError("Не найдено")
    return _card(stored, hidden_mark=access is View.owner_marked)


def list_feed(videos: VideoRepository) -> list[VideoCard]:
    return [_card(video, hidden_mark=False) for video in videos.feed() if in_feed(_snapshot(video))]


def search_videos(videos: VideoRepository, query: str) -> list[VideoCard]:
    return [_card(video, hidden_mark=False) for video in videos.search(query) if in_feed(_snapshot(video))]
