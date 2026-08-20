"""RFC 8785 Canonical JSON & Unicode Bytes Gauntlet.

Governed by Invariant 6: RFC 8785 Canonical JSON & Ed25519 Custody.
Verifies deterministic UTF-8 byte serialization with ensure_ascii=False for non-ASCII characters.
"""

import pytest

from credence.identity import (
    canonical_json_bytes,
    load_or_create_node_identity,
    sign_audit_report,
    verify_attestation_signature,
)
from credence.pipeline.schemas import AuditReport


@pytest.mark.unit
def test_rfc_8785_unicode_preservation_and_key_sorting() -> None:
    """RFC 8785 canonical bytes must preserve Unicode characters and sort keys lexicographically."""
    data = {
        "z_field": "São Paulo",
        "a_field": "Tokyo 東京",
        "m_field": {"nested": "München €100"},
    }
    canonical = canonical_json_bytes(data)
    # Keys must be alphabetically sorted: a_field, m_field, z_field
    expected = '{"a_field":"Tokyo 東京","m_field":{"nested":"München €100"},"z_field":"São Paulo"}'.encode("utf-8")
    assert canonical == expected


@pytest.mark.unit
def test_ed25519_attestation_signing_and_verification(tmp_path) -> None:
    """Attestation reports signed by NodeIdentity verify cleanly and detect tampering."""
    identity = load_or_create_node_identity(tmp_path / "test_node.key")

    report = AuditReport(
        url="https://example.com/unicode-test-café",
        content_sha256="sha256:1111222233334444555566667777888811112222333344445555666677778888",
        simhash_64="0x1111222233334444",
        suspicion_score=12.5,
        suspicion_density=0.8,
        confidence_score=0.98,
        classification="CLEAN",
    )

    signed = sign_audit_report(report, identity)
    assert signed.node_pubkey == identity.public_key_hex
    assert signed.node_signature is not None

    # Verification must succeed
    assert verify_attestation_signature(signed) is True

    # Tampering with suspicion_score invalidates signature
    signed.suspicion_score = 12.6
    assert verify_attestation_signature(signed) is False
