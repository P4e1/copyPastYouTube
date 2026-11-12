# Бэкенд

Чистые слои. Стрелки зависимостей направлены только внутрь: `presentation` вызывает `application`, `application` вызывает порты `domain`, `infrastructure` реализует эти порты. Обратных импортов нет.

```mermaid
flowchart TB
  presentation[presentation_FastAPI]
  application[application_use_cases]
  domain[domain_entities_and_ports]
  infrastructure[infrastructure_db_s3_ffmpeg]
  presentation --> application
  application --> domain
  infrastructure --> domain
  infrastructure --> application
```

## Что можно и нельзя

- `domain` не импортирует FastAPI, SQLAlchemy, Alembic, boto3, MinIO и ffmpeg.
- `application` не собирает HTTP-ответ и не знает коды статусов. Сценарий возвращает результат или доменную ошибку.
- `presentation` не импортирует сессию базы и клиент хранилища. SQL здесь не пишется.
- `infrastructure` не импортирует роутеры и не отвечает на HTTP.

Короткие правила лежат в README каждого слоя: [domain](app/domain/README.md), [application](app/application/README.md), [infrastructure](app/infrastructure/README.md), [presentation](app/presentation/README.md).

## Модули

Внутри слоёв код режется по темам: `auth`, `videos`, `feed`, `channels`, `playlists`, `moderation`, `media`. Пользователь, роль и правила видимости видео объявляются один раз в `domain`.

Точка входа [app/main.py](app/main.py) только собирает приложение и подключает роутеры. Сейчас `create_app()` ещё не собрано.

## Сценарии приложения

Их реализует слой `application`.

- Регистрация создаёт пользователя с ролью `user` и его канал. Дубликат email — доменная ошибка.
- Логин проверяет хеш пароля и возвращает данные для JWT. Выпуск токена делает infrastructure, проверка токена на входе — presentation.
- Создание видео пишет статус `uploading` и серверный ключ объекта. Клиент ключ не выбирает.
- Завершение загрузки доступно владельцу и ставит строку в `media_jobs`.
- Лента и поиск отдают только `public` и `ready`.
- Просмотр `ready` увеличивает счётчик и выдаёт право на presigned GET.
- Лайк хранит одно значение на пару пользователь–видео: `1` или `-1`.
- Комментарий виден в списке ролика. Чужой комментарий автор ролика не удаляет от имени зрителя, зритель не удаляет чужой.
- Подписка и отписка идемпотентны.
- Плейлист хранит порядок роликов. Чужой канал и чужой плейлист не редактируются.
- Private без записи в `video_grants` не отдаёт ни карточку, ни адрес просмотра. Unlisted открывается по id и не попадает в ленту и поиск.
- Жалобу создаёт пользователь. Модератор скрывает видео. Администратор назначает роль модератора. Модератор администратора не назначает.

Маршруты, которые presentation повесит на эти сценарии, перечислены в [app/main.py](app/main.py). Контракт данных — в [docs/database.md](../docs/database.md) и [docs/security.md](../docs/security.md).

## Тесты

Тесты пишутся до кода. Порядок срезов зафиксирован в [tests/conftest.py](tests/conftest.py). Запуск из корня репозитория:

```bash
pytest backend/tests
```

Сейчас тестов нет: команда завершится сообщением, что собирать нечего. Первый срез — регистрация и вход против PostgreSQL.
