"""Сессия SQLAlchemy и проверка доступности PostgreSQL."""

from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

class Base(DeclarativeBase):
    """База моделей. Таблицы появятся в миграциях модулей."""


_engine = None
SessionLocal = None


def init_engine(database_url: str) -> None:
    global _engine, SessionLocal
    _engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def check_database() -> None:
    """Бросает исключение, если PostgreSQL не отвечает на SELECT 1."""
    if _engine is None:
        raise RuntimeError("Подключение к базе не настроено")
    with _engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def get_session() -> Iterator[Session]:
    if SessionLocal is None:
        raise RuntimeError("Подключение к базе не настроено")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
