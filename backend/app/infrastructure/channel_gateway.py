"""Сборка сценариев канала, подписки и плейлистов."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.application.channels import (
    ChannelCard,
    ChannelRecord,
    PlaylistCard,
    add_playlist_item,
    create_playlist,
    open_channel,
    playlists_of,
    rename_channel,
    subscribe,
    unsubscribe,
)
from app.infrastructure import db
from app.infrastructure.channel_repository import SqlChannelRepository


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


def channel_card(channel_id: str, viewer_id: str | None) -> ChannelCard:
    with _session_scope() as session:
        return open_channel(SqlChannelRepository(session), channel_id, viewer_id)


def subscribe_channel(channel_id: str, subscriber_id: str) -> None:
    with _session_scope() as session:
        subscribe(SqlChannelRepository(session), channel_id, subscriber_id)


def unsubscribe_channel(channel_id: str, subscriber_id: str) -> None:
    with _session_scope() as session:
        unsubscribe(SqlChannelRepository(session), channel_id, subscriber_id)


def update_channel_name(channel_id: str, actor_id: str, name: str) -> ChannelRecord:
    with _session_scope() as session:
        return rename_channel(SqlChannelRepository(session), channel_id, actor_id, name)


def open_playlist(channel_id: str, actor_id: str, title: str, visibility: str) -> PlaylistCard:
    with _session_scope() as session:
        return create_playlist(SqlChannelRepository(session), channel_id, actor_id, title, visibility)


def place_playlist_item(playlist_id: str, actor_id: str, video_id: str, position: int) -> None:
    with _session_scope() as session:
        add_playlist_item(SqlChannelRepository(session), playlist_id, actor_id, video_id, position)


def channel_playlists(channel_id: str, viewer_id: str | None) -> list[PlaylistCard]:
    with _session_scope() as session:
        return playlists_of(SqlChannelRepository(session), channel_id, viewer_id)
