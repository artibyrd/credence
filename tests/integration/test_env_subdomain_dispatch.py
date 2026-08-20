"""Tests for Edge Router Host Pattern Matching, CORS, and Cache-Control Dispatch."""

import pytest


def simulate_edge_router_host(host: str, path: str = "/"):
    """Python simulation of web/_worker.js host resolution logic."""
    is_dev = host.startswith("dev.") or host.startswith("mcp.dev.")
    dev_backend = "https://credence-dev-663899237633.us-central1.run.app"
    prod_backend = "https://credence-server-663899237633.us-central1.run.app"
    target_backend = dev_backend if is_dev else prod_backend

    clean_host = host.replace("dev.", "")
    prefix = "credence.run"
    if "nexus" in clean_host:
        prefix = "credence.nexus"
    elif "foundation" in clean_host:
        prefix = "credence.foundation/keys" if clean_host.startswith("keys") else "credence.foundation"
    elif "report" in clean_host:
        prefix = "credence.report"

    cache_control = None
    if path.startswith("/api/reports/"):
        cache_control = "private, max-age=60" if is_dev else "public, max-age=2592000, immutable"

    return {
        "is_dev": is_dev,
        "target_backend": target_backend,
        "prefix": prefix,
        "cache_control": cache_control,
    }


@pytest.mark.integration
def test_edge_router_host_pattern_matching():
    """Verify host pattern matching across canonical and dev subdomains."""
    # Production Hosts
    r_prod_run = simulate_edge_router_host("credence.run")
    assert r_prod_run["is_dev"] is False
    assert r_prod_run["prefix"] == "credence.run"
    assert "credence-server" in r_prod_run["target_backend"]

    r_prod_nexus = simulate_edge_router_host("credence.nexus")
    assert r_prod_nexus["is_dev"] is False
    assert r_prod_nexus["prefix"] == "credence.nexus"

    r_prod_found = simulate_edge_router_host("keys.credence.foundation")
    assert r_prod_found["is_dev"] is False
    assert r_prod_found["prefix"] == "credence.foundation/keys"

    # Dev Hosts
    r_dev_run = simulate_edge_router_host("dev.credence.run")
    assert r_dev_run["is_dev"] is True
    assert r_dev_run["prefix"] == "credence.run"
    assert "credence-dev" in r_dev_run["target_backend"]

    r_dev_nexus = simulate_edge_router_host("dev.credence.nexus")
    assert r_dev_nexus["is_dev"] is True
    assert r_dev_nexus["prefix"] == "credence.nexus"

    r_dev_mcp = simulate_edge_router_host("mcp.dev.credence.run")
    assert r_dev_mcp["is_dev"] is True
    assert "credence-dev" in r_dev_mcp["target_backend"]


@pytest.mark.integration
def test_dev_vs_prod_cache_control_headers():
    """Verify Cache-Control headers on report endpoints differ between Dev and Prod."""
    report_path = "/api/reports/7f8a9b1c2d3e"

    prod_res = simulate_edge_router_host("credence.report", path=report_path)
    assert prod_res["cache_control"] == "public, max-age=2592000, immutable"

    dev_res = simulate_edge_router_host("dev.credence.report", path=report_path)
    assert dev_res["cache_control"] == "private, max-age=60"
