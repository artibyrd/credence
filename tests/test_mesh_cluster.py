"""Multi-Node Cluster Integration Tests for Credence Mesh P2P Relay.

Hermetically simulates 3-node and 7-node P2P mesh clusters,
verifying multi-hop gossip epidemics across non-trivial graph topologies,
Ed25519 signature verification, broadcast storm suppression, and
Byzantine colluding sybil attack isolation.
"""

import asyncio
from pathlib import Path

import pytest

from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.mesh.consensus import BayesianConsensusAggregator
from credence.mesh.protocol import (
    MeshMessageEnvelope,
    MeshMessageType,
)
from credence.mesh.relay import MeshGossipRelay
from credence.pipeline.schemas import AuditReport


@pytest.mark.unit
async def test_3_node_cluster_gossip_propagation(tmp_path: Path) -> None:
    """Verify that an attestation announced on Node 1 is gossiped to Node 2 and Node 3."""
    id1 = load_or_create_node_identity(tmp_path / "node1.key")
    id2 = load_or_create_node_identity(tmp_path / "node2.key")
    id3 = load_or_create_node_identity(tmp_path / "node3.key")

    relay1 = MeshGossipRelay(port=8901, node_identity=id1, peer_seeds=["ws://127.0.0.1:8902", "ws://127.0.0.1:8903"])
    relay2 = MeshGossipRelay(port=8902, node_identity=id2, peer_seeds=["ws://127.0.0.1:8901"])
    relay3 = MeshGossipRelay(port=8903, node_identity=id3, peer_seeds=["ws://127.0.0.1:8901"])

    try:
        await relay1.start()
        await relay2.start()
        await relay3.start()

        # Allow handshakes to establish
        await asyncio.sleep(0.3)

        raw_report = AuditReport(
            url="https://example.com/breaking-news",
            content_sha256="sha256:abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
            simhash_64="0x1234567890abcdef",
            suspicion_score=10.0,
            suspicion_density=0.5,
            confidence_score=0.95,
            classification="CLEAN",
        )
        signed_report = sign_audit_report(raw_report, id1)

        # Broadcast from Node 1
        await relay1.broadcast_attestation(signed_report)

        # Allow gossip propagation through mesh
        await asyncio.sleep(0.3)

        # Verify deduplicator on Node 2 and Node 3 registered the message
        assert relay2.deduplicator._seen
        assert relay3.deduplicator._seen

    finally:
        await relay1.stop()
        await relay2.stop()
        await relay3.stop()


@pytest.mark.unit
async def test_7_node_multi_hop_gossip_epidemic(tmp_path: Path) -> None:
    """Verify that an attestation travels across multiple hops (diameter > 1) in a 7-node mesh."""
    relays = []
    identities = [load_or_create_node_identity(tmp_path / f"n{i}.key") for i in range(1, 8)]

    # Topology: Ring with cross-links:
    # 1 -> 2, 2 -> 3, 3 -> 4 & 6, 4 -> 5, 5 -> 6, 6 -> 7, 7 -> 1
    peer_map = {
        1: [2, 7],
        2: [1, 3],
        3: [2, 4, 6],
        4: [3, 5],
        5: [4, 6],
        6: [3, 5, 7],
        7: [1, 6],
    }

    for i in range(1, 8):
        port = 8930 + i
        seeds = [f"ws://127.0.0.1:{8930 + peer_num}" for peer_num in peer_map[i] if peer_num > i]
        r = MeshGossipRelay(port=port, node_identity=identities[i - 1], peer_seeds=seeds)
        relays.append(r)

    try:
        for r in relays:
            await r.start()

        # Allow all 7 nodes to complete peer hello handshakes
        await asyncio.sleep(0.5)

        report = AuditReport(
            url="https://example.com/multi-hop-target",
            content_sha256="sha256:7777777777777777777777777777777777777777777777777777777777777777",
            simhash_64="0x7777777777777777",
            suspicion_score=85.0,
            suspicion_density=6.0,
            confidence_score=0.98,
            classification="DECEPTIVE",
        )
        signed_report = sign_audit_report(report, identities[0])  # Signed by Node 1

        # Broadcast from Node 1 (has no direct connection to Node 4 or 5)
        await relays[0].broadcast_attestation(signed_report)

        # Allow multi-hop gossip epidemic to converge across all 7 nodes
        await asyncio.sleep(0.8)

        # Verify that distant nodes (Node 4, Node 5, Node 7) received and processed the attestation
        assert relays[3].deduplicator._seen  # Node 4
        assert relays[4].deduplicator._seen  # Node 5
        assert relays[6].deduplicator._seen  # Node 7

    finally:
        for r in relays:
            await r.stop()


