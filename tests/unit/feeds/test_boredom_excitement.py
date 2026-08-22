from datetime import datetime, timedelta, timezone

import pytest

from credence.feeds.boredom import ExcitementMode, compute_curiosity_excitement


@pytest.mark.unit
def test_excitement_mode_cold_node_hyper_excited() -> None:
    """Verify cold node with high headroom enters HYPER_EXCITED mode with burst 5."""
    now = datetime.now(timezone.utc)
    decision = compute_curiosity_excitement(
        total_audits=10,
        daily_headroom_pct=100.0,
        last_audit_time=now - timedelta(minutes=5),
        now=now,
    )
    assert decision.mode == ExcitementMode.HYPER_EXCITED.value
    assert decision.should_audit is True
    assert decision.audit_burst == 5
    assert decision.expand_roots_appetite == 3
    assert decision.excitement_score > 0.8


@pytest.mark.unit
def test_excitement_mode_maturing_node_active_burst() -> None:
    """Verify maturing node (100 audits) enters ACTIVE_BURST mode with burst 3."""
    now = datetime.now(timezone.utc)
    decision = compute_curiosity_excitement(
        total_audits=100,
        daily_headroom_pct=60.0,
        last_audit_time=now - timedelta(minutes=10),
        now=now,
    )
    assert decision.mode == ExcitementMode.ACTIVE_BURST.value
    assert decision.should_audit is True
    assert decision.audit_burst == 3
    assert decision.expand_roots_appetite == 1


@pytest.mark.unit
def test_excitement_mode_established_node_backoff() -> None:
    """Verify established node (250 audits) with recent audit (<30m) enters ADAPTIVE_BACKOFF."""
    now = datetime.now(timezone.utc)
    decision = compute_curiosity_excitement(
        total_audits=250,
        daily_headroom_pct=80.0,
        last_audit_time=now - timedelta(minutes=10),
        now=now,
    )
    assert decision.mode == ExcitementMode.ADAPTIVE_BACKOFF.value
    assert decision.should_audit is False
    assert decision.audit_burst == 0


@pytest.mark.unit
def test_excitement_mode_established_node_maintenance_window() -> None:
    """Verify established node (250 audits) past 30m window enters STEADY_MAINTENANCE."""
    now = datetime.now(timezone.utc)
    decision = compute_curiosity_excitement(
        total_audits=250,
        daily_headroom_pct=80.0,
        last_audit_time=now - timedelta(minutes=35),
        now=now,
    )
    assert decision.mode == ExcitementMode.STEADY_MAINTENANCE.value
    assert decision.should_audit is True
    assert decision.audit_burst == 2


@pytest.mark.unit
def test_excitement_mode_low_headroom_quota_preserved() -> None:
    """Verify headroom below 30% trips circuit breaker regardless of volume."""
    now = datetime.now(timezone.utc)
    decision = compute_curiosity_excitement(
        total_audits=5,
        daily_headroom_pct=25.0,
        last_audit_time=now - timedelta(minutes=10),
        now=now,
    )
    assert decision.mode == ExcitementMode.QUOTA_PRESERVED.value
    assert decision.should_audit is False
    assert decision.audit_burst == 0
