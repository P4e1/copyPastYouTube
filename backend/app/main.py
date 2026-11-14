"""Точка входа HTTP API.

create_app собирает FastAPI, проверку PostgreSQL, Swagger /docs и маршруты auth.
Секреты читаются из DATABASE_URL и JWT_SECRET.

Подключённые маршруты:
- auth: /auth/register, /auth/login, /auth/me

Планируемые роутеры следующих срезов:
- videos: /videos, /videos/{id}, /videos/{id}/complete, /videos/{id}/playback,
  /videos/{id}/view, /videos/{id}/like, /videos/{id}/comments
- feed: /feed, /search
- channels: /channels/{id}, /channels/{id}/subscribe
- playlists: /playlists
- moderation: /reports, /moderation/reports, /moderation/videos/{id}/hide
- admin: /admin/users/{id}/role
"""

import os

from fastapi import FastAPI

from app.infrastructure.auth_gateway import account_by_token, login_account, register_account
from app.infrastructure.db import check_database, init_engine
from app.presentation.auth import router as auth_router
from app.presentation.errors import register_exception_handlers
from app.presentation.health import router as health_router


def create_app() -> FastAPI:
    database_url = os.environ["DATABASE_URL"]
    init_engine(database_url)
    app = FastAPI(title="CopyPast YouTube")
    app.state.check_database = check_database
    app.state.register_account = register_account
    app.state.login_account = login_account
    app.state.account_by_token = account_by_token
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    return app
