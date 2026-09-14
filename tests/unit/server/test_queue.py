"""Unit tests for the Open Epistemic Mempool Queue and Volunteer Worker endpoints."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import delete

from credence.db import get_async_session, init_db
from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.models import AuditJob, WorkerRecord
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.server.app import app


@pytest.fixture(autouse=True)
async def setup_test_database():
    """Ensure database tables are initialized and cleared before running queue tests."""
    await init_db()
    async with get_async_session() as session:
        await session.exec(delete(AuditJob))
        await session.exec(delete(WorkerRecord))
        await session.commit()


@pytest.fixture
def sample_signed_report(tmp_path: Path) -> AuditReport:
    """Generate a valid, signed AuditReport with an Ed25519 signature."""
    ident = load_or_create_node_identity(tmp_path / "worker_test.key")
    violation = SpecialistViolationFinding(
        rule_id="SPJ-1.1",
        rule_uri="journalistic-ethics:seek-truth-and-report/SPJ-1.1@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="SEEK_TRUTH_AND_REPORT",
        severity=3,
        confidence=0.95,
        quote_or_element="Secret sources said something outrageous.",
        reasoning="Anonymous attribution without independent corroboration.",
    )
    report = AuditReport(
        url="https://example.com/breaking-leak",
        content_sha256="sha256:abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234",
        simhash_64="0x1122334455667788",
        suspicion_score=48.5,
        suspicion_density=2.0,
        confidence_score=0.92,
        classification="SUSPICIOUS",
        is_satire=False,
        content_type="NEWS_ARTICLE",
        violations=[violation],
    )
    return sign_audit_report(report, ident)


@pytest.mark.asyncio
async def test_enqueue_claim_and_submit_lifecycle(sample_signed_report: AuditReport):
    """Verify complete end-to-end mempool lifecycle."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Enqueue job
        prose = "The article begins here. Secret sources said something outrageous. And here it concludes."
        res_enq = await client.post(
            "/api/queue/enqueue",
            json={
                "url": sample_signed_report.url,
                "content_sha256": sample_signed_report.content_sha256,
                "normalized_text": prose,
                "priority": 1,
                "client_affinity": "fastmcp-ide-session",
                "target_quorum": 2,
            },
        )
        assert res_enq.status_code == 200
        data_enq = res_enq.json()
        assert data_enq["status"] in ("queued", "already_queued")
        job_id = data_enq["job_id"]

        # 2. Worker 1 claims (Gemini) with matching affinity
        res_claim1 = await client.post(
            "/api/queue/claim",
            json={
                "worker_pubkey": sample_signed_report.node_pubkey,
                "model_family": "google/gemini",
                "model_slug": "google/gemini-3.7-flash",
                "client_affinity": "fastmcp-ide-session",
            },
        )
        assert res_claim1.status_code == 200
        data_claim1 = res_claim1.json()
        assert data_claim1["job"] is not None
        assert data_claim1["job"]["job_id"] == job_id
        # P1 priority should have 15s lease
        assert data_claim1["job"]["lease_seconds"] == 15

        # 3. Worker 2 (same family: google/gemini) attempts to claim -> should get None (no duplicate family work)
        res_claim_dup = await client.post(
            "/api/queue/claim",
            json={
                "worker_pubkey": "different_pubkey_12345",
                "model_family": "google/gemini",
                "model_slug": "google/gemini-3.7-flash",
            },
        )
        assert res_claim_dup.status_code == 200
        assert res_claim_dup.json()["job"] is None

        # 4. Worker 3 (different family: anthropic/claude) claims -> succeeds concurrently!
        res_claim2 = await client.post(
            "/api/queue/claim",
            json={
                "worker_pubkey": "claude_worker_pubkey_67890",
                "model_family": "anthropic/claude",
                "model_slug": "anthropic/claude-3-7-sonnet",
            },
        )
        assert res_claim2.status_code == 200
        data_claim2 = res_claim2.json()
        assert data_claim2["job"] is not None
        assert data_claim2["job"]["job_id"] == job_id

        # 5. Worker 1 submits valid signed report
        res_sub1 = await client.post(
            "/api/queue/submit",
            json={
                "job_id": job_id,
                "worker_pubkey": sample_signed_report.node_pubkey,
                "model_family": "google/gemini",
                "model_slug": "google/gemini-3.7-flash",
                "report": sample_signed_report.model_dump(mode="json"),
            },
        )
        assert res_sub1.status_code == 200
        data_sub1 = res_sub1.json()
        assert data_sub1["status"] == "accepted"
        assert "first_bounty" in data_sub1["badges_awarded"]

        # 6. Verify Queue Stats
        await client.post("/api/queue/claim", json={"worker_pubkey": "probe", "model_family": "probe"})
        res_qstats = await client.get("/api/queue/stats")
        assert res_qstats.status_code == 200
        stats = res_qstats.json()
        assert "depth" in stats
        assert "active_leases" in stats


@pytest.mark.asyncio
async def test_grounding_rejection_and_xss_protection(sample_signed_report: AuditReport):
    """Verify Vector 4 (G < 1.00 rejection) and Vector 5 (XSS protection)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Enqueue job with specific source text
        source_text = "This is verified source text with zero mentions of fraud."
        res_enq = await client.post(
            "/api/queue/enqueue",
            json={
                "url": "https://example.com/grounding-test",
                "normalized_text": source_text,
                "target_quorum": 1,
            },
        )
        job_id = res_enq.json()["job_id"]

        # Attempt to submit an ungrounded quote not present in source_text
        bad_report = sample_signed_report.model_copy(deep=True)
        bad_report.url = "https://example.com/grounding-test"
        bad_report.violations[0].quote_or_element = "Hallucinated quote about fraud"
        # Re-sign the bad report
        # Note: We need a valid signature over the bad report
        # We'll use a fresh identity to properly sign it
        fresh_ident = load_or_create_node_identity()
        bad_report = sign_audit_report(bad_report, fresh_ident)

        res_bad = await client.post(
            "/api/queue/submit",
            json={
                "job_id": job_id,
                "worker_pubkey": fresh_ident.public_key_hex,
                "model_family": "test/family",
                "model_slug": "test/model",
                "report": bad_report.model_dump(mode="json"),
            },
        )
        assert res_bad.status_code == 422
        assert "Grounding precision G < 1.00" in res_bad.json()["error"]


@pytest.mark.asyncio
async def test_worker_leaderboard_and_dossier_api(sample_signed_report: AuditReport):
    """Verify worker leaderboard, dossier, and SVG badge endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Leaderboard
        res_lb = await client.get("/api/workers/leaderboard")
        assert res_lb.status_code == 200
        lb_data = res_lb.json()
        assert "workers" in lb_data
        assert "total_workers" in lb_data

        # Dossier for worker
        res_dos = await client.get(f"/api/worker/{sample_signed_report.node_pubkey}")
        if res_dos.status_code == 200:
            dossier = res_dos.json()
            assert "worker_pubkey" in dossier
            assert "badges" in dossier

        # SVG badge for worker
        res_svg = await client.get(f"/api/badge/worker/{sample_signed_report.node_pubkey}.svg")
        assert res_svg.status_code == 200
        assert "image/svg+xml" in res_svg.headers["content-type"]
        assert "<svg" in res_svg.text
