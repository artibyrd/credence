"""Unit tests for the Autonomous Cost Profile Optimizer."""

from __future__ import annotations

import pytest

from credence.config import CostProfile
from credence.pipeline.cost_optimizer import evaluate_cost_profile_recommendation


@pytest.mark.unit
def test_optimizer_suggests_upgrade_on_circuit_trips():
    """Verify upgrade recommendation when node experiences frequent circuit trips."""
    rec = evaluate_cost_profile_recommendation(
        current_profile=CostProfile.ECONOMY,
        trips_last_72h=4,
        hours_throttled_last_72h=5.0,
        sifter_deferred_count=25,
    )
    assert rec.action == "UPGRADE"
    assert rec.recommended_profile == CostProfile.BALANCED
    assert rec.estimated_monthly_delta_usd > 0.0
    assert rec.confidence >= 0.85


@pytest.mark.unit
def test_optimizer_suggests_downgrade_on_chronic_idle():
    """Verify downgrade recommendation when ultra profile is under-utilized."""
    rec = evaluate_cost_profile_recommendation(
        current_profile=CostProfile.ULTRA,
        trips_last_72h=0,
        hours_throttled_last_72h=0.0,
        avg_daily_spend_usd=0.20,
    )
    assert rec.action == "DOWNGRADE"
    assert rec.recommended_profile == CostProfile.BALANCED
    assert rec.estimated_monthly_delta_usd < 0.0


@pytest.mark.unit
def test_optimizer_suggests_optimal_on_calibrated_load():
    """Verify optimal status when profile matches current spend."""
    rec = evaluate_cost_profile_recommendation(
        current_profile=CostProfile.ECONOMY,
        trips_last_72h=0,
        hours_throttled_last_72h=0.0,
        avg_daily_spend_usd=0.10,
    )
    assert rec.action == "OPTIMAL"
    assert rec.recommended_profile == CostProfile.ECONOMY
    assert rec.estimated_monthly_delta_usd == 0.0
