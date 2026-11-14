"""Видимость ролика. Отсутствие доступа совпадает с неизвестным id."""

from dataclasses import dataclass
from enum import Enum


class Visibility(str, Enum):
    public = "public"
    unlisted = "unlisted"
    private = "private"


class VideoStatus(str, Enum):
    uploading = "uploading"
    processing = "processing"
    ready = "ready"
    failed = "failed"
    hidden = "hidden"


class View(Enum):
    allowed = "allowed"
    owner_marked = "owner_marked"
    denied = "denied"


_NOT_READY = {VideoStatus.uploading, VideoStatus.processing, VideoStatus.failed}


@dataclass(frozen=True)
class VideoSnapshot:
    visibility: Visibility
    status: VideoStatus
    owner_id: str
    grant_user_ids: frozenset[str] = frozenset()


def in_feed(video: VideoSnapshot) -> bool:
    return video.visibility is Visibility.public and video.status is VideoStatus.ready


def visible_on_owner_channel(video: VideoSnapshot, viewer_id: str | None) -> bool:
    return viewer_id is not None and viewer_id == video.owner_id


def view_access(video: VideoSnapshot, viewer_id: str | None) -> View:
    is_owner = visible_on_owner_channel(video, viewer_id)
    has_grant = viewer_id is not None and viewer_id in video.grant_user_ids
    if video.status is VideoStatus.hidden or video.status in _NOT_READY:
        if is_owner:
            return View.owner_marked
        return View.denied
    if video.visibility is Visibility.public:
        return View.allowed
    if video.visibility is Visibility.unlisted:
        return View.allowed
    if is_owner or has_grant:
        return View.allowed
    return View.denied
