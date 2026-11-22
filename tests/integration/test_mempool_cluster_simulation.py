"""Integration test suite implementing the 11-Scenario Mempool Cluster Simulation.

Simulates multi-node, multi-worker clusters under true concurrent asyncio load, verifying:
1. Concurrent asyncio.gather race across 10 workers (atomic lease lock)
2. Redundant family blocking
3. Single-flight deduplication
4. Soft lease reclamation
5. Fast provisional unblocking
6. Bayesian consensus convergence
7. The Galileo Rule override
8. Sybil cartel rejection (same key under DIFFERENT model family)
9. Worker quality score (Q_w) and badge unlocks
10. Self-Serve Affinity routing
11. Multi-model audits surviving init_db() schema startup migrations
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import delete, select

from credence.db import get_async_session, init_db
from credence.identity import NodeIdentity, load_or_create_node_identity, sign_audit_report
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.mesh.worker_badges import evaluate_worker_badges
from credence.models import Audit, AuditJob, Snapshot, Violation, WorkerRecord
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.server.api.queue import compute_consensus_verdict, get_completed_report
from credence.server.app import app
from credence.worker.leases import sign_claim_proof

pytestmark = pytest.mark.integration

OPERATOR_HEADERS = {"X-Credence-Admin-Key": "dev_admin_key"}


def _claim_body(ident: NodeIdentity, model_slug: str, client_affinity: str | None = None) -> dict:
    ts, sig = sign_claim_proof(ident, model_slug)
    body: dict = {
        "worker_pubkey": ident.public_key_hex,
        "model_slug": model_slug,
        "claim_timestamp": ts,
        "claim_signature": sig,
    }
    if client_affinity:
        body["client_affinity"] = client_affinity
    return body


@pytest.fixture(autouse=True)
async def setup_cluster_db():
    """Ensure clean database state before each cluster simulation."""
    await init_db()
    async with get_async_session() as session:
        await session.exec(delete(Violation))
        await session.exec(delete(Audit))
        await session.exec(delete(Snapshot))
        await session.exec(delete(AuditJob))
        await session.exec(delete(WorkerRecord))
        await session.commit()


@pytest.fixture
def cluster_identities(tmp_path: Path) -> dict[str, NodeIdentity]:
    return {
        name: load_or_create_node_identity(tmp_path / f"worker_{name}.key")
        for name in ("alpha", "beta", "gamma", "delta", "eps", "zeta", "eta", "theta", "iota", "kappa")
    }


def make_cluster_report(
    url: str,
    prose: str,
    identity: NodeIdentity,
    score: float = 20.0,
    violation_quote: str | None = None,
) -> AuditReport:
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
        content_sha256=compute_content_sha256(prose),
        simhash_64=compute_simhash(prose),
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
async def test_scenario_01_concurrent_gather_atomic_claims(cluster_identities: dict[str, NodeIdentity]):
    """Scenario 1: Race 10 concurrent claims (5 Gemini + 5 Claude) against 1 job; assert exactly 1 winner per family."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Breaking story text for concurrent asyncio.gather race test."
        enq = await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={"url": "https://example.com/scen1", "normalized_text": prose, "target_quorum": 3},
        )
        assert enq.status_code == 200

        names = list(cluster_identities.keys())
        gemini_tasks = [
            client.post("/api/queue/claim", json=_claim_body(cluster_identities[n], "google/gemini-3.8-flash"))
            for n in names[:5]
        ]
        claude_tasks = [
            client.post("/api/queue/claim", json=_claim_body(cluster_identities[n], "anthropic/claude-3-7-sonnet"))
            for n in names[5:]
        ]
        results = await asyncio.gather(*(gemini_tasks + claude_tasks))

        gemini_winners = [r.json()["job"] for r in results[:5] if r.json().get("job") is not None]
        claude_winners = [r.json()["job"] for r in results[5:] if r.json().get("job") is not None]

        assert len(gemini_winners) == 1, f"Expected exactly 1 Gemini winner, got {len(gemini_winners)}"
        assert len(claude_winners) == 1, f"Expected exactly 1 Claude winner, got {len(claude_winners)}"


