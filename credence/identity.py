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


def canonical_json_bytes(data: Dict[str, Any]) -> bytes:
    """Serialize dictionary into deterministic RFC 8785-compliant canonical JSON bytes."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_payload_hash(data: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of canonical JSON payload."""
    raw_bytes = canonical_json_bytes(data)
    digest = hashlib.sha256(raw_bytes).hexdigest()
    return f"sha256:{digest}"


def generate_node_keypair() -> ed25519.Ed25519PrivateKey:
    """Generate a new Ed25519 private key."""
    return ed25519.Ed25519PrivateKey.generate()


def load_or_create_node_identity(key_path: Path | None = None) -> NodeIdentity:
    """Load existing Ed25519 key from disk or generate and persist a new one."""
    target_path = key_path or settings.NODE_KEY_PATH

    if target_path.exists():
        pem_data = target_path.read_bytes()
        private_key = serialization.load_pem_private_key(pem_data, password=None)
        if not isinstance(private_key, ed25519.Ed25519PrivateKey):
            raise ValueError(f"Key at {target_path} is not an Ed25519 key.")
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
