"""Выбор фейка или MinIO по окружению. Пакет minio импортируется только для бакета."""

import os

from app.domain.storage import FakeObjectStorage


def build_storage():
    endpoint = os.environ.get("MINIO_ENDPOINT", "").strip()
    if not endpoint:
        return FakeObjectStorage()
    from app.infrastructure.minio_storage import MinioObjectStorage

    return MinioObjectStorage(
        endpoint=endpoint,
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        bucket=os.environ.get("MINIO_BUCKET", "videos"),
        public_endpoint=os.environ.get("MINIO_PUBLIC_ENDPOINT", endpoint),
    )
