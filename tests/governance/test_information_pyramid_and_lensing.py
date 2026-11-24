"""Shift-left governance tests verifying the Information Pyramid & Lensing Invariant."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_information_pyramid_invariants_declared():
    """Verify inv-cart-before-horse in AGENTS.md and Epistemic Lensing in architecture-review overlay."""
    repo_root = Path(__file__).resolve().parents[2]
    agents_path = repo_root / "AGENTS.md"
    assert agents_path.exists(), "AGENTS.md must exist in repository root"
    agents_content = agents_path.read_text(encoding="utf-8")
    assert "inv-cart-before-horse" in agents_content
    assert ".agents/overrides/" in agents_content

    arch_overlay = repo_root / ".agents" / "overrides" / "architecture-review.md"
    assert arch_overlay.exists(), ".agents/overrides/architecture-review.md must exist"
    overlay_content = arch_overlay.read_text(encoding="utf-8")
    assert "Epistemic Lensing & Information Pyramid" in overlay_content
    assert "inv-epistemic-lensing" in overlay_content


def test_lexicon_contains_v210_terms():
    """Verify terminology-and-ontology-lexicon.md contains the 10 v2.1.0 coined terms."""
    repo_root = Path(__file__).resolve().parents[2]
    docs_lex = repo_root.parent / "credence-docs" / "docs" / "blueprints" / "terminology-and-ontology-lexicon.md"
    if not docs_lex.exists():
        pytest.skip("credence-docs not present in standalone repository CI runner")

    content = docs_lex.read_text(encoding="utf-8")
    assert "The Information Pyramid" in content
    assert "Epistemic Lensing" in content
    assert "DOM Extraction Scrubber" in content
    assert "Temporal Score Trajectory" in content
    assert "Content Evolution Forensics" in content
    assert "Dogfood Attestation" in content
    assert "Differential Dogfooding" in content
    assert "Order-of-Operations Invariant" in content
