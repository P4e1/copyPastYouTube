# База данных

PostgreSQL. Схема появляется миграциями Alembic в `backend/alembic`. Ниже — таблицы и смысл связей. Имена полей можно уточнять в миграции, смысл менять нельзя без правки этого файла.

## Таблицы

### users

Учётная запись. Поля: id, email (уникальный), username, password_hash, role (`user`, `moderator`, `admin`), avatar, created_at. Пароль в открытом виде не хранится.

### channels

Один канал на пользователя. Поля: id, owner_id (уникальный внешний ключ на users), name, description, banner. Регистрация создаёт канал вместе с пользователем.

### videos

Ролик канала. Поля: id, channel_id, title, description, visibility (`public`, `unlisted`, `private`), status (`uploading`, `processing`, `ready`, `failed`, `hidden`), object_key, thumbnail_key, duration_sec, view_count, created_at. Ключ объекта назначает сервер.

### video_grants

Кому дополнительно открыто private-видео. Поля: video_id, user_id. Пара уникальна. Для public и unlisted таблица не используется.

### watch_history

Просмотр, который зритель засчитал. Поля: user_id, video_id, watched_at. Пара зритель–ролик уникальна: повторный просмотр обновляет время и не создаёт вторую строку. В списке истории ролик есть, только если зрителю он всё ещё доступен.

### likes

Одна реакция на пару зритель–видео. Поля: user_id, video_id, value (`1` или `-1`). Повторный выбор меняет value, вторую строку не создаёт.

### comments

Комментарий под видео. Поля: id, video_id, user_id, parent_id (ответ, может быть пустым), body, is_hidden, created_at.

### subscriptions

Подписка пользователя на канал. Поля: subscriber_id, channel_id. Пара уникальна. Повторная подписка не создаёт вторую строку. Отписка удаляет строку.

### playlists и playlist_items

Плейлист автора. У плейлиста: id, channel_id, title, visibility. У элемента: playlist_id, video_id, position. Порядок на экране канала совпадает с position. Повторная запись той же пары не создаёт вторую строку и не меняет position. Удаление пары убирает ролик из плейлиста.

### reports

Жалоба на видео. Поля: id, reporter_id, video_id, reason, status (`open`, `resolved`, `rejected`), resolved_by, created_at. Скрытие видео модератором переводит ролик в `hidden` и закрывает связанные открытые жалобы как `resolved`.

### media_jobs

Очередь воркера. Отдельного брокера нет. Поля: id, video_id, kind (`thumbnail`, `finalize`), status (`pending`, `running`, `done`, `failed`), error, created_at. Воркер забирает `pending`, помечает `running`, по завершении пишет `done` или `failed`.

## Кто видит видео

Проверка одна и та же для ленты, поиска, карточки и ссылки на файл.

| Кто смотрит | public ready | unlisted ready | private ready | hidden | uploading, processing, failed |
| --- | --- | --- | --- | --- | --- |
| Зритель | да, есть в ленте и поиске | только по id | нет | нет | нет |
| Пользователь из video_grants | да | только по id | да, по id | нет | нет |
| Владелец | да | да | да | да, с пометкой | да, в своём канале |
| Модератор и администратор | да | да | как зритель, если нет grant | видят в модерации | нет в ленте |

«Нет» означает: запись не попадает в выдачу, а прямой запрос карточки и playback отвечает так же, как запрос несуществующего видео.

## Что где лежит

Метаданные, права, комментарии, жалобы и очередь задач — только в PostgreSQL. Байты видео и картинка превью — только в MinIO. В базе хранятся ключи объектов, не сами файлы.
