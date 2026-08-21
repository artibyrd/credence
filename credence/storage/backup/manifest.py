"""Cryptographic Manifests, Serialization & Integrity Signatures for Sovereign Backups."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from credence.identity import canonical_json_bytes, load_or_create_node_identity

logger = logging.getLogger("credence.storage.backup.manifest")


class BackupIntegrityError(Exception):
    """Raised when a backup archive fails SHA-256 manifest verification or is corrupted."""


class BackupMetadata(BaseModel):
    """Metadata manifest describing an atomic database backup archive."""

    backup_id: str = Field(..., description="Unique backup identifier / timestamp slug")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC creation timestamp",
    )
    file_name: str = Field(..., description="Backup filename (e.g. credence_latest.db.gz)")
    size_bytes: int = Field(..., description="Compressed archive size in bytes")
    uncompressed_bytes: int = Field(default=0, description="Raw database size in bytes")
    sha256_hash: str = Field(..., description="SHA-256 hex digest of compressed archive")
    database_type: str = Field(default="sqlite", description="Database engine type (sqlite, postgresql)")
    audit_count: int = Field(default=0, description="Total audits captured in backup")
    snapshot_count: int = Field(default=0, description="Total snapshots captured in backup")
    node_pubkey: Optional[str] = Field(default=None, description="Node Ed25519 public key hex")
    manifest_signature: Optional[str] = Field(default=None, description="Ed25519 signature over canonical metadata")
    storage_backend: str = Field(default="local", description="Active storage backend (local, gcs, s3)")
    cloud_uri: Optional[str] = Field(default=None, description="Canonical cloud storage URI if uploaded")


class RestoreMetadata(BaseModel):
    """Telemetry report describing a completed database restoration operation."""

    status: str = Field(default="restored", description="Restoration status")
    restored_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC restore timestamp",
    )
    source_file: str = Field(..., description="Source backup archive path or URI")
    target_database: str = Field(..., description="Target database file path")
    audit_count: int = Field(default=0, description="Total audits active after restoration")
    snapshot_count: int = Field(default=0, description="Total snapshots active after restoration")
    sha256_verified: bool = Field(default=True, description="Whether SHA-256 checksum matched manifest")
    duration_ms: float = Field(default=0.0, description="Restoration duration in milliseconds")


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file on disk."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def sign_backup_metadata(metadata: BackupMetadata) -> BackupMetadata:
    """Sign BackupMetadata dictionary with node's Ed25519 private key."""
    identity = load_or_create_node_identity()
    data = metadata.model_dump(mode="json")
    data.pop("manifest_signature", None)
    data.pop("node_pubkey", None)
    canon_bytes = canonical_json_bytes(data)
    sig = identity.private_key.sign(canon_bytes)
    metadata.node_pubkey = identity.public_key_hex
    metadata.manifest_signature = sig.hex()
    return metadata


def verify_backup_manifest(metadata: BackupMetadata) -> bool:
    """Verify Ed25519 signature over BackupMetadata if signature fields are present."""
    if not metadata.node_pubkey or not metadata.manifest_signature:
        return True
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(metadata.node_pubkey))
        data = metadata.model_dump(mode="json")
        data.pop("manifest_signature", None)
        data.pop("node_pubkey", None)
        canon_bytes = canonical_json_bytes(data)
        pubkey.verify(bytes.fromhex(metadata.manifest_signature), canon_bytes)
        return True
    except Exception as e:
        logger.warning("Manifest signature verification failed: %s", e)
        return False
