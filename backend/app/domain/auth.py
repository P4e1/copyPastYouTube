"""Учётная запись, роль и порты auth. JWT здесь не выпускается."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class Role(str, Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class EmailTakenError(Exception):
    """Такой email уже зарегистрирован."""


class InvalidCredentialsError(Exception):
    """Email или пароль не подходят, либо токен недействителен."""


@dataclass(frozen=True)
class Account:
    id: str
    email: str
    username: str
    role: str
    channel_id: str


@dataclass(frozen=True)
class StoredUser:
    id: str
    email: str
    username: str
    password_hash: str
    role: str
    channel_id: str


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> StoredUser | None:
        """Найти пользователя по email вместе с его каналом."""

    def get_by_id(self, user_id: str) -> StoredUser | None:
        """Найти пользователя по идентификатору вместе с его каналом."""

    def search(self, query: str) -> list[StoredUser]:
        """Найти пользователей по части имени, без пароля в ответе сценария."""

    def add_user_with_channel(
        self,
        *,
        user_id: str,
        email: str,
        username: str,
        password_hash: str,
        role: str,
        channel_id: str,
        channel_name: str,
    ) -> StoredUser:
        """Сохранить пользователя и ровно один его канал."""


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str:
        """Вернуть хеш пароля."""

    def verify(self, password: str, password_hash: str) -> bool:
        """Проверить пароль против сохранённого хеша."""
