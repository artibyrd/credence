"""Comprehensive Unit Tests for Credence Operational Cost Profiles (FREE, BALANCED, ULTRA).

Verifies:
1. Preset configurations, pricing models, and thinking token allocations.
2. Token headroom calculations and circuit breaker tripping limits per profile.
3. Full pipeline evaluation execution under each profile.
4. FastMCP server tool execution with profile parameter overrides.
5. CLI profile commands and argument routing.
"""

import json
from typing import Any

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.cli.main import cli_profile
from credence.config import COST_PROFILES, CostProfile
from credence.ingestion.extractor import ExtractedContent
from credence.ingestion.hasher import compute_content_sha256, compute_simhash
from credence.ingestion.snapshot import DualCaptureResult
from credence.pipeline.evaluator import evaluate_snapshot
from credence.pipeline.governor import (
    check_budget_before_call,
    get_token_headroom_status,
    record_token_usage,
)
from credence.server.app import create_mcp_server


@pytest.mark.unit
def test_cost_profile_presets_structure() -> None:
    """Verify that all 5 CostProfile presets are correctly structured."""
    assert CostProfile.OFFLINE in COST_PROFILES
    assert CostProfile.FREE in COST_PROFILES
    assert CostProfile.ECONOMY in COST_PROFILES
    assert CostProfile.BALANCED in COST_PROFILES
    assert CostProfile.ULTRA in COST_PROFILES

    # Economy Profile Invariants (Default)
    econ_cfg = COST_PROFILES[CostProfile.ECONOMY]
    assert econ_cfg.max_daily_budget_usd == 0.15
    assert econ_cfg.default_thinking_budget == 512
    assert econ_cfg.escalation_thinking_budget == 1024
    assert econ_cfg.primary_model == "gemini-3.7-flash"
    assert econ_cfg.concurrency_limit == 2

    # Free Profile Invariants
    free_cfg = COST_PROFILES[CostProfile.FREE]
    assert free_cfg.max_daily_budget_usd == 0.00
    assert free_cfg.default_thinking_budget == 0
    assert free_cfg.escalation_thinking_budget == 0
    assert free_cfg.primary_model == "gemini-2.0-flash-lite"
    assert free_cfg.max_article_words == 1500
    assert free_cfg.concurrency_limit == 1

    # Balanced Profile Invariants
    bal_cfg = COST_PROFILES[CostProfile.BALANCED]
    assert bal_cfg.max_daily_budget_usd == 0.50
    assert bal_cfg.default_thinking_budget == 1024
    assert bal_cfg.escalation_thinking_budget == 4096
    assert bal_cfg.primary_model == "gemini-3.7-flash"
    assert bal_cfg.max_article_words == 3000
    assert bal_cfg.concurrency_limit == 3

    # Ultra Profile Invariants
    ultra_cfg = COST_PROFILES[CostProfile.ULTRA]
    assert ultra_cfg.max_daily_budget_usd == 5.00
    assert ultra_cfg.default_thinking_budget == 4096
    assert ultra_cfg.escalation_thinking_budget == 16384
    assert ultra_cfg.max_article_words == 10000
    assert ultra_cfg.concurrency_limit == 8
    assert ultra_cfg.enable_deep_verification is True


@pytest.mark.unit
async def test_governor_circuit_breaker_per_profile(db_session: AsyncSession) -> None:
    """Verify that token consumption limits and circuit breakers behave correctly per profile."""
    free_cfg = COST_PROFILES[CostProfile.FREE]
    bal_cfg = COST_PROFILES[CostProfile.BALANCED]
    ultra_cfg = COST_PROFILES[CostProfile.ULTRA]

    # Initial state
    free_status = await get_token_headroom_status(db_session, profile_override=free_cfg)
    assert free_status.active_profile == "free"
    assert free_status.hourly_tokens_max == 50_000

    bal_status = await get_token_headroom_status(db_session, profile_override=bal_cfg)
    assert bal_status.active_profile == "balanced"
    assert bal_status.hourly_tokens_max == 100_000

    ultra_status = await get_token_headroom_status(db_session, profile_override=ultra_cfg)
    assert ultra_status.active_profile == "ultra"
    assert ultra_status.hourly_tokens_max == 2_000_000

    # Consume 60k tokens (exceeds Free limit of 50k, but within Balanced 100k and Ultra 2M)
    await record_token_usage(
        session=db_session,
        model_name="gemini-3.7-flash",
        prompt_tokens=40_000,
        completion_tokens=20_000,
        caller="profile_tester",
    )

    # Check budget for 5k more tokens:
    # 1. FREE should reject because 60k + 5k > 50k
    free_ok, free_msg = await check_budget_before_call(db_session, estimated_tokens=5000, profile_override=free_cfg)
    assert free_ok is False

    # 2. BALANCED should allow because 60k + 5k <= 100k
    bal_ok, bal_msg = await check_budget_before_call(db_session, estimated_tokens=5000, profile_override=bal_cfg)
    assert bal_ok is True

    # 3. ULTRA should allow because 60k + 5k <= 2M
    ultra_ok, ultra_msg = await check_budget_before_call(db_session, estimated_tokens=5000, profile_override=ultra_cfg)
    assert ultra_ok is True


