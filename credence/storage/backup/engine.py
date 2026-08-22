"""Universal Database Backup, Cold-Boot Restoration & Rotation Engine."""

from __future__ import annotations

import asyncio
import gzip
import json
import logging
import shutil
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from credence.config import settings
from credence.storage.backup.manifest import (
    BackupIntegrityError,
    BackupMetadata,
    RestoreMetadata,
    compute_file_sha256,
    sign_backup_metadata,
)
from credence.storage.backup.transports import (
    download_from_cloud_storage,
    upload_to_cloud_storage,
)

logger = logging.getLogger("credence.storage.backup.engine")


def create_database_backup(
    db_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    storage_backend: Optional[str] = None,
    upload_cloud: bool = True,
    backup_bucket: Optional[str] = None,
) -> BackupMetadata:
    """Create an atomic, compressed SQLite snapshot with SHA-256 manifest and Ed25519 signature."""
    source_db = db_path or settings.DB_PATH
    if not source_db.exists():
        raise FileNotFoundError(f"Database file not found at {source_db}")

    backup_dir = settings.CREDENCE_BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_id = f"backup_{timestamp_slug}"

    if output_path is None:
        target_gz = backup_dir / f"credence_{timestamp_slug}.db.gz"
        latest_gz = backup_dir / "credence_latest.db.gz"
    else:
        target_gz = output_path
        latest_gz = target_gz.parent / "credence_latest.db.gz"

    target_gz.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = Path(tmp_db.name)

    try:
        src_conn = sqlite3.connect(str(source_db))
        src_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

        dst_conn = sqlite3.connect(str(tmp_db_path))
        src_conn.backup(dst_conn)
        dst_conn.close()

        cur = src_conn.cursor()
        try:
            cur.execute("SELECT count(*) FROM audit;")
            audit_cnt = cur.fetchone()[0]
        except sqlite3.OperationalError:
            audit_cnt = 0

        try:
            cur.execute("SELECT count(*) FROM snapshot;")
            snap_cnt = cur.fetchone()[0]
        except sqlite3.OperationalError:
            snap_cnt = 0

        src_conn.close()
        uncompressed_size = tmp_db_path.stat().st_size

        with open(tmp_db_path, "rb") as f_in, gzip.open(target_gz, "wb", compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)

        if target_gz != latest_gz:
            shutil.copyfile(target_gz, latest_gz)

    finally:
        if tmp_db_path.exists():
            tmp_db_path.unlink()

    sha256_hash = compute_file_sha256(target_gz)
    archive_size = target_gz.stat().st_size

    active_backend = storage_backend or settings.effective_storage_backend
    bucket = backup_bucket or settings.effective_backup_bucket

    metadata = BackupMetadata(
        backup_id=backup_id,
        file_name=target_gz.name,
        size_bytes=archive_size,
        uncompressed_bytes=uncompressed_size,
        sha256_hash=sha256_hash,
        audit_count=audit_cnt,
        snapshot_count=snap_cnt,
        storage_backend=active_backend,
    )

    metadata = sign_backup_metadata(metadata)

    manifest_file = target_gz.with_suffix(".manifest.json")
    manifest_file.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    latest_manifest = latest_gz.with_suffix(".manifest.json")
    if manifest_file != latest_manifest:
        shutil.copyfile(manifest_file, latest_manifest)

    if upload_cloud and bucket:
        try:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(upload_to_cloud_storage(target_gz, manifest_file, bucket, active_backend))
            except RuntimeError:
                asyncio.run(upload_to_cloud_storage(target_gz, manifest_file, bucket, active_backend))
        except Exception as ce:
            logger.debug("Cloud backup upload scheduled or non-blocking: %s", ce)

    rotate_local_backups(backup_dir, retain_count=5)

    logger.info(
        "💾 Created atomic database backup: %s (%d bytes, sha256:%s..., %d audits)",
        target_gz.name,
        archive_size,
        sha256_hash[:12],
        audit_cnt,
    )
    return metadata


