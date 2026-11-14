"""MinIO: короткие ссылки, проверка объекта и байты для воркера."""

from datetime import timedelta
from io import BytesIO
from urllib.parse import urlparse

from app.domain.storage import ObjectInfo


class MinioObjectStorage:
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        public_endpoint: str,
    ) -> None:
        from minio import Minio

        self._bucket = bucket
        self._io = self._client(Minio, endpoint, access_key, secret_key)
        self._public = self._client(Minio, public_endpoint, access_key, secret_key)
        if not self._io.bucket_exists(bucket):
            self._io.make_bucket(bucket)

    @staticmethod
    def _client(minio_cls, endpoint: str, access_key: str, secret_key: str):
        parsed = urlparse(endpoint)
        return minio_cls(
            parsed.netloc,
            access_key=access_key,
            secret_key=secret_key,
            secure=parsed.scheme == "https",
        )

    def allocate_upload(self, video_id: str) -> tuple[str, str]:
        key = f"videos/{video_id}/source.mp4"
        url = self._public.presigned_put_object(self._bucket, key, expires=timedelta(minutes=15))
        return key, url

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        self._io.put_object(
            self._bucket,
            key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    def get_bytes(self, key: str) -> bytes:
        response = self._io.get_object(self._bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def inspect(self, key: str) -> ObjectInfo | None:
        from minio.error import S3Error

        try:
            stat = self._io.stat_object(self._bucket, key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject"}:
                return None
            raise
        return ObjectInfo(size=stat.size or 0, content_type=stat.content_type or "")

    def presign_download(self, key: str) -> str:
        return self._public.presigned_get_object(self._bucket, key, expires=timedelta(minutes=15))
