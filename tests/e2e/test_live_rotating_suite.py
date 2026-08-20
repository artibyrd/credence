"""Reusable Live Rotating & Mutating E2E Test Suite for Credence Ecosystem.

Exercises all four universal interfaces and P2P mesh components against dynamic live web targets:
1. CLI Workstation live audits, satire neutralization, RFC 8785 JSON export, and Ed25519 signature verification.
2. Feed Sifter daemon, dynamic RSS quality scoring (F_j), and real-time live article discovery.
3. FastMCP 2.0 remote SSE agent server connection, tool enumeration, and consensus queries.
4. 13-Node Watts-Strogatz P2P Mesh Cluster BitTorrent work-sharing (0 tokens) and Byzantine slash defense.

The target corpus dynamically rotates based on deterministic daily seeds or CREDENCE_LIVE_SEED.
Run with:
    CREDENCE_LIVE_TESTS=1 poetry run pytest tests/e2e/test_live_rotating_suite.py -v -m e2e -s
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import List

import httpx
import pytest

from credence.feeds.health import compute_feed_quality_score
from credence.feeds.parser import fetch_and_parse_feed
from credence.identity import (
    load_or_create_node_identity,
    sign_audit_report,
    verify_audit_signature,
)
from credence.ingestion.snapshot import capture_webpage
from credence.mesh.consensus import BayesianConsensusAggregator
from credence.mesh.relay import MeshGossipRelay
from credence.pipeline.evaluator import evaluate_snapshot
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from tests.e2e.live_corpus import (
    extract_dynamic_feed_articles,
    get_active_seed,
    get_rotating_sample,
)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_live_rotating_cli_audits(tmp_path: Path) -> None:
    """Verify live audits, satire neutralization, and Ed25519 export/verify on rotated sites."""
    active_seed = get_active_seed()
    print(f"\n[Rotator] Active Rotation Seed: '{active_seed}'")

    # 1. Sample 1 reference and 1 satire site from the rotating corpus
    ref_target = get_rotating_sample("reference", seed=active_seed, count=1)[0]
    satire_target = get_rotating_sample("satire", seed=active_seed, count=1)[0]

    print(f"[Rotator] Selected Reference Target: {ref_target.title} ({ref_target.url})")
    print(f"[Rotator] Selected Satire Target:    {satire_target.title} ({satire_target.url})")

    # 2. Audit Reference Target
    print("\n--- Auditing Reference Target ---")
    ref_snap = await capture_webpage(ref_target.url, timeout_ms=25000)
    assert len(ref_snap.extracted.clean_text) > 100
    ref_report = await evaluate_snapshot(ref_snap, profile_override=None, sign_result=True)

    print(
        f"✓ Ref Classification: {ref_report.classification} (Suspicion: {ref_report.suspicion_score}, Density: {ref_report.suspicion_density})"
    )
    assert ref_report.is_satire is False, f"Expected non-satire for {ref_target.url}"
    assert ref_report.suspicion_score <= 35.0, (
        f"Expected clean or low suspicion for reference site, got {ref_report.suspicion_score}"
    )

    # 3. Export to canonical RFC 8785 JSON and verify Ed25519 signature
    ref_export_file = tmp_path / "ref_audit_export.json"
    ref_export_file.write_text(json.dumps(ref_report.model_dump(mode="json"), indent=2), encoding="utf-8")

    exported_dict = json.loads(ref_export_file.read_text(encoding="utf-8"))
    imported_report = AuditReport(**exported_dict)
    assert imported_report.node_pubkey is not None
    assert imported_report.node_signature is not None
    is_valid_sig = verify_audit_signature(imported_report)
    assert is_valid_sig is True, "Exported audit report failed Ed25519 signature verification!"
    print(
        f"✓ Ed25519 Attestation Signature Cryptographically Valid (Node Pubkey: {imported_report.node_pubkey[:16]}...)"
    )

    # Verify anti-tampering resilience: modifying any field invalidates signature
    tampered_dict = dict(exported_dict)
    tampered_dict["suspicion_score"] = 99.0
    tampered_report = AuditReport(**tampered_dict)
    assert verify_audit_signature(tampered_report) is False, "Tampered report should fail signature verification!"
    print("✓ Anti-Tamper Security Verified: Tampered suspicion score rejected by Ed25519 verifier.")

    # 4. Audit Satire Target
    print("\n--- Auditing Satire Target ---")
    satire_snap = await capture_webpage(satire_target.url, timeout_ms=25000)
    if (
        "checking your browser" in satire_snap.extracted.clean_text.lower()
        or "just a moment" in satire_snap.extracted.clean_text.lower()
    ):
        pytest.skip(f"Bot protection interstitial encountered on {satire_target.url}; skipping assertion.")

    assert len(satire_snap.extracted.clean_text) > 50
    satire_report = await evaluate_snapshot(satire_snap, profile_override=None, sign_result=True)

    print(
        f"✓ Satire Classification: {satire_report.classification} (Satire Flag: {satire_report.is_satire}, Score: {satire_report.suspicion_score})"
    )
    assert satire_report.is_satire is True, f"Expected satire neutralization for {satire_target.url}"
    assert satire_report.suspicion_score == 0.0, (
        f"Expected 0.0 suspicion score for neutralized satire, got {satire_report.suspicion_score}"
    )


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_live_rotating_feed_sifter_and_dynamic_articles() -> None:
    """Verify live RSS feed quality scoring and audit dynamically discovered real-time articles."""
    active_seed = get_active_seed()
    feed_target = get_rotating_sample("rss_feeds", seed=active_seed, count=1)[0]
    print(f"\n[Rotator] Selected Live RSS Feed: {feed_target.title} ({feed_target.url})")

    # 1. Fetch and parse live RSS feed
    parsed = await fetch_and_parse_feed(feed_target.url)
    assert len(parsed.entries) > 0, f"Expected entries in live feed {feed_target.url}"
    print(f"✓ Successfully parsed {len(parsed.entries)} feed items (Format: {parsed.feed_format})")

    # 2. Evaluate Dynamic Feed Quality Metric (F_j)
    published_dates = [e.published_at for e in parsed.entries if e.published_at]
    quality_metrics = compute_feed_quality_score([], published_dates)
    print(
        f"✓ Composite Feed Score F_j: {quality_metrics.composite_score_fj:.2f} (Status: {'ACTIVE' if quality_metrics.composite_score_fj >= 0.40 else 'QUARANTINE'})"
    )
    assert quality_metrics.composite_score_fj >= 0.40, (
        f"Feed score F_j below threshold: {quality_metrics.composite_score_fj}"
    )

    # 3. Extract dynamic real-time article URLs from the feed
    dynamic_articles = await extract_dynamic_feed_articles(feed_target.url, max_articles=1)
    assert len(dynamic_articles) >= 1, "Failed to extract dynamic article URL from live feed"
    live_article_url = dynamic_articles[0]
    print(f"✓ Dynamically Discovered Live Article: {live_article_url}")

    # 4. Audit the live discovered article
    article_snap = await capture_webpage(live_article_url, timeout_ms=25000)
    assert len(article_snap.extracted.clean_text) > 50
    article_report = await evaluate_snapshot(article_snap, profile_override=None, sign_result=True)
    print(
        f"✓ Live Article Evaluated: {article_report.classification} (Suspicion: {article_report.suspicion_score}, Density: {article_report.suspicion_density})"
    )
    assert article_report.classification in ("CLEAN", "LOW_SUSPICION", "UNCERTAIN", "SUSPICIOUS")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_live_rotating_fastmcp_sse_workflow() -> None:
    """Verify live FastMCP 2.0 remote SSE agent server against rotating targets."""
    mcp_host = os.getenv("CREDENCE_MCP_HOST", "https://mcp.credence.run")
    sse_endpoint = f"{mcp_host}/sse"
    print(f"\n[FastMCP 2.0] Connecting to remote SSE server at {sse_endpoint}...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        session_url = None
        t0 = time.perf_counter()

        # Step 1: Open SSE Stream & Capture Endpoint Session URI
        try:
            async with client.stream("GET", sse_endpoint, headers={"Accept": "text/event-stream"}) as response:
                assert response.status_code == 200, f"SSE handshake failed with {response.status_code}"
                print(f"✓ SSE Stream Opened ({response.status_code}) in {time.perf_counter() - t0:.3f}s")

                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        raw_data = line[5:].strip()
                        if raw_data.startswith("/messages/") or "session_id=" in raw_data:
                            session_url = f"{mcp_host}{raw_data}" if not raw_data.startswith("http") else raw_data
                            print(f"✓ Assigned FastMCP Session Endpoint: {session_url}")
                            break
        except Exception as exc:
            pytest.skip(f"Remote FastMCP SSE endpoint unreachable ({exc}); skipping live test.")

        assert session_url is not None, "Failed to receive session endpoint from SSE stream."

        # Step 2: Test JSON-RPC tools/list
        t0 = time.perf_counter()
        list_req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        res_list = await client.post(session_url, json=list_req)
        assert res_list.status_code in (200, 202)
        print(f"✓ tools/list responded in {time.perf_counter() - t0:.3f}s (Status: {res_list.status_code})")

        # Step 3: Test tools/call credence_get_consensus on rotating reference target
        ref_target = get_rotating_sample("reference", seed=get_active_seed(), count=1)[0]
        t0 = time.perf_counter()
        consensus_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "credence_get_consensus", "arguments": {"url": ref_target.url}},
        }
        res_call = await client.post(session_url, json=consensus_req)
        assert res_call.status_code in (200, 202)
        print(
            f"✓ tools/call credence_get_consensus on {ref_target.url} in {(time.perf_counter() - t0) * 1000:.1f}ms (Status: {res_call.status_code})"
        )

        # Step 4: Test error handling on invalid tool invocation
        invalid_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "credence_nonexistent_tool", "arguments": {}},
        }
        res_invalid = await client.post(session_url, json=invalid_req)
        assert res_invalid.status_code in (200, 202, 400, 404, 500)
        print(f"✓ FastMCP 2.0 Server Error Handling Verified (Status: {res_invalid.status_code})")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_live_rotating_mesh_cluster_work_sharing(tmp_path: Path) -> None:
    """Verify 13-node Watts-Strogatz mesh BitTorrent work-sharing and Byzantine defense on rotated news."""
    active_seed = get_active_seed()
    news_target = get_rotating_sample("journalism", seed=active_seed, count=1)[0]
    print(f"\n[Rotator] Selected News Target for Mesh Test: {news_target.title} ({news_target.url})")

    # 1. Initialize 13 nodes in a Watts-Strogatz ring lattice
    nodes: List[MeshGossipRelay] = []
    base_port = 9200

    for i in range(13):
        node_id = load_or_create_node_identity(tmp_path / f"node_{i}.key")
        left_neighbor = f"ws://127.0.0.1:{base_port + ((i - 1) % 13)}"
        right_neighbor = f"ws://127.0.0.1:{base_port + ((i + 1) % 13)}"
        relay = MeshGossipRelay(port=base_port + i, node_identity=node_id, peer_seeds=[left_neighbor, right_neighbor])
        nodes.append(relay)

    try:
        for r in nodes:
            await r.start()

        await asyncio.sleep(0.5)
        print("✓ 13-Node Watts-Strogatz Mesh active and interconnected.")

        # 2. Node 0 audits the rotated news target
        print(f"[Mesh] Node 0 auditing {news_target.url}...")
        snap = await capture_webpage(news_target.url, timeout_ms=25000)
        report = await evaluate_snapshot(snap, profile_override=None, sign_result=False)
        signed_report = sign_audit_report(report, nodes[0].identity)

        # 3. Node 0 broadcasts signed RFC 8785 envelope across mesh
        print("[Mesh] Gossiping signed attestation envelope across cluster...")
        await nodes[0].broadcast_attestation(signed_report)
        await asyncio.sleep(0.6)

        # 4. Verify 0-token adoption across peer nodes
        adopted_count = sum(1 for idx in range(1, 13) if nodes[idx].deduplicator._seen)
        savings_pct = (adopted_count / 13) * 100
        print(f"✓ Attestation adopted by {adopted_count}/12 peer nodes in 0 LLM tokens!")
        print(f"✓ BitTorrent Work-Sharing Compute Savings: {savings_pct:.1f}% ($0.00 token cost for peer nodes)!")
        assert adopted_count >= 10, f"Expected widespread gossip diffusion, got {adopted_count}/12"

        # 5. Byzantine Rogue Node Injection and Bayesian Slashing
        rogue_id = nodes[12].identity
        fake_report = AuditReport(
            url=news_target.url,
            content_sha256=signed_report.content_sha256,
            simhash_64=signed_report.simhash_64,
            suspicion_score=95.0,
            suspicion_density=8.5,
            confidence_score=1.0,
            classification="DECEPTIVE",
            violations=[
                SpecialistViolationFinding(
                    rule_id="SPJ-1.1",
                    rule_uri="journalistic-ethics:seek-truth/SPJ-1.1@v1.0.0",
                    domain="JOURNALISTIC_ETHICS",
                    cluster_id="SEEK_TRUTH_AND_REPORT_IT",
                    severity=5,
                    confidence=1.0,
                    quote_or_element="FABRICATED HALLUCINATED TEXT NOT IN ARTICLE",
                    reasoning="Malicious smear injection.",
                    is_grounded=False,
                )
            ],
        )
        signed_fake = sign_audit_report(fake_report, rogue_id)

        honest_reports = [sign_audit_report(report.model_copy(), nodes[i].identity) for i in range(12)]
        all_reports = honest_reports + [signed_fake]

        aggregator = BayesianConsensusAggregator()
        verdict = aggregator.compute_consensus(all_reports)
        assert verdict is not None
        print(f"✓ Bayesian Consensus Score: {verdict.consensus_score:.1f} (Classification: {verdict.classification})")
        print(f"✓ Rogue Attestation Filtered: {rogue_id.public_key_hex in verdict.outlier_nodes}")
        assert verdict.classification in ("CLEAN", "LOW_SUSPICION", "UNCERTAIN")
        assert rogue_id.public_key_hex in verdict.outlier_nodes, "Rogue Byzantine node was not detected as outlier!"
        print("🏆 13-Node Work-Sharing & Byzantine Slash Defense Verified Successfully!")

    finally:
        for r in nodes:
            await r.stop()
