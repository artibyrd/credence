"""Unit tests for Content-Addressable Blob Storage and CAS path traversal validation."""

from __future__ import annotations

import pytest

from credence.storage.base import validate_cas_key
from credence.storage.local import LocalFileBlobStorage
from credence.storage.s3 import S3BlobStorage


@pytest.mark.unit
def test_cas_key_validation():
    """Verify CAS key pattern matching and directory traversal rejection."""
    valid_key = "cas/sha256/a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0.html"
    assert validate_cas_key(valid_key) is True

    # Traversal attempts
    assert validate_cas_key("../etc/passwd") is False
    assert validate_cas_key("cas/sha256/../../secret.html") is False
    assert validate_cas_key("cas/sha256/invalid_hash.html") is False
    assert validate_cas_key("cas/sha256/a1b2c3.exe") is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_local_blob_storage_put_and_get(tmp_path):
    """Test LocalFileBlobStorage write and read operations."""
    storage = LocalFileBlobStorage(base_dir=tmp_path)
    key = "cas/sha256/1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff.html"
    data = b"<html><body>Credence Verified Text</body></html>"

    uri = await storage.put_blob(key, data, content_type="text/plain; charset=utf-8")
    assert uri.startswith("file://")

    exists = await storage.exists(key)
    assert exists is True

    retrieved = await storage.get_blob(key)
    assert retrieved == data

    deleted = await storage.delete_blob(key)
    assert deleted is True
    assert await storage.exists(key) is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_s3_blob_storage_mock():
    """Test S3BlobStorage mock store for hermetic testing."""
    storage = S3BlobStorage(bucket_name="test-bucket")
    key = "cas/sha256/2222333344445555666677778888999900001111bbbbccccddddeeeeffffaaaa.png"
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

    uri = await storage.put_blob(key, png_bytes, content_type="image/png")
    assert "test-bucket" in uri

    assert await storage.exists(key) is True
    retrieved = await storage.get_blob(key)
    assert retrieved == png_bytes
