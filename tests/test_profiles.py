"""Unit tests for Credence Operational Cost Profiles."""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.cli.main import cli_profile
from credence.config import COST_PROFILES, CostProfile
from credence.pipeline.governor import (
    check_budget_before_call,
    get_token_headroom_status,
)


@pytest.mark.unit
def test_cost_profile_presets_structure() -> None:
    """Verify that all 3 CostProfile presets are correctly structured."""
    assert CostProfile.FREE in COST_PROFILES
    assert CostProfile.BALANCED in COST_PROFILES
    assert CostProfile.ULTRA in COST_PROFILES

    # Free Profile Invariants
    free_cfg = COST_PROFILES[CostProfile.FREE]
    assert free_cfg.max_daily_budget_usd == 0.00
    assert free_cfg.default_thinking_budget == 0
    assert free_cfg.escalation_thinking_budget == 0
    assert free_cfg.primary_model == "gemini-2.0-flash-lite"
    assert free_cfg.concurrency_limit == 1

    # Balanced Profile Invariants
    bal_cfg = COST_PROFILES[CostProfile.BALANCED]
    assert bal_cfg.max_daily_budget_usd == 0.50
    assert bal_cfg.default_thinking_budget == 1024
    assert bal_cfg.primary_model == "gemini-3.7-flash"

    # Ultra Profile Invariants
    ultra_cfg = COST_PROFILES[CostProfile.ULTRA]
    assert ultra_cfg.max_daily_budget_usd == 15.00
    assert ultra_cfg.default_thinking_budget == 4096
    assert ultra_cfg.escalation_thinking_budget == 16384
    assert ultra_cfg.max_article_words == 10000
    assert ultra_cfg.enable_deep_verification is True


@pytest.mark.unit
async def test_governor_with_free_profile_override(db_session: AsyncSession) -> None:
    """Verify that the Free profile enforces 0 thinking tokens and lower token caps."""
    free_cfg = COST_PROFILES[CostProfile.FREE]
    status = await get_token_headroom_status(db_session, profile_override=free_cfg)

    assert status.active_profile == "free"
    assert status.daily_budget_usd == 0.00
    assert status.hourly_tokens_max == 50_000
    assert status.daily_tokens_max == 250_000


@pytest.mark.unit
async def test_governor_with_ultra_profile_override(db_session: AsyncSession) -> None:
    """Verify that the Ultra profile allocates massive token headroom and $15 budget."""
    ultra_cfg = COST_PROFILES[CostProfile.ULTRA]
    status = await get_token_headroom_status(db_session, profile_override=ultra_cfg)

    assert status.active_profile == "ultra"
    assert status.daily_budget_usd == 15.00
    assert status.hourly_tokens_max == 2_000_000
    assert status.daily_tokens_max == 20_000_000

    # Ultra can handle large requests without tripping
    budget_ok, reason = await check_budget_before_call(db_session, estimated_tokens=50000, profile_override=ultra_cfg)
    assert budget_ok is True


@pytest.mark.unit
def test_cli_profile_list_and_show(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI profile command outputs formatted tables without errors."""
    cli_profile("list")
    cli_profile("show", "ultra")
    cli_profile("show", "free")
    cli_profile("show", "invalid_name")
