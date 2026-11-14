"""Жалоба и границы ролей модерации."""

from enum import Enum

from app.domain.auth import Role
from app.domain.errors import ForbiddenError


class ReportStatus(str, Enum):
    open = "open"
    resolved = "resolved"
    rejected = "rejected"


def ensure_moderator(role: str) -> None:
    if role not in (Role.moderator.value, Role.admin.value):
        raise ForbiddenError("Недостаточно прав")


def ensure_can_assign_role(actor_role: str, new_role: str) -> None:
    if actor_role != Role.admin.value:
        raise ForbiddenError("Роль назначает только администратор")
    if new_role not in (Role.user.value, Role.moderator.value, Role.admin.value):
        raise ValueError("Неизвестная роль")
