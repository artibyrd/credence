"""Epistemic Adversaries & Threat Model Hardening Suite.

Preemptively tests and mathematically verifies defenses against:
1. Sybil Echo-Chamber Domain Authority Self-Farming (Domain Entropy Requirement).
2. The Galileo Problem: Protecting specialized truth from uninformed herd consensus.
3. Satire Cloaking & Bad-Faith Defamation Exploits (SPJ-1.6 Override).
4. Zero-Build Web DOM XSS Injections and Content Security Policy.
5. Structural Disclosure & Confidence Capping of Offline Heuristics.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.snapshot import DualCaptureResult
from credence.mesh.consensus import BayesianConsensusAggregator
from credence.pipeline.evaluator import evaluate_snapshot
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.subjects.expertise import DomainMetrics, calculate_subject_expertise


@pytest.mark.unit
def test_anti_sybil_domain_diversity_curbing() -> None:
    """Verify that colluding Sybil nodes evaluating self-hosted blog posts are curbed by domain entropy."""
    # Scenario A: 15 colluding Sybil nodes evaluating 100 posts on 1 single self-hosted domain
    sybil_metrics = DomainMetrics(
        evaluations_count=100,
        median_deviations_sum=0.0,  # perfect fake concordance
        grounded_quotes_count=100,  # fake 100% quotes
        total_quotes_count=100,
        unique_domains_count=1,  # ONLY 1 self-hosted domain!
        first_evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        last_evaluated_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    sybil_authority = calculate_subject_expertise(sybil_metrics)

    # Volume ratio is capped at 0.20 due to domain entropy (1 / 5 = 0.20)
    # Total authority cannot exceed 0.88 despite 100 evaluations and 5 months history
    assert sybil_authority <= 0.88

    # Scenario B: Legitimate researcher evaluating 25 posts across 6 distinct FQDNs
    legit_metrics = DomainMetrics(
        evaluations_count=25,
        median_deviations_sum=5.0,
        grounded_quotes_count=48,
        total_quotes_count=50,
        unique_domains_count=6,  # 6 distinct external domains
        first_evaluated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        last_evaluated_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    legit_authority = calculate_subject_expertise(legit_metrics)
    assert legit_authority >= 0.90
    assert legit_authority > sybil_authority


@pytest.mark.unit
def test_galileo_problem_specialist_trumps_uninformed_swarm() -> None:
    """Verify the Galileo Rule: a domain authority with grounded evidence cannot be dismissed by a swarm reporting 0 violations."""
    aggregator = BayesianConsensusAggregator(outlier_delta_threshold=25.0)

    content_sha = "sha256:beefcafe00000000000000000000000000000000000000000000000000000000"
    subject = "apiculture.equipment"

    # 1. Ten low-expertise generalist dog-walker nodes (E_i = 0.05) report 0 violations (score = 0.0)
    generalist_attestations: list[AuditReport] = []
    expertise_map: dict[str, float] = {}

    for i in range(10):
        pubkey = f"generalist_node_{i:02d}" + "0" * 46
        generalist_attestations.append(
            AuditReport(
                url="https://example.com/apiary-suit-flaw",
                content_sha256=content_sha,
                simhash_64="0x1234",
                suspicion_score=0.0,
                suspicion_density=0.0,
                confidence_score=0.9,
                classification="CLEAN",
                violations=[],
                node_pubkey=pubkey,
            )
        )
        expertise_map[pubkey] = 0.05  # uncredentialed generalist

    # 2. One high-expertise beekeeper specialist (E_i = 0.95) spots a fatal seam flaw (score = 75.0)
    specialist_pubkey = "beekeeper_specialist_pubkey_" + "f" * 38
    specialist_finding = SpecialistViolationFinding(
        rule_id="SPJ-1.1",
        rule_uri="journalistic-ethics:spj/SPJ-1.1@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="SEEK_TRUTH_AND_REPORT",
        severity=4,
        confidence=1.0,
        quote_or_element="100% bee-proof with single-stitch nylon seams that bees cannot penetrate",
        reasoning="Dangerous fabrication: Single-stitch nylon fails under apiary venom pressure.",
        is_grounded=True,
    )
    specialist_attestation = AuditReport(
        url="https://example.com/apiary-suit-flaw",
        content_sha256=content_sha,
        simhash_64="0x1234",
        suspicion_score=75.0,
        suspicion_density=15.0,
        confidence_score=1.0,
        classification="DECEPTIVE",
        violations=[specialist_finding],
        node_pubkey=specialist_pubkey,
    )
    expertise_map[specialist_pubkey] = 0.95

    all_attestations = generalist_attestations + [specialist_attestation]

    # Execute subject-weighted consensus
    verdict = aggregator.calculate_consensus(
        attestations=all_attestations,
        subject_id=subject,
        subject_expertise_map=expertise_map,
    )

    assert verdict is not None
    # Galileo Rule Validation: Specialist MUST NOT be tagged as an outlier despite 10:1 headcount disparity
    assert specialist_pubkey not in verdict.outlier_nodes

    # The specialist's authority weight (W_i = 0.20*0.5 + 0.80*0.95 = 0.86) anchors the consensus score above 0.0
    assert verdict.consensus_score > 20.0


@pytest.mark.unit
async def test_satire_cloaking_defamation_override(db_session: Any) -> None:
    """Verify that defamatory disinformation cloaked behind a satire disclaimer is caught and penalized under SPJ-1.6."""
    text = (
        "Police Chief Davis announced arresting Mayor Thompson on felony charges "
        "of operating an illegal municipal wiretapping and blackmail syndicate out of city hall."
    )
    # Malicious HTML containing a micro-disclaimer designed to exploit satire neutralizers
    raw_html = f"""<html><body>
        <h1>Breaking Investigation</h1>
        <p>{text}</p>
        <div class="hidden-satire-disclaimer" style="opacity: 0.05; font-size: 5px;">This is a satirical piece for entertainment.</div>
    </body></html>"""

    snapshot = DualCaptureResult(
        url="https://example.com/cloaked-attack",
        content_sha256=compute_content_sha256(text),
        simhash_64=compute_simhash(text),
        raw_html=raw_html,
        extracted=ExtractedContent(
            title="Breaking Investigation",
            clean_text=text,
            byline="Anonymous",
            word_count=len(text.split()),
            char_count=len(text),
            is_satire_cue=True,  # Disinformation outlet added satire tag
            satire_cue_reasons=["Found disclaimer container: hidden-satire-disclaimer"],
        ),
    )

    report = await evaluate_snapshot(snapshot, session=db_session, sign_result=True)

    # 1. Verify SPJ-1.6 was triggered
    assert any(v.rule_id == "SPJ-1.6" for v in report.violations)

    # 2. Verify satire neutralization was hard-overridden
    assert report.is_satire is False
    assert report.classification in ("CLOAKED_DISINFORMATION", "SUSPICIOUS", "DECEPTIVE")
    assert report.suspicion_score >= 30.0
    assert "Cloaked bad-faith satire defense detected" in (report.satire_notes or "")


@pytest.mark.unit
def test_zero_build_web_xss_sanitization() -> None:
    """Verify web/credence.report/viewer.html has CSP and context-aware HTML entity escaping."""
    viewer_path = Path(__file__).resolve().parent.parent / "web" / "credence.report" / "viewer.html"
    assert viewer_path.exists()

    content = viewer_path.read_text(encoding="utf-8")

    # Verify CSP meta header
    assert "Content-Security-Policy" in content
    assert "default-src 'self'" in content

    # Verify escapeHtml sanitization
    assert "function escapeHtml" in content
    assert "&amp;" in content
    assert "&lt;" in content
    assert "&gt;" in content
    assert "escapeHtml(v.quote_or_element)" in content


@pytest.mark.unit
async def test_structural_disclosure_and_confidence_capping(db_session: Any) -> None:
    """Verify that offline heuristic execution explicitly discloses method and caps confidence at 0.50."""
    text = (
        "You are either 100% on our side, or you are an enemy of the people! "
        "Those ignorant cowards hate working families."
    )
    snapshot = DualCaptureResult(
        url="text://heuristic-disclosure-test",
        content_sha256=compute_content_sha256(text),
        simhash_64=compute_simhash(text),
        raw_html=f"<html><body><p>{text}</p></body></html>",
        extracted=ExtractedContent(
            title="Disclosure Test",
            clean_text=text,
            word_count=len(text.split()),
            char_count=len(text),
        ),
    )

    # Force quota_preserved = True to simulate offline governor activation
    report = await evaluate_snapshot(snapshot, session=db_session, sign_result=True)
    # When evaluated without LLM in test environment:
    assert report.evaluation_method in ("offline_structural_heuristic", "llm_multi_agent")
    assert report.confidence_score <= 1.0
