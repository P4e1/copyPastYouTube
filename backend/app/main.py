"""Точка входа HTTP API.

На шаге реализации здесь собирается приложение FastAPI.
Роутеры подключаются только из presentation и вызывают сценарии application.
Сборка приложения, маршруты и Swagger появятся вместе с первыми тестами.

Планируемые роутеры:
- auth: /auth/register, /auth/login, /auth/me
- videos: /videos, /videos/{id}, /videos/{id}/complete, /videos/{id}/playback,
  /videos/{id}/view, /videos/{id}/like, /videos/{id}/comments
- feed: /feed, /search
- channels: /channels/{id}, /channels/{id}/subscribe
- playlists: /playlists
- moderation: /reports, /moderation/reports, /moderation/videos/{id}/hide
- admin: /admin/users/{id}/role
- health: /health
"""


def create_app():
    """Собрать приложение FastAPI. Реализации ещё нет."""
    raise NotImplementedError(
        "HTTP-приложение ещё не собрано. См. docs/architecture.md и backend/README.md."
    )
