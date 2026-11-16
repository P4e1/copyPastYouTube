"""Фикстуры каркаса: PostgreSQL по DATABASE_URL и HTTP-клиент на create_app().

Дальнейшие срезы идут после каркаса: auth, видео и лента, просмотр с лайками
и комментариями, канал с подпиской и плейлистами, приватность, модерация и роли,
загрузка в MinIO, сквозной сценарий
«регистрация → загрузка → просмотр → лайк → комментарий».

Запуск из корня репозитория: pytest backend/tests
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["JWT_SECRET"] = "test-jwt-secret-ok"
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ["AUTH_RATE_LIMIT"] = "10000"
os.environ["CORS_ORIGINS"] = "http://127.0.0.1:5173,http://localhost:5173"


@pytest.fixture(scope="session")
def database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.fail("Задайте DATABASE_URL для PostgreSQL. Команда подъёма базы есть в backend/README.md.")
    os.environ["DATABASE_URL"] = url
    return url


@pytest.fixture(scope="session")
def app(database_url):
    os.environ["JWT_SECRET"] = "test-jwt-secret-ok"
    os.environ["AUTH_RATE_LIMIT"] = "10000"
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    from app.main import create_app

    return create_app()


@pytest.fixture(scope="session", autouse=True)
def migrated_database(database_url):
    from alembic import command
    from alembic.config import Config

    config = Config("backend/alembic.ini")
    command.upgrade(config, "head")


@pytest.fixture
def client(app):
    import anyio
    from httpx import ASGITransport, AsyncClient

    class SyncClient:
        def request(self, method, path, json=None, headers=None):
            async def _call():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as http_client:
                    return await http_client.request(method, path, json=json, headers=headers)

            return anyio.run(_call)

        def get(self, path, headers=None):
            return self.request("GET", path, headers=headers)

        def post(self, path, json=None, headers=None):
            return self.request("POST", path, json=json, headers=headers)

        def patch(self, path, json=None, headers=None):
            return self.request("PATCH", path, json=json, headers=headers)

        def delete(self, path, headers=None):
            return self.request("DELETE", path, headers=headers)

    return SyncClient()
