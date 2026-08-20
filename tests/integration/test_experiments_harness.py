"""Hermetic unit tests for Bicameral Experiments, Shadow Auditing, and Federation Bridging."""

from __future__ import annotations

from pathlib import Path

import pytest

from credence.experiments.env_verifier import (
    InstanceTelemetry,
    verify_telemetry_invariants,
)
from credence.experiments.federation_bridge import FederationBridgeHarness
from credence.experiments.shadow_audit import run_shadow_audit


@pytest.mark.integration
def test_env_verifier_valid_configuration():
    """Verify that correctly separated Dev and Prod configurations pass the verification gate."""
    dev = InstanceTelemetry(
        target_url="http://localhost:8000",
        is_live=True,
        env_name="development",
        cost_profile="economy",
        primary_model="gemini-2.5-flash-lite",
        default_thinking_budget=512,
        escalation_thinking_budget=1024,
        storage_backend="local",
        node_pubkey="aaaa1111222233334444555566667777888899990000aaaabbbbccccddddeeee0001",
    )
    prod = InstanceTelemetry(
        target_url="https://credence-server.run.app",
        is_live=True,
        env_name="production",
        cost_profile="balanced",
        primary_model="gemini-3.7-flash",
        default_thinking_budget=4096,
        escalation_thinking_budget=16384,
        storage_backend="s3",
        node_pubkey="bbbb1111222233334444555566667777888899990000aaaabbbbccccddddeeee0002",
    )

    report = verify_telemetry_invariants(dev, prod)
    assert report.is_valid is True
    assert len(report.violations) == 0


@pytest.mark.integration
def test_env_verifier_catches_pubkey_collision():
    """Verify that key reuse between Dev and Prod triggers an invariant violation."""
    shared_key = "aaaa1111222233334444555566667777888899990000aaaabbbbccccddddeeee0001"
    dev = InstanceTelemetry(
        target_url="http://localhost:8000",
        is_live=True,
        cost_profile="economy",
        node_pubkey=shared_key,
    )
    prod = InstanceTelemetry(
        target_url="https://credence-server.run.app",
        is_live=True,
        cost_profile="balanced",
        node_pubkey=shared_key,
    )

    report = verify_telemetry_invariants(dev, prod)
    assert report.is_valid is False
    assert any(v.invariant_id == "INV-03-PUBKEY-COLLISION" for v in report.violations)


@pytest.mark.integration
def test_env_verifier_catches_offline_instance():
    """Verify that unreachable instances trigger offline invariant violations."""
    dev = InstanceTelemetry(target_url="http://localhost:8000", is_live=False)
    prod = InstanceTelemetry(target_url="https://credence-server.run.app", is_live=True)

    report = verify_telemetry_invariants(dev, prod)
    assert report.is_valid is False
    assert any(v.invariant_id == "INV-01-DEV-OFFLINE" for v in report.violations)


@pytest.mark.integration
def test_shadow_audit_differential_calculation():
    """Verify that shadow audit calculates differential metrics over fixtures."""
    fixtures_dir = Path("tests/fixtures/html")
    report = run_shadow_audit(fixtures_dir=fixtures_dir)

    assert report.total_fixtures == 12
    assert report.average_divergence >= 0.0
    assert report.total_prod_monolithic_cost_usd > 0.0
    assert report.total_cascaded_bicameral_cost_usd > 0.0
    assert report.finops_cost_savings_pct > 0.0
    assert len(report.items) == 12


@pytest.mark.integration
def test_federation_bridge_simulation():
    """Verify that federation bridge simulates attestation signing, HRW routing, and Byzantine isolation."""
    harness = FederationBridgeHarness()
    result = harness.run_bridge_simulation(feed_count=20)

    assert result.is_healthy is True
    assert result.signature_verifications_passed == 20
    assert result.byzantine_faults_isolated == 1
    assert result.hrw_distribution_balance >= 0.40
    assert result.consensus_rate_pct == 100.0
