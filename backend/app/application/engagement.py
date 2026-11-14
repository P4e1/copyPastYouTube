"""Просмотр, лайк и комментарии. Доступ берётся из правила видимости."""

import uuid
from dataclasses import dataclass

from app.domain.engagement import ensure_comment_author, reaction_value
from app.domain.errors import NotFoundError
from app.domain.videos import VideoSnapshot, VideoStatus, View, Visibility, view_access


@dataclass(frozen=True)
class Comment:
    id: str
    video_id: str
    user_id: str
    parent_id: str | None
    body: str


class EngagementRepository:
    def increment_view(self, video_id: str) -> int:
        raise NotImplementedError

    def upsert_like(self, user_id: str, video_id: str, value: int) -> int:
        raise NotImplementedError

    def add_comment(
        self,
        *,
        comment_id: str,
        video_id: str,
        user_id: str,
        parent_id: str | None,
        body: str,
    ) -> Comment:
        raise NotImplementedError

    def list_comments(self, video_id: str) -> list[Comment]:
        raise NotImplementedError

    def get_comment(self, comment_id: str) -> Comment | None:
        raise NotImplementedError

    def delete_comment(self, comment_id: str) -> None:
        raise NotImplementedError


def _require_ready(videos, video_id: str, viewer_id: str):
    stored = videos.get(video_id)
    if stored is None:
        raise NotFoundError("Не найдено")
    snapshot = VideoSnapshot(
        visibility=Visibility(stored.visibility),
        status=VideoStatus(stored.status),
        owner_id=stored.owner_id,
        grant_user_ids=stored.grant_user_ids,
    )
    if stored.status != VideoStatus.ready.value or view_access(snapshot, viewer_id) is not View.allowed:
        raise NotFoundError("Не найдено")
    return stored


def record_view(videos, engagement: EngagementRepository, video_id: str, viewer_id: str) -> int:
    _require_ready(videos, video_id, viewer_id)
    return engagement.increment_view(video_id)


def set_like(videos, engagement: EngagementRepository, video_id: str, user_id: str, value: int) -> int:
    _require_ready(videos, video_id, user_id)
    return engagement.upsert_like(user_id, video_id, reaction_value(value))


def add_comment(
    videos,
    engagement: EngagementRepository,
    video_id: str,
    user_id: str,
    body: str,
    parent_id: str | None,
) -> Comment:
    _require_ready(videos, video_id, user_id)
    if parent_id is not None:
        parent = engagement.get_comment(parent_id)
        if parent is None or parent.video_id != video_id:
            raise NotFoundError("Не найдено")
    return engagement.add_comment(
        comment_id=str(uuid.uuid4()),
        video_id=video_id,
        user_id=user_id,
        parent_id=parent_id,
        body=body,
    )


def list_comments(videos, engagement: EngagementRepository, video_id: str, viewer_id: str) -> list[Comment]:
    _require_ready(videos, video_id, viewer_id)
    return engagement.list_comments(video_id)


def remove_comment(
    videos,
    engagement: EngagementRepository,
    video_id: str,
    comment_id: str,
    actor_id: str,
) -> None:
    _require_ready(videos, video_id, actor_id)
    comment = engagement.get_comment(comment_id)
    if comment is None or comment.video_id != video_id:
        raise NotFoundError("Не найдено")
    ensure_comment_author(comment.user_id, actor_id)
    engagement.delete_comment(comment_id)
