"""Точка входа HTTP API.

create_app собирает FastAPI, проверку PostgreSQL, Swagger /docs и маршруты auth.
Секреты читаются из DATABASE_URL и JWT_SECRET.

Подключённые маршруты:
- auth: /auth/register, /auth/login, /auth/me
- videos: POST /videos, GET /videos/{id}, GET /feed, GET /search

Планируемые роутеры следующих срезов:
- videos: /videos/{id}/complete, /videos/{id}/playback,
  /videos/{id}/view, /videos/{id}/like, /videos/{id}/comments
- channels: /channels/{id}, /channels/{id}/subscribe
- playlists: /playlists
- moderation: /reports, /moderation/reports, /moderation/videos/{id}/hide
- admin: /admin/users/{id}/role
"""

import os

from fastapi import FastAPI

from app.infrastructure.auth_gateway import account_by_token, login_account, register_account
from app.infrastructure.db import check_database, init_engine
from app.infrastructure.video_gateway import create_video_for_channel, feed_cards, search_cards, video_card
from app.presentation.auth import router as auth_router
from app.presentation.errors import register_exception_handlers
from app.presentation.health import router as health_router
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
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(video_router)
    return app
