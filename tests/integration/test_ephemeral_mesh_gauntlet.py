"""Integration Gauntlet: Ephemeral Contributor -> Signed Attestation -> Remote Inoculation.

Verifies:
1. Local node generates valid signed AuditReport via offline heuristics or LLM.
2. Contributor sends signed report over public REST gateway (POST /api/mesh/submit-attestation).
3. Receiving node verifies RFC 8785 Ed25519 signature and adopts report into SQLite without token spend.
4. Subsequent model comparison queries reflect the contributed audit pass.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from starlette.testclient import TestClient

from credence.db import get_async_session, init_db
from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.pipeline.schemas import AuditReport
from credence.server.app import create_server_app
from credence.storage.revisions import get_model_comparison_matrix


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ephemeral_contributor_submission_gauntlet() -> None:
    """Execute complete end-to-end contributor workflow."""
    await init_db()

    test_url = "https://local-herald.com/blotters/unique-case-98765"
    identity = load_or_create_node_identity()
    local_report = AuditReport(
        url=test_url,
        content_sha256="sha256:9999888877776666555544443333222211110000aaaabbbbccccddddeeeeffff",
        simhash_64="0x9876543210fedcba",
        audited_at=datetime.now(timezone.utc),
        suspicion_score=20.0,
        suspicion_density=1.5,
        confidence_score=0.25,
        classification="LOW_SUSPICION",
        violations=[],
        taxonomies_used={},
        evaluation_method="offline_structural_heuristic@v1.1.0",
        quota_preserved=True,
    )
    local_report = sign_audit_report(local_report, identity)
    assert local_report.node_pubkey is not None
    assert local_report.node_signature is not None

    # Step 2: Submit to Starlette Server via public mesh gateway
    app = create_server_app(enable_sifter=False, enable_boredom=False)
    client = TestClient(app)

    payload = local_report.model_dump(mode="json")
    resp = client.post("/api/mesh/submit-attestation", json=payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "adopted"
    assert res_data["url"] == test_url

    # Step 3: Verify inoculation in local DB and check comparison matrix
    async with get_async_session() as session:
        matrix = await get_model_comparison_matrix(session, test_url)
        assert len(matrix.passes) >= 1
        assert matrix.passes[0].content_sha256 == local_report.content_sha256
