"""Репозиторий пользователей и каналов."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.auth import EmailTakenError, StoredUser
from app.infrastructure.auth_models import ChannelRow, UserRow


class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> StoredUser | None:
        row = self._session.scalar(select(UserRow).where(UserRow.email == email))
        if row is None:
            return None
        return self._to_stored(row)

    def search(self, query: str) -> list[StoredUser]:
        pattern = f"%{query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')}%"
        rows = self._session.scalars(
            select(UserRow).where(UserRow.username.ilike(pattern, escape="\\")).order_by(UserRow.username).limit(8)
        )
        return [self._to_stored(row) for row in rows]

    def get_by_id(self, user_id: str) -> StoredUser | None:
        row = self._session.get(UserRow, user_id)
        if row is None:
            return None
        return self._to_stored(row)

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
        self._session.add(
            UserRow(
                id=user_id,
                email=email,
                username=username,
                password_hash=password_hash,
                role=role,
                created_at=datetime.now(timezone.utc),
            )
        )
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise EmailTakenError("Email уже занят") from exc
        self._session.add(
            ChannelRow(
                id=channel_id,
                owner_id=user_id,
                name=channel_name,
                description="",
            )
        )
        self._session.flush()
        return StoredUser(
            id=user_id,
            email=email,
            username=username,
            password_hash=password_hash,
            role=role,
            channel_id=channel_id,
        )

    def _to_stored(self, row: UserRow) -> StoredUser:
        channel_id = self._session.scalar(select(ChannelRow.id).where(ChannelRow.owner_id == row.id))
        if channel_id is None:
            raise RuntimeError("У пользователя нет канала")
        return StoredUser(
            id=row.id,
            email=row.email,
            username=row.username,
            password_hash=row.password_hash,
            role=row.role,
            channel_id=channel_id,
        )
