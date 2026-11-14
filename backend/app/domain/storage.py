"""Ключ объекта и временная ссылка без MinIO."""

from typing import Protocol


class ObjectStorage(Protocol):
    def allocate_upload(self, video_id: str) -> tuple[str, str]:
        """Вернуть серверный ключ объекта и временную ссылку загрузки."""


class FakeObjectStorage:
    """Заглушка хранилища, пока нет MinIO."""

    def allocate_upload(self, video_id: str) -> tuple[str, str]:
        key = f"videos/{video_id}/source.mp4"
        return key, f"https://storage.test/{key}"
