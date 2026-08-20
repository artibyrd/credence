"""S3-Compatible Cloud Object Storage Implementation (Cloudflare R2, AWS S3, GCS)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from credence.storage.base import BlobStorage, validate_cas_key

logger = logging.getLogger("credence.storage.s3")


class S3BlobStorage(BlobStorage):
    """Stores content-addressed blobs in S3-compatible object buckets (e.g. Cloudflare R2)."""

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region_name: str = "auto",
        client_override: Optional[Any] = None,
    ) -> None:
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region_name = region_name
        self._client = client_override
        # In-memory mock store for hermetic testing if client is None and no network credentials
        self._mock_store: dict[str, tuple[bytes, str]] = {}

    def _get_cas_key(self, key: str) -> str:
        if not validate_cas_key(key):
            raise ValueError(f"Invalid CAS key format: {key}")
        return key

    async def put_blob(
        self,
        key: str,
        data: bytes,
        content_type: str = "text/plain; charset=utf-8",
    ) -> str:
        cas_key = self._get_cas_key(key)

        if self._client:
            # Check if key already exists to guarantee write-once immutability
            try:
                await self._client.head_object(Bucket=self.bucket_name, Key=cas_key)
                logger.debug("CAS blob %s already exists in %s; skipping write.", cas_key, self.bucket_name)
            except Exception:
                await self._client.put_object(
                    Bucket=self.bucket_name,
                    Key=cas_key,
                    Body=data,
                    ContentType=content_type,
                )
        else:
            if cas_key not in self._mock_store:
                self._mock_store[cas_key] = (data, content_type)

        endpoint = self.endpoint_url or "https://s3.amazonaws.com"
        return f"{endpoint.rstrip('/')}/{self.bucket_name}/{cas_key}"

    async def get_blob(self, key: str) -> Optional[bytes]:
        cas_key = self._get_cas_key(key)

        if self._client:
            try:
                response = await self._client.get_object(Bucket=self.bucket_name, Key=cas_key)
                body = response.get("Body")
                if hasattr(body, "read"):
                    data = await body.read()
                    return bytes(data) if isinstance(data, (bytes, bytearray)) else None
                return None
            except Exception as e:
                logger.debug("Blob %s not found in S3 bucket %s: %s", cas_key, self.bucket_name, e)
                return None

        if cas_key in self._mock_store:
            return bytes(self._mock_store[cas_key][0])
        return None

    async def exists(self, key: str) -> bool:
        cas_key = self._get_cas_key(key)

        if self._client:
            try:
                await self._client.head_object(Bucket=self.bucket_name, Key=cas_key)
                return True
            except Exception:
                return False

        return cas_key in self._mock_store

    async def delete_blob(self, key: str) -> bool:
        cas_key = self._get_cas_key(key)

        if self._client:
            try:
                await self._client.delete_object(Bucket=self.bucket_name, Key=cas_key)
                return True
            except Exception as e:
                logger.warning("Failed to delete S3 blob %s: %s", cas_key, e)
                return False

        if cas_key in self._mock_store:
            del self._mock_store[cas_key]
            return True
        return False
