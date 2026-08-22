"""P2P Mesh Message Envelope & Protocol Schemas for Credence.

Defines standardized P2P message envelopes, handshake formats, and
cryptographically signed gossip packets exchanged over WebSockets.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from credence.pipeline.schemas import AuditReport


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MeshMessageType(str, Enum):
    """P2P Gossip Message Types."""

    PEER_HELLO = "PEER_HELLO"
    ANNOUNCE_ATTESTATION = "ANNOUNCE_ATTESTATION"
    REQUEST_ATTESTATION = "REQUEST_ATTESTATION"
    ATTESTATION_RESPONSE = "ATTESTATION_RESPONSE"
    HEARTBEAT = "HEARTBEAT"


class PeerHelloPayload(BaseModel):
    """Handshake payload exchanged upon WebSocket connection."""

    model_config = ConfigDict(extra="ignore")

    node_pubkey: str = Field(..., description="Sender node Ed25519 public key hex")
    node_alias: str = Field(default="credence-node", description="Human-readable node label")
    listen_mesh_port: int = Field(default=8765, description="Inbound WebSocket mesh port")
    protocol_version: str = Field(default="2.6.0", description="Mesh protocol version")
    supported_catalog_hashes: Dict[str, str] = Field(
        default_factory=dict, description="Map of {catalog_id: sha256_hash}"
    )
    recent_attestations: List[str] = Field(
        default_factory=list, description="Recent content SHA-256 hashes for partition catchup sync"
    )


class AnnounceAttestationPayload(BaseModel):
    """Gossip payload broadcasting a newly signed AuditReport."""

    model_config = ConfigDict(extra="ignore")

    attestation: AuditReport = Field(..., description="Full signed AuditReport")
    gossip_ttl: int = Field(default=3, ge=0, le=10, description="Hops remaining before gossip termination")


class RequestAttestationPayload(BaseModel):
    """Query payload requesting an attestation from peers by content SHA-256."""

    model_config = ConfigDict(extra="ignore")

    content_sha256: str = Field(..., description="Target content SHA-256")


class AttestationResponsePayload(BaseModel):
    """Response returning a requested attestation."""

    model_config = ConfigDict(extra="ignore")

    content_sha256: str = Field(..., description="Target content SHA-256")
    attestation: Optional[AuditReport] = Field(default=None, description="Signed attestation if found")


class HeartbeatPayload(BaseModel):
    """Ping/Pong liveness and health probe."""

    model_config = ConfigDict(extra="ignore")

    timestamp: datetime = Field(default_factory=utc_now)
    peer_count: int = Field(default=0)


class MeshMessageEnvelope(BaseModel):
    """Top-level cryptographically verifiable P2P message envelope.

    Governed by Invariant 6 (RFC 8785 Canonical JSON & Ed25519 Custody).
    """

    model_config = ConfigDict(extra="ignore")

    message_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique message UUID for deduplication"
    )
    message_type: MeshMessageType = Field(..., description="Protocol message type")
    sender_pubkey: str = Field(..., description="Sender node Ed25519 public key hex")
    timestamp: datetime = Field(default_factory=utc_now, description="UTC transmission timestamp")
    payload: Dict[str, Any] = Field(..., description="Inner payload dict")
    signature: Optional[str] = Field(default=None, description="Ed25519 signature over canonical envelope content")

    def get_canonical_bytes(self) -> bytes:
        """Serialize envelope payload deterministically into RFC 8785 canonical bytes.

        Returns:
            Deterministic UTF-8 bytes with ensure_ascii=False for Ed25519 signing/verification.
        """
        from credence.identity import canonical_json_bytes

        payload_data = {
            "message_id": self.message_id,
            "message_type": self.message_type.value if hasattr(self.message_type, "value") else str(self.message_type),
            "payload": self.payload,
            "sender_pubkey": self.sender_pubkey,
            "timestamp": self.timestamp.isoformat(),
        }
        return canonical_json_bytes(payload_data)
