"""Hermetic unit tests for Red Team and Adversarial Gamification Defenses.

Covers:
- Sybil /24 IP subnet saturation dampening
- Attestation adoption criteria
- Traffic class rate limiting & choking
"""

from __future__ import annotations

from unittest.mock import MagicMock

from credence.mesh.consensus import should_adopt_attestation
from credence.mesh.relay import (
    PeerConnection,
    PeerTrafficClass,
    extract_ip_subnet,
)
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


def test_ip_subnet_extraction() -> None:
    """Verify robust /24 subnet extraction from various WebSocket endpoints."""
    assert extract_ip_subnet("ws://192.168.1.50:8765") == "192.168.1.0/24"
    assert extract_ip_subnet("wss://10.0.5.21:8765/ws") == "10.0.5.0/24"
    assert extract_ip_subnet("ws://localhost:8765") == "localhost/32"
    assert extract_ip_subnet("wss://relay.credence.nexus:8765") == "relay.credence.nexus"


def test_traffic_class_rate_limiting() -> None:
    """Verify rate limits for FAST_LANE (500), STANDARD (50), CHOKED (1), and QUARANTINED (0)."""
    mock_ws = MagicMock()

    conn_fast = PeerConnection(mock_ws, "192.168.1.10:8765", traffic_class=PeerTrafficClass.FAST_LANE)
    assert conn_fast.get_max_rate() == 500
    assert conn_fast.check_rate_limit() is True

    conn_std = PeerConnection(mock_ws, "192.168.1.11:8765", traffic_class=PeerTrafficClass.STANDARD)
    assert conn_std.get_max_rate() == 50
    assert conn_std.check_rate_limit() is True

    conn_quarantine = PeerConnection(mock_ws, "192.168.1.12:8765", traffic_class=PeerTrafficClass.QUARANTINED)
    assert conn_quarantine.get_max_rate() == 0
    assert conn_quarantine.check_rate_limit() is False

    conn_choked = PeerConnection(mock_ws, "192.168.1.13:8765", traffic_class=PeerTrafficClass.CHOKED)
    assert conn_choked.get_max_rate() == 1
    assert conn_choked.check_rate_limit() is True
    # Second message in same 1-second window rejected
    assert conn_choked.check_rate_limit() is False


def test_consensus_adoption_gate() -> None:
    """Verify should_adopt_attestation requires valid signature, peer quality >= 0.70 and grounding >= 0.85."""
    report_valid = AuditReport(
        url="https://reuters.com/news",
        content_sha256="11" * 32,
        simhash_64="1234567890abcdef",
        suspicion_score=10.0,
        suspicion_density=0.5,
        classification="CLEAN",
        violations=[
            SpecialistViolationFinding(
                rule_id="SPJ-1.1",
                rule_uri="journalism:accuracy/SPJ-1.1@1.0.0",
                domain="JOURNALISTIC_ETHICS",
                cluster_id="accuracy",
                severity=1,
                confidence=0.9,
                quote_or_element="verbatim quote",
                reasoning="Minor check",
                is_grounded=True,
            )
        ],
        node_pubkey="aa" * 32,
        node_signature="sig" * 20,
    )

    # Valid report with high peer quality -> Adopted
    assert should_adopt_attestation(report_valid, peer_quality=0.90) is True

    # Low peer quality (< 0.70) -> Rejected
    assert should_adopt_attestation(report_valid, peer_quality=0.60) is False

    # Missing signature -> Rejected
    report_unsigned = report_valid.model_copy()
    report_unsigned.node_signature = None
    assert should_adopt_attestation(report_unsigned, peer_quality=0.90) is False

    # Low quote grounding ratio (< 0.85) -> Rejected
    report_ungrounded = report_valid.model_copy()
    report_ungrounded.violations = [
        SpecialistViolationFinding(
            rule_id="SPJ-1.1",
            rule_uri="journalism:accuracy/SPJ-1.1@1.0.0",
            domain="JOURNALISTIC_ETHICS",
            cluster_id="accuracy",
            severity=1,
            confidence=0.9,
            quote_or_element="not in text",
            reasoning="Hallucinated violation",
            is_grounded=False,
        )
    ]
    assert should_adopt_attestation(report_ungrounded, peer_quality=0.90) is False
