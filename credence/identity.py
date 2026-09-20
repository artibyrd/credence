"""Ed25519 Cryptographic Identity and Signed Attestations for Credence Nodes.

Provides:
- Node keypair generation and secure on-disk persistence.
- RFC 8785 canonical JSON serialization for tamper-proof attestation signing.
- Cryptographic signature generation and verification.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from credence.config import settings
from credence.pipeline.schemas import AuditReport


@dataclass
class NodeIdentity:
    """Represents a local Credence node's cryptographic identity."""

    private_key: ed25519.Ed25519PrivateKey
    public_key: ed25519.Ed25519PublicKey
    public_key_hex: str
    key_path: Path


def _rfc8785_utf16_sort_key(s: str) -> bytes:
    """Return UTF-16BE bytes for strict RFC 8785 object member key sorting."""
    return s.encode("utf-16-be")


def _rfc8785_normalize(obj: Any) -> Any:
    """Recursively normalize data structure for deterministic RFC 8785 JSON serialization."""
    if isinstance(obj, dict):
        # Sort keys by UTF-16 code units
        sorted_keys = sorted(obj.keys(), key=_rfc8785_utf16_sort_key)
        return {k: _rfc8785_normalize(obj[k]) for k in sorted_keys}
    elif isinstance(obj, (list, tuple)):
        return [_rfc8785_normalize(item) for item in obj]
    elif isinstance(obj, float):
        if obj.is_integer():
            return int(obj)
        return obj
    return obj


