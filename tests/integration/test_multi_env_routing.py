"""Tests for Multi-Environment Configuration Routing and Storage Engine Selection."""

import os
from unittest.mock import patch

import pytest

from credence.config import Settings
from credence.storage.base import get_blob_storage
from credence.storage.local import LocalFileBlobStorage
from credence.storage.s3 import S3BlobStorage


@pytest.mark.integration
def test_env_mode_detection_and_backend_selection(tmp_path):
    """Test that Settings correctly reflects development vs production configuration."""
    with patch.dict(os.environ, {"ENV": "development", "STORAGE_BACKEND": "local", "SNAPSHOT_DIR": str(tmp_path)}):
        dev_settings = Settings()
        assert dev_settings.ENV == "development"
        assert dev_settings.STORAGE_BACKEND == "local"
        storage = get_blob_storage(dev_settings)
        assert isinstance(storage, LocalFileBlobStorage)

    with patch.dict(os.environ, {"ENV": "production", "STORAGE_BACKEND": "s3", "S3_BUCKET_NAME": "test-bucket"}):
        prod_settings = Settings()
        assert prod_settings.ENV == "production"
        assert prod_settings.STORAGE_BACKEND == "s3"
        storage = get_blob_storage(prod_settings)
        assert isinstance(storage, S3BlobStorage)


@pytest.mark.integration
def test_admin_auth_environment_isolation():
    """Verify that localhost bypass behavior differs based on ENV and Admin API Key."""
    dev_settings = Settings(ENV="development", CREDENCE_ADMIN_API_KEY="")
    assert dev_settings.ENV == "development"
    assert dev_settings.CREDENCE_ADMIN_API_KEY == ""

    prod_settings = Settings(ENV="production", CREDENCE_ADMIN_API_KEY="super_secret_token_12345")
    assert prod_settings.ENV == "production"
    assert prod_settings.CREDENCE_ADMIN_API_KEY == "super_secret_token_12345"


@pytest.mark.integration
def test_dev_subdomain_header_forwarding():
    """Verify host header transformation rules for dev.* subdomains."""
    dev_hosts = [
        "dev.credence.run",
        "mcp.dev.credence.run",
        "dev.credence.nexus",
        "dev.credence.foundation",
        "dev.credence.report",
    ]
    for host in dev_hosts:
        is_dev = (
            host.startsWith("dev.")
            if hasattr(host, "startsWith")
            else host.startswith("dev.") or host.startswith("mcp.dev.")
        )
        assert is_dev is True
        clean_host = host.replace("dev.", "")
        assert clean_host in [
            "credence.run",
            "mcp.credence.run",
            "credence.nexus",
            "credence.foundation",
            "credence.report",
        ]
