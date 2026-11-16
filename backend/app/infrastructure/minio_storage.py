"""MinIO: короткие ссылки, проверка объекта и байты для воркера."""

import socket
import sys
import time
from datetime import timedelta
from io import BytesIO
from urllib.parse import urlparse

import urllib3
from urllib3.util import Timeout

from app.domain.storage import ObjectInfo


def ipv4_netloc(netloc: str, lookup) -> str:
    host, separator, port = netloc.rpartition(":")
    if not separator:
        host, port = netloc, ""
    if host.startswith("[") or host in {"localhost", "127.0.0.1"}:
        return netloc
    try:
        address = lookup(host, int(port) if port else 0)
    except OSError:
        return netloc
    if port:
        return f"{address}:{port}"
    return address


def call_with_retry(action, attempts: int, pause: float, sleep):
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except Exception:
            if attempt == attempts:
                raise
            sleep(pause)


def _ipv4_lookup(host: str, port: int) -> str:
    infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
    if not infos:
        raise OSError(host)
    return infos[0][4][0]


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
        self._io = self._client(Minio, endpoint, access_key, secret_key, resolve_ipv4=True)
        self._public = self._client(Minio, public_endpoint, access_key, secret_key, resolve_ipv4=False)
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        def once() -> None:
            try:
                if not self._io.bucket_exists(self._bucket):
                    self._io.make_bucket(self._bucket)
            except Exception as exc:
                print(f"MinIO: {exc}", file=sys.stderr, flush=True)
                raise

        call_with_retry(once, attempts=15, pause=2, sleep=time.sleep)

    @staticmethod
    def _client(minio_cls, endpoint: str, access_key: str, secret_key: str, *, resolve_ipv4: bool):
        parsed = urlparse(endpoint)
        netloc = ipv4_netloc(parsed.netloc, _ipv4_lookup) if resolve_ipv4 else parsed.netloc
        http = urllib3.PoolManager(
            timeout=Timeout(connect=3.0, read=300.0),
            retries=False,
        )
        return minio_cls(
            netloc,
            access_key=access_key,
            secret_key=secret_key,
            secure=parsed.scheme == "https",
            region="us-east-1",
            http_client=http,
        )

    def allocate_upload(self, video_id: str) -> tuple[str, str]:
        key = f"videos/{video_id}/source.mp4"
        url = self._public.presigned_put_object(self._bucket, key, expires=timedelta(hours=12))
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
