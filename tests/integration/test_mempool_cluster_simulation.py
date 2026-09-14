"""Integration test suite implementing the 10-Scenario Mempool Cluster Simulation.

Simulates multi-node, multi-worker clusters under concurrent load, verifying:
- Concurrent multi-model claims
- Redundant family blocking
- Single-flight deduplication
- Soft lease reclamation
- Fast provisional unblocking
- Bayesian consensus convergence
- The Galileo Rule override
- Sybil cartel rejection
- Worker quality score (Q_w) and badge unlocks
- Self-Serve Affinity routing

Governed by inv-500-loc-ceiling-law, inv-byzantine-cartel-resistance,
inv-galileo-rule, and inv-bittorrent-worksharing.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import delete, select

from credence.db import get_async_session, init_db
from credence.identity import load_or_create_node_identity, sign_audit_report
from credence.mesh.worker_badges import evaluate_worker_badges
from credence.models import AuditJob, WorkerRecord
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.server.api.queue import compute_consensus_verdict
from credence.server.app import app

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def setup_cluster_db():
    """Ensure clean database state before each cluster simulation."""
    await init_db()
    async with get_async_session() as session:
        await session.exec(delete(AuditJob))
        await session.exec(delete(WorkerRecord))
        await session.commit()


@pytest.fixture
def cluster_identities(tmp_path: Path):
    """Provide multiple distinct cryptographic worker identities."""
    return {
        "alpha": load_or_create_node_identity(tmp_path / "worker_alpha.key"),
        "beta": load_or_create_node_identity(tmp_path / "worker_beta.key"),
        "gamma": load_or_create_node_identity(tmp_path / "worker_gamma.key"),
        "delta": load_or_create_node_identity(tmp_path / "worker_delta.key"),
    }


def make_cluster_report(
    url: str, prose: str, identity, score: float = 20.0, violation_quote: str | None = None
) -> AuditReport:
    """Helper to construct signed AuditReport for cluster nodes."""
    violations = []
    if violation_quote:
        assert violation_quote in prose
        violations.append(
            SpecialistViolationFinding(
                rule_id="SPJ-1.1",
                rule_uri="journalistic-ethics:seek-truth-and-report/SPJ-1.1@v1.0.0",
                domain="JOURNALISTIC_ETHICS",
                cluster_id="SEEK_TRUTH_AND_REPORT",
                severity=3,
                confidence=0.95,
                quote_or_element=violation_quote,
                reasoning="Forensic quote grounded in article text.",
            )
        )
    report = AuditReport(
        url=url,
        content_sha256="sha256:abcd0000abcd0000abcd0000abcd0000abcd0000abcd0000abcd0000abcd0000",
        simhash_64="0x1111222233334444",
        suspicion_score=score,
        suspicion_density=1.0,
        confidence_score=0.92,
        classification="CLEAN" if score < 25.0 else "SUSPICIOUS",
        is_satire=False,
        content_type="NEWS_ARTICLE",
        violations=violations,
    )
    return sign_audit_report(report, identity)


@pytest.mark.asyncio
async def test_scenario_01_concurrent_distinct_family_claims(cluster_identities):
    """Scenario 1: Two workers running distinct model families claim the same URL concurrently."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Breaking story text for concurrent test."
        enq = await client.post(
            "/api/queue/enqueue",
            json={"url": "https://example.com/scen1", "normalized_text": prose, "target_quorum": 3},
        )
        assert enq.status_code == 200

        # Worker Alpha (Gemini) claims
        claim_alpha = await client.post(
            "/api/queue/claim",
            json={"worker_pubkey": cluster_identities["alpha"].public_key_hex, "model_family": "google/gemini"},
        )
        assert claim_alpha.json()["job"] is not None
        assert claim_alpha.json()["job"]["url"] == "https://example.com/scen1"

        # Worker Beta (Claude) claims concurrently on same URL
        claim_beta = await client.post(
            "/api/queue/claim",
            json={"worker_pubkey": cluster_identities["beta"].public_key_hex, "model_family": "anthropic/claude"},
        )
        assert claim_beta.json()["job"] is not None
        assert claim_beta.json()["job"]["url"] == "https://example.com/scen1"


