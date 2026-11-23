"""Unit tests for Cost Profiles and the ECONOMY default configuration."""

from __future__ import annotations

import pytest

from credence.config import COST_PROFILES, CostProfile, Settings


@pytest.mark.unit
def test_cost_profile_enum_values():
    """Verify all 5 cost profiles are defined."""
    assert CostProfile.OFFLINE.value == "offline"
    assert CostProfile.FREE.value == "free"
    assert CostProfile.ECONOMY.value == "economy"
    assert CostProfile.BALANCED.value == "balanced"
    assert CostProfile.ULTRA.value == "ultra"


@pytest.mark.unit
def test_economy_profile_is_default():
    """Verify that Settings defaults to ECONOMY profile aligned with Gemini 3.8 Flash."""
    s = Settings()
    assert s.CREDENCE_PROFILE == CostProfile.ECONOMY
    assert s.DEFAULT_SPECIALIST_MODEL == "gemini-3.8-flash"
    assert s.DEFAULT_TRIAGE_MODEL == "gemini-3.8-flash"
    assert s.DEFAULT_WORKER_MODEL == "google/gemini-3.8-flash"

    cfg = s.get_profile_config()
    assert cfg.profile == CostProfile.ECONOMY
    assert cfg.primary_model == "gemini-3.8-flash"
    assert cfg.escalation_model == "gemini-3.8-flash"
    assert cfg.triage_model == "gemini-3.8-flash"
    assert cfg.default_thinking_level == "low"
    assert cfg.escalation_thinking_level == "low"
    assert cfg.triage_thinking_level == "minimal"
    assert cfg.default_thinking_budget == 512
    assert cfg.max_daily_budget_usd == 0.15


@pytest.mark.unit
def test_all_cost_profiles_configured():
    """Verify each profile has valid token, thinkingLevel, and spend ceilings."""
    valid_levels = {"minimal", "low", "medium", "high"}
    for prof in CostProfile:
        cfg = COST_PROFILES[prof]
        assert cfg.profile == prof
        assert cfg.max_daily_budget_usd >= 0.0
        assert cfg.max_tokens_per_hour > 0
        assert cfg.max_tokens_per_day > 0
        assert cfg.concurrency_limit >= 1
        assert cfg.default_thinking_level in valid_levels
        assert cfg.escalation_thinking_level in valid_levels
        assert cfg.triage_thinking_level in valid_levels
