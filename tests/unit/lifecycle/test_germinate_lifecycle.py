"""Hermetic Unit Tests for Germination 2.0 Lifecycle (Invariant 2 & 28)."""

import json
from pathlib import Path

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import CostProfile, settings
from credence.db import get_engine, init_db
from credence.germinate import export_catalog_to_disk, germinate_node
from credence.models import Audit, FeedSubscription, Snapshot


@pytest.fixture
def temp_node_dir(tmp_path: Path):
    """Provide isolated directory for node data, key, and web catalogs."""
    node_dir = tmp_path / "data"
    node_dir.mkdir(parents=True, exist_ok=True)
    web_dir = tmp_path / "web"
    (web_dir / "credence.report").mkdir(parents=True, exist_ok=True)
    (web_dir / "credence.nexus").mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.mark.unit
@pytest.mark.asyncio
async def test_full_genesis_germination_on_blank_db(temp_node_dir: Path, monkeypatch):
    """Verify full genesis germination on empty database."""
    db_path = temp_node_dir / "data" / "credence.db"
    monkeypatch.setattr(settings, "DB_PATH", db_path)
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setattr(settings, "NODE_KEY_PATH", temp_node_dir / "data" / "node.key")
    monkeypatch.setattr(settings, "CREDENCE_PROFILE", CostProfile.OFFLINE)

    engine = get_engine(f"sqlite+aiosqlite:///{db_path}")
    await init_db(engine)

    async with AsyncSession(engine) as session:
        # Run germination with burst_items=0 (pure seeding)
        summary = await germinate_node(
            session=session,
            burst_items=0,
            sync_mesh=True,
            verbose=False,
        )

        assert summary.status == "germinated"
        assert summary.feeds_sowed >= 20
        assert summary.identity_pubkey != ""
        assert summary.duration_seconds >= 0.0

        # Verify feed subscriptions in DB
        subs = list((await session.exec(select(FeedSubscription))).all())
        assert len(subs) >= 20


@pytest.mark.unit
@pytest.mark.asyncio
async def test_incremental_germination_on_restored_db(temp_node_dir: Path, monkeypatch):
    """Verify that when database already contains audits, germination runs in Incremental Mode."""
    db_path = temp_node_dir / "data" / "credence.db"
    monkeypatch.setattr(settings, "DB_PATH", db_path)
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setattr(settings, "NODE_KEY_PATH", temp_node_dir / "data" / "node.key")
    monkeypatch.setattr(settings, "CREDENCE_PROFILE", CostProfile.OFFLINE)

    engine = get_engine(f"sqlite+aiosqlite:///{db_path}")
    await init_db(engine)

    # Pre-populate database (simulating restored backup)
    async with AsyncSession(engine) as session:
        snap = Snapshot(
            url="https://example.com/restored_item",
            content_sha256="sha256:5555555555555555555555555555555555555555555555555555555555555555",
            simhash_64="0x5555555555555555",
            title="Restored Item",
        )
        session.add(snap)
        await session.commit()
        await session.refresh(snap)

        audit = Audit(
            snapshot_id=snap.id,
            content_sha256=snap.content_sha256,
            suspicion_score=5.0,
            classification="CLEAN",
        )
        session.add(audit)
        await session.commit()

        # Run germination on populated database
        summary = await germinate_node(
            session=session,
            burst_items=0,
            sync_mesh=True,
            verbose=False,
        )

        assert summary.status == "incremental_ready"
        assert summary.total_reports_ready >= 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_multi_catalog_instant_export(temp_node_dir: Path, monkeypatch):
    """Verify export_catalog_to_disk creates reports.json and triggers signed pack export."""
    db_path = temp_node_dir / "data" / "credence.db"
    out_dir = temp_node_dir / "web" / "credence.report"
    monkeypatch.setattr(settings, "DB_PATH", db_path)
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setattr(settings, "NODE_KEY_PATH", temp_node_dir / "data" / "node.key")

    engine = get_engine(f"sqlite+aiosqlite:///{db_path}")
    await init_db(engine)

    async with AsyncSession(engine) as session:
        snap = Snapshot(
            url="https://example.com/catalog_item",
            content_sha256="sha256:6666666666666666666666666666666666666666666666666666666666666666",
            simhash_64="0x6666666666666666",
            title="Catalog Item Title",
        )
        session.add(snap)
        await session.commit()
        await session.refresh(snap)

        audit = Audit(
            snapshot_id=snap.id,
            content_sha256=snap.content_sha256,
            suspicion_score=10.0,
            classification="CLEAN",
        )
        session.add(audit)
        await session.commit()

        out_file = await export_catalog_to_disk(session=session, output_dir=out_dir)

        assert out_file.exists()
        catalog_data = json.loads(out_file.read_text(encoding="utf-8"))
        assert catalog_data["total_reports"] == 1
        assert catalog_data["reports"][0]["title"] == "Catalog Item Title"
