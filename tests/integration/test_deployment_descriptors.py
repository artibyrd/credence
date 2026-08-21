"""Shift-left Integration Tests for Deployment Descriptors & Presets."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_docker_compose_descriptors_parity():
    """Verify docker-compose.yml and docker-compose.prod.yml declare sovereign backup and daemon env vars."""
    compose_basic = REPO_ROOT / "docker-compose.yml"
    compose_prod = REPO_ROOT / "docker-compose.prod.yml"

    assert compose_basic.exists()
    assert compose_prod.exists()

    basic_data = yaml.safe_load(compose_basic.read_text(encoding="utf-8"))
    prod_data = yaml.safe_load(compose_prod.read_text(encoding="utf-8"))

    basic_env = basic_data["services"]["credence"]["environment"]
    prod_env = prod_data["services"]["credence"]["environment"]

    # Basic env checks
    assert any("CREDENCE_BACKUP_ENABLED=true" in e for e in basic_env)
    assert any("CREDENCE_BOREDOM_ENABLED=true" in e for e in basic_env)
    assert any("CREDENCE_SIFTER_ENABLED=true" in e for e in basic_env)

    # Prod env checks
    assert any("CREDENCE_BACKUP_ENABLED=true" in e for e in prod_env)
    assert any("CREDENCE_BOREDOM_ENABLED=true" in e for e in prod_env)
    assert any("CREDENCE_SIFTER_ENABLED=true" in e for e in prod_env)


@pytest.mark.integration
def test_k8s_manifest_descriptor_parity():
    """Verify k8s/deployment.yaml declares sovereign backup and daemon env vars."""
    k8s_file = REPO_ROOT / "k8s" / "deployment.yaml"
    assert k8s_file.exists()

    docs = list(yaml.safe_load_all(k8s_file.read_text(encoding="utf-8")))
    deployment_doc = next(d for d in docs if d and d.get("kind") == "Deployment")
    container = deployment_doc["spec"]["template"]["spec"]["containers"][0]
    env_vars = {e["name"]: e.get("value") for e in container.get("env", []) if "name" in e}

    assert env_vars.get("CREDENCE_BACKUP_ENABLED") == "true"
    assert env_vars.get("CREDENCE_BOREDOM_ENABLED") == "true"
    assert env_vars.get("CREDENCE_SIFTER_ENABLED") == "true"


@pytest.mark.integration
def test_env_example_descriptor_parity():
    """Verify .env.example documents all v2.4.0 configuration parameters."""
    env_file = REPO_ROOT / ".env.example"
    assert env_file.exists()
    content = env_file.read_text(encoding="utf-8")

    assert "CREDENCE_BACKUP_ENABLED" in content
    assert "CREDENCE_BACKUP_DIR" in content
    assert "CREDENCE_BOREDOM_ENABLED" in content
    assert "CREDENCE_SIFTER_ENABLED" in content
