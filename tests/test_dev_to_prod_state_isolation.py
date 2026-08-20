"""Integration tests verifying state isolation between Dev and Prod configurations."""

import pytest

from credence.cache.distributed import DistributedStateStore


@pytest.mark.integration
@pytest.mark.asyncio
async def test_parallel_client_state_isolation():
    """Verify separate state stores maintain independent counters and overrides."""
    dev_state = DistributedStateStore(redis_url=None)  # In-memory dev
    prod_state = DistributedStateStore(redis_url=None)  # In-memory prod

    # Set daily budget in dev
    await dev_state.set_runtime_budget_override(daily_budget_usd=0.15)
    # Set daily budget in prod
    await prod_state.set_runtime_budget_override(daily_budget_usd=5.00)

    dev_settings = await dev_state.get_runtime_cost_settings()
    prod_settings = await prod_state.get_runtime_cost_settings()

    assert dev_settings.daily_budget_usd == 0.15
    assert prod_settings.daily_budget_usd == 5.00


@pytest.mark.integration
@pytest.mark.asyncio
async def test_emergency_brake_isolation():
    """Verify emergency brake in one store does not affect another."""
    dev_state = DistributedStateStore(redis_url=None)
    prod_state = DistributedStateStore(redis_url=None)

    await dev_state.pull_emergency_brake()
    dev_settings = await dev_state.get_runtime_cost_settings()
    prod_settings = await prod_state.get_runtime_cost_settings()

    assert dev_settings.emergency_brake_pulled is True
    assert prod_settings.emergency_brake_pulled is False

    await dev_state.release_emergency_brake()
    dev_settings_released = await dev_state.get_runtime_cost_settings()
    assert dev_settings_released.emergency_brake_pulled is False
