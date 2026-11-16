"""Подписка и право править канал."""

from app.domain.errors import ForbiddenError


def ensure_channel_owner(owner_id: str, actor_id: str) -> None:
    if owner_id != actor_id:
        raise ForbiddenError("Канал может менять только владелец")


def ensure_not_own_subscription(owner_id: str, subscriber_id: str) -> None:
    if owner_id == subscriber_id:
        raise ForbiddenError("Нельзя подписаться на свой канал")


def subscription_visible(owner_id: str, subscriber_id: str | None, stored: bool) -> bool:
    if not subscriber_id or subscriber_id == owner_id:
        return False
    return stored
