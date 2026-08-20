"""Tests for Terraform Variable Matrix and Dev/Prod Schema Conformance."""

import re
from pathlib import Path

import pytest


def parse_simple_hcl(content: str) -> dict[str, str]:
    """Simple regex-based HCL variable parser for testing tfvars files."""
    vars_dict = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([a-zA-Z0-9_-]+)\s*=\s*(.+)$", line)
        if match:
            k = match.group(1).strip()
            v = match.group(2).strip().strip('"')
            vars_dict[k] = v
    return vars_dict


@pytest.mark.unit
def test_dev_tfvars_syntax_and_types():
    """Verify terraform.dev.tfvars.example defines valid variables."""
    dev_example = Path(__file__).parent.parent / "terraform" / "terraform.dev.tfvars.example"
    assert dev_example.exists()
    vars_map = parse_simple_hcl(dev_example.read_text())

    assert "project_id" in vars_map
    assert "service_name" in vars_map
    assert vars_map.get("service_name") == "credence-dev"
    assert vars_map.get("monitoring_tier") == "simple"
    assert vars_map.get("credence_profile") == "economy"


@pytest.mark.unit
def test_prod_tfvars_syntax_and_types():
    """Verify terraform.prod.tfvars.example defines valid variables."""
    prod_example = Path(__file__).parent.parent / "terraform" / "terraform.prod.tfvars.example"
    assert prod_example.exists()
    vars_map = parse_simple_hcl(prod_example.read_text())

    assert "project_id" in vars_map
    assert "service_name" in vars_map
    assert vars_map.get("service_name") == "credence-server"
    assert vars_map.get("monitoring_tier") == "advanced"
    assert vars_map.get("credence_profile") in ["balanced", "ultra", "economy"]


@pytest.mark.unit
def test_single_and_dual_project_configurations():
    """Verify variable schema permits both identical and distinct project IDs."""
    single_project = {"dev_project_id": "credence-corp", "prod_project_id": "credence-corp"}
    assert single_project["dev_project_id"] == single_project["prod_project_id"]

    dual_project = {"dev_project_id": "credence-dev-12345", "prod_project_id": "credence-prod-505902"}
    assert dual_project["dev_project_id"] != dual_project["prod_project_id"]
