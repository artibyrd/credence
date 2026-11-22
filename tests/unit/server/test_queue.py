"""Unit tests for the Open Epistemic Mempool Queue and Volunteer Worker endpoints."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import delete

from credence.db import get_async_session, init_db
from credence.identity import NodeIdentity, load_or_create_node_identity, sign_audit_report
from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.snapshot import DualCaptureResult
from credence.models import Audit, AuditJob, Snapshot, Violation, WorkerRecord
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.server.app import app
from credence.worker.leases import sign_claim_proof

OPERATOR_HEADERS = {"X-Credence-Admin-Key": "dev_admin_key"}


def signed_claim_payload(
    ident: NodeIdentity,
    model_slug: str,
    model_family: str | None = None,
    client_affinity: str | None = None,
) -> dict:
    ts, sig = sign_claim_proof(ident, model_slug)
    body: dict = {
        "worker_pubkey": ident.public_key_hex,
        "model_slug": model_slug,
        "claim_timestamp": ts,
        "claim_signature": sig,
    }
    if model_family:
        body["model_family"] = model_family
    if client_affinity:
        body["client_affinity"] = client_affinity
    return body


@pytest.fixture(autouse=True)
async def setup_test_database():
    """Ensure database tables are initialized and cleared before running queue tests."""
    await init_db()
    async with get_async_session() as session:
        await session.exec(delete(Violation))
        await session.exec(delete(Audit))
        await session.exec(delete(Snapshot))
        await session.exec(delete(AuditJob))
        await session.exec(delete(WorkerRecord))
        await session.commit()


@pytest.fixture
def worker_identities(tmp_path: Path) -> dict[str, NodeIdentity]:
    return {
        "w1": load_or_create_node_identity(tmp_path / "worker_1.key"),
        "w2": load_or_create_node_identity(tmp_path / "worker_2.key"),
        "w3": load_or_create_node_identity(tmp_path / "worker_3.key"),
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_enqueue_claim_and_submit_lifecycle(worker_identities: dict[str, NodeIdentity]):
    """Verify complete end-to-end mempool lifecycle with signed claim proofs."""
    prose = "The article begins here. Secret sources said something outrageous. And here it concludes."
    sha = compute_content_sha256(prose)
    w1, w2, w3 = worker_identities["w1"], worker_identities["w2"], worker_identities["w3"]

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
    sample_signed_report = sign_audit_report(
        AuditReport(
            url="https://example.com/breaking-leak",
            content_sha256=sha,
            simhash_64=compute_simhash(prose),
            suspicion_score=48.5,
            suspicion_density=2.0,
            confidence_score=0.92,
            classification="SUSPICIOUS",
            is_satire=False,
            content_type="NEWS_ARTICLE",
            violations=[violation],
        ),
        w1,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Enqueue job as authenticated operator with pre-extracted text
        res_enq = await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={
                "url": sample_signed_report.url,
                "content_sha256": sha,
                "normalized_text": prose,
                "priority": 1,
                "client_affinity": "fastmcp-ide-session",
                "target_quorum": 2,
            },
        )
        assert res_enq.status_code == 200
        job_id = res_enq.json()["job_id"]

        # 1b. Unsigned claim proof must be rejected with HTTP 401
        res_unauth_claim = await client.post(
            "/api/queue/claim",
            json={"worker_pubkey": w1.public_key_hex, "model_slug": "google/gemini-3.7-flash"},
        )
        assert res_unauth_claim.status_code == 401

        # 2. Worker 1 claims (Gemini) with matching affinity and valid PoP signature
        res_claim1 = await client.post(
            "/api/queue/claim",
            json=signed_claim_payload(w1, "google/gemini-3.7-flash", client_affinity="fastmcp-ide-session"),
        )
        assert res_claim1.status_code == 200
        data_claim1 = res_claim1.json()
        assert data_claim1["job"] is not None
        assert data_claim1["job"]["job_id"] == job_id
        assert data_claim1["job"]["lease_seconds"] == 15

        # 3. Worker 2 (same family: google/gemini) attempts to claim -> None
        res_claim_dup = await client.post(
            "/api/queue/claim",
            json=signed_claim_payload(w2, "google/gemini-3.7-flash"),
        )
        assert res_claim_dup.status_code == 200
        assert res_claim_dup.json()["job"] is None

        # 4. Worker 3 (different family: anthropic/claude) claims -> succeeds concurrently
        res_claim2 = await client.post(
            "/api/queue/claim",
            json=signed_claim_payload(w3, "anthropic/claude-3-7-sonnet"),
        )
        assert res_claim2.status_code == 200
        assert res_claim2.json()["job"] is not None
        assert res_claim2.json()["job"]["job_id"] == job_id

        # 5. Worker 1 submits valid signed report
        res_sub1 = await client.post(
            "/api/queue/submit",
            json={
                "job_id": job_id,
                "worker_pubkey": w1.public_key_hex,
                "model_slug": "google/gemini-3.7-flash",
                "tokens_donated": 1450,
                "report": sample_signed_report.model_dump(mode="json"),
            },
        )
        assert res_sub1.status_code == 200
        data_sub1 = res_sub1.json()
        assert data_sub1["status"] == "accepted"
        assert "first_bounty" in data_sub1["badges_awarded"]
        assert "model_pioneer" in data_sub1["badges_awarded"]

        # 6. Queue stats & leaderboard validation
        res_qstats = await client.get("/api/queue/stats")
        assert res_qstats.status_code == 200
        assert "depth" in res_qstats.json()
        assert "active_leases" in res_qstats.json()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_public_enqueue_ignores_untrusted_text_and_fetches_authoritatively(
    worker_identities: dict[str, NodeIdentity],
):
    """Verify Decision 4: public http(s):// enqueue ignores caller text and uses coordinator fastpath fetch."""
    authoritative_prose = "Authoritative coordinator captured newsroom text with verified facts."
    fake_capture = DualCaptureResult(
        url="https://example.com/public-news",
        content_sha256=compute_content_sha256(authoritative_prose),
        simhash_64=compute_simhash(authoritative_prose),
        raw_html=f"<html><body><p>{authoritative_prose}</p></body></html>",
        extracted=ExtractedContent(
            url="https://example.com/public-news",
            clean_text=authoritative_prose,
            word_count=len(authoritative_prose.split()),
        ),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch(
            "credence.server.api.queue_guards.capture_webpage_fastpath",
            new_callable=AsyncMock,
            return_value=fake_capture,
        ) as mock_fetch:
            res_enq = await client.post(
                "/api/queue/enqueue",
                json={
                    "url": "https://example.com/public-news",
                    "normalized_text": "POISONED CALLER TEXT THAT MUST BE IGNORED",
                    "target_quorum": 1,
                },
            )
            assert res_enq.status_code == 200
            mock_fetch.assert_awaited_once()

        res_claim = await client.post(
            "/api/queue/claim",
            json=signed_claim_payload(worker_identities["w1"], "google/gemini-3.8-flash"),
        )
        assert res_claim.status_code == 200
        job = res_claim.json()["job"]
        assert job["normalized_text"] == authoritative_prose
        assert "POISONED" not in job["normalized_text"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_grounding_rejection_and_worker_api_guards(worker_identities: dict[str, NodeIdentity]):
    """Verify G < 1.00 rejection slashes quality and invalid params return HTTP 400."""
    w1 = worker_identities["w1"]
    source_text = "This is verified source text with zero mentions of fraud."
    sha = compute_content_sha256(source_text)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_enq = await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={
                "url": "https://example.com/grounding-test",
                "content_sha256": sha,
                "normalized_text": source_text,
                "target_quorum": 1,
            },
        )
        job_id = res_enq.json()["job_id"]

        res_claim = await client.post(
            "/api/queue/claim",
            json=signed_claim_payload(w1, "anthropic/claude-3-7-sonnet"),
        )
        assert res_claim.status_code == 200
        assert res_claim.json()["job"] is not None

        bad_report = sign_audit_report(
            AuditReport(
                url="https://example.com/grounding-test",
                content_sha256=sha,
                simhash_64=compute_simhash(source_text),
                suspicion_score=65.0,
                suspicion_density=2.0,
                confidence_score=0.92,
                classification="DECEPTIVE",
                violations=[
                    SpecialistViolationFinding(
                        rule_id="SPJ-1.1",
                        rule_uri="journalistic-ethics:seek-truth/SPJ-1.1@v1.0.0",
                        domain="JOURNALISTIC_ETHICS",
                        cluster_id="SEEK_TRUTH",
                        severity=4,
                        confidence=0.95,
                        quote_or_element="Hallucinated quote about fraud",
                        reasoning="Ungrounded fabrication.",
                    )
                ],
            ),
            w1,
        )

        res_bad = await client.post(
            "/api/queue/submit",
            json={
                "job_id": job_id,
                "worker_pubkey": w1.public_key_hex,
                "model_slug": "anthropic/claude-3-7-sonnet",
                "report": bad_report.model_dump(mode="json"),
            },
        )
        assert res_bad.status_code == 422
        assert "Grounding precision G < 1.00" in res_bad.json()["error"]

        # Non-integer leaderboard params must return 400
        res_bad_lb = await client.get("/api/workers/leaderboard?limit=notanumber")
        assert res_bad_lb.status_code == 400

        # Non-hex SVG badge pubkey must return 400
        res_bad_svg = await client.get("/api/badge/worker/not-valid-hex.svg")
        assert res_bad_svg.status_code == 400

        # Valid hex SVG badge renders cleanly
        res_svg = await client.get(f"/api/badge/worker/{w1.public_key_hex}.svg")
        assert res_svg.status_code == 200
        assert "image/svg+xml" in res_svg.headers["content-type"]
        assert "<svg" in res_svg.text
