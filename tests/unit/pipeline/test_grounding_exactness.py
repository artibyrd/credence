"""Strict Epistemic Verbatim Grounding Gauntlet (G=1.00).

Governed by Invariant 5: Epistemic Verbatim Grounding (G=1.00).
Verifies that citations match source DOM text character-for-character after whitespace collapse,
with zero fuzzy tolerance.
"""

import pytest

from credence.pipeline.subagents import validate_grounded_quote


@pytest.mark.unit
def test_exact_verbatim_grounding_matches() -> None:
    """Exact quoted substrings must pass validation."""
    source_text = "The quick brown fox jumps over the lazy dog."
    raw_html = "<p>The quick brown fox jumps over the lazy dog.</p>"

    assert validate_grounded_quote("quick brown fox", source_text, raw_html) is True
    assert validate_grounded_quote('"The quick brown fox"', source_text, raw_html) is True
    assert validate_grounded_quote("“The quick brown fox”", source_text, raw_html) is True


@pytest.mark.unit
def test_fuzzy_or_altered_quote_fails_g_100() -> None:
    """Altered or hallucinated words must fail character-for-character grounding (G=1.00)."""
    source_text = "The quick brown fox jumps over the lazy dog."
    raw_html = "<p>The quick brown fox jumps over the lazy dog.</p>"

    # 1 word altered: "swift" instead of "quick"
    assert validate_grounded_quote("The swift brown fox jumps", source_text, raw_html) is False

    # Paraphrased summary
    assert validate_grounded_quote("A brown animal leaped over a canine", source_text, raw_html) is False


@pytest.mark.unit
def test_whitespace_and_quotation_mark_resilience() -> None:
    """Whitespace collapse and standard outer quotation marks are normalized."""
    source_text = "Headline: Local Economy Grew By 4.2% In Q3."
    raw_html = "<h1>Headline: Local Economy Grew By 4.2% In Q3.</h1>"

    assert validate_grounded_quote("  Local   Economy   Grew   By   4.2%  ", source_text, raw_html) is True
    assert validate_grounded_quote("«Local Economy Grew By 4.2%»", source_text, raw_html) is True
