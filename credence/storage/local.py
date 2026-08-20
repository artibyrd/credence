"""Local Filesystem Implementation of BlobStorage for Credence."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from credence.storage.base import BlobStorage, validate_cas_key


class LocalFileBlobStorage(BlobStorage):
    """Stores content-addressed blobs directly on the local filesystem."""

    def __init__(self, base_dir: Path | str = "data/snapshots") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        if not validate_cas_key(key):
            raise ValueError(f"Invalid CAS key format: {key}")
        # Strip cas/ prefix for local relative path
        rel_path = key.removeprefix("cas/")
        full_path = self.base_dir / rel_path
        return full_path

    async def put_blob(
        self,
        key: str,
        data: bytes,
        content_type: str = "text/plain; charset=utf-8",
    ) -> str:
        full_path = self._resolve_path(key)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        def _write() -> None:
            # Write once if not present
            if not full_path.exists():
                full_path.write_bytes(data)

        await asyncio.to_thread(_write)
        return f"file://{full_path.resolve()}"

    async def get_blob(self, key: str) -> Optional[bytes]:
        full_path = self._resolve_path(key)

        def _read() -> Optional[bytes]:
            if full_path.is_file():
                return full_path.read_bytes()
            return None

        return await asyncio.to_thread(_read)

    async def exists(self, key: str) -> bool:
        full_path = self._resolve_path(key)
        return await asyncio.to_thread(full_path.is_file)

    async def delete_blob(self, key: str) -> bool:
        full_path = self._resolve_path(key)

        def _delete() -> bool:
            if full_path.is_file():
                full_path.unlink()
                return True
            return False

        return await asyncio.to_thread(_delete)
