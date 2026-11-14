"""Реакция на ролик и право удалить комментарий."""

from app.domain.errors import ForbiddenError


def reaction_value(value: int) -> int:
    if value not in (1, -1):
        raise ValueError("Реакция должна быть 1 или -1")
    return value


def ensure_comment_author(author_id: str, actor_id: str) -> None:
    if author_id != actor_id:
        raise ForbiddenError("Чужой комментарий удалить нельзя")