def canonical_json_bytes(data: Dict[str, Any]) -> bytes:
    """Serialize dictionary into deterministic RFC 8785-compliant canonical JSON bytes."""
    normalized = _rfc8785_normalize(data)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_payload_hash(data: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of canonical JSON payload."""
    raw_bytes = canonical_json_bytes(data)
    digest = hashlib.sha256(raw_bytes).hexdigest()
    return f"sha256:{digest}"


def generate_node_keypair() -> ed25519.Ed25519PrivateKey:
    """Generate a new Ed25519 private key."""
    return ed25519.Ed25519PrivateKey.generate()


def load_or_create_node_identity(key_path: Path | str | None = None) -> NodeIdentity:
    """Load existing Ed25519 key from environment or disk, or generate and persist a new one."""
    import os

    # 1. Environment variable injection (for headless Docker, Cloud Run, or CI/CD)
    env_pem = os.environ.get("CREDENCE_NODE_KEY_PEM")
    if env_pem and env_pem.strip():
        try:
            private_key = serialization.load_pem_private_key(env_pem.encode("utf-8"), password=None)
            if not isinstance(private_key, ed25519.Ed25519PrivateKey):
                raise ValueError("Key provided via CREDENCE_NODE_KEY_PEM is not an Ed25519 private key.")
        except Exception as e:
            if isinstance(e, ValueError) and "Ed25519" in str(e):
                raise
            raise ValueError(f"Failed to load Ed25519 key from CREDENCE_NODE_KEY_PEM: {e}") from e

        public_key = private_key.public_key()
        pub_raw_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return NodeIdentity(
            private_key=private_key,
            public_key=public_key,
            public_key_hex=pub_raw_bytes.hex(),
            key_path=Path(":memory:env:CREDENCE_NODE_KEY_PEM"),
        )

    # 2. File-based persistence
    target_path = Path(key_path) if key_path else settings.NODE_KEY_PATH

    if target_path.exists():
        pem_data = target_path.read_bytes()
        try:
            private_key = serialization.load_pem_private_key(pem_data, password=None)
            if not isinstance(private_key, ed25519.Ed25519PrivateKey):
                raise ValueError(f"Key at {target_path} is not an Ed25519 key.")
        except Exception as e:
            if isinstance(e, ValueError) and "Ed25519" in str(e):
                raise
            raise ValueError(f"Corrupted or invalid key at {target_path}: {e}") from e
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        private_key = generate_node_keypair()
        pem_data = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        target_path.write_bytes(pem_data)
        # Set restrictive permissions on private key file
        try:
            target_path.chmod(0o600)
        except OSError:
            pass  # noqa: S110

    public_key = private_key.public_key()
    pub_raw_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_key_hex = pub_raw_bytes.hex()

    return NodeIdentity(
        private_key=private_key,
        public_key=public_key,
        public_key_hex=public_key_hex,
        key_path=target_path,
    )


def export_private_key_pem(identity: NodeIdentity) -> str:
    """Export the NodeIdentity private key as a PKCS8 PEM string."""
    pem_bytes = identity.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem_bytes.decode("utf-8")


def import_private_key_pem(pem_data: str | bytes, key_path: Path | None = None) -> NodeIdentity:
    """Validate and persist an Ed25519 private key from PEM format."""
    raw_bytes = pem_data.encode("utf-8") if isinstance(pem_data, str) else pem_data
    try:
        private_key = serialization.load_pem_private_key(raw_bytes, password=None)
        if not isinstance(private_key, ed25519.Ed25519PrivateKey):
            raise ValueError("Provided PEM does not contain a valid Ed25519 private key.")
    except Exception as e:
        if isinstance(e, ValueError) and "Ed25519" in str(e):
            raise
        raise ValueError(f"Corrupted or unsupported private key PEM: {e}") from e

    target_path = key_path or settings.NODE_KEY_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(raw_bytes)
    try:
        target_path.chmod(0o600)
    except OSError:
        pass

    public_key = private_key.public_key()
    pub_raw_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return NodeIdentity(
        private_key=private_key,
        public_key=public_key,
        public_key_hex=pub_raw_bytes.hex(),
        key_path=target_path,
    )


def generate_new_keypair_at_path(key_path: Path | None = None, overwrite: bool = False) -> NodeIdentity:
    """Generate a fresh Ed25519 keypair and persist it to the specified path."""
    target_path = key_path or settings.NODE_KEY_PATH
    if target_path.exists() and not overwrite:
        raise FileExistsError(f"Key file already exists at {target_path}. Use overwrite=True or --force to replace.")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    private_key = generate_node_keypair()
    pem_data = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    target_path.write_bytes(pem_data)
    try:
        target_path.chmod(0o600)
    except OSError:
        pass

    public_key = private_key.public_key()
    pub_raw_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return NodeIdentity(
        private_key=private_key,
        public_key=public_key,
        public_key_hex=pub_raw_bytes.hex(),
        key_path=target_path,
    )


def extract_signable_payload(report: AuditReport) -> Dict[str, Any]:
    """Extract dict representation of AuditReport excluding signature fields."""
    data = report.model_dump(mode="json")
    data.pop("node_signature", None)
    data.pop("node_pubkey", None)
    return data


def sign_audit_report(report: AuditReport, identity: NodeIdentity) -> AuditReport:
    """Sign an AuditReport with the node's private key, attaching public key and signature."""
    payload = extract_signable_payload(report)
    canonical_bytes = canonical_json_bytes(payload)

    signature_bytes = identity.private_key.sign(canonical_bytes)
    report.node_pubkey = identity.public_key_hex
    report.node_signature = signature_bytes.hex()

    return report


def verify_audit_signature(report: AuditReport) -> bool:
    """Verify that an AuditReport's signature matches its canonical content and public key."""
    if not report.node_pubkey or not report.node_signature:
        return False

    try:
        pubkey_bytes = bytes.fromhex(report.node_pubkey)
        signature_bytes = bytes.fromhex(report.node_signature)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pubkey_bytes)

        payload = extract_signable_payload(report)
        canonical_bytes = canonical_json_bytes(payload)

        public_key.verify(signature_bytes, canonical_bytes)
        return True
    except (ValueError, InvalidSignature):
        return False


# Alias for backward compatibility
verify_audit_report = verify_audit_signature
verify_attestation_signature = verify_audit_signature