@pytest.mark.unit
async def test_pipeline_evaluation_under_all_three_profiles(db_session: AsyncSession) -> None:
    """Verify that evaluate_snapshot executes successfully across all 3 profiles."""
    raw_text = (
        "Either you are 100% on our side, or you are an enemy of the people! Those ignorant cowards hate progress."
    )
    extracted = ExtractedContent(
        title="Political Statement",
        clean_text=raw_text,
        byline=None,
        word_count=len(raw_text.split()),
        char_count=len(raw_text),
    )
    snapshot = DualCaptureResult(
        url="https://example.com/test-profiles",
        content_sha256=compute_content_sha256(raw_text),
        simhash_64=compute_simhash(raw_text),
        raw_html=f"<html><body><h1>Political Statement</h1><p>{raw_text}</p></body></html>",
        extracted=extracted,
    )

    # 1. Evaluate with FREE Profile
    free_report = await evaluate_snapshot(
        snapshot,
        session=db_session,
        profile_override=COST_PROFILES[CostProfile.FREE],
    )
    assert free_report.suspicion_score > 0.0
    assert free_report.node_signature is not None

    # 2. Evaluate with BALANCED Profile
    bal_report = await evaluate_snapshot(
        snapshot,
        session=db_session,
        profile_override=COST_PROFILES[CostProfile.BALANCED],
    )
    assert bal_report.suspicion_score > 0.0
    assert bal_report.classification in ("LOW_SUSPICION", "SUSPICIOUS", "DECEPTIVE")

    # 3. Evaluate with ULTRA Profile
    ultra_report = await evaluate_snapshot(
        snapshot,
        session=db_session,
        profile_override=COST_PROFILES[CostProfile.ULTRA],
    )
    assert ultra_report.suspicion_score > 0.0
    assert ultra_report.confidence_score > 0.0
    assert ultra_report.classification in ("LOW_SUSPICION", "SUSPICIOUS", "DECEPTIVE")


@pytest.mark.unit
async def test_fastmcp_tools_with_profile_overrides() -> None:
    """Verify that FastMCP tools correctly accept and execute profile overrides."""
    server = create_mcp_server()

    # 1. Quota status tool returns active profile metadata
    quota_res: Any = await server.call_tool("credence_get_quota_status", {})
    quota_data = json.loads(quota_res.content[0].text)
    assert "active_profile" in quota_data
    assert "profile_target_tier" in quota_data

    # 2. credence_evaluate_text with profile='free'
    res_free: Any = await server.call_tool(
        "credence_evaluate_text",
        {
            "text": "100% on our side, or you are an enemy of the people! Those ignorant cowards hate progress.",
            "profile": "free",
        },
    )
    data_free = json.loads(res_free.content[0].text)
    assert data_free["suspicion_score"] > 0.0

    # 3. credence_evaluate_text with profile='ultra'
    res_ultra: Any = await server.call_tool(
        "credence_evaluate_text",
        {
            "text": "100% on our side, or you are an enemy of the people! Those ignorant cowards hate progress.",
            "profile": "ultra",
        },
    )
    data_ultra = json.loads(res_ultra.content[0].text)
    assert data_ultra["suspicion_score"] > 0.0


@pytest.mark.unit
def test_cli_profile_list_and_show() -> None:
    """Verify CLI profile command outputs formatted tables without errors."""
    cli_profile("list")
    cli_profile("show", "ultra")
    cli_profile("show", "balanced")
    cli_profile("show", "free")
    cli_profile("show", "invalid_name")
