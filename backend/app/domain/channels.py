"""Подписка и право править канал."""

from app.domain.errors import ForbiddenError


def ensure_channel_owner(owner_id: str, actor_id: str) -> None:
    if owner_id != actor_id:
        raise ForbiddenError("Канал может менять только владелец")
