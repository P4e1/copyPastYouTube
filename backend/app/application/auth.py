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
    stored = users.get_by_email(email)
    if stored is None or not hasher.verify(password, stored.password_hash):
        raise InvalidCredentialsError("Неверный email или пароль")
    return _account(stored)


def account_by_id(users: UserRepository, user_id: str) -> Account:
    stored = users.get_by_id(user_id)
    if stored is None:
        raise InvalidCredentialsError("Недействительный токен")
    return _account(stored)
