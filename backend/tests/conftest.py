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


@pytest.fixture(scope="session")
def database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.fail("Задайте DATABASE_URL для PostgreSQL. Команда подъёма базы есть в backend/README.md.")
    os.environ["DATABASE_URL"] = url
    return url


@pytest.fixture(scope="session")
def app(database_url):
    from app.main import create_app

    return create_app()


@pytest.fixture
def client(app):
    import anyio
    from httpx import ASGITransport, AsyncClient

    class SyncClient:
        def get(self, path):
            async def _call():
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as http_client:
                    return await http_client.get(path)

            return anyio.run(_call)

    return SyncClient()