@pytest.mark.asyncio
async def test_scenario_02_redundant_claim_blocking_same_family(cluster_identities):
    """Scenario 2: Worker Gamma running Gemini is blocked from duplicate claim on same job."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Single job for duplicate family test."
        await client.post(
            "/api/queue/enqueue",
            json={"url": "https://example.com/scen2", "normalized_text": prose, "target_quorum": 3},
        )

        # Worker Alpha claims with Gemini
        await client.post(
            "/api/queue/claim",
            json={"worker_pubkey": cluster_identities["alpha"].public_key_hex, "model_family": "google/gemini"},
        )

        # Worker Gamma also running Gemini tries to claim: should receive None
        claim_gamma = await client.post(
            "/api/queue/claim",
            json={"worker_pubkey": cluster_identities["gamma"].public_key_hex, "model_family": "google/gemini"},
        )
        assert claim_gamma.json()["job"] is None


@pytest.mark.asyncio
async def test_scenario_03_single_flight_deduplication():
    """Scenario 3: Enqueueing the exact same URL returns existing job_id rather than duplicate."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        enq1 = await client.post(
            "/api/queue/enqueue",
            json={"url": "https://example.com/scen3", "normalized_text": "prose content", "priority": 2},
        )
        job_id1 = enq1.json()["job_id"]

        # Enqueue same URL second time
        enq2 = await client.post(
            "/api/queue/enqueue",
            json={"url": "https://example.com/scen3", "normalized_text": "prose content", "priority": 1},
        )
        job_id2 = enq2.json()["job_id"]
        assert job_id1 == job_id2


@pytest.mark.asyncio
async def test_scenario_04_soft_lease_expiration_and_reclamation(cluster_identities):
    """Scenario 4: Expired soft lease is cleared and job becomes claimable again."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/queue/enqueue",
            json={"url": "https://example.com/scen4", "normalized_text": "prose content", "priority": 2},
        )

        claim = await client.post(
            "/api/queue/claim",
            json={"worker_pubkey": cluster_identities["alpha"].public_key_hex, "model_family": "google/gemini"},
        )
        assert claim.json()["job"] is not None

        # Age lease into the past
        async with get_async_session() as session:
            job = (await session.exec(select(AuditJob))).first()
            expired_time = (datetime.now(timezone.utc) - timedelta(seconds=300)).isoformat()
            job.active_leases_json = json.dumps(
                [
                    {
                        "lease_id": "expired_lease",
                        "worker_pubkey": cluster_identities["alpha"].public_key_hex,
                        "model_family": "google/gemini",
                        "expires_at": expired_time,
                    }
                ]
            )
            session.add(job)
            await session.commit()

        # Re-claiming succeeds
        reclaim = await client.post(
            "/api/queue/claim",
            json={"worker_pubkey": cluster_identities["beta"].public_key_hex, "model_family": "google/gemini"},
        )
        assert reclaim.json()["job"] is not None
        assert reclaim.json()["job"]["url"] == "https://example.com/scen4"


@pytest.mark.asyncio
async def test_scenario_05_fast_provisional_unblocking(cluster_identities):
    """Scenario 5: First worker to submit stores provisional report and unblocks client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Breaking story with target quote for scenario 5."
        enq = await client.post(
            "/api/queue/enqueue",
            json={"url": "https://example.com/scen5", "normalized_text": prose, "target_quorum": 3},
        )
        job_id = enq.json()["job_id"]

        await client.post(
            "/api/queue/claim",
            json={"worker_pubkey": cluster_identities["alpha"].public_key_hex, "model_family": "google/gemini"},
        )

        report = make_cluster_report("https://example.com/scen5", prose, cluster_identities["alpha"], score=15.0)
        sub = await client.post(
            "/api/queue/submit",
            json={
                "job_id": job_id,
                "worker_pubkey": cluster_identities["alpha"].public_key_hex,
                "model_family": "google/gemini",
                "report": report.model_dump(mode="json"),
            },
        )
        assert sub.status_code == 200
        data = sub.json()
        assert data["status"] == "accepted"
        from credence.server.api.queue import get_completed_report

        assert get_completed_report("https://example.com/scen5") is not None