@pytest.mark.asyncio
async def test_scenario_02_redundant_family_blocked(cluster_identities: dict[str, NodeIdentity]):
    """Scenario 2: Second worker from an already-claimed model family receives None."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Story prose for redundant family check."
        await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={"url": "https://example.com/scen2", "normalized_text": prose, "target_quorum": 3},
        )
        c1 = await client.post(
            "/api/queue/claim", json=_claim_body(cluster_identities["alpha"], "google/gemini-3.8-flash")
        )
        assert c1.json()["job"] is not None

        c2 = await client.post(
            "/api/queue/claim", json=_claim_body(cluster_identities["beta"], "google/gemini-2.5-pro")
        )
        assert c2.json()["job"] is None


@pytest.mark.asyncio
async def test_scenario_03_single_flight_deduplication():
    """Scenario 3: Re-enqueuing an active URL returns already_queued without creating a duplicate job."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={"url": "https://example.com/scen3", "normalized_text": "Dedup prose.", "target_quorum": 2},
        )
        r2 = await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={"url": "https://example.com/scen3", "normalized_text": "Dedup prose.", "target_quorum": 2},
        )
        assert r1.json()["status"] == "queued"
        assert r2.json()["status"] == "already_queued"
        assert r1.json()["job_id"] == r2.json()["job_id"]


@pytest.mark.asyncio
async def test_scenario_04_soft_lease_reclamation(cluster_identities: dict[str, NodeIdentity]):
    """Scenario 4: Expired active lease is automatically reclaimed for another worker."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={"url": "https://example.com/scen4", "normalized_text": "Lease reclamation prose."},
        )
        await client.post("/api/queue/claim", json=_claim_body(cluster_identities["alpha"], "google/gemini-3.8-flash"))

        async with get_async_session() as session:
            job = (await session.exec(select(AuditJob))).first()
            assert job is not None
            expired_time = (datetime.now(timezone.utc) - timedelta(seconds=200)).isoformat()
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

        reclaim = await client.post(
            "/api/queue/claim", json=_claim_body(cluster_identities["beta"], "google/gemini-3.8-flash")
        )
        assert reclaim.json()["job"] is not None
        assert reclaim.json()["job"]["url"] == "https://example.com/scen4"


@pytest.mark.asyncio
async def test_scenario_05_fast_provisional_unblocking(cluster_identities: dict[str, NodeIdentity]):
    """Scenario 5: First worker submission populates completion report and unblocks listeners."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Breaking story with target quote for scenario 5."
        enq = await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={"url": "https://example.com/scen5", "normalized_text": prose, "target_quorum": 3},
        )
        job_id = enq.json()["job_id"]

        await client.post("/api/queue/claim", json=_claim_body(cluster_identities["alpha"], "google/gemini-3.8-flash"))
        report = make_cluster_report("https://example.com/scen5", prose, cluster_identities["alpha"], score=15.0)
        sub = await client.post(
            "/api/queue/submit",
            json={
                "job_id": job_id,
                "worker_pubkey": cluster_identities["alpha"].public_key_hex,
                "model_slug": "google/gemini-3.8-flash",
                "report": report.model_dump(mode="json"),
            },
        )
        assert sub.status_code == 200
        assert get_completed_report("https://example.com/scen5") is not None


@pytest.mark.asyncio
async def test_scenario_06_bayesian_consensus_convergence(cluster_identities: dict[str, NodeIdentity]):
    """Scenario 6: Three distinct model families submit passes and converge via BayesianConsensusAggregator."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Consensus story text with valid quote for scenario 6."
        enq = await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={"url": "https://example.com/scen6", "normalized_text": prose, "target_quorum": 3},
        )
        job_id = enq.json()["job_id"]

        workers = [
            ("alpha", "google/gemini-3.8-flash", 18.0),
            ("beta", "anthropic/claude-3-7-sonnet", 22.0),
            ("gamma", "deepseek/deepseek-r1", 20.0),
        ]
        last_res = None
        for name, slug, score in workers:
            c = await client.post("/api/queue/claim", json=_claim_body(cluster_identities[name], slug))
            assert c.json()["job"] is not None
            rep = make_cluster_report("https://example.com/scen6", prose, cluster_identities[name], score=score)
            last_res = await client.post(
                "/api/queue/submit",
                json={
                    "job_id": job_id,
                    "worker_pubkey": cluster_identities[name].public_key_hex,
                    "model_slug": slug,
                    "report": rep.model_dump(mode="json"),
                },
            )
            assert last_res.status_code == 200

        assert last_res is not None
        assert last_res.json()["is_consensus_ready"] is True

        async with get_async_session() as session:
            job = (await session.exec(select(AuditJob).where(AuditJob.job_id == job_id))).first()
            assert job is not None and job.consensus_verdict_json is not None
            verdict = json.loads(job.consensus_verdict_json)
            assert verdict["evaluations_count"] == 3
            assert verdict["classification"] == "CLEAN"


def test_scenario_07_galileo_rule_override():
    """Scenario 7: Grounded finding from minority specialist overrides ungrounded clean majority."""
    audits = [
        {"suspicion_score": 10.0, "violations": []},
        {"suspicion_score": 12.0, "violations": []},
        {
            "suspicion_score": 58.0,
            "violations": [{"rule_id": "SPJ-1.1", "quote": "Secret source claim", "severity": 3}],
        },
    ]
    verdict = compute_consensus_verdict(audits)
    assert verdict["galileo_override"] is True
    assert verdict["consensus_score"] >= 45.0
    assert verdict["classification"] in ("SUSPICIOUS", "DECEPTIVE")


@pytest.mark.asyncio
async def test_scenario_08_sybil_same_key_different_family_rejected(cluster_identities: dict[str, NodeIdentity]):
    """Scenario 8: Same worker key CANNOT claim a second pass even under a DIFFERENT model family."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Sybil protection story prose."
        enq = await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={"url": "https://example.com/scen8", "normalized_text": prose, "target_quorum": 3},
        )
        job_id = enq.json()["job_id"]

        await client.post("/api/queue/claim", json=_claim_body(cluster_identities["alpha"], "google/gemini-3.8-flash"))
        rep1 = make_cluster_report("https://example.com/scen8", prose, cluster_identities["alpha"], score=20.0)
        sub1 = await client.post(
            "/api/queue/submit",
            json={
                "job_id": job_id,
                "worker_pubkey": cluster_identities["alpha"].public_key_hex,
                "model_slug": "google/gemini-3.8-flash",
                "report": rep1.model_dump(mode="json"),
            },
        )
        assert sub1.status_code == 200

        # Same pubkey tries to claim again claiming to run a DIFFERENT model family (anthropic/claude)
        claim2 = await client.post(
            "/api/queue/claim", json=_claim_body(cluster_identities["alpha"], "anthropic/claude-3-7-sonnet")
        )
        assert claim2.status_code == 200
        assert claim2.json()["job"] is None


