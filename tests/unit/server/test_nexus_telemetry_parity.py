"""Hermetic Unit Tests for Host Node & Nexus Workstation Telemetry Schema Parity."""

import asyncio

import pytest
from starlette.testclient import TestClient

from credence.config import CostProfile, settings
from credence.db import get_engine, init_db
from credence.server.app import create_server_app


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """Instantiate lightweight test client for schema contract validation."""
    db_path = tmp_path / "telemetry_test.db"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "DB_PATH", db_path)
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setattr(settings, "CREDENCE_BACKUP_DIR", backup_dir)
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "CREDENCE_PROFILE", CostProfile.OFFLINE)

    engine = get_engine(f"sqlite+aiosqlite:///{db_path}")
    asyncio.run(init_db(engine))

    app = create_server_app()
    return TestClient(app)


@pytest.mark.unit
def test_mesh_stats_schema_parity(api_client: TestClient):
    """Verify /api/mesh/stats provides all properties required by the Nexus Workstation."""
    res = api_client.get("/api/mesh/stats")
    assert res.status_code == 200
    data = res.json()

    # Core high-level keys
    assert "my_node" in data
    assert "sre_telemetry" in data
    assert "mesh_dynamics" in data
    assert "categories_breakdown" in data
    assert "recent_audits" in data

    # Telemetry sub-keys
    my_node = data["my_node"]
    assert "node_pubkey" in my_node
    assert "active_profile" in my_node
    assert "memory_rss_mb" in my_node or "memory_mb" in my_node


@pytest.mark.unit
def test_boredom_status_schema_parity(api_client: TestClient):
    """Verify /api/boredom/status provides all properties required by the Boredom gauge."""
    res = api_client.get("/api/boredom/status")
    assert res.status_code == 200
    data = res.json()

    assert "boredom_trigger_eligible" in data
    assert "status" in data
    assert "token_headroom" in data

    headroom = data["token_headroom"]
    assert "hourly_pct" in headroom
    assert "daily_pct" in headroom
    assert "daily_spend_usd" in headroom


@pytest.mark.unit
def test_node_stats_schema_parity(api_client: TestClient):
    """Verify /api/node/stats provides comprehensive performance, processing, and storage metrics."""
    res = api_client.get("/api/node/stats")
    assert res.status_code == 200
    data = res.json()

    assert "status" in data
    assert "uptime_seconds" in data
    assert "memory_mb" in data
    assert "latencies_ms" in data
    assert "article_processing" in data
    assert "storage_gravity" in data
    assert "boredom_engine" in data
    assert "work_sharing_savings" in data

    processing = data["article_processing"]
    assert "total_audits" in processing
    assert "total_snapshots" in processing
    assert "audits_today" in processing
    assert "avg_suspicion_score" in processing
    assert "grounding_quotient" in processing
    assert "avg_eval_duration_ms" in processing
    assert "evaluations_per_minute" in processing

    storage = data["storage_gravity"]
    assert "database_path" in storage
    assert "database_size_bytes" in storage
    assert "database_size_mb" in storage
    assert "storage_engine" in storage
    assert "retained_backups_count" in storage

