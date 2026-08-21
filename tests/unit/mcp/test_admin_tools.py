"""Hermetic Unit Tests for FastMCP 2.0 Administrator Tools (Invariant 8 & 28)."""

import json
from pathlib import Path

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import CostProfile, settings
from credence.db import get_engine, init_db
from credence.models import Audit, Snapshot
from credence.server.mcp.server import create_mcp_server


@pytest.fixture
def temp_mcp_env(tmp_path: Path, monkeypatch):
    """Provide isolated environment for FastMCP server tests."""
    db_path = tmp_path / "mcp_test.db"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "DB_PATH", db_path)
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setattr(settings, "CREDENCE_BACKUP_DIR", backup_dir)
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "NODE_KEY_PATH", tmp_path / "node.key")
    monkeypatch.setattr(settings, "CREDENCE_PROFILE", CostProfile.OFFLINE)
    return tmp_path


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fastmcp_admin_tools_registration(temp_mcp_env: Path):
    """Verify that all admin tools are properly registered on the FastMCP server."""
    server = create_mcp_server()
    tool_names = [t.name for t in server._tool_manager.list_tools()]

    assert "credence_admin_backup_db" in tool_names
    assert "credence_admin_restore_db" in tool_names
    assert "credence_admin_export_attestations" in tool_names
    assert "credence_admin_import_attestations" in tool_names
    assert "credence_admin_trigger_boredom" in tool_names
    assert "credence_admin_backup_status" in tool_names


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fastmcp_admin_backup_and_restore_roundtrip(temp_mcp_env: Path):
    """Verify calling credence_admin_backup_db and credence_admin_restore_db via FastMCP."""
    db_path = temp_mcp_env / "mcp_test.db"
    engine = get_engine(f"sqlite+aiosqlite:///{db_path}")
    await init_db(engine)

    async with AsyncSession(engine) as session:
        snap = Snapshot(
            url="https://example.com/mcp_article",
            content_sha256="sha256:7777777777777777777777777777777777777777777777777777777777777777",
            simhash_64="0x7777777777777777",
            title="MCP Test Article",
        )
        session.add(snap)
        await session.commit()
        await session.refresh(snap)

        audit = Audit(
            snapshot_id=snap.id,
            content_sha256=snap.content_sha256,
            suspicion_score=8.0,
            classification="CLEAN",
        )
        session.add(audit)
        await session.commit()

    server = create_mcp_server()

    # Call backup tool
    backup_tool = server._tool_manager.get_tool("credence_admin_backup_db")
    assert backup_tool is not None
    backup_res_str = await backup_tool.fn(upload_cloud=False)
    backup_res = json.loads(backup_res_str)

    assert backup_res["status"] == "success"
    assert backup_res["audit_count"] == 1
    assert backup_res["file_name"] is not None

    # Call status tool
    status_tool = server._tool_manager.get_tool("credence_admin_backup_status")
    assert status_tool is not None
    status_res_str = await status_tool.fn()
    status_res = json.loads(status_res_str)

    assert status_res["backup_enabled"] is True
    assert status_res["latest_backup_available"] is True
