"""RFC 8785 Cryptographically Signed Bootstrap Seed Manifest Protocol for Credence.

Defines schemas and signing mechanisms for publishing and validating
tamper-proof peer bootstrap seed manifests (`peers.json`).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519
from pydantic import BaseModel, Field

from credence.identity import NodeIdentity, canonical_json_bytes


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SeedNodeEntry(BaseModel):
    """Vetted, high-reputation bootstrap seed peer entry."""

    node_pubkey: str = Field(..., description="Ed25519 public key hex of the seed node")
    node_alias: str = Field(default="credence-seed", description="Human-readable seed label")
    ws_url: str = Field(..., description="P2P WebSocket endpoint URL")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Evaluated composite Q_i score")
    uptime_pct: float = Field(..., ge=0.0, le=100.0, description="Observed historical uptime percentage")
    region: str = Field(default="us-central1", description="Geographic region of seed node")
    supported_catalogs: Dict[str, str] = Field(default_factory=dict, description="Map of {catalog_id: sha256_hash}")


class BootstrapSeedFile(BaseModel):
    """Canonical RFC 8785 signed bootstrap seed manifest."""

    protocol: str = Field(default="credence-mesh/1.0", description="Mesh protocol identifier")
    canonical_domain: str = Field(
        default="https://seeds.credence.nexus/peers.json",
        description="Canonical URL backing this seed file",
    )
    generated_at: datetime = Field(default_factory=utc_now, description="UTC generation timestamp")
    expires_at: datetime = Field(..., description="UTC expiration timestamp")
    seed_nodes: List[SeedNodeEntry] = Field(default_factory=list, description="Vetted top seed nodes")
    root_pubkey: Optional[str] = Field(default=None, description="Network root Ed25519 public key hex")
    root_signature: Optional[str] = Field(default=None, description="Ed25519 signature over canonical JSON")


def extract_signable_seed_payload(seed_file: BootstrapSeedFile) -> Dict[str, Any]:
    """Extract serializable dict from BootstrapSeedFile excluding root signature fields."""
    data = seed_file.model_dump(mode="json")
    data.pop("root_signature", None)
    data.pop("root_pubkey", None)
    return data


def generate_seed_file(
    nodes: List[SeedNodeEntry],
    identity: NodeIdentity,
    valid_hours: int = 24,
    canonical_domain: str = "https://seeds.credence.nexus/peers.json",
    now: Optional[datetime] = None,
) -> BootstrapSeedFile:
    """Construct and cryptographically sign a new BootstrapSeedFile manifest."""
    current_time = now or utc_now()
    expiration_time = current_time + timedelta(hours=valid_hours)

    seed_file = BootstrapSeedFile(
        protocol="credence-mesh/1.0",
        canonical_domain=canonical_domain,
        generated_at=current_time,
        expires_at=expiration_time,
        seed_nodes=nodes,
    )

    payload = extract_signable_seed_payload(seed_file)
    canonical_bytes = canonical_json_bytes(payload)

    signature_bytes = identity.private_key.sign(canonical_bytes)
    seed_file.root_pubkey = identity.public_key_hex
    seed_file.root_signature = signature_bytes.hex()

    return seed_file


def verify_seed_file(
    seed_file: BootstrapSeedFile,
    trusted_root_pubkey: Optional[str] = None,
    current_time: Optional[datetime] = None,
) -> bool:
    """Verify cryptographic signature, canonical JSON encoding, and validity period of seed manifest."""
    if not seed_file.root_pubkey or not seed_file.root_signature:
        return False

    # 1. Verify trusted root public key if specified
    if trusted_root_pubkey and seed_file.root_pubkey != trusted_root_pubkey:
        return False

    # 2. Verify timestamp expiration
    check_time = current_time or utc_now()
    if check_time > seed_file.expires_at:
        return False

    # 3. Verify cryptographic Ed25519 signature
    try:
        pubkey_bytes = bytes.fromhex(seed_file.root_pubkey)
        signature_bytes = bytes.fromhex(seed_file.root_signature)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pubkey_bytes)

        payload = extract_signable_seed_payload(seed_file)
        canonical_bytes = canonical_json_bytes(payload)

        public_key.verify(signature_bytes, canonical_bytes)
        return True
    except (ValueError, InvalidSignature):
        return False
