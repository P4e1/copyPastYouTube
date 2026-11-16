"""Сценарии регистрации, входа и чтения текущего пользователя."""

import uuid

from app.domain.auth import (
    Account,
    EmailTakenError,
    InvalidCredentialsError,
    PasswordHasher,
    Role,
    StoredUser,
    UserRepository,
)
from app.domain.security import ensure_password

_dummy_hash: str | None = None


def _account(stored: StoredUser) -> Account:
    return Account(
        id=stored.id,
        email=stored.email,
        username=stored.username,
        role=stored.role,
        channel_id=stored.channel_id,
    )


def register_user(
    users: UserRepository,
    hasher: PasswordHasher,
    email: str,
    username: str,
    password: str,
) -> Account:
    ensure_password(password)
    if users.get_by_email(email) is not None:
        raise EmailTakenError("Email уже занят")
    stored = users.add_user_with_channel(
        user_id=str(uuid.uuid4()),
        email=email,
        username=username,
        password_hash=hasher.hash(password),
        role=Role.user.value,
        channel_id=str(uuid.uuid4()),
        channel_name=username,
    )
    return _account(stored)


def authenticate(
    users: UserRepository,
    hasher: PasswordHasher,
    email: str,
    password: str,
) -> Account:
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hasher.hash("not-a-real-password")
    stored = users.get_by_email(email)
    password_hash = stored.password_hash if stored is not None else _dummy_hash
    if stored is None or not hasher.verify(password, password_hash):
        raise InvalidCredentialsError("Неверный email или пароль")
    return _account(stored)


def find_people(users: UserRepository, query: str) -> list[Account]:
    text = query.strip()
    if not text:
        return []
    return [_account(user) for user in users.search(text)]


def account_by_id(users: UserRepository, user_id: str) -> Account:
    stored = users.get_by_id(user_id)
    if stored is None:
        raise InvalidCredentialsError("Недействительный токен")
    return _account(stored)
