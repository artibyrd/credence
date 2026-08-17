"""Unit tests for Suspicion Scoring, Density Index, and Satire Calibration."""

import pytest

from credence.pipeline.schemas import SpecialistViolationFinding
from credence.pipeline.scoring import (
    calculate_aggregate_confidence,
    calculate_calibrated_score,
    calculate_raw_suspicion,
    calculate_suspicion_density,
    classify_verdict,
)


@pytest.fixture
def sample_violations() -> list[SpecialistViolationFinding]:
    """Return a list of test violations across different domains."""
    return [
        SpecialistViolationFinding(
            rule_id="SPJ-1.1",
            rule_uri="journalistic-ethics:seek-truth-and-report/SPJ-1.1@v1.0.0",
            domain="JOURNALISTIC_ETHICS",
            cluster_id="SEEK_TRUTH_AND_REPORT",
            severity=3,
            confidence=1.0,
            quote_or_element="Unverified claim.",
            reasoning="Reasoning.",
            is_grounded=True,
        ),
        SpecialistViolationFinding(
            rule_id="FALLACY-1.1",
            rule_uri="logical-fallacy:relevance/FALLACY-1.1@v1.0.0",
            domain="LOGICAL_FALLACY",
            cluster_id="RELEVANCE_AND_PERSONAL_ATTACKS",
            severity=4,
            confidence=0.9,
            quote_or_element="Personal attack.",
            reasoning="Reasoning.",
            is_grounded=True,
        ),
        SpecialistViolationFinding(
            rule_id="DP-2.2",
            rule_uri="deceptive-pattern:emotional-and-social-pressure/DP-2.2@v1.0.0",
            domain="DECEPTIVE_PATTERN",
            cluster_id="EMOTIONAL_AND_SOCIAL_PRESSURE",
            severity=4,
            confidence=1.0,
            quote_or_element="Fake countdown timer.",
            reasoning="Reasoning.",
            is_grounded=True,
        ),
        # Ungrounded violation (hallucinated) -> should be ignored in scoring
        SpecialistViolationFinding(
            rule_id="SPJ-2.1",
            rule_uri="journalistic-ethics:minimize-harm/SPJ-2.1@v1.0.0",
            domain="JOURNALISTIC_ETHICS",
            cluster_id="MINIMIZE_HARM",
            severity=5,
            confidence=1.0,
            quote_or_element="Hallucinated quote.",
            reasoning="Reasoning.",
            is_grounded=False,
        ),
    ]


@pytest.mark.unit
def test_calculate_raw_suspicion(sample_violations: list[SpecialistViolationFinding]) -> None:
    """Verify raw score calculation respects severity, confidence, and domain weights."""
    # SPJ-1.1: 3 * 1.0 * 1.2 = 3.6
    # FALLACY-1.1: 4 * 0.9 * 1.0 = 3.6
    # DP-2.2: 4 * 1.0 * 1.5 = 6.0
    # SPJ-2.1: ungrounded -> 0.0
    # Total = 3.6 + 3.6 + 6.0 = 13.2
    raw = calculate_raw_suspicion(sample_violations)
    assert raw == 13.2


@pytest.mark.unit
def test_suspicion_density_calculation() -> None:
    """Verify violations per 1,000 words calculation."""
    # 3 violations across 300 words -> (3 / 300) * 1000 = 10.0
    density = calculate_suspicion_density(violation_count=3, word_count=300)
    assert density == 10.0

    # Test short text floor constraint (min 50 words)
    density_short = calculate_suspicion_density(violation_count=1, word_count=10)
    assert density_short == 20.0  # (1 / 50) * 1000


@pytest.mark.unit
def test_satire_neutralization_scoring() -> None:
    """Verify legitimate satire score is neutralized to 0.0."""
    raw_score = 25.0

    # Legitimate satire -> 0.0
    satire_score = calculate_calibrated_score(raw_score, is_satire=True, has_cloaked_disinfo=False)
    assert satire_score == 0.0

    # Standard article -> normal saturation
    normal_score = calculate_calibrated_score(raw_score, is_satire=False, has_cloaked_disinfo=False)
    assert normal_score > 80.0

    # Cloaked disinformation with fake satire defense -> full penalty applied
    cloaked_score = calculate_calibrated_score(raw_score, is_satire=True, has_cloaked_disinfo=True)
    assert cloaked_score == normal_score


@pytest.mark.unit
def test_verdict_classification_bands() -> None:
    """Verify classification band boundaries."""
    assert classify_verdict(5.0, is_satire=False) == "CLEAN"
    assert classify_verdict(25.0, is_satire=False) == "LOW_SUSPICION"
    assert classify_verdict(55.0, is_satire=False) == "SUSPICIOUS"
    assert classify_verdict(85.0, is_satire=False) == "DECEPTIVE"

    # Satire overrides
    assert classify_verdict(0.0, is_satire=True) == "SATIRE_PARODY"
    assert classify_verdict(80.0, is_satire=True, has_cloaked_disinfo=True) == "CLOAKED_DISINFORMATION"


@pytest.mark.unit
def test_aggregate_confidence(sample_violations: list[SpecialistViolationFinding]) -> None:
    """Verify mean confidence computation ignores ungrounded citations."""
    conf = calculate_aggregate_confidence(sample_violations)
    # Grounded confidences: 1.0, 0.9, 1.0 -> avg = 0.97
    assert conf == 0.97
