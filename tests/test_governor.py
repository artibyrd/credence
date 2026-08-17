"""Unit tests for TokenBudgetGovernor, Response Quality Gates, and Circuit Breaker."""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import settings
from credence.pipeline.governor import (
    calculate_call_cost,
    check_budget_before_call,
    evaluate_quality_and_should_escalate,
    get_active_api_key,
    get_token_headroom_status,
    record_token_usage,
)
from credence.pipeline.schemas import SpecialistViolationFinding


@pytest.mark.unit
def test_calculate_call_cost_with_thinking_tokens() -> None:
    """Verify call cost estimation calculates prompt, completion, and thinking tokens."""
    # gemini-3.7-flash: prompt $0.15/1M, completion $0.60/1M, thinking $0.60/1M
    cost = calculate_call_cost(
        model_name="gemini-3.7-flash",
        prompt_tokens=10_000,  # 0.0015
        completion_tokens=1_000,  # 0.0006
        thinking_tokens=2_000,  # 0.0012
    )
    # Total = 0.0015 + 0.0006 + 0.0012 = 0.0033
    assert cost == 0.0033


@pytest.mark.unit
async def test_record_and_query_token_headroom(db_session: AsyncSession) -> None:
    """Verify token usage recording and headroom calculation from database records."""
    status_initial = await get_token_headroom_status(db_session)
    assert status_initial.hourly_tokens_used == 0
    assert status_initial.hourly_headroom_pct == 100.0
    assert status_initial.circuit_breaker_tripped is False

    # Record usage
    await record_token_usage(
        session=db_session,
        model_name="gemini-3.7-flash",
        prompt_tokens=20_000,
        completion_tokens=5_000,
        thinking_tokens=5_000,
        caller="spj_ethics_auditor",
    )

    status_updated = await get_token_headroom_status(db_session)
    assert status_updated.hourly_tokens_used == 30_000
    assert status_updated.hourly_headroom_pct == 70.0  # 100k max -> 70% headroom remaining
    assert status_updated.daily_spend_usd > 0.0


@pytest.mark.unit
async def test_circuit_breaker_tripping(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify circuit breaker trips and prevents API calls when hourly or daily limits are exceeded."""
    monkeypatch.setattr(settings, "MAX_TOKENS_PER_HOUR", 10_000)

    # Within budget
    ok, msg = await check_budget_before_call(db_session, estimated_tokens=2_000)
    assert ok is True
    assert msg == "BUDGET_AVAILABLE"

    # Burn tokens exceeding hourly limit
    await record_token_usage(
        session=db_session,
        model_name="gemini-3.7-flash",
        prompt_tokens=8_000,
        completion_tokens=3_000,
        caller="stress_test",
    )

    # Next check should be rejected by circuit breaker
    ok_after, msg_after = await check_budget_before_call(db_session, estimated_tokens=2_000)
    assert ok_after is False
    assert "TRIPPED" in msg_after or "safety ceiling" in msg_after


@pytest.mark.unit
def test_quality_gate_evaluation() -> None:
    """Verify quality gate triggers escalation on low grounded ratio, low confidence, or boundary score."""
    # Case 1: High quality grounded response
    v_grounded = SpecialistViolationFinding(
        rule_id="SPJ-1.1",
        rule_uri="journalistic-ethics:seek-truth/SPJ-1.1@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="SEEK_TRUTH",
        severity=3,
        confidence=0.95,
        quote_or_element="Grounded quote from article.",
        reasoning="Reasoning.",
        is_grounded=True,
    )
    should_esc, _ = evaluate_quality_and_should_escalate([v_grounded], confidence=0.95, suspicion_score=5.0)
    assert should_esc is False

    # Case 2: Hallucinated / ungrounded citations (<75% grounded)
    v_ungrounded = SpecialistViolationFinding(
        rule_id="SPJ-1.2",
        rule_uri="journalistic-ethics:seek-truth/SPJ-1.2@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="SEEK_TRUTH",
        severity=4,
        confidence=0.9,
        quote_or_element="Hallucinated fake quote.",
        reasoning="Reasoning.",
        is_grounded=False,
    )
    should_esc_hallucination, reason = evaluate_quality_and_should_escalate(
        [v_grounded, v_ungrounded, v_ungrounded],  # 1/3 = 33% grounded < 75%
        confidence=0.95,
        suspicion_score=35.0,
    )
    assert should_esc_hallucination is True
    assert "Low grounded citation ratio" in reason

    # Case 3: Low confidence (<0.80)
    should_esc_conf, reason_conf = evaluate_quality_and_should_escalate(
        [v_grounded], confidence=0.65, suspicion_score=5.0
    )
    assert should_esc_conf is True
    assert "confidence low" in reason_conf

    # Case 4: Ambiguous decision boundary (12.0 - 18.0)
    should_esc_bound, reason_bound = evaluate_quality_and_should_escalate(
        [v_grounded], confidence=0.90, suspicion_score=15.2
    )
    assert should_esc_bound is True
    assert "ambiguous decision boundary" in reason_bound


@pytest.mark.unit
def test_active_api_key_prioritization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify CREDENCE_GEMINI_API_KEY is prioritized over general GEMINI_API_KEY."""
    monkeypatch.setattr(settings, "CREDENCE_GEMINI_API_KEY", "credence-isolated-key-123")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "general-dev-key-456")

    key, source = get_active_api_key()
    assert key == "credence-isolated-key-123"
    assert source == "CREDENCE_GEMINI_API_KEY"

    # Fallback to general if isolated not provided
    monkeypatch.setattr(settings, "CREDENCE_GEMINI_API_KEY", None)
    key_fb, source_fb = get_active_api_key()
    assert key_fb == "general-dev-key-456"
    assert source_fb == "GEMINI_API_KEY"
