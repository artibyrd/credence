"""Red Team Suite: Epistemic & Cryptographic Attacks against Public Mesh Ingestion Gate.

Tests:
- Vector 1: Malformed / Unsigned Attestations
- Vector 2: Tampered Payload Mutation (Invalid RFC 8785 Ed25519)
- Vector 3: Forged Public Key Impersonation
- Vector 4: Script Injection in DOM Quotes (<script> / XSS)
- Vector 5: SSRF Probing (Cloud Metadata & Loopback)
- Vector 6: Legitimate Signed Egalitarian Mesh Submission & Inoculation
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from starlette.responses import JSONResponse

from credence.identity import (
    load_or_create_node_identity,
    sign_audit_report,
)
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.server.api.mesh import api_mesh_submit_attestation


class MockStarletteRequest:
    def __init__(self, data: dict):
        self._data = data

    async def json(self) -> dict:
        return self._data


def _make_valid_signed_report(url: str = "https://legit-news.org/article-1") -> AuditReport:
    identity = load_or_create_node_identity()
    report = AuditReport(
        url=url,
        content_sha256="sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
        simhash_64="0x1234567890abcdef",
        audited_at=datetime.now(timezone.utc),
        suspicion_score=12.5,
        suspicion_density=1.2,
        confidence_score=0.95,
        classification="CLEAN",
        violations=[],
        taxonomies_used={"spj_ethics": "hash_spj"},
        evaluation_method="llm_multi_agent_gemini-3.7-flash",
    )
    return sign_audit_report(report, identity)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redteam_vector1_unsigned_payload_rejected() -> None:
    """Vector 1: Attestation missing Ed25519 signature is rejected with HTTP 422."""
    report = _make_valid_signed_report()
    report_dict = report.model_dump(mode="json")
    report_dict["node_signature"] = None

    req = MockStarletteRequest(report_dict)
    resp: JSONResponse = await api_mesh_submit_attestation(req)
    assert resp.status_code == 422
    data = json.loads(bytes(resp.body).decode("utf-8"))
    assert "Cryptographic violation" in data["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redteam_vector2_tampered_payload_rejected() -> None:
    """Vector 2: Attestation with altered score after signing fails RFC 8785 Ed25519 check."""
    report = _make_valid_signed_report()
    report_dict = report.model_dump(mode="json")
    # Attacker alters score from 12.5 to 0.0 (whitewashing)
    report_dict["suspicion_score"] = 0.0

    req = MockStarletteRequest(report_dict)
    resp: JSONResponse = await api_mesh_submit_attestation(req)
    assert resp.status_code == 422
    data = json.loads(bytes(resp.body).decode("utf-8"))
    assert "signature mismatch" in data["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redteam_vector3_forged_pubkey_rejected() -> None:
    """Vector 3: Attestation signed by key A but claiming pubkey B is rejected."""
    report = _make_valid_signed_report()
    report_dict = report.model_dump(mode="json")
    # Forged foreign public key
    report_dict["node_pubkey"] = "00" * 32

    req = MockStarletteRequest(report_dict)
    resp: JSONResponse = await api_mesh_submit_attestation(req)
    assert resp.status_code == 422
    data = json.loads(bytes(resp.body).decode("utf-8"))
    assert "signature mismatch" in data["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redteam_vector4_malicious_script_quote_rejected() -> None:
    """Vector 4: Malicious XSS/script payloads inside violation quotes are rejected."""
    identity = load_or_create_node_identity()
    violation = SpecialistViolationFinding(
        rule_id="SPJ-1.1",
        rule_uri="journalistic-ethics:spj/SPJ-1.1@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="SEEK_TRUTH_AND_REPORT",
        severity=3,
        confidence=0.9,
        quote_or_element="<script>alert('xss')</script>",
        reasoning="Test attack",
        is_grounded=True,
    )
    report = AuditReport(
        url="https://example.com/clean-article",
        content_sha256="sha256:2222333344445555666677778888999900001111aaaabbbbccccddddeeeeffff",
        simhash_64="0xabcdef1234567890",
        audited_at=datetime.now(timezone.utc),
        suspicion_score=25.0,
        suspicion_density=2.0,
        confidence_score=0.9,
        classification="LOW_SUSPICION",
        violations=[violation],
        taxonomies_used={},
    )
    signed = sign_audit_report(report, identity)

    req = MockStarletteRequest(signed.model_dump(mode="json"))
    resp: JSONResponse = await api_mesh_submit_attestation(req)
    assert resp.status_code == 422
    data = json.loads(bytes(resp.body).decode("utf-8"))
    assert "malicious script tag" in data["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_redteam_vector5_ssrf_cloud_metadata_probe_rejected() -> None:
    """Vector 5: Attestation targeting GCP/AWS metadata endpoint (169.254.169.254) is blocked."""
    identity = load_or_create_node_identity()
    report = AuditReport(
        url="http://169.254.169.254/computeMetadata/v1/",
        content_sha256="sha256:3333444455556666777788889999000011112222aaaabbbbccccddddeeeeffff",
        simhash_64="0x1122334455667788",
        audited_at=datetime.now(timezone.utc),
        suspicion_score=0.0,
        suspicion_density=0.0,
        confidence_score=0.9,
        classification="CLEAN",
        violations=[],
        taxonomies_used={},
    )
    signed = sign_audit_report(report, identity)

    req = MockStarletteRequest(signed.model_dump(mode="json"))
    resp: JSONResponse = await api_mesh_submit_attestation(req)
    assert resp.status_code == 422
    data = json.loads(bytes(resp.body).decode("utf-8"))
    assert "SSRF violation" in data["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_legitimate_egalitarian_mesh_submission_accepted() -> None:
    """Valid signed attestation from ephemeral contributor is accepted with HTTP 200."""
    report = _make_valid_signed_report(url="https://civic-tribune.org/budget-hearing-2026")
    req = MockStarletteRequest(report.model_dump(mode="json"))

    resp: JSONResponse = await api_mesh_submit_attestation(req)
    assert resp.status_code == 200
    data = json.loads(bytes(resp.body).decode("utf-8"))
    assert data["status"] == "adopted"
    assert data["url"] == "https://civic-tribune.org/budget-hearing-2026"
    assert data["node_pubkey"] == report.node_pubkey
