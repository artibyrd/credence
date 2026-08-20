"""Unit tests for Credence Mesh Protocol, Consensus, and P2P Relay."""

import pytest

from credence.mesh.consensus import BayesianConsensusAggregator
from credence.mesh.protocol import MeshMessageEnvelope, MeshMessageType
from credence.mesh.relay import LRUDeduplicator, MeshGossipRelay
from credence.pipeline.schemas import AuditReport


@pytest.mark.unit
def test_lru_deduplicator() -> None:
    """Verify LRU deduplicator detects duplicates and evicts oldest entries at capacity."""
    dedupe = LRUDeduplicator(capacity=3)
    assert dedupe.is_seen_or_add("msg-1") is False
    assert dedupe.is_seen_or_add("msg-1") is True  # Duplicate

    assert dedupe.is_seen_or_add("msg-2") is False
    assert dedupe.is_seen_or_add("msg-3") is False
    # Capacity 3 reached (msg-1, msg-2, msg-3)

    # Adding msg-4 should evict msg-1
    assert dedupe.is_seen_or_add("msg-4") is False
    assert dedupe.is_seen_or_add("msg-1") is False  # msg-1 was evicted, so treated as new again


@pytest.mark.unit
def test_envelope_canonical_bytes_and_signing() -> None:
    """Verify deterministic canonical byte serialization of mesh envelopes."""
    from datetime import datetime, timezone

    fixed_time = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    env1 = MeshMessageEnvelope(
        message_id="fixed-uuid",
        message_type=MeshMessageType.PEER_HELLO,
        sender_pubkey="pubkey123",
        timestamp=fixed_time,
        payload={"b": 2, "a": 1},
    )
    env2 = MeshMessageEnvelope(
        message_id="fixed-uuid",
        message_type=MeshMessageType.PEER_HELLO,
        sender_pubkey="pubkey123",
        timestamp=fixed_time,
        payload={"a": 1, "b": 2},
    )
    # Sorted key serialization ensures bytes are identical regardless of key insertion order
    assert env1.get_canonical_bytes() == env2.get_canonical_bytes()


@pytest.mark.unit
def test_bayesian_consensus_normal_aggregation() -> None:
    """Verify Bayesian consensus calculates weighted suspicion score across consistent nodes."""
    agg = BayesianConsensusAggregator()

    r1 = AuditReport(
        url="https://example.com/art",
        content_sha256="sha256:abc",
        simhash_64="0x123",
        suspicion_score=40.0,
        suspicion_density=1.5,
        confidence_score=0.9,
        classification="LOW_SUSPICION",
        node_pubkey="node_1_pubkey",
    )
    r2 = AuditReport(
        url="https://example.com/art",
        content_sha256="sha256:abc",
        simhash_64="0x123",
        suspicion_score=45.0,
        suspicion_density=1.8,
        confidence_score=0.95,
        classification="SUSPICIOUS",
        node_pubkey="node_2_pubkey",
    )

    verdict = agg.compute_consensus([r1, r2])
    assert verdict is not None
    assert verdict.node_count == 2
    assert 40.0 <= verdict.consensus_score <= 45.0
    assert len(verdict.outlier_nodes) == 0


@pytest.mark.unit
def test_bayesian_consensus_rogue_outlier_filtering() -> None:
    """Verify consensus aggregator filters out rogue outlier nodes deviating significantly from cluster."""
    agg = BayesianConsensusAggregator(outlier_delta_threshold=25.0)

    # Node 1 & Node 2 detect high deception (65 & 70)
    r1 = AuditReport(
        url="https://example.com/scam",
        content_sha256="sha256:scam_hash",
        simhash_64="0x123",
        suspicion_score=65.0,
        suspicion_density=4.0,
        confidence_score=0.95,
        classification="SUSPICIOUS",
        node_pubkey="node_1",
    )
    r2 = AuditReport(
        url="https://example.com/scam",
        content_sha256="sha256:scam_hash",
        simhash_64="0x123",
        suspicion_score=70.0,
        suspicion_density=4.5,
        confidence_score=0.95,
        classification="DECEPTIVE",
        node_pubkey="node_2",
    )
    # Rogue Node 3 tries to whitewash the scam with 0.0
    r3_rogue = AuditReport(
        url="https://example.com/scam",
        content_sha256="sha256:scam_hash",
        simhash_64="0x123",
        suspicion_score=0.0,
        suspicion_density=0.0,
        confidence_score=0.9,
        classification="CLEAN",
        node_pubkey="rogue_node_3",
    )

    verdict = agg.compute_consensus([r1, r2, r3_rogue])
    assert verdict is not None
    assert "rogue_node_3" in verdict.outlier_nodes
    # Consensus score is calculated from honest nodes (around 67.5) and not dragged down to 0
    assert verdict.consensus_score > 60.0
    assert verdict.classification in ["SUSPICIOUS", "DECEPTIVE"]


@pytest.mark.unit
async def test_mesh_relay_lifecycle(free_tcp_port: int) -> None:
    """Verify MeshGossipRelay starts WebSocket server and shuts down cleanly."""
    relay = MeshGossipRelay(port=free_tcp_port, peer_seeds=[])
    await relay.start()
    assert relay.get_peer_count() == 0
    await relay.stop()