async def create_database_backup_async(
    db_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    storage_backend: Optional[str] = None,
    upload_cloud: bool = True,
    backup_bucket: Optional[str] = None,
) -> BackupMetadata:
    """Create atomic database snapshot and await cloud upload completion asynchronously."""
    source_db = db_path or settings.DB_PATH
    if not source_db.exists():
        raise FileNotFoundError(f"Database file not found at {source_db}")

    backup_dir = settings.CREDENCE_BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_id = f"backup_{timestamp_slug}"

    if output_path is None:
        target_gz = backup_dir / f"credence_{timestamp_slug}.db.gz"
        latest_gz = backup_dir / "credence_latest.db.gz"
    else:
        target_gz = output_path
        latest_gz = target_gz.parent / "credence_latest.db.gz"

    target_gz.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = Path(tmp_db.name)

    def _sync_sqlite_backup() -> tuple[int, int, int]:
        src_conn = sqlite3.connect(str(source_db))
        src_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")

        dst_conn = sqlite3.connect(str(tmp_db_path))
        src_conn.backup(dst_conn)
        dst_conn.close()

        cur = src_conn.cursor()
        try:
            cur.execute("SELECT count(*) FROM audit;")
            audit_cnt = cur.fetchone()[0]
        except sqlite3.OperationalError:
            audit_cnt = 0

        try:
            cur.execute("SELECT count(*) FROM snapshot;")
            snap_cnt = cur.fetchone()[0]
        except sqlite3.OperationalError:
            snap_cnt = 0

        src_conn.close()
        uncompressed_size = tmp_db_path.stat().st_size

        with open(tmp_db_path, "rb") as f_in, gzip.open(target_gz, "wb", compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)

        if target_gz != latest_gz:
            shutil.copyfile(target_gz, latest_gz)

        return audit_cnt, snap_cnt, uncompressed_size

    try:
        audit_cnt, snap_cnt, uncompressed_size = await asyncio.to_thread(_sync_sqlite_backup)
    finally:
        if tmp_db_path.exists():
            tmp_db_path.unlink()

    sha256_hash = compute_file_sha256(target_gz)
    archive_size = target_gz.stat().st_size

    active_backend = storage_backend or settings.effective_storage_backend
    bucket = backup_bucket or settings.effective_backup_bucket

    metadata = BackupMetadata(
        backup_id=backup_id,
        file_name=target_gz.name,
        size_bytes=archive_size,
        uncompressed_bytes=uncompressed_size,
        sha256_hash=sha256_hash,
        audit_count=audit_cnt,
        snapshot_count=snap_cnt,
        storage_backend=active_backend,
    )

    metadata = sign_backup_metadata(metadata)

    manifest_file = target_gz.with_suffix(".manifest.json")
    manifest_file.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    latest_manifest = latest_gz.with_suffix(".manifest.json")
    if manifest_file != latest_manifest:
        shutil.copyfile(manifest_file, latest_manifest)

    if upload_cloud and bucket:
        try:
            await upload_to_cloud_storage(target_gz, manifest_file, bucket, active_backend)
        except Exception as ce:
            logger.debug("Cloud backup upload exception: %s", ce)

    rotate_local_backups(backup_dir, retain_count=5)

    logger.info(
        "💾 Created atomic database backup: %s (%d bytes, sha256:%s..., %d audits)",
        target_gz.name,
        archive_size,
        sha256_hash[:12],
        audit_cnt,
    )
    return metadata


def rotate_local_backups(backup_dir: Path, retain_count: int = 5) -> None:
    """Retain the N most recent database backups, pruning older files."""
    backups = sorted(
        [f for f in backup_dir.glob("credence_*.db.gz") if f.name != "credence_latest.db.gz"],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    for old_backup in backups[retain_count:]:
        try:
            old_backup.unlink()
            manifest = old_backup.with_suffix(".manifest.json")
            if manifest.exists():
                manifest.unlink()
            logger.debug("Pruned older backup: %s", old_backup.name)
        except Exception as e:
            logger.debug("Failed to prune old backup %s: %s", old_backup, e)


def restore_database_backup(
    source_path: Path,
    target_db_path: Optional[Path] = None,
    verify_checksum: bool = True,
    force: bool = False,
) -> RestoreMetadata:
    """Restore SQLite database from a compressed .db.gz archive with integrity verification."""
    t_start = time.perf_counter()

    if not source_path.exists():
        raise FileNotFoundError(f"Backup archive not found at {source_path}")

    target_db = target_db_path or settings.DB_PATH

    manifest_file = source_path.with_suffix(".manifest.json")
    if verify_checksum:
        actual_sha = compute_file_sha256(source_path)
        if manifest_file.exists():
            try:
                manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
                expected_sha = manifest_data.get("sha256_hash", "")
                if expected_sha and actual_sha != expected_sha:
                    raise BackupIntegrityError(
                        f"SHA-256 checksum mismatch! Expected: {expected_sha}, Got: {actual_sha}"
                    )
            except json.JSONDecodeError as je:
                logger.warning("Corrupt manifest file: %s; verifying raw gzip stream only", je)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_dst:
        tmp_dst_path = Path(tmp_dst.name)

    try:
        try:
            with gzip.open(source_path, "rb") as f_in, open(tmp_dst_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        except Exception as ge:
            raise BackupIntegrityError(f"Corrupt gzip backup archive: {ge}") from ge

        test_conn = sqlite3.connect(str(tmp_dst_path))
        cur = test_conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        check_result = cur.fetchone()[0]
        if check_result != "ok":
            test_conn.close()
            raise BackupIntegrityError(f"SQLite PRAGMA integrity_check failed: {check_result}")

        try:
            cur.execute("SELECT count(*) FROM audit;")
            audit_cnt = cur.fetchone()[0]
        except sqlite3.OperationalError:
            audit_cnt = 0

        try:
            cur.execute("SELECT count(*) FROM snapshot;")
            snap_cnt = cur.fetchone()[0]
        except sqlite3.OperationalError:
            snap_cnt = 0

        test_conn.close()

        target_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp_dst_path), str(target_db))

        conn = sqlite3.connect(str(target_db))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.close()

    finally:
        if tmp_dst_path.exists():
            tmp_dst_path.unlink()

    duration = (time.perf_counter() - t_start) * 1000.0

    logger.info(
        "🔄 Database restored successfully from %s in %.1fms (Audits: %d, Snapshots: %d)",
        source_path.name,
        duration,
        audit_cnt,
        snap_cnt,
    )

    return RestoreMetadata(
        status="restored",
        source_file=str(source_path),
        target_database=str(target_db),
        audit_count=audit_cnt,
        snapshot_count=snap_cnt,
        sha256_verified=verify_checksum,
        duration_ms=round(duration, 2),
    )


