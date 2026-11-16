"""Сборка сценариев видео поверх сессии и выбранного хранилища."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace

from sqlalchemy.orm import Session

from app.application.channels import list_subscriptions
from app.application.engagement import list_history
from app.application.videos import (
    VideoCard,
    create_video,
    list_feed,
    list_subscription_feed,
    open_video,
    revise_upload,
    search_videos,
)
from app.infrastructure.channel_repository import SqlChannelRepository
from app.infrastructure.engagement_repository import SqlEngagementRepository
from app.domain.storage import ObjectStorage
from app.infrastructure import db
from app.infrastructure.user_repository import SqlUserRepository
from app.infrastructure.video_repository import SqlVideoRepository


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


def bind_create_video(storage: ObjectStorage):
    def create_video_for_channel(
        *,
        channel_id: str,
        owner_id: str,
        title: str,
        description: str,
        visibility: str,
        grant_user_ids: list[str],
    ) -> tuple[VideoCard, str]:
        with _session_scope() as session:
            return create_video(
                SqlVideoRepository(session),
                storage,
                channel_id=channel_id,
                owner_id=owner_id,
                title=title,
                description=description,
                visibility=visibility,
                grant_user_ids=grant_user_ids,
            )

    return create_video_for_channel


def revise_for_owner(
    video_id: str,
    actor_id: str,
    *,
    title: str,
    description: str,
    visibility: str,
    grant_user_ids: list[str],
) -> VideoCard:
    with _session_scope() as session:
        users = SqlUserRepository(session)
        return revise_upload(
            SqlVideoRepository(session),
            lambda user_id: users.get_by_id(user_id) is not None,
            video_id,
            actor_id,
            title=title,
            description=description,
            visibility=visibility,
            grant_user_ids=grant_user_ids,
        )


def _with_thumbnail(card: VideoCard, storage: ObjectStorage | None) -> VideoCard:
    if storage is None or not card.thumbnail_key:
        return card
    return replace(card, thumbnail_url=storage.presign_download(card.thumbnail_key))


def video_card(video_id: str, viewer_id: str | None, storage: ObjectStorage | None = None) -> VideoCard:
    with _session_scope() as session:
        return _with_thumbnail(open_video(SqlVideoRepository(session), video_id, viewer_id), storage)


def subscription_feed_cards(viewer_id: str, storage: ObjectStorage | None = None) -> list[VideoCard]:
    with _session_scope() as session:
        channels = list_subscriptions(SqlChannelRepository(session), viewer_id)
        cards = list_subscription_feed(SqlVideoRepository(session), [channel.id for channel in channels])
        return [_with_thumbnail(card, storage) for card in cards]


def history_cards(viewer_id: str, storage: ObjectStorage | None = None) -> list[VideoCard]:
    with _session_scope() as session:
        cards = list_history(SqlVideoRepository(session), SqlEngagementRepository(session), viewer_id)
        return [_with_thumbnail(card, storage) for card in cards]


def feed_cards(storage: ObjectStorage | None = None) -> list[VideoCard]:
    with _session_scope() as session:
        return [_with_thumbnail(card, storage) for card in list_feed(SqlVideoRepository(session))]


def search_cards(query: str, storage: ObjectStorage | None = None) -> list[VideoCard]:
    with _session_scope() as session:
        return [_with_thumbnail(card, storage) for card in search_videos(SqlVideoRepository(session), query)]
