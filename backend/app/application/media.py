"""Завершение загрузки, ссылка просмотра и один проход очереди."""

from dataclasses import dataclass

from app.domain.errors import ForbiddenError, NotFoundError, UploadRejected
from app.domain.storage import ObjectStorage
from app.domain.videos import VideoStatus, View, view_access
from app.application.videos import VideoRepository, _snapshot


@dataclass(frozen=True)
class ClaimedJob:
    id: str
    video_id: str
    object_key: str


class MediaJobRepository:
    def enqueue(self, video_id: str) -> None:
        raise NotImplementedError

    def claim_next(self) -> ClaimedJob | None:
        raise NotImplementedError

    def finish(self, job_id: str, video_id: str, thumbnail_key: str, duration_sec: int) -> None:
        raise NotImplementedError

    def fail(self, job_id: str, video_id: str, error: str) -> None:
        raise NotImplementedError


class FrameExtractor:
    def preview(self, source: bytes) -> tuple[bytes, int]:
        """Кадр JPEG и длительность в секундах."""
        raise NotImplementedError


def _require_mp4(storage: ObjectStorage, object_key: str, max_bytes: int) -> None:
    info = storage.inspect(object_key)
    if info is None:
        raise UploadRejected("Файл не загружен")
    content_type = info.content_type.split(";", 1)[0].strip().lower()
    if content_type != "video/mp4":
        raise UploadRejected("Нужен файл mp4")
    if info.size <= 0 or info.size > max_bytes:
        raise UploadRejected("Размер файла не подходит")


def complete_upload(
    videos: VideoRepository,
    jobs: MediaJobRepository,
    storage: ObjectStorage,
    video_id: str,
    owner_id: str,
    max_bytes: int,
) -> None:
    stored = videos.get(video_id)
    if stored is None:
        raise NotFoundError("Не найдено")
    if stored.owner_id != owner_id:
        raise ForbiddenError("Чужой ролик завершить нельзя")
    if stored.status != VideoStatus.uploading.value:
        raise UploadRejected("Ролик уже отправлен в обработку")
    _require_mp4(storage, stored.object_key, max_bytes)
    jobs.enqueue(video_id)


def playback_url(videos: VideoRepository, storage: ObjectStorage, video_id: str, viewer_id: str | None) -> str:
    stored = videos.get(video_id)
    if stored is None:
        raise NotFoundError("Не найдено")
    if view_access(_snapshot(stored), viewer_id) is not View.allowed:
        raise NotFoundError("Не найдено")
    if stored.status != VideoStatus.ready.value:
        raise NotFoundError("Не найдено")
    return storage.presign_download(stored.object_key)


def process_next(jobs: MediaJobRepository, storage: ObjectStorage, extractor: FrameExtractor) -> bool:
    claimed = jobs.claim_next()
    if claimed is None:
        return False
    try:
        source = storage.get_bytes(claimed.object_key)
        preview, duration = extractor.preview(source)
        thumbnail_key = f"videos/{claimed.video_id}/thumbnail.jpg"
        storage.put_bytes(thumbnail_key, preview, "image/jpeg")
        jobs.finish(claimed.id, claimed.video_id, thumbnail_key, duration)
    except Exception as exc:
        jobs.fail(claimed.id, claimed.video_id, str(exc)[:500] or "Ошибка обработки")
    return True