@pytest.mark.unit
def test_7_node_byzantine_colluding_sybil_isolation() -> None:
    """Verify that Bayesian consensus isolates 2 colluding rogue nodes out of 7."""
    agg = BayesianConsensusAggregator(outlier_delta_threshold=25.0)

    # 5 Honest Nodes detect phishing attack (Scores 80 to 90)
    honest_reports = [
        AuditReport(
            url="https://example.com/phish",
            content_sha256="sha256:phish_payload",
            simhash_64="0x111",
            suspicion_score=82.0 + i * 1.5,
            suspicion_density=5.0,
            confidence_score=0.95,
            classification="DECEPTIVE",
            node_pubkey=f"honest_node_{i}",
        )
        for i in range(1, 6)
    ]

    # 2 Colluding Rogue Nodes attempt a Sybil whitewash (Scores 0.0 & 5.0)
    rogue_reports = [
        AuditReport(
            url="https://example.com/phish",
            content_sha256="sha256:phish_payload",
            simhash_64="0x111",
            suspicion_score=0.0,
            suspicion_density=0.0,
            confidence_score=0.99,
            classification="CLEAN",
            node_pubkey="sybil_rogue_1",
        ),
        AuditReport(
            url="https://example.com/phish",
            content_sha256="sha256:phish_payload",
            simhash_64="0x111",
            suspicion_score=5.0,
            suspicion_density=0.2,
            confidence_score=0.99,
            classification="CLEAN",
            node_pubkey="sybil_rogue_2",
        ),
    ]

    all_reports = honest_reports + rogue_reports
    verdict = agg.calculate_consensus(all_reports)

    assert verdict is not None
    assert verdict.node_count == 7
    # Both rogue nodes should be flagged as outliers
    assert "sybil_rogue_1" in verdict.outlier_nodes
    assert "sybil_rogue_2" in verdict.outlier_nodes
    # Consensus suspicion score stays firmly in DECEPTIVE territory
    assert verdict.consensus_score >= 80.0
    assert verdict.classification == "DECEPTIVE"
    assert verdict.is_byzantine_resilient is True


@pytest.mark.unit
async def test_byzantine_signature_tampering_rejection(tmp_path: Path) -> None:
    """Verify that an envelope with a forged signature is dropped and never ingested."""
    id1 = load_or_create_node_identity(tmp_path / "node_test_1.key")
    relay = MeshGossipRelay(port=8911, node_identity=id1, peer_seeds=[])

    raw_env = MeshMessageEnvelope(
        message_type=MeshMessageType.ANNOUNCE_ATTESTATION,
        sender_pubkey=id1.public_key_hex,
        payload={"dummy": "data"},
        signature="deadbeef" * 16,  # Forged invalid signature
    )

    assert relay._verify_envelope(raw_env) is False


@pytest.mark.unit
def test_storm_suppression_deduplication() -> None:
    """Verify that re-broadcasting the same message ID is suppressed by the deduplicator."""
    relay = MeshGossipRelay(port=8921, peer_seeds=[])
    msg_id = "unique-gossip-msg-12345"

    assert relay.deduplicator.is_seen_or_add(msg_id) is False  # First time seen
    assert relay.deduplicator.is_seen_or_add(msg_id) is True  # Duplicate suppressed
