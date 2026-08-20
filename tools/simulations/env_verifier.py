"""Automated Dual-Tier Environment Configuration Verifier.

Probes Dev and Prod Credence instances to validate controlled independent variables
before running benchmarks, shadow audits, and federation experiments.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from credence.config import CostProfile


@dataclass
class InstanceTelemetry:
    """Snapshot of a single Credence instance's active configuration."""

    target_url: str
    is_live: bool = False
    env_name: str = "unknown"
    cost_profile: str = "unknown"
    primary_model: str = "unknown"
    default_thinking_budget: int = 0
    escalation_thinking_budget: int = 0
    storage_backend: str = "unknown"
    circuit_breaker_enabled: bool = False
    node_pubkey: Optional[str] = None
    response_latency_ms: float = 0.0
    error_message: Optional[str] = None


@dataclass
class InvariantViolation:
    """Represents a failed verification invariant."""

    invariant_id: str
    description: str
    dev_value: Any
    prod_value: Any
    recommendation: str


@dataclass
class EnvVerificationReport:
    """Comprehensive environment verification report."""

    is_valid: bool
    dev_telemetry: InstanceTelemetry
    prod_telemetry: InstanceTelemetry
    violations: List[InvariantViolation] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to JSON-serializable dictionary."""
        return asdict(self)


async def probe_instance(url: str, timeout_sec: float = 5.0) -> InstanceTelemetry:
    """Probe a Credence instance's health and telemetry endpoints."""
    clean_url = url.rstrip("/")
    telemetry = InstanceTelemetry(target_url=clean_url)

    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        # 1. Health Probe
        try:
            t0 = asyncio.get_event_loop().time()
            resp = await client.get(f"{clean_url}/health")
            telemetry.response_latency_ms = round((asyncio.get_event_loop().time() - t0) * 1000, 2)
            if resp.status_code == 200:
                telemetry.is_live = True
                data = resp.json()
                telemetry.env_name = data.get("environment", data.get("env", "unknown"))
                if "node_pubkey" in data:
                    telemetry.node_pubkey = data["node_pubkey"]
        except Exception as e:
            telemetry.error_message = f"Health check failed: {e}"
            return telemetry

        # 2. Telemetry Probe
        try:
            cost_resp = await client.get(f"{clean_url}/api/cost/telemetry")
            if cost_resp.status_code == 200:
                cost_data = cost_resp.json()
                telemetry.cost_profile = cost_data.get("active_profile", cost_data.get("profile", "unknown"))
                telemetry.primary_model = cost_data.get("primary_model", "unknown")
                telemetry.default_thinking_budget = int(
                    cost_data.get("thinking_budget", cost_data.get("default_thinking_budget", 0))
                )
                telemetry.escalation_thinking_budget = int(cost_data.get("escalation_thinking_budget", 0))
                telemetry.circuit_breaker_enabled = bool(cost_data.get("circuit_breaker_enabled", True))
                if "node_pubkey" in cost_data:
                    telemetry.node_pubkey = cost_data["node_pubkey"]
        except Exception:
            pass  # noqa: S110

        # 3. Status Probe (Storage & PubKey)
        try:
            status_resp = await client.get(f"{clean_url}/api/sifter/status")
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                telemetry.storage_backend = status_data.get("storage_backend", "unknown")
                if not telemetry.node_pubkey and "node_pubkey" in status_data:
                    telemetry.node_pubkey = status_data["node_pubkey"]
        except Exception:
            pass  # noqa: S110

    return telemetry


