"""
Abstract storage backend for documents and artifacts.

Supports local filesystem (development) and S3 (production).
Auto-selects based on s3_bucket_name in config.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path

from munipal.config import get_settings


class StorageBackend(ABC):
    """Abstract interface for file storage."""

    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store data at key. Returns the storage key."""
        ...

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """Retrieve data by key."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete data by key."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...

    @abstractmethod
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a time-limited URL for direct access (S3 only; local returns file path)."""
        ...


class LocalStorageBackend(StorageBackend):
    """Filesystem-based storage for development."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self.base_path / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    async def get(self, key: str) -> bytes:
        path = self.base_path / key
        if not path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return path.read_bytes()

    async def delete(self, key: str) -> None:
        path = self.base_path / key
        if path.exists():
            path.unlink()

    async def exists(self, key: str) -> bool:
        return (self.base_path / key).exists()

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return str(self.base_path / key)


class S3StorageBackend(StorageBackend):
    """AWS S3 storage for production."""

    def __init__(self, bucket: str, region: str, access_key: str | None, secret_key: str | None):
        import boto3

        session_kwargs: dict = {"region_name": region}
        if access_key and secret_key:
            session_kwargs["aws_access_key_id"] = access_key
            session_kwargs["aws_secret_access_key"] = secret_key

        self._s3 = boto3.client("s3", **session_kwargs)
        self._bucket = bucket

    async def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    async def get(self, key: str) -> bytes:
        response = self._s3.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    async def delete(self, key: str) -> None:
        self._s3.delete_object(Bucket=self._bucket, Key=key)

    async def exists(self, key: str) -> bool:
        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
            return True
        except self._s3.exceptions.ClientError:
            return False

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )


def get_storage_backend() -> StorageBackend:
    """Get the configured storage backend (singleton-ish via settings)."""
    settings = get_settings()
    if settings.s3_bucket_name:
        return S3StorageBackend(
            bucket=settings.s3_bucket_name,
            region=settings.aws_region,
            access_key=settings.aws_access_key_id,
            secret_key=settings.aws_secret_access_key,
        )
    return LocalStorageBackend(settings.document_storage_path)
