"""Integration Tests for Database Backup CLI and REST API Endpoints."""

import asyncio
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from credence.config import CostProfile, settings
from credence.db import get_engine, init_db
from credence.server.app import create_server_app


@pytest.fixture
def test_client(tmp_path: Path, monkeypatch):
    """Provide TestClient with isolated temporary database and admin auth configuration."""
    db_path = tmp_path / "api_test.db"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "DB_PATH", db_path)
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setattr(settings, "CREDENCE_BACKUP_DIR", backup_dir)
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "NODE_KEY_PATH", tmp_path / "node.key")
    monkeypatch.setattr(settings, "CREDENCE_ADMIN_API_KEY", "secret_admin_token_123")
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "CREDENCE_PROFILE", CostProfile.OFFLINE)

    # Initialize DB file on disk
    engine = get_engine(f"sqlite+aiosqlite:///{db_path}")
    asyncio.run(init_db(engine))

    app = create_server_app()
    return TestClient(app)


@pytest.mark.integration
def test_api_db_backup_auth_gating(test_client: TestClient):
    """Verify POST /api/db/backup requires administrator authentication."""
    # 1. Unauthorized request without header
    res_unauth = test_client.post("/api/db/backup", json={})
    assert res_unauth.status_code == 401
    assert "Unauthorized" in res_unauth.json().get("error", "")

    # 2. Authorized request with Bearer token
    headers = {"Authorization": "Bearer secret_admin_token_123"}
    res_auth = test_client.post("/api/db/backup", json={"upload_cloud": False}, headers=headers)
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["status"] == "success"
    assert "backup" in data
    assert data["backup"]["sha256_hash"] != ""


@pytest.mark.integration
def test_api_db_status_public(test_client: TestClient):
    """Verify GET /api/db/status returns public telemetry data."""
    res = test_client.get("/api/db/status")
    assert res.status_code == 200
    data = res.json()
    assert "backup_enabled" in data
    assert "storage_backend" in data
    assert "total_backups" in data