async def restore_latest_cloud_backup(
    target_db_path: Optional[Path] = None,
    bucket_name: Optional[str] = None,
    storage_backend: Optional[str] = None,
) -> bool:
    """Cold-boot pre-boot hook called before init_db()."""
    target_db = target_db_path or settings.DB_PATH
    bucket = bucket_name or settings.effective_backup_bucket
    backend = storage_backend or settings.effective_storage_backend

    # If database file exists, verify whether it has accumulated audit data beyond basic genesis
    if target_db.exists() and target_db.stat().st_size > 16384:
        try:
            conn = sqlite3.connect(str(target_db))
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM audit;")
            cnt = cur.fetchone()[0]
            conn.close()
            if cnt > 10:
                logger.debug(
                    "Target database already exists with valid data (%d audits, %d bytes); skipping cloud restore",
                    cnt,
                    target_db.stat().st_size,
                )
                return False
        except Exception:
            pass

    backup_dir = settings.CREDENCE_BACKUP_DIR
    local_latest = backup_dir / "credence_latest.db.gz"

    if bucket:
        temp_download = backup_dir / "cloud_latest_download.db.gz"
        success = await download_from_cloud_storage(
            bucket_name=bucket,
            remote_filename="credence_latest.db.gz",
            target_local_path=temp_download,
            storage_backend=backend,
        )
        if success and temp_download.exists():
            try:
                restore_database_backup(temp_download, target_db_path=target_db, verify_checksum=False)
                temp_download.unlink()
                logger.info("🚀 Cold-boot cloud restore successful from %s", bucket)
                return True
            except Exception as e:
                logger.warning("Failed to restore downloaded cloud backup: %s", e)

    if local_latest.exists():
        try:
            restore_database_backup(local_latest, target_db_path=target_db, verify_checksum=False)
            logger.info("🚀 Cold-boot restore successful from local archive: %s", local_latest)
            return True
        except Exception as e:
            logger.warning("Failed to restore local backup archive: %s", e)

    return False


def get_backup_status() -> Dict[str, Any]:
    """Retrieve current backup inventory, latest snapshot metadata, and storage backend status."""
    backup_dir = settings.CREDENCE_BACKUP_DIR
    latest_gz = backup_dir / "credence_latest.db.gz"
    manifest_file = latest_gz.with_suffix(".manifest.json")

    has_latest = latest_gz.exists()
    manifest_data: Dict[str, Any] = {}

    if manifest_file.exists():
        try:
            manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception:
            manifest_data = {}

    all_backups = list(backup_dir.glob("credence_*.db.gz")) if backup_dir.exists() else []

    return {
        "backup_enabled": settings.CREDENCE_BACKUP_ENABLED,
        "storage_backend": settings.effective_storage_backend,
        "cloud_bucket": settings.effective_backup_bucket,
        "local_backup_dir": str(backup_dir),
        "total_backups": len(all_backups),
        "latest_backup_available": has_latest,
        "latest_backup_size_bytes": latest_gz.stat().st_size if has_latest else 0,
        "latest_backup_mtime": datetime.fromtimestamp(latest_gz.stat().st_mtime, timezone.utc).isoformat()
        if has_latest
        else None,
        "manifest": manifest_data,
    }
