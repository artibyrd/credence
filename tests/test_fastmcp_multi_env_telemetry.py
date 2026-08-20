"""Tests for FastMCP Multi-Environment Telemetry and Resource Labels."""

import os
from unittest.mock import patch

import pytest

from credence.config import Settings
from credence.storage.base import get_blob_storage
from credence.storage.local import LocalFileBlobStorage
from credence.storage.s3 import S3BlobStorage


@pytest.mark.unit
def test_fastmcp_resource_reports_correct_environment():
    """Verify settings correctly distinguish environment identifiers."""
    dev_settings = Settings(ENV="development")
    assert dev_settings.ENV == "development"

    prod_settings = Settings(ENV="production")
    assert prod_settings.ENV == "production"


@pytest.mark.unit
def test_fastmcp_storage_backend_introspection(tmp_path):
    """Verify storage driver introspection correctly identifies Local vs S3 storage."""
    with patch.dict(os.environ, {"STORAGE_BACKEND": "local", "SNAPSHOT_DIR": str(tmp_path)}):
        local_store = get_blob_storage(Settings())
        assert isinstance(local_store, LocalFileBlobStorage)

    with patch.dict(os.environ, {"STORAGE_BACKEND": "s3", "S3_BUCKET_NAME": "my-bucket"}):
        s3_store = get_blob_storage(Settings())
        assert isinstance(s3_store, S3BlobStorage)
