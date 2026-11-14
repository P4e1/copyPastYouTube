"""Жалобы, скрытие ролика и назначение роли."""

import uuid
from dataclasses import dataclass

from app.domain.errors import NotFoundError
from app.domain.moderation import ReportStatus, ensure_can_assign_role, ensure_moderator
from app.domain.videos import VideoSnapshot, VideoStatus, View, Visibility, view_access


@dataclass(frozen=True)
class Report:
    id: str
    reporter_id: str
    video_id: str
    reason: str
    status: str


class ModerationRepository:
    def add_report(self, report_id: str, reporter_id: str, video_id: str, reason: str) -> Report:
        raise NotImplementedError

    def list_open(self) -> list[Report]:
        raise NotImplementedError

    def resolve_open(self, video_id: str, resolved_by: str) -> None:
        raise NotImplementedError

    def set_video_status(self, video_id: str, status: str) -> None:
        raise NotImplementedError

    def set_user_role(self, user_id: str, role: str) -> str:
        raise NotImplementedError


def _visible_video(videos, video_id: str, viewer_id: str):
    stored = videos.get(video_id)
    if stored is None:
        raise NotFoundError("Не найдено")
    snapshot = VideoSnapshot(
        visibility=Visibility(stored.visibility),
        status=VideoStatus(stored.status),
        owner_id=stored.owner_id,
        grant_user_ids=stored.grant_user_ids,
    )
    if view_access(snapshot, viewer_id) is not View.allowed:
        raise NotFoundError("Не найдено")
    return stored


def create_report(videos, moderation: ModerationRepository, video_id: str, reporter_id: str, reason: str) -> Report:
    _visible_video(videos, video_id, reporter_id)
    return moderation.add_report(str(uuid.uuid4()), reporter_id, video_id, reason)


def open_reports(moderation: ModerationRepository, actor_role: str) -> list[Report]:
    ensure_moderator(actor_role)
    return moderation.list_open()


def hide_video(videos, moderation: ModerationRepository, video_id: str, actor_id: str, actor_role: str) -> None:
    ensure_moderator(actor_role)
    if videos.get(video_id) is None:
        raise NotFoundError("Не найдено")
    moderation.set_video_status(video_id, VideoStatus.hidden.value)
    moderation.resolve_open(video_id, actor_id)


def restore_video(videos, moderation: ModerationRepository, video_id: str, actor_role: str) -> None:
    ensure_moderator(actor_role)
    stored = videos.get(video_id)
    if stored is None:
        raise NotFoundError("Не найдено")
    if stored.status != VideoStatus.hidden.value:
        return
    moderation.set_video_status(video_id, VideoStatus.ready.value)


def assign_role(moderation: ModerationRepository, actor_role: str, user_id: str, new_role: str) -> str:
    ensure_can_assign_role(actor_role, new_role)
    return moderation.set_user_role(user_id, new_role)
