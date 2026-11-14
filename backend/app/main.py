"""Точка входа HTTP API.

create_app собирает FastAPI, проверку PostgreSQL и Swagger /docs.
Секрет подключения читается из DATABASE_URL.

Планируемые роутеры модулей подключаются в следующих срезах:
- auth: /auth/register, /auth/login, /auth/me
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

from app.infrastructure.db import check_database, init_engine
from app.presentation.errors import register_exception_handlers
from app.presentation.health import router as health_router


def create_app() -> FastAPI:
    database_url = os.environ["DATABASE_URL"]
    init_engine(database_url)
    app = FastAPI(title="CopyPast YouTube")
    app.state.check_database = check_database
    register_exception_handlers(app)
    app.include_router(health_router)
    return app