def test_scenario_09_worker_quality_and_badge_unlocks():
    """Scenario 9: Evaluate badge unlocks and quality scores based on worker telemetry."""
    worker = WorkerRecord(
        worker_pubkey="c" * 64,
        total_completed=30,
        bounties_cleared=28,
        grounded_violations_count=15,
        tokens_donated=6_000_000,
        quality_score=0.92,
    )
    badge_ids = {b.badge_id for b in evaluate_worker_badges(worker)}
    assert "first_bounty" in badge_ids
    assert "bounty_hunter" in badge_ids


@pytest.mark.asyncio
async def test_scenario_10_self_serve_affinity_routing(cluster_identities: dict[str, NodeIdentity]):
    """Scenario 10: Worker with affinity snatches matched job with priority over older jobs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={"url": "https://example.com/job1", "normalized_text": "prose", "priority": 1},
        )
        await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={
                "url": "https://example.com/job2_affinity",
                "normalized_text": "prose",
                "priority": 2,
                "client_affinity": "my-workstation",
            },
        )

        claim = await client.post(
            "/api/queue/claim",
            json=_claim_body(cluster_identities["alpha"], "google/gemini-3.8-flash", client_affinity="my-workstation"),
        )
        assert claim.json()["job"] is not None
        assert claim.json()["job"]["url"] == "https://example.com/job2_affinity"


@pytest.mark.asyncio
async def test_scenario_11_multi_model_audits_survive_init_db(cluster_identities: dict[str, NodeIdentity]):
    """Scenario 11: Multi-model quorum audits for the same URL survive repeated init_db() invocations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        prose = "Multi-model persistence regression test prose."
        enq = await client.post(
            "/api/queue/enqueue",
            headers=OPERATOR_HEADERS,
            json={"url": "https://example.com/scen11", "normalized_text": prose, "target_quorum": 3},
        )
        job_id = enq.json()["job_id"]

        for name, slug in (
            ("alpha", "google/gemini-3.8-flash"),
            ("beta", "anthropic/claude-3-7-sonnet"),
            ("gamma", "deepseek/deepseek-r1"),
        ):
            await client.post("/api/queue/claim", json=_claim_body(cluster_identities[name], slug))
            rep = make_cluster_report("https://example.com/scen11", prose, cluster_identities[name], score=25.0)
            res = await client.post(
                "/api/queue/submit",
                json={
                    "job_id": job_id,
                    "worker_pubkey": cluster_identities[name].public_key_hex,
                    "model_slug": slug,
                    "report": rep.model_dump(mode="json"),
                },
            )
            assert res.status_code == 200

    # Re-run init_db() (which executes migrate_db_v1_to_v2) and verify all 3 distinct audits remain intact
    await init_db()
    async with get_async_session() as session:
        audits = (await session.exec(select(Audit))).all()
        assert len(audits) == 3, f"init_db() wiped multi-model audits! Remaining: {len(audits)}"