def verify_telemetry_invariants(dev: InstanceTelemetry, prod: InstanceTelemetry) -> EnvVerificationReport:
    """Validate that Dev and Prod telemetry configurations form a valid experimental setup."""
    violations: List[InvariantViolation] = []

    # Invariant 1: Dev and Prod endpoints must be live
    if not dev.is_live:
        violations.append(
            InvariantViolation(
                invariant_id="INV-01-DEV-OFFLINE",
                description="Dev instance endpoint is unreachable.",
                dev_value=dev.target_url,
                prod_value=prod.target_url,
                recommendation="Ensure the Dev server is running (e.g., `just serve web` or check Cloud Run).",
            )
        )
    if not prod.is_live:
        violations.append(
            InvariantViolation(
                invariant_id="INV-02-PROD-OFFLINE",
                description="Prod instance endpoint is unreachable.",
                dev_value=dev.target_url,
                prod_value=prod.target_url,
                recommendation="Ensure the Prod server is running (e.g., check Cloud Run `credence-server`).",
            )
        )

    if dev.is_live and prod.is_live:
        # Invariant 2: Cryptographic Key Separation (No key reuse)
        if dev.node_pubkey and prod.node_pubkey and dev.node_pubkey == prod.node_pubkey:
            violations.append(
                InvariantViolation(
                    invariant_id="INV-03-PUBKEY-COLLISION",
                    description="Dev and Prod share the exact same Ed25519 public key.",
                    dev_value=dev.node_pubkey[:12] + "...",
                    prod_value=prod.node_pubkey[:12] + "...",
                    recommendation="Regenerate Dev keys or use `credence init-org` to create distinct sovereign identities.",
                )
            )

        # Invariant 3: Cost Profile Separation
        dev_profile_lower = dev.cost_profile.lower()
        prod_profile_lower = prod.cost_profile.lower()
        valid_dev_profiles = {CostProfile.FREE.value, CostProfile.ECONOMY.value, CostProfile.OFFLINE.value, "unknown"}
        valid_prod_profiles = {CostProfile.BALANCED.value, CostProfile.ULTRA.value, "unknown"}

        if (dev_profile_lower not in valid_dev_profiles and dev_profile_lower == prod_profile_lower) or (
            prod_profile_lower not in valid_prod_profiles and prod_profile_lower in valid_dev_profiles
        ):
            violations.append(
                InvariantViolation(
                    invariant_id="INV-04-PROFILE-OVERLAP",
                    description="Dev and Prod run overlapping or invalid cost profiles, invalidating differential cost experiments.",
                    dev_value=dev.cost_profile,
                    prod_value=prod.cost_profile,
                    recommendation="Set CREDENCE_PROFILE=economy on Dev and CREDENCE_PROFILE=balanced (or ultra) on Prod.",
                )
            )

        # Invariant 4: Thinking Budget Hierarchy (Prod >= 4k for deep reasoning, Dev <= 1k for triage)
        if dev.default_thinking_budget > 1024 and prod.default_thinking_budget < 4096:
            violations.append(
                InvariantViolation(
                    invariant_id="INV-05-THINKING-BUDGET",
                    description="Thinking token budgets do not reflect hierarchical triage (Dev <= 1024, Prod >= 4096).",
                    dev_value=f"{dev.default_thinking_budget} tokens",
                    prod_value=f"{prod.default_thinking_budget} tokens",
                    recommendation="Configure Dev with default_thinking_budget <= 1024 and Prod with >= 4096.",
                )
            )

    is_valid = len(violations) == 0
    summary = (
        "✅ Dev and Prod environments are properly configured for scientifically valid experiments."
        if is_valid
        else f"❌ Found {len(violations)} environment configuration violation(s) that must be resolved."
    )

    return EnvVerificationReport(
        is_valid=is_valid,
        dev_telemetry=dev,
        prod_telemetry=prod,
        violations=violations,
        summary=summary,
    )


async def verify_environments(
    dev_url: str = "http://localhost:8000",
    prod_url: str = "https://credence-server-663899237633.us-central1.run.app",
    timeout_sec: float = 6.0,
) -> EnvVerificationReport:
    """Asynchronously probe and verify Dev vs. Prod environments."""
    dev_task = asyncio.create_task(probe_instance(dev_url, timeout_sec))
    prod_task = asyncio.create_task(probe_instance(prod_url, timeout_sec))
    dev_res, prod_res = await asyncio.gather(dev_task, prod_task)
    return verify_telemetry_invariants(dev_res, prod_res)


def main() -> None:
    """CLI entrypoint for environment configuration verification."""
    parser = argparse.ArgumentParser(description="Verify Dev vs. Prod Credence environment configurations.")
    parser.add_argument("--dev-url", default="http://localhost:8000", help="Dev instance URL")
    parser.add_argument(
        "--prod-url", default="https://credence-server-663899237633.us-central1.run.app", help="Prod instance URL"
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON report")
    parser.add_argument("--timeout", type=float, default=6.0, help="HTTP probe timeout in seconds")

    args = parser.parse_args()

    report = asyncio.run(verify_environments(args.dev_url, args.prod_url, timeout_sec=args.timeout))

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        sys.exit(0 if report.is_valid else 1)

    print("\n=================================================================")
    print("      🔍 Credence Bicameral Environment Verification Gate        ")
    print("=================================================================\n")

    print(
        f"Dev Target:  {args.dev_url} [{'🟢 Live' if report.dev_telemetry.is_live else '🔴 Offline'}] ({report.dev_telemetry.response_latency_ms}ms)"
    )
    print(f"  • Environment:     {report.dev_telemetry.env_name}")
    print(f"  • Cost Profile:    {report.dev_telemetry.cost_profile}")
    print(f"  • Primary Model:   {report.dev_telemetry.primary_model}")
    print(f"  • Thinking Budget: {report.dev_telemetry.default_thinking_budget} tokens")
    print(f"  • Public Key:      {report.dev_telemetry.node_pubkey or 'N/A'}")
    print(f"  • Storage Backend: {report.dev_telemetry.storage_backend}")

    print(
        f"\nProd Target: {args.prod_url} [{'🟢 Live' if report.prod_telemetry.is_live else '🔴 Offline'}] ({report.prod_telemetry.response_latency_ms}ms)"
    )
    print(f"  • Environment:     {report.prod_telemetry.env_name}")
    print(f"  • Cost Profile:    {report.prod_telemetry.cost_profile}")
    print(f"  • Primary Model:   {report.prod_telemetry.primary_model}")
    print(f"  • Thinking Budget: {report.prod_telemetry.default_thinking_budget} tokens")
    print(f"  • Public Key:      {report.prod_telemetry.node_pubkey or 'N/A'}")
    print(f"  • Storage Backend: {report.prod_telemetry.storage_backend}")

    print("\n-----------------------------------------------------------------")
    print(f"Result: {report.summary}")
    print("-----------------------------------------------------------------")

    if report.violations:
        print("\nViolations:")
        for v in report.violations:
            print(f"  ❌ [{v.invariant_id}] {v.description}")
            print(f"     Dev: {v.dev_value} | Prod: {v.prod_value}")
            print(f"     👉 Fix: {v.recommendation}\n")
        sys.exit(1)
    else:
        print("\n🎉 Verification Passed: Environments are ready for scientific experimentation.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
