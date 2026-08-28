"""Unit & Red Team Suite: Evaluator State Machine, Exhaustion Policy, and Re-scoring.

Tests:
1. NodeRole transitions (EVALUATOR, SERVING, HYBRID).
2. ExhaustionStrategy transitions (HEURISTIC_FALLBACK, SERVING_MODE, DEFER).
3. Evaluator re-scoring sweep logic and headroom guard.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from credence.config import ExhaustionStrategy, NodeRole, settings
from credence.db import get_async_session, init_db
from credence.pipeline.rescore import rescore_heuristic_audits


@pytest.mark.unit
def test_node_role_and_strategy_configuration() -> None:
    """Verify NodeRole and ExhaustionStrategy enum definitions and default states."""
    assert NodeRole.EVALUATOR == "evaluator"
    assert NodeRole.SERVING == "serving"
    assert NodeRole.HYBRID == "hybrid"

    assert ExhaustionStrategy.HEURISTIC_FALLBACK == "heuristic_fallback"
    assert ExhaustionStrategy.SERVING_MODE == "serving_mode"
    assert ExhaustionStrategy.DEFER == "defer"

    # Verify versioned heuristic constants
    assert settings.HEURISTIC_ENGINE_VERSION == "v1.1.0"
    assert settings.HEURISTIC_MAX_CONFIDENCE_CEILING == 0.25


@pytest.mark.unit
@pytest.mark.asyncio
async def test_serving_mode_skips_active_rescore() -> None:
    """In SERVING role, active LLM re-scoring is skipped to conserve compute/tokens."""
    await init_db()
    original_role = settings.CREDENCE_NODE_ROLE
    try:
        settings.CREDENCE_NODE_ROLE = NodeRole.SERVING
        async with get_async_session() as session:
            rescored = await rescore_heuristic_audits(session, limit=10, force=False)
            assert rescored == []
    finally:
        settings.CREDENCE_NODE_ROLE = original_role


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rescore_heuristic_audits_governor_headroom_guard() -> None:
    """If budget headroom is exhausted, background re-scoring yields without calls."""
    await init_db()
    original_role = settings.CREDENCE_NODE_ROLE
    try:
        settings.CREDENCE_NODE_ROLE = NodeRole.EVALUATOR
        with (
            patch("credence.pipeline.rescore.get_active_api_key", return_value=("fake_key", "test")),
            patch(
                "credence.pipeline.rescore.check_budget_before_call",
                return_value=(False, "Daily spend ceiling exceeded"),
            ),
        ):
            async with get_async_session() as session:
                rescored = await rescore_heuristic_audits(session, limit=10, force=False)
                assert rescored == []
    finally:
        settings.CREDENCE_NODE_ROLE = original_role
