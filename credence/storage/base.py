"""Content-Addressable Blob Storage (CAS) Abstraction for Credence.

Provides an abstract interface for persisting and retrieving HTML DOM dumps,
screenshots, and raw snapshot artifacts in local or cloud storage.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Optional

# Content-Addressable Storage key pattern: cas/sha256/<64_hex_hash>.<ext>
CAS_KEY_PATTERN = re.compile(r"^cas/sha256/[a-f0-9]{64}\.(html|png|json|txt)$")


def validate_cas_key(key: str) -> bool:
    """Validate that a blob storage key conforms to strict content-addressable constraints.

    Prevents directory traversal, arbitrary file writes, and non-hash filenames.
    """
    if ".." in key or "\\" in key or "\x00" in key:
        return False
    return bool(CAS_KEY_PATTERN.match(key))


class BlobStorage(ABC):
    """Abstract Base Class for Credence Blob Storage."""

    @abstractmethod
    async def put_blob(
        self,
        key: str,
        data: bytes,
        content_type: str = "text/plain; charset=utf-8",
    ) -> str:
        """Store binary data under a validated CAS key.

        Returns the canonical storage URI.
        """
        ...

    @abstractmethod
    async def get_blob(self, key: str) -> Optional[bytes]:
        """Retrieve binary blob by CAS key. Returns None if not found."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a blob exists by CAS key."""
        ...

    @abstractmethod
    async def delete_blob(self, key: str) -> bool:
        """Delete a blob by CAS key. Returns True if deleted."""
        ...


_default_storage: Optional[BlobStorage] = None


def get_blob_storage(cfg: Optional[Any] = None) -> BlobStorage:
    """Factory to retrieve the configured global or custom BlobStorage instance."""
    global _default_storage
    active_settings = cfg
    if active_settings is None:
        if _default_storage is not None:
            return _default_storage
        from credence.config import settings

        active_settings = settings

    store: BlobStorage
    if active_settings.STORAGE_BACKEND.lower() == "s3" and active_settings.S3_BUCKET_NAME:
        from credence.storage.s3 import S3BlobStorage

        store = S3BlobStorage(
            bucket_name=active_settings.S3_BUCKET_NAME,
            endpoint_url=active_settings.S3_ENDPOINT_URL,
            access_key_id=active_settings.S3_ACCESS_KEY_ID,
            secret_access_key=active_settings.S3_SECRET_ACCESS_KEY,
            region_name=active_settings.S3_REGION_NAME,
        )
    else:
        from credence.storage.local import LocalFileBlobStorage

        store = LocalFileBlobStorage(base_dir=active_settings.SNAPSHOT_DIR)

    if cfg is None:
        _default_storage = store
    return store
