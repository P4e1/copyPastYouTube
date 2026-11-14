"""Ключ объекта и временная ссылка. Реализация MinIO живёт в infrastructure."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ObjectInfo:
    size: int
    content_type: str


class ObjectStorage(Protocol):
    def allocate_upload(self, video_id: str) -> tuple[str, str]:
        """Вернуть серверный ключ объекта и временную ссылку загрузки."""

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        """Положить байты объекта. Нужно воркеру и фейку в тестах."""

    def get_bytes(self, key: str) -> bytes:
        """Прочитать объект целиком."""

    def inspect(self, key: str) -> ObjectInfo | None:
        """Размер и content-type. None, если объекта нет."""

    def presign_download(self, key: str) -> str:
        """Короткая ссылка на чтение объекта."""


class FakeObjectStorage:
    """Память вместо бакета, пока тест не поднимает MinIO."""

    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str]] = {}

    def allocate_upload(self, video_id: str) -> tuple[str, str]:
        key = f"videos/{video_id}/source.mp4"
        return key, f"https://storage.test/{key}"

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        self._objects[key] = (data, content_type)

    def get_bytes(self, key: str) -> bytes:
        return self._objects[key][0]

    def inspect(self, key: str) -> ObjectInfo | None:
        stored = self._objects.get(key)
        if stored is None:
            return None
        data, content_type = stored
        return ObjectInfo(size=len(data), content_type=content_type)

    def presign_download(self, key: str) -> str:
        return f"https://storage.test/{key}"
