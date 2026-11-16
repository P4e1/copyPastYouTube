# domain

Сущности, перечисления, правила видимости, ошибки домена, порты репозиториев и хранилища.

Можно импортировать только стандартную библиотеку Python и код этого слоя.

Нельзя импортировать FastAPI, HTTP-схемы, SQLAlchemy, Alembic, boto3, MinIO, ffmpeg, `presentation` и `infrastructure`.

Общие типы пользователя и ролей живут здесь и не дублируются в модулях `auth`, `videos`, `feed`, `channels`, `playlists`, `moderation`, `media`. Политика пароля, секрет JWT и окно попыток входа живут в `security.py`.
