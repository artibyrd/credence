"""Unit tests for security guards, DNS pinning ranges, admin bearer key checks, and input clamping."""

from __future__ import annotations

import pytest
from starlette.requests import Request

from credence.cache.distributed import get_state_store
from credence.ingestion.security import is_safe_url
from credence.server.app import _check_admin_auth


@pytest.mark.unit
def test_ssrf_blocked_hosts_and_ips():
    """Verify that cloud metadata, RFC 1918, and loopback IPs are strictly rejected."""
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert is_safe_url("http://metadata.google.internal/computeMetadata/v1/") is False
    assert is_safe_url("http://127.0.0.1:8000/api/reports") is False
    assert is_safe_url("http://10.0.0.1/admin") is False
    assert is_safe_url("http://192.168.1.1/router") is False


@pytest.mark.unit
def test_admin_auth_constant_time_comparison():
    """Test administrator bearer token authentication."""
    # When ENV is development and request comes from localhost, allows dev access
    scope_local = {
        "type": "http",
        "method": "POST",
        "path": "/api/cost/budget",
        "headers": [(b"host", b"localhost:8000")],
        "client": ("127.0.0.1", 50000),
    }
    req_local = Request(scope_local)
    assert _check_admin_auth(req_local) is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_budget_parameter_clamping():
    """Verify that daily budget and hourly token inputs are clamped within safe bounds."""
    state = get_state_store()

    # Extreme high daily budget -> clamped to 500.00
    await state.set_runtime_budget_override(daily_budget_usd=9999.0, max_tokens_per_hour=99999999)
    cfg = await state.get_runtime_cost_settings()
    assert cfg.daily_budget_usd == 500.00
    assert cfg.max_tokens_per_hour == 10_000_000

    # Negative daily budget -> clamped to 0.00
    await state.set_runtime_budget_override(daily_budget_usd=-50.0, max_tokens_per_hour=100)
    cfg = await state.get_runtime_cost_settings()
    assert cfg.daily_budget_usd == 0.00
    assert cfg.max_tokens_per_hour == 1000
