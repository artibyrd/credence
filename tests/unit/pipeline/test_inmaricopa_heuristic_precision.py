"""Unit tests for offline heuristic precision on InMaricopa case study archetypes.

Governed by: inv-hermetic-unit-tests
"""

from __future__ import annotations

import pytest

from credence.ingestion.extractor import ExtractedContent
from credence.pipeline.heuristics import heuristic_evaluate_content
from credence.pipeline.scoring import compute_calibrated_score, compute_raw_suspicion
from credence.taxonomy_loader import TaxonomyRegistry


@pytest.mark.unit
def test_inmaricopa_copper_sky_coi_heuristic_detection() -> None:
    """Verify that council defense op-ed cues and anonymous staff bylines trigger SPJ-3.1 and SPJ-4.1."""
    text = (
        "Your candidate won. Now you are searching for a scandal that does not exist. "
        "Every day on social media, we see more hatred from the same small group of angry people. "
        "Councilmember Vincent Manfredi voted on the commercial rezoning after careful deliberation. "
        "City records prove all ethical guidelines were satisfied."
    )
    extracted = ExtractedContent(
        url="https://inmaricopa.com/copper-sky-land-sale-is-no-scandal/",
        title="Copper Sky Land Sale is No Scandal",
        clean_text=text,
        byline="InMaricopa Staff",
    )
    raw_html = f"<html><body><p>{text}</p></body></html>"
    reg = TaxonomyRegistry()

    findings = heuristic_evaluate_content(extracted, raw_html, reg=reg)
    rule_ids = {f.rule_id for f in findings}

    assert "SPJ-3.1" in rule_ids or "SPJ-4.1" in rule_ids
    raw_score = compute_raw_suspicion(findings)
    calibrated = compute_calibrated_score(raw_score)
    assert calibrated >= 15.0


@pytest.mark.unit
def test_inmaricopa_tattoo_advertorial_heuristic_detection() -> None:
    """Verify that first-person clinic promotions and contact cues trigger DP-1.1 and SPJ-3.2."""
    text = (
        "Every once in a while, a new technology genuinely changes what we’re able to offer our patients. "
        "That’s why I’m excited to officially introduce Picofy to Maricopa Wellness Center. "
        "Join us for education, refreshments, raffles, giveaways and exclusive savings. "
        "Maricopa Wellness Center, 520-464-6193, MaricopaWellnessCenter.com"
    )
    extracted = ExtractedContent(
        url="https://inmaricopa.com/a-new-option-for-pigmentation-and-tattoo-removal-comes-to-maricopa-next-month/",
        title="A New Option for Pigmentation and Tattoo Removal",
        clean_text=text,
        byline="InMaricopa Staff",
    )
    raw_html = f"<html><body><p>{text}</p></body></html>"
    reg = TaxonomyRegistry()

    findings = heuristic_evaluate_content(extracted, raw_html, reg=reg)
    rule_ids = {f.rule_id for f in findings}

    assert "DP-1.1" in rule_ids or "SPJ-3.2" in rule_ids
    raw_score = compute_raw_suspicion(findings)
    calibrated = compute_calibrated_score(raw_score)
    assert calibrated >= 40.0


@pytest.mark.unit
def test_inmaricopa_landlords_advertorial_heuristic_detection() -> None:
    """Verify that property management advertorial copy with contact footer triggers DP-1.1 and SPJ-3.2."""
    text = (
        "For many landlords, managing their own rental property seems like the obvious choice. "
        "At Crest Premier Properties, we believe professional property management is an investment in protecting both your property and your peace of mind. "
        "Phone: 480-838-9558. Web: CrestPremierProperties.com. Address: 4625 S. Lakeshore Drive, Tempe."
    )
    extracted = ExtractedContent(
        url="https://inmaricopa.com/what-landlords-discover-after-managing-a-rental-on-their-own/",
        title="What Landlords Discover After Managing a Rental on Their Own",
        clean_text=text,
        byline="Staff Reports",
    )
    raw_html = f"<html><body><p>{text}</p></body></html>"
    reg = TaxonomyRegistry()

    findings = heuristic_evaluate_content(extracted, raw_html, reg=reg)
    rule_ids = {f.rule_id for f in findings}

    assert "SPJ-3.2" in rule_ids
    assert "DP-1.1" in rule_ids
    raw_score = compute_raw_suspicion(findings)
    calibrated = compute_calibrated_score(raw_score)
    assert calibrated >= 50.0
