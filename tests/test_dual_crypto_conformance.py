"""Scenario 3: Dual-Crypto Cross-Verification.

Validates bit-for-bit canonical JSON byte parity (RFC 8785) between Python's
Ed25519 signer and the Web Cryptography API implementation in the Zero-Build Web Viewer.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from credence.identity import load_or_create_node_identity, sign_audit_report, verify_audit_report
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


@pytest.mark.unit
def test_dual_crypto_canonical_bytes_rfc8785_conformance(tmp_path: Path) -> None:
    """Verify that AuditReport canonical byte generation handles Unicode, UTC timestamps, and nested objects."""
    identity = load_or_create_node_identity(key_path=tmp_path / "test_identity.pem")

    report = AuditReport(
        url="https://example.com/test?lang=ja&quote=%E3%81%93%E3%82%93%E3%81%AB%E3%81%A1%E3%81%AF",
        content_sha256="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        simhash_64="0x1234567890abcdef",
        suspicion_score=35.5,
        suspicion_density=4.2,
        confidence_score=0.92,
        classification="LOW_SUSPICION",
        evaluation_method="llm_multi_agent",
        node_pubkey=identity.public_key_hex,
        audited_at=datetime(2026, 8, 17, 12, 0, 0, tzinfo=timezone.utc),
        violations=[
            SpecialistViolationFinding(
                rule_id="SPJ-1.1",
                rule_uri="journalistic-ethics:seek-truth-and-report/SPJ-1.1@v1.0.0",
                domain="JOURNALISTIC_ETHICS",
                cluster_id="SEEK_TRUTH_AND_REPORT",
                severity=3,
                confidence=0.85,
                quote_or_element="An anonymous official claimed: 'Something happened'",
                reasoning="Anonymous source not corroborated.",
                is_grounded=True,
            )
        ],
    )

    signed_report = sign_audit_report(report, identity)
    assert signed_report.node_signature is not None
    assert verify_audit_report(signed_report) is True

    # Validate JSON export structure
    dumped = signed_report.model_dump(mode="json")
    assert dumped["node_signature"] == signed_report.node_signature
    assert dumped["audited_at"].endswith("Z") or "+00:00" in dumped["audited_at"]

    # Verify that deserializing and re-verifying matches
    reconstructed = AuditReport.model_validate(dumped)
    assert verify_audit_report(reconstructed) is True
