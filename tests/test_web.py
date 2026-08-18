"""Unit tests for the Zero-Build Web Presentation Layer (Invariant 20).

Validates:
1. All public frontends use vanilla HTML5/CSS/ES Modules with zero npm dependencies.
2. Report viewer contains valid attestation rendering and Ed25519 verification elements.
3. Seed manifests and taxonomy mirrors contain valid JSON schemas.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def web_dir() -> Path:
    """Return path to web presentation directory."""
    return Path(__file__).resolve().parent.parent / "web"


@pytest.mark.unit
def test_web_run_landing_hub(web_dir: Path) -> None:
    """Verify credence.run landing page structure and zero-build integrity."""
    index_file = web_dir / "credence.run" / "index.html"
    assert index_file.exists(), "credence.run/index.html must exist"

    content = index_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Credence" in content
    assert "FastMCP" in content
    assert "epistemic" in content.lower()

    # Invariant 20: Zero npm/node JS frameworks (no react, vue, angular bundles)
    assert "react.production.min.js" not in content
    assert "vue.global.js" not in content
    assert "bundle.js" not in content


@pytest.mark.unit
def test_web_report_viewer_web_crypto(web_dir: Path) -> None:
    """Verify credence.report viewer implements zero-build attestation rendering."""
    viewer_file = web_dir / "credence.report" / "viewer.html"
    assert viewer_file.exists(), "credence.report/viewer.html must exist"

    content = viewer_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "ED25519 VERIFIED" in content
    assert "RFC 8785" in content
    assert "violations-container" in content
    assert "score-big" in content


@pytest.mark.unit
def test_web_nexus_peers_manifest(web_dir: Path) -> None:
    """Verify seeds.credence.nexus peers.json manifest format."""
    peers_file = web_dir / "credence.nexus" / "peers.json"
    assert peers_file.exists(), "credence.nexus/peers.json must exist"

    data = json.loads(peers_file.read_text(encoding="utf-8"))
    assert "generated_at" in data
    assert "canonical_domain" in data
    assert "seed_nodes" in data
    assert isinstance(data["seed_nodes"], list)
    assert len(data["seed_nodes"]) >= 1


@pytest.mark.unit
def test_web_foundation_taxonomies_and_keys(web_dir: Path) -> None:
    """Verify credence.foundation static taxonomy mirrors and public key custody."""
    foundation_dir = web_dir / "credence.foundation"
    assert foundation_dir.exists()

    # Verify root.pub exists
    root_pub = foundation_dir / "keys" / "root.pub"
    assert root_pub.exists()
    assert len(root_pub.read_text(encoding="utf-8").strip()) == 64

    # Verify v1 JSON taxonomy catalogs
    v1_dir = foundation_dir / "v1"
    for cat_name in ("spj_ethics.json", "iep_fallacies.json", "deceptive_patterns.json"):
        cat_file = v1_dir / cat_name
        assert cat_file.exists(), f"Catalog {cat_name} must exist"
        data = json.loads(cat_file.read_text(encoding="utf-8"))
        assert "catalog_id" in data
        assert "clusters" in data