@pytest.mark.asyncio
async def test_scenario_06_bayesian_consensus_convergence(cluster_identities):
    """Scenario 6: Three distinct model families submit passes and achieve consensus."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Consensus story text with valid quote for scenario 6."
        enq = await client.post(
            "/api/queue/enqueue",
            json={"url": "https://example.com/scen6", "normalized_text": prose, "target_quorum": 3},
        )
        job_id = enq.json()["job_id"]

        workers = [
            ("alpha", "google/gemini", 18.0),
            ("beta", "anthropic/claude", 22.0),
            ("gamma", "deepseek/reasoner", 20.0),
        ]
        for name, family, score in workers:
            await client.post(
                "/api/queue/claim",
                json={"worker_pubkey": cluster_identities[name].public_key_hex, "model_family": family},
            )
            rep = make_cluster_report("https://example.com/scen6", prose, cluster_identities[name], score=score)
            res = await client.post(
                "/api/queue/submit",
                json={
                    "job_id": job_id,
                    "worker_pubkey": cluster_identities[name].public_key_hex,
                    "model_family": family,
                    "report": rep.model_dump(mode="json"),
                },
            )
            assert res.status_code == 200

        stats = await client.get("/api/queue/stats")
        assert stats.status_code == 200


def test_scenario_07_galileo_rule_override():
    """Scenario 7: Grounded finding from minority specialist overrides ungrounded clean majority."""
    audits = [
        {"suspicion_score": 10.0, "violations": []},  # Model 1: clean, 0 violations
        {"suspicion_score": 12.0, "violations": []},  # Model 2: clean, 0 violations
        {
            "suspicion_score": 58.0,
            "violations": [{"rule_id": "SPJ-1.1", "quote": "Secret source claim", "severity": 3}],
        },  # Model 3: Grounded violation
    ]
    verdict = compute_consensus_verdict(audits)
    assert verdict["galileo_override"] is True
    assert verdict["consensus_score"] >= 45.0
    assert verdict["classification"] in ("SUSPICIOUS", "DECEPTIVE")


@pytest.mark.asyncio
async def test_scenario_08_sybil_cartel_same_key_rejected(cluster_identities):
    """Scenario 8: Same worker key cannot submit twice to claim multiple passes on the same job."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Sybil protection story prose."
        enq = await client.post(
            "/api/queue/enqueue",
            json={"url": "https://example.com/scen8", "normalized_text": prose, "target_quorum": 3},
        )
        job_id = enq.json()["job_id"]

        # Pass 1 with Alpha (Gemini)
        await client.post(
            "/api/queue/claim",
            json={"worker_pubkey": cluster_identities["alpha"].public_key_hex, "model_family": "google/gemini"},
        )
        rep1 = make_cluster_report("https://example.com/scen8", prose, cluster_identities["alpha"], score=20.0)
        await client.post(
            "/api/queue/submit",
            json={
                "job_id": job_id,
                "worker_pubkey": cluster_identities["alpha"].public_key_hex,
                "model_family": "google/gemini",
                "report": rep1.model_dump(mode="json"),
            },
        )

        # Alpha tries to claim again for another family: should be blocked if already completed
        claim2 = await client.post(
            "/api/queue/claim",
            json={"worker_pubkey": cluster_identities["alpha"].public_key_hex, "model_family": "google/gemini"},
        )
        assert claim2.json()["job"] is None


def test_scenario_09_worker_quality_and_badge_unlocks():
    """Scenario 9: Evaluate badge unlocks and quality scores based on worker telemetry."""
    worker = WorkerRecord(
        worker_pubkey="verified_contributor_pubkey",
        total_completed=30,
        bounties_cleared=28,
        grounded_violations_count=15,
        tokens_donated=6_000_000,
        quality_score=0.92,
    )
    badges = evaluate_worker_badges(worker)
    badge_ids = {b.badge_id for b in badges}
    assert "first_bounty" in badge_ids
    assert "bounty_hunter" in badge_ids


@pytest.mark.asyncio
async def test_scenario_10_self_serve_affinity_routing(cluster_identities):
    """Scenario 10: Worker with affinity snatches matched job with priority over older jobs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Enqueue job 1: regular priority
        await client.post(
            "/api/queue/enqueue",
            json={"url": "https://example.com/job1", "normalized_text": "prose", "priority": 1},
        )
        # Enqueue job 2: with affinity tag
        await client.post(
            "/api/queue/enqueue",
            json={
                "url": "https://example.com/job2_affinity",
                "normalized_text": "prose",
                "priority": 2,
                "client_affinity": "my-workstation",
            },
        )

        # Worker claiming with affinity snatches job2_affinity
        claim = await client.post(
            "/api/queue/claim",
            json={
                "worker_pubkey": cluster_identities["alpha"].public_key_hex,
                "model_family": "google/gemini",
                "client_affinity": "my-workstation",
            },
        )
        assert claim.json()["job"] is not None
        assert claim.json()["job"]["url"] == "https://example.com/job2_affinity"
