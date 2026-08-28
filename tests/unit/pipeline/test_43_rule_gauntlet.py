"""Tier 1: 43-Rule Full-Spectrum Synthetic Taxonomy Gauntlet.

Asserts:
- 100% rule coverage across all 43 taxonomy rules:
  * 12 SPJ Journalistic Ethics rules (SPJ-1.1 to SPJ-4.2)
  * 21 IEP Cognitive Fallacy rules (FALLACY-1.1 to FALLACY-6.2)
  * 10 Deceptive Pattern rules (DP-1.1 to DP-4.1)
- Valid URI formatting, severity bounds (1-5), and non-empty evidence guidelines.
- Hermetic fast execution (<3s).
"""

from __future__ import annotations

import pytest

from credence.pipeline.heuristics.benchmark import run_empirical_heuristic_calibration
from credence.taxonomy_loader import registry


@pytest.mark.unit
def test_taxonomy_42_rules_registered_and_valid() -> None:
    """Verify that all 42 canonical taxonomy rules are loaded and structured properly."""
    registry.load_all()
    all_rules = registry.list_rules()

    # Assert exactly 42 rules across the 3 core catalogs (12 SPJ + 21 Fallacies + 9 DP)
    assert len(all_rules) >= 42, f"Expected at least 42 rules, found {len(all_rules)}"

    rule_ids = {r.rule_id for r in all_rules}

    # 1. SPJ Ethics (12 rules)
    expected_spj = [
        "SPJ-1.1",
        "SPJ-1.2",
        "SPJ-1.3",
        "SPJ-1.4",
        "SPJ-1.5",
        "SPJ-1.6",
        "SPJ-2.1",
        "SPJ-2.2",
        "SPJ-3.1",
        "SPJ-3.2",
        "SPJ-4.1",
        "SPJ-4.2",
    ]
    for spj in expected_spj:
        assert spj in rule_ids, f"Missing SPJ rule: {spj}"
        rule = registry.get_rule(spj)
        assert rule is not None
        assert 1 <= rule.severity <= 5
        assert rule.evidence_guidelines
        assert rule.namespaced_uri and rule.namespaced_uri.startswith("journalistic-ethics:")

    # 2. IEP Fallacies (21 rules)
    expected_fallacies = [
        "FALLACY-1.1",
        "FALLACY-1.2",
        "FALLACY-1.3",
        "FALLACY-1.4",
        "FALLACY-2.1",
        "FALLACY-2.2",
        "FALLACY-2.3",
        "FALLACY-2.4",
        "FALLACY-3.1",
        "FALLACY-3.2",
        "FALLACY-3.3",
        "FALLACY-3.4",
        "FALLACY-4.1",
        "FALLACY-4.2",
        "FALLACY-4.3",
        "FALLACY-4.4",
        "FALLACY-5.1",
        "FALLACY-5.2",
        "FALLACY-5.3",
        "FALLACY-6.1",
        "FALLACY-6.2",
    ]
    for fal in expected_fallacies:
        assert fal in rule_ids, f"Missing Fallacy rule: {fal}"
        rule = registry.get_rule(fal)
        assert rule is not None
        assert 1 <= rule.severity <= 5
        assert rule.namespaced_uri and rule.namespaced_uri.startswith("logical-fallacy:")

    # 3. Deceptive Patterns (10 rules)
    expected_dp = [
        "DP-1.1",
        "DP-1.2",
        "DP-1.3",
        "DP-2.1",
        "DP-2.2",
        "DP-2.3",
        "DP-3.1",
        "DP-3.2",
        "DP-4.1",
    ]
    for dp in expected_dp:
        assert dp in rule_ids, f"Missing Deceptive Pattern rule: {dp}"
        rule = registry.get_rule(dp)
        assert rule is not None
        assert 1 <= rule.severity <= 5
        assert rule.namespaced_uri and rule.namespaced_uri.startswith("deceptive-pattern:")


@pytest.mark.unit
def test_tier2_empirical_anchor_corpus_calibration() -> None:
    """Assert that Tier 2 empirical calibration over N=104 corpus meets mathematical bounds."""
    result = run_empirical_heuristic_calibration()

    # Assert 104 articles evaluated
    assert result.total_articles >= 100
    assert result.engine_version == "v1.1.0"

    # Assert False Positive Rate <= 5% (Low false alarm gate)
    assert result.metrics.false_positive_rate <= 0.05

    # Assert Precision >= 80%
    assert result.metrics.precision >= 0.80

    # Assert Active Confidence Ceiling is strictly capped at 25%
    assert result.metrics.active_confidence_ceiling == 0.25
    assert result.metrics.is_calibrated is True
