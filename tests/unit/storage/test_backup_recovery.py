"""Hermetic Unit Tests for Universal Sovereign Backup & Recovery Engine (Invariant 6 & 28)."""

import json
from pathlib import Path

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import settings
from credence.db import get_engine, init_db
from credence.models import Audit, Snapshot, Violation
from credence.storage.backup import (
    BackupIntegrityError,
    create_database_backup,
    export_attestation_pack,
    import_attestation_pack,
    restore_database_backup,
    restore_latest_cloud_backup,
    verify_backup_manifest,
)


@pytest.fixture
def temp_db_dir(tmp_path: Path):
    """Provide isolated directory for temporary test databases and backups."""
    db_dir = tmp_path / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = db_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return db_dir


@pytest.mark.unit
@pytest.mark.asyncio
async def test_atomic_sqlite_backup_and_gzip_compression(temp_db_dir: Path, monkeypatch):
    """Verify atomic SQLite snapshot creation, gzip compression, and SHA-256 manifest."""
    test_db = temp_db_dir / "credence_test.db"
    backup_dir = temp_db_dir / "backups"
    monkeypatch.setattr(settings, "DB_PATH", test_db)
    monkeypatch.setattr(settings, "CREDENCE_BACKUP_DIR", backup_dir)
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite+aiosqlite:///{test_db}")

    engine = get_engine(f"sqlite+aiosqlite:///{test_db}")
    await init_db(engine)

    # Populate sample records
    async with AsyncSession(engine) as session:
        snap = Snapshot(
            url="https://example.com/article1",
            content_sha256="sha256:1111111111111111111111111111111111111111111111111111111111111111",
            simhash_64="0x123456789abcdef0",
            title="Sample Article 1",
        )
        session.add(snap)
        await session.commit()
        await session.refresh(snap)

        audit = Audit(
            snapshot_id=snap.id,
            content_sha256=snap.content_sha256,
            suspicion_score=12.5,
            classification="CLEAN",
        )
        session.add(audit)
        await session.commit()

    # Create backup
    output_backup = backup_dir / "test_backup.db.gz"
    meta = create_database_backup(
        db_path=test_db,
        output_path=output_backup,
        upload_cloud=False,
    )

    assert output_backup.exists()
    assert output_backup.stat().st_size > 0
    assert meta.audit_count == 1
    assert meta.snapshot_count == 1
    assert meta.sha256_hash != ""
    assert meta.manifest_signature is not None

    # Verify manifest JSON file
    manifest_path = output_backup.with_suffix(".manifest.json")
    assert manifest_path.exists()
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_data["sha256_hash"] == meta.sha256_hash
    assert verify_backup_manifest(meta) is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_restore_integrity_and_pragmas(temp_db_dir: Path, monkeypatch):
    """Verify restoring a .db.gz archive into a new database file restores schema and rows."""
    test_db = temp_db_dir / "credence_src.db"
    restored_db = temp_db_dir / "credence_restored.db"
    backup_dir = temp_db_dir / "backups"
    monkeypatch.setattr(settings, "DB_PATH", test_db)
    monkeypatch.setattr(settings, "CREDENCE_BACKUP_DIR", backup_dir)

    engine = get_engine(f"sqlite+aiosqlite:///{test_db}")
    await init_db(engine)

    async with AsyncSession(engine) as session:
        snap = Snapshot(
            url="https://example.com/restore_test",
            content_sha256="sha256:2222222222222222222222222222222222222222222222222222222222222222",
            simhash_64="0xabcdef0123456789",
            title="Restore Test Article",
        )
        session.add(snap)
        await session.commit()
        await session.refresh(snap)

        audit = Audit(
            snapshot_id=snap.id,
            content_sha256=snap.content_sha256,
            suspicion_score=85.0,
            classification="DECEPTIVE",
        )
        session.add(audit)
        await session.commit()

    # Create backup
    output_backup = backup_dir / "test_restore.db.gz"
    create_database_backup(db_path=test_db, output_path=output_backup, upload_cloud=False)

    # Restore into restored_db
    res = restore_database_backup(source_path=output_backup, target_db_path=restored_db)

    assert res.status == "restored"
    assert res.audit_count == 1
    assert res.snapshot_count == 1
    assert restored_db.exists()

    # Verify query on restored db
    restored_engine = get_engine(f"sqlite+aiosqlite:///{restored_db}")
    async with AsyncSession(restored_engine) as session:
        audits = list((await session.exec(select(Audit))).all())
        assert len(audits) == 1
        assert audits[0].classification == "DECEPTIVE"
        assert audits[0].suspicion_score == 85.0


