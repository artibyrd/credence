"""Unit tests for Ed25519 Cryptographic Node Identity and Signed Attestations."""

from pathlib import Path

import pytest

from credence.identity import (
    canonical_json_bytes,
    compute_payload_hash,
    load_or_create_node_identity,
    sign_audit_report,
    verify_audit_signature,
)
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


@pytest.fixture
def sample_audit_report() -> AuditReport:
    """Return a populated AuditReport for testing."""
    violation = SpecialistViolationFinding(
        rule_id="SPJ-1.1",
        rule_uri="journalistic-ethics:seek-truth-and-report/SPJ-1.1@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="SEEK_TRUTH_AND_REPORT",
        severity=3,
        confidence=0.95,
        quote_or_element="Studies indicate 100% agreement.",
        reasoning="Unverified empirical claim without primary citation.",
    )
    return AuditReport(
        url="https://example.org/test-report",
        content_sha256="sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
        simhash_64="0x1234567890abcdef",
        suspicion_score=26.0,
        suspicion_density=4.5,
        confidence_score=0.95,
        classification="LOW_SUSPICION",
        is_satire=False,
        content_type="NEWS_ARTICLE",
        violations=[violation],
        taxonomies_used={"spj_ethics": "sha256:7f8a1b2c3d4e5f6a"},
    )


@pytest.mark.unit
def test_node_identity_generation_and_persistence(tmp_path: Path) -> None:
    """Verify Ed25519 keypair is generated and reloaded consistently from disk."""
    key_file = tmp_path / "test_node.key"
    identity1 = load_or_create_node_identity(key_file)

    assert key_file.exists()
    assert len(identity1.public_key_hex) == 64  # 32 bytes in hex

    # Reload from existing file
    identity2 = load_or_create_node_identity(key_file)
    assert identity1.public_key_hex == identity2.public_key_hex


@pytest.mark.unit
def test_canonical_json_determinism() -> None:
    """Verify RFC 8785 canonical JSON sorting and formatting."""
    d1 = {"b": 2, "a": 1, "nested": {"z": 9, "y": 8}}
    d2 = {"nested": {"y": 8, "z": 9}, "a": 1, "b": 2}

    assert canonical_json_bytes(d1) == canonical_json_bytes(d2)
    assert compute_payload_hash(d1) == compute_payload_hash(d2)


@pytest.mark.unit
def test_sign_and_verify_audit_report(sample_audit_report: AuditReport, tmp_path: Path) -> None:
    """Verify cryptographic signing and verification of an AuditReport."""
    identity = load_or_create_node_identity(tmp_path / "node.key")

    signed_report = sign_audit_report(sample_audit_report, identity)

    assert signed_report.node_pubkey == identity.public_key_hex
    assert signed_report.node_signature is not None
    assert len(signed_report.node_signature) == 128  # 64 bytes in hex

    # Verify signature
    assert verify_audit_signature(signed_report) is True


@pytest.mark.unit
def test_tamper_detection(sample_audit_report: AuditReport, tmp_path: Path) -> None:
    """Verify modifying any field in a signed report invalidates the signature."""
    identity = load_or_create_node_identity(tmp_path / "node.key")
    signed_report = sign_audit_report(sample_audit_report, identity)

    # Valid before tampering
    assert verify_audit_signature(signed_report) is True

    # Tamper with suspicion score
    signed_report.suspicion_score = 0.0
    assert verify_audit_signature(signed_report) is False

    # Restore score and tamper with URL
    signed_report.suspicion_score = 26.0
    signed_report.url = "https://tampered.example.org"
    assert verify_audit_signature(signed_report) is False
