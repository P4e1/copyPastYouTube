"""Сборка сценариев auth поверх сессии, хеша и JWT."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.application.auth import account_by_id, authenticate, register_user
from app.domain.auth import Account
from app.infrastructure import db
from app.infrastructure.passwords import PwdlibHasher
from app.infrastructure.tokens import issue_token, read_user_id
from app.infrastructure.user_repository import SqlUserRepository

_hasher = PwdlibHasher()


@contextmanager
def _session_scope() -> Iterator[Session]:
    if db.SessionLocal is None:
        raise RuntimeError("Подключение к базе не настроено")
    session = db.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def register_account(email: str, username: str, password: str) -> Account:
    with _session_scope() as session:
        return register_user(SqlUserRepository(session), _hasher, email, username, password)


def login_account(email: str, password: str) -> tuple[Account, str]:
    with _session_scope() as session:
        account = authenticate(SqlUserRepository(session), _hasher, email, password)
    return account, issue_token(account.id)


def account_by_token(token: str) -> Account:
    user_id = read_user_id(token)
    with _session_scope() as session:
        return account_by_id(SqlUserRepository(session), user_id)