@pytest.mark.unit
def test_checksum_tamper_defense(temp_db_dir: Path):
    """Verify that tampered or corrupted backup bytes raise BackupIntegrityError."""
    backup_dir = temp_db_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    corrupted_gz = backup_dir / "corrupted.db.gz"
    corrupted_manifest = backup_dir / "corrupted.manifest.json"

    # Write corrupt archive
    corrupted_gz.write_bytes(b"corrupt_gzip_stream_bytes_here")
    manifest_data = {
        "backup_id": "backup_fake",
        "file_name": "corrupted.db.gz",
        "size_bytes": 30,
        "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    }
    corrupted_manifest.write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(BackupIntegrityError):
        restore_database_backup(
            source_path=corrupted_gz,
            target_db_path=temp_db_dir / "target.db",
            verify_checksum=True,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_attestation_pack_export_and_import(temp_db_dir: Path, monkeypatch):
    """Verify exporting signed attestation packs and adopting them with 0 token spend."""
    db_a = temp_db_dir / "db_a.db"
    db_b = temp_db_dir / "db_b.db"
    monkeypatch.setattr(settings, "DATA_DIR", temp_db_dir)

    engine_a = get_engine(f"sqlite+aiosqlite:///{db_a}")
    await init_db(engine_a)

    # Seed DB A with an audit and violation
    async with AsyncSession(engine_a) as session_a:
        snap = Snapshot(
            url="https://sciencedaily.com/releases/2026/08/sample.htm",
            content_sha256="sha256:3333333333333333333333333333333333333333333333333333333333333333",
            simhash_64="0x9999999999999999",
            title="Science Daily Discovery",
        )
        session_a.add(snap)
        await session_a.commit()
        await session_a.refresh(snap)

        audit = Audit(
            snapshot_id=snap.id,
            content_sha256=snap.content_sha256,
            suspicion_score=4.0,
            classification="CLEAN",
        )
        session_a.add(audit)
        await session_a.commit()
        await session_a.refresh(audit)

        viol = Violation(
            audit_id=audit.id,
            rule_id="SPJ-1.1",
            rule_uri="https://taxonomies.credence.foundation/spj#1.1",
            domain="JOURNALISM",
            cluster_id=1,
            severity="LOW",
            confidence=0.95,
            quote_or_element="Evidence quote",
            reasoning="Minor attribution note",
        )
        session_a.add(viol)
        await session_a.commit()

        # Export pack
        pack_path = temp_db_dir / "exported_seeds.json"
        await export_attestation_pack(session=session_a, output_path=pack_path)

    assert pack_path.exists()
    pack_data = json.loads(pack_path.read_text(encoding="utf-8"))
    assert pack_data["total_attestations"] == 1
    assert pack_data["bundle_signature"] is not None

    # Import pack into clean DB B
    engine_b = get_engine(f"sqlite+aiosqlite:///{db_b}")
    await init_db(engine_b)

    async with AsyncSession(engine_b) as session_b:
        res = await import_attestation_pack(session=session_b, pack_path_or_url=pack_path)
        assert res["adopted_count"] == 1
        assert res["skipped_existing"] == 0

        # Verify adopted rows
        audits_b = list((await session_b.exec(select(Audit))).all())
        assert len(audits_b) == 1
        assert audits_b[0].content_sha256 == snap.content_sha256

        # Second import is idempotent
        res_idempotent = await import_attestation_pack(session=session_b, pack_path_or_url=pack_path)
        assert res_idempotent["adopted_count"] == 0
        assert res_idempotent["skipped_existing"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cold_boot_pre_restore_hook_lifecycle(temp_db_dir: Path, monkeypatch):
    """Verify restore_latest_cloud_backup correctly restores when target DB is empty."""
    target_db = temp_db_dir / "boot_target.db"
    backup_dir = temp_db_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "DB_PATH", target_db)
    monkeypatch.setattr(settings, "CREDENCE_BACKUP_DIR", backup_dir)
    monkeypatch.setattr(settings, "CREDENCE_BACKUP_BUCKET", None)

    # Create dummy database to back up
    seed_db = temp_db_dir / "seed.db"
    engine = get_engine(f"sqlite+aiosqlite:///{seed_db}")
    await init_db(engine)
    async with AsyncSession(engine) as session:
        snap = Snapshot(
            url="https://example.com/seed",
            content_sha256="sha256:4444444444444444444444444444444444444444444444444444444444444444",
            simhash_64="0x1111222233334444",
            title="Seed Article",
        )
        session.add(snap)
        await session.commit()

    # Create latest backup in backup_dir
    create_database_backup(db_path=seed_db, output_path=backup_dir / "credence_latest.db.gz", upload_cloud=False)

    # Run cold boot restore
    restored = await restore_latest_cloud_backup(target_db_path=target_db)
    assert restored is True
    assert target_db.exists()

    # Subsequent run skips because DB is populated
    restored_again = await restore_latest_cloud_backup(target_db_path=target_db)
    assert restored_again is False
