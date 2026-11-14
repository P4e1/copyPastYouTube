"""Точка входа HTTP API.

create_app собирает FastAPI, проверку PostgreSQL, Swagger /docs и маршруты auth.
Секреты читаются из DATABASE_URL и JWT_SECRET.

Подключённые маршруты:
- auth: /auth/register, /auth/login, /auth/me
- videos: POST /videos, GET /videos/{id}, GET /feed, GET /search
- engagement: POST /videos/{id}/view, POST /videos/{id}/like, GET и POST /videos/{id}/comments, DELETE /videos/{id}/comments/{comment_id}
- channels: GET /channels/{id}, PATCH /channels/{id}, POST и DELETE /channels/{id}/subscribe
- playlists: GET и POST /playlists, POST /playlists/{id}/items
- moderation: POST /reports, GET /moderation/reports, POST /moderation/videos/{id}/hide, POST /moderation/videos/{id}/restore
- admin: PATCH /admin/users/{id}/role

Планируемые роутеры следующих срезов:
- videos: /videos/{id}/complete, /videos/{id}/playback
"""

import os

from fastapi import FastAPI

from app.infrastructure.auth_gateway import account_by_token, login_account, register_account
from app.infrastructure.db import check_database, init_engine
from app.infrastructure.engagement_gateway import (
    comments_for_video,
    delete_own_comment,
    publish_comment,
    register_like,
    register_view,
)
from app.infrastructure.channel_gateway import (
    channel_card,
    channel_playlists,
    open_playlist,
    place_playlist_item,
    subscribe_channel,
    unsubscribe_channel,
    update_channel_name,
)
from app.infrastructure.moderation_gateway import (
    change_user_role,
    file_report,
    hide_reported_video,
    queue_reports,
    restore_hidden_video,
)
from app.infrastructure.video_gateway import create_video_for_channel, feed_cards, search_cards, video_card
from app.presentation.auth import router as auth_router
from app.presentation.channels import router as channel_router
from app.presentation.engagement import router as engagement_router
from app.presentation.errors import register_exception_handlers
from app.presentation.health import router as health_router
from app.presentation.moderation import router as moderation_router
from app.presentation.videos import router as video_router


def create_app() -> FastAPI:
    database_url = os.environ["DATABASE_URL"]
    init_engine(database_url)
    app = FastAPI(title="CopyPast YouTube")
    app.state.check_database = check_database
    app.state.register_account = register_account
    app.state.login_account = login_account
    app.state.account_by_token = account_by_token
    app.state.create_video = create_video_for_channel
    app.state.get_video = video_card
    app.state.list_feed = feed_cards
    app.state.search_videos = search_cards
    app.state.register_view = register_view
    app.state.register_like = register_like
    app.state.publish_comment = publish_comment
    app.state.comments_for_video = comments_for_video
    app.state.delete_own_comment = delete_own_comment
    app.state.channel_card = channel_card
    app.state.update_channel_name = update_channel_name
    app.state.subscribe_channel = subscribe_channel
    app.state.unsubscribe_channel = unsubscribe_channel
    app.state.open_playlist = open_playlist
    app.state.place_playlist_item = place_playlist_item
    app.state.channel_playlists = channel_playlists
    app.state.file_report = file_report
    app.state.queue_reports = queue_reports
    app.state.hide_reported_video = hide_reported_video
    app.state.restore_hidden_video = restore_hidden_video
    app.state.change_user_role = change_user_role
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(video_router)
    app.include_router(engagement_router)
    app.include_router(channel_router)
    app.include_router(moderation_router)
    return app
