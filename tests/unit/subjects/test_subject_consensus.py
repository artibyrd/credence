"""Unit tests for Subject-Weighted Consensus and Empirical Domain Dominance."""

from datetime import datetime, timezone

import pytest

from credence.mesh.consensus import BayesianConsensusAggregator
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


def _make_mock_attestation(
    node_pubkey: str,
    suspicion_score: float,
    classification: str,
    confidence: float = 0.95,
    is_grounded: bool = True,
) -> AuditReport:
    """Helper to construct synthetic signed AuditReport."""
    findings = (
        [
            SpecialistViolationFinding(
                rule_id="SPJ-1.1",
                rule_uri="journalistic-ethics:seek-truth/SPJ-1.1@v1.0.0",
                domain="JOURNALISTIC_ETHICS",
                cluster_id="accuracy",
                severity=3,
                confidence=0.9,
                quote_or_element="verbatim excerpt",
                reasoning="reasoning",
                is_grounded=is_grounded,
            )
        ]
        if suspicion_score > 0
        else []
    )

    return AuditReport(
        url="https://apiculture-daily.org/protective-suits-test",
        content_sha256="hash_apiculture_test_123",
        simhash_64="aabbccdd11223344",
        suspicion_score=suspicion_score,
        suspicion_density=4.0 if suspicion_score > 0 else 0.0,
        confidence_score=confidence,
        classification=classification,
        is_satire=False,
        content_type="NEWS_ARTICLE",
        violations=findings,
        node_pubkey=node_pubkey,
        node_signature="sig_" + node_pubkey,
        audited_at=datetime.now(timezone.utc),
    )


@pytest.mark.unit
def test_subject_consensus_beekeeper_vs_dogwalker():
    """Verify 2 beekeepers heavily dominate 4 dog walkers on apiary suit evaluation."""
    aggregator = BayesianConsensusAggregator()

    # 2 Expert Beekeeper Nodes: find real safety flaws in bee suit (S = 82.0)
    att_bee1 = _make_mock_attestation("beekeeper_1", 82.0, "DECEPTIVE")
    att_bee2 = _make_mock_attestation("beekeeper_2", 80.0, "DECEPTIVE")

    # 4 Generalist / Dog Walker Nodes: superficially rate it clean (S = 5.0)
    att_dog1 = _make_mock_attestation("dogwalker_1", 5.0, "CLEAN")
    att_dog2 = _make_mock_attestation("dogwalker_2", 6.0, "CLEAN")
    att_dog3 = _make_mock_attestation("dogwalker_3", 4.0, "CLEAN")
    att_dog4 = _make_mock_attestation("dogwalker_4", 5.0, "CLEAN")

    attestations = [att_bee1, att_bee2, att_dog1, att_dog2, att_dog3, att_dog4]

    # Reputations all high (0.95)
    reps = {p.node_pubkey: 0.95 for p in attestations}

    # Domain Expertise in apiculture.equipment:
    # Beekeepers have 0.98 expertise; dog walkers have baseline 0.05
    expertise_map = {
        "beekeeper_1": 0.98,
        "beekeeper_2": 0.96,
        "dogwalker_1": 0.05,
        "dogwalker_2": 0.05,
        "dogwalker_3": 0.05,
        "dogwalker_4": 0.05,
    }

    verdict = aggregator.compute_consensus(
        attestations=attestations,
        node_reputations=reps,
        subject_id="apiculture.equipment",
        subject_expertise_map=expertise_map,
    )

    assert verdict is not None
    assert verdict.subject_id == "apiculture.equipment"

    # Expert score (80-82) should dominate despite being outnumbered 2 to 4!
    assert verdict.consensus_score >= 70.0
    assert verdict.classification == "DECEPTIVE"

    # Beekeeper weights should be ~0.97 while dog walkers are ~0.23
    for pw in verdict.peer_weights:
        if "beekeeper" in pw.node_pubkey:
            assert pw.effective_weight >= 0.90
            assert pw.domain_expertise >= 0.95
        else:
            assert pw.effective_weight <= 0.25
            assert pw.domain_expertise == 0.05


@pytest.mark.unit
def test_subject_consensus_canine_reversal():
    """Verify dog walkers dominate beekeepers on a canine leash review."""
    aggregator = BayesianConsensusAggregator()

    # 2 Beekeepers rate leash as clean (S = 5.0)
    att_bee1 = _make_mock_attestation("beekeeper_1", 5.0, "CLEAN")
    att_bee2 = _make_mock_attestation("beekeeper_2", 6.0, "CLEAN")

    # 4 Dog Walkers detect trachea hazard (S = 75.0)
    att_dog1 = _make_mock_attestation("dogwalker_1", 75.0, "DECEPTIVE")
    att_dog2 = _make_mock_attestation("dogwalker_2", 78.0, "DECEPTIVE")
    att_dog3 = _make_mock_attestation("dogwalker_3", 72.0, "DECEPTIVE")
    att_dog4 = _make_mock_attestation("dogwalker_4", 76.0, "DECEPTIVE")

    attestations = [att_bee1, att_bee2, att_dog1, att_dog2, att_dog3, att_dog4]
    reps = {p.node_pubkey: 0.95 for p in attestations}

    # On veterinary.canine, dog walkers have 0.98 expertise; beekeepers have 0.05
    expertise_map = {
        "beekeeper_1": 0.05,
        "beekeeper_2": 0.05,
        "dogwalker_1": 0.98,
        "dogwalker_2": 0.96,
        "dogwalker_3": 0.95,
        "dogwalker_4": 0.97,
    }

    verdict = aggregator.compute_consensus(
        attestations=attestations,
        node_reputations=reps,
        subject_id="veterinary.canine",
        subject_expertise_map=expertise_map,
    )

    assert verdict is not None
    assert verdict.consensus_score >= 70.0
    assert verdict.classification == "DECEPTIVE"
