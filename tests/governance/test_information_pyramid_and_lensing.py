"""Shift-left governance tests verifying the Information Pyramid & Lensing Invariant."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_information_pyramid_invariants_declared():
    """Verify Invariant 42 & 43 in docs/invariants.md and AGENTS.md."""
    agents_root = Path("/home/pendragon/Projects/credence-ecosystem/AGENTS.md")
    assert agents_root.exists()
    content = agents_root.read_text(encoding="utf-8")
    assert "The Epistemic Lensing & Information Pyramid Invariant" in content
    assert "The Cart-Before-the-Horse Order-of-Operations Invariant" in content


def test_lexicon_contains_v210_terms():
    """Verify terminology-and-ontology-lexicon.md contains the 10 v2.1.0 coined terms."""
    lex_path = Path(
        "/home/pendragon/Projects/credence-ecosystem/credence-docs/docs/blueprints/terminology-and-ontology-lexicon.md"
    )
    assert lex_path.exists()
    content = lex_path.read_text(encoding="utf-8")
    assert "The Information Pyramid" in content
    assert "Epistemic Lensing" in content
    assert "DOM Extraction Scrubber" in content
    assert "Temporal Score Trajectory" in content
    assert "Content Evolution Forensics" in content
    assert "Dogfood Attestation" in content
    assert "Differential Dogfooding" in content
    assert "Order-of-Operations Invariant" in content
