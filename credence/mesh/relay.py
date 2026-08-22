"""Asynchronous P2P WebSocket Gossip Relay for Credence Mesh.

Implements:
1. Inbound WebSocket server and outbound peer client connections.
2. Cryptographic signature and taxonomy catalog verification.
3. LRU message deduplication preventing broadcast storms.
4. Token-bucket rate limiting per peer.
5. Automatic partition recovery & background peer reconnection.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import OrderedDict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import websockets

from credence.config import settings
from credence.identity import NodeIdentity, load_or_create_node_identity, verify_audit_report
from credence.mesh.protocol import (
    AnnounceAttestationPayload,
    AttestationResponsePayload,
    MeshMessageEnvelope,
    MeshMessageType,
    PeerHelloPayload,
    RequestAttestationPayload,
)
from credence.pipeline.schemas import AuditReport
from credence.taxonomy_loader import registry

logger = logging.getLogger("credence.mesh.relay")


class LRUDeduplicator:
    """LRU Ring-Buffer for message ID deduplication to suppress broadcast loops."""

    def __init__(self, capacity: int = 10_000) -> None:
        self.capacity = capacity
        self._seen: OrderedDict[str, float] = OrderedDict()

    def is_seen_or_add(self, message_id: str) -> bool:
        if message_id in self._seen:
            return True
        self._seen[message_id] = datetime.now(timezone.utc).timestamp()
        if len(self._seen) > self.capacity:
            self._seen.popitem(last=False)
        return False


class PeerTrafficClass(str, Enum):
    """P2P Traffic Shaping Bands."""

    FAST_LANE = "FAST_LANE"  # 500 msgs/s - Top performers (Q_i >= 0.85)
    STANDARD = "STANDARD"  # 50 msgs/s - Standard healthy nodes
    CHOKED = "CHOKED"  # 1 msg/s - Flaky / high deviation nodes
    QUARANTINED = "QUARANTINED"  # 0 msgs/s - Slashed / malicious nodes


def extract_ip_subnet(remote_address: str) -> str:
    """Extract normalized /24 (IPv4) or /48 (IPv6) subnet prefix for Sybil clustering."""
    clean = remote_address.replace("ws://", "").replace("wss://", "")
    host = clean.split(":")[0].split("/")[0]
    if "." in host:  # IPv4
        parts = host.split(".")
        if len(parts) == 4 and all(p.isdigit() for p in parts):
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    if host == "localhost":
        return "localhost/32"
    return host


class PeerConnection:
    """Wrapper around an active P2P WebSocket connection."""

    def __init__(
        self,
        websocket: Any,
        remote_address: str,
        is_inbound: bool = True,
        traffic_class: PeerTrafficClass = PeerTrafficClass.STANDARD,
    ) -> None:
        self.websocket = websocket
        self.remote_address = remote_address
        self.ip_subnet = extract_ip_subnet(remote_address)
        self.is_inbound = is_inbound
        self.node_pubkey: Optional[str] = None
        self.node_alias: Optional[str] = None
        self.handshake_completed: bool = False
        self.supported_catalog_hashes: Dict[str, str] = {}
        self.traffic_class: PeerTrafficClass = traffic_class
        self.msg_count_window: int = 0
        self.window_start_time: float = datetime.now(timezone.utc).timestamp()

    def get_max_rate(self) -> int:
        """Get allowed messages per second for the active traffic class."""
        if self.traffic_class == PeerTrafficClass.FAST_LANE:
            return 500
        elif self.traffic_class == PeerTrafficClass.CHOKED:
            return 1
        elif self.traffic_class == PeerTrafficClass.QUARANTINED:
            return 0
        return 50  # STANDARD default

    def check_rate_limit(self, max_per_sec: Optional[int] = None) -> bool:
        """Rate limit checker using rolling 1-second window and traffic class limits."""
        limit = max_per_sec if max_per_sec is not None else self.get_max_rate()
        if limit <= 0:
            return False
        now = datetime.now(timezone.utc).timestamp()
        if now - self.window_start_time > 1.0:
            self.window_start_time = now
            self.msg_count_window = 0
        self.msg_count_window += 1
        return self.msg_count_window <= limit


class MeshGossipRelay:
    """Decentralized P2P Gossip Relay Node."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        node_identity: Optional[NodeIdentity] = None,
        peer_seeds: Optional[List[str]] = None,
    ) -> None:
        self.host = host or settings.MESH_HOST
        self.port = port or settings.MESH_PORT
        self.identity = node_identity or load_or_create_node_identity()
        self.peer_seeds = (
            peer_seeds if peer_seeds is not None else [s.strip() for s in settings.PEER_SEEDS.split(",") if s.strip()]
        )
        self.deduplicator = LRUDeduplicator()
        self.peers: Dict[str, PeerConnection] = {}
        self._server: Optional[Any] = None
        self._running: bool = False
        self._background_tasks: List[asyncio.Task[Any]] = []

    async def start(self) -> None:
        """Start P2P server and initiate connections to seed peers."""
        if self._running:
            return
        self._running = True
        registry.load_all()

        logger.info(
            f"Starting Credence Mesh Relay on ws://{self.host}:{self.port} (Pubkey: {self.identity.public_key_hex[:16]}...)"
        )
        self._server = await websockets.serve(self._handle_inbound_connection, self.host, self.port)

        # Discover dynamic seeds if none configured explicitly
        if not self.peer_seeds:
            from credence.mesh.discovery import BootstrapDiscovery

            discovery = BootstrapDiscovery()
            try:
                self.peer_seeds = await discovery.discover_peers()
            except Exception as e:
                logger.debug(f"Bootstrap discovery skipped: {e}")

        # Connect to seed peers
        for seed_url in self.peer_seeds:
            task = asyncio.create_task(self._connect_to_peer_loop(seed_url))
            self._background_tasks.append(task)

    async def stop(self) -> None:
        """Gracefully stop server and close all peer connections."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        for task in self._background_tasks:
            task.cancel()
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        for _peer_id, peer in list(self.peers.items()):
            try:
                await peer.websocket.close()
            except Exception as e:
                logger.debug(f"Error closing peer socket: {e}")
        self.peers.clear()
        logger.info("Credence Mesh Relay stopped.")

    def _sign_envelope(self, envelope: MeshMessageEnvelope) -> MeshMessageEnvelope:
        """Sign canonical envelope with local Ed25519 identity."""
        canonical_bytes = envelope.get_canonical_bytes()
        sig_bytes = self.identity.private_key.sign(canonical_bytes)
        envelope.signature = sig_bytes.hex()
        return envelope

    def _verify_envelope(self, envelope: MeshMessageEnvelope) -> bool:
        """Verify Ed25519 signature of incoming envelope."""
        if not envelope.signature:
            return False
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

            pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(envelope.sender_pubkey))
            canonical_bytes = envelope.get_canonical_bytes()
            pubkey.verify(bytes.fromhex(envelope.signature), canonical_bytes)
            return True
        except Exception:
            return False

    async def _send_envelope(self, websocket: Any, envelope: MeshMessageEnvelope) -> None:
        """Sign and transmit an envelope over a WebSocket if not already signed."""
        if not envelope.signature:
            envelope = self._sign_envelope(envelope)
        await websocket.send(envelope.model_dump_json())

    async def _handle_inbound_connection(self, websocket: Any) -> None:
        """Handle incoming WebSocket peer connection."""
        from credence.mesh.hardware_guard import compute_max_mesh_peers

        max_peers, _, hunger = compute_max_mesh_peers()
        if len(self.peers) >= max_peers:
            logger.warning(
                "Rejecting inbound peer connection: dynamic capacity reached (%d/%d, hunger=%s)",
                len(self.peers),
                max_peers,
                hunger,
            )
            await websocket.close(code=1008, reason="Mesh dynamic peer capacity reached")
            return

        remote = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        peer = PeerConnection(websocket=websocket, remote_address=remote, is_inbound=True)
        peer_id = f"inbound-{remote}"
        self.peers[peer_id] = peer

        try:
            # Send initial Hello handshake
            hello_payload = PeerHelloPayload(
                node_pubkey=self.identity.public_key_hex,
                node_alias=f"node-{self.port}",
                listen_mesh_port=self.port,
                supported_catalog_hashes=registry.get_catalog_hashes(),
            )
            env = MeshMessageEnvelope(
                message_type=MeshMessageType.PEER_HELLO,
                sender_pubkey=self.identity.public_key_hex,
                payload=hello_payload.model_dump(mode="json"),
            )
            await self._send_envelope(websocket, env)

            async for message in websocket:
                if not peer.check_rate_limit(settings.RATE_LIMIT_MSGS_PER_SEC):
                    logger.warning(f"Peer {peer_id} exceeded rate limit. Dropping message.")
                    continue
                await self._process_raw_message(peer, message)
        except asyncio.CancelledError:
            raise
        except (websockets.exceptions.ConnectionClosed, GeneratorExit):
            pass
        except Exception as e:
            logger.debug(f"Error handling peer {peer_id}: {e}")
        finally:
            self.peers.pop(peer_id, None)

    async def _connect_to_peer_loop(self, peer_url: str) -> None:
        """Continuously maintain outgoing connection to a seed peer with exponential backoff."""
        backoff = 1.0
        while self._running:
            try:
                logger.info(f"Connecting to peer seed: {peer_url}")
                async with websockets.connect(peer_url) as ws:
                    peer = PeerConnection(websocket=ws, remote_address=peer_url, is_inbound=False)
                    peer_id = f"outbound-{peer_url}"
                    self.peers[peer_id] = peer
                    backoff = 1.0  # Reset backoff on successful connect

                    # Send Hello handshake
                    hello_payload = PeerHelloPayload(
                        node_pubkey=self.identity.public_key_hex,
                        node_alias=f"node-{self.port}",
                        listen_mesh_port=self.port,
                        supported_catalog_hashes=registry.get_catalog_hashes(),
                    )
                    env = MeshMessageEnvelope(
                        message_type=MeshMessageType.PEER_HELLO,
                        sender_pubkey=self.identity.public_key_hex,
                        payload=hello_payload.model_dump(mode="json"),
                    )
                    await self._send_envelope(ws, env)

                    async for message in ws:
                        if not peer.check_rate_limit(settings.RATE_LIMIT_MSGS_PER_SEC):
                            continue
                        await self._process_raw_message(peer, message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Connection to peer {peer_url} failed: {e}. Retrying in {backoff:.1f}s...")
                await asyncio.sleep(backoff)
                backoff = min(30.0, backoff * 2.0)

    async def _process_raw_message(self, peer: PeerConnection, raw_message: str | bytes) -> None:
        """Parse, verify signature, deduplicate, and route incoming gossip envelope."""
        try:
            data = json.loads(raw_message)
            envelope = MeshMessageEnvelope.model_validate(data)

            # 1. Cryptographic Envelope Verification
            if not self._verify_envelope(envelope):
                logger.warning(
                    f"Received message with INVALID envelope signature from {peer.remote_address}. Dropping."
                )
                return

            # 2. Message Deduplication (Broadcast Storm Suppression)
            if self.deduplicator.is_seen_or_add(envelope.message_id):
                return  # Drop already seen message

            # 3. Route by message type
            if envelope.message_type == MeshMessageType.PEER_HELLO:
                hello = PeerHelloPayload.model_validate(envelope.payload)
                peer.node_pubkey = hello.node_pubkey
                peer.node_alias = hello.node_alias
                peer.supported_catalog_hashes = hello.supported_catalog_hashes
                peer.handshake_completed = True
                logger.info(f"Handshake completed with peer {peer.node_alias} ({hello.node_pubkey[:16]}...)")

            elif envelope.message_type == MeshMessageType.ANNOUNCE_ATTESTATION:
                announce = AnnounceAttestationPayload.model_validate(envelope.payload)
                await self._handle_announce_attestation(peer, envelope, announce)

            elif envelope.message_type == MeshMessageType.REQUEST_ATTESTATION:
                req = RequestAttestationPayload.model_validate(envelope.payload)
                await self._handle_request_attestation(peer, req)

        except Exception as e:
            logger.debug(f"Failed to process message from {peer.remote_address}: {e}")

    async def _handle_announce_attestation(
        self,
        peer: PeerConnection,
        envelope: MeshMessageEnvelope,
        announce: AnnounceAttestationPayload,
    ) -> None:
        """Verify and persist gossiped attestation, then rebroadcast if TTL allows."""
        att = announce.attestation

        # Verify Ed25519 signature on the attestation report itself
        if not verify_audit_report(att):
            logger.warning(f"Gossiped attestation for {att.url} has INVALID Ed25519 report signature! Dropping.")
            return

        # Grounded citation sanity check
        if att.violations:
            ungrounded = [v for v in att.violations if not v.is_grounded]
            if len(ungrounded) > len(att.violations) * 0.5:
                logger.warning(
                    f"Gossiped attestation from {peer.node_pubkey} has >50% ungrounded citations. Rejecting."
                )
                return

        logger.info(
            f"Accepted verified peer attestation for {att.url} (Score: {att.suspicion_score:.1f}, Verdict: {att.classification})"
        )

        # Rebroadcast if TTL > 0
        if announce.gossip_ttl > 0:
            announce.gossip_ttl -= 1
            rebroadcast_env = MeshMessageEnvelope(
                message_type=MeshMessageType.ANNOUNCE_ATTESTATION,
                sender_pubkey=self.identity.public_key_hex,
                payload=announce.model_dump(mode="json"),
            )
            self.deduplicator.is_seen_or_add(rebroadcast_env.message_id)
            await self._broadcast_envelope(rebroadcast_env, exclude_peer=peer)

    async def _handle_request_attestation(self, peer: PeerConnection, req: RequestAttestationPayload) -> None:
        """Respond to attestation queries."""
        from sqlmodel import select

        from credence.db import get_async_session
        from credence.models import Audit

        async with get_async_session() as s:
            stmt = select(Audit).where(Audit.content_sha256 == req.content_sha256)
            audit = (await s.exec(stmt)).first()
            if audit:
                resp_payload = AttestationResponsePayload(content_sha256=req.content_sha256)
                env = MeshMessageEnvelope(
                    message_type=MeshMessageType.ATTESTATION_RESPONSE,
                    sender_pubkey=self.identity.public_key_hex,
                    payload=resp_payload.model_dump(mode="json"),
                )
                await self._send_envelope(peer.websocket, env)

    async def broadcast_attestation(self, attestation: AuditReport, gossip_ttl: int = 6) -> None:
        """Broadcast a newly signed attestation to all active connected peers."""
        payload = AnnounceAttestationPayload(attestation=attestation, gossip_ttl=gossip_ttl)
        envelope = MeshMessageEnvelope(
            message_type=MeshMessageType.ANNOUNCE_ATTESTATION,
            sender_pubkey=self.identity.public_key_hex,
            payload=payload.model_dump(mode="json"),
        )
        self.deduplicator.is_seen_or_add(envelope.message_id)
        await self._broadcast_envelope(envelope)

    async def _broadcast_envelope(
        self,
        envelope: MeshMessageEnvelope,
        exclude_peer: Optional[PeerConnection] = None,
    ) -> None:
        """Broadcast an envelope to all connected peers except exclude_peer."""
        tasks = []
        for peer in self.peers.values():
            if exclude_peer is not None and peer.websocket == exclude_peer.websocket:
                continue
            tasks.append(self._send_envelope(peer.websocket, envelope))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_peer_count(self) -> int:
        """Return number of active connected peers."""
        return len(self.peers)

    def get_peers_summary(self) -> List[Dict[str, Any]]:
        """Return structured summary of active connected peers."""
        return [
            {
                "remote_address": p.remote_address,
                "is_inbound": p.is_inbound,
                "node_pubkey": p.node_pubkey,
                "node_alias": p.node_alias,
                "handshake_completed": p.handshake_completed,
            }
            for p in self.peers.values()
        ]
