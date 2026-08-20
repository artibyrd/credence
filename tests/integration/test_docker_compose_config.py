"""Tests for Docker Compose and Kubernetes Manifest Static Syntax Validation."""

from pathlib import Path

import pytest
import yaml


@pytest.mark.integration
def test_docker_compose_basic_syntax_and_ports():
    """Verify docker-compose.yml defines valid syntax and port mappings."""
    compose_file = Path(__file__).resolve().parents[2] / "docker-compose.yml"
    assert compose_file.exists()
    data = yaml.safe_load(compose_file.read_text())

    assert "services" in data
    assert "credence" in data["services"]
    credence = data["services"]["credence"]
    assert "8000:8000" in credence["ports"]
    assert "volumes" in data


@pytest.mark.integration
def test_docker_compose_prod_cluster_services():
    """Verify docker-compose.prod.yml defines postgres, minio, valkey, and credence."""
    prod_compose = Path(__file__).resolve().parents[2] / "docker-compose.prod.yml"
    assert prod_compose.exists()
    data = yaml.safe_load(prod_compose.read_text())

    assert "services" in data
    services = data["services"]
    assert "postgres" in services
    assert "minio" in services
    assert "valkey" in services
    assert "credence" in services
    assert "depends_on" in services["credence"]


@pytest.mark.integration
def test_k8s_manifest_syntax_and_labels():
    """Verify k8s/deployment.yaml contains valid Deployment and Service manifests."""
    k8s_file = Path(__file__).resolve().parents[2] / "k8s" / "deployment.yaml"
    assert k8s_file.exists()
    docs = list(yaml.safe_load_all(k8s_file.read_text()))
    assert len(docs) == 2

    deployment, service = docs[0], docs[1]
    assert deployment["kind"] == "Deployment"
    assert deployment["metadata"]["name"] == "credence-server"
    assert service["kind"] == "Service"
    assert service["metadata"]["name"] == "credence-service"
