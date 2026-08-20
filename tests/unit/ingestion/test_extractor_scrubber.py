"""Hermetic unit tests for DOM scrubber, badge stripping, and SEC-1.1 camouflage guard."""

import pytest

from credence.ingestion.extractor import extract_clean_content, extract_editorial_notices, strip_ignored_elements
from credence.ingestion.hasher import compute_content_sha256

pytestmark = pytest.mark.unit


def test_strip_credence_badge_custom_element():
    html = """
    <html>
      <body>
        <h1>Article Headline</h1>
        <credence-badge url="https://example.com" score="98.5"></credence-badge>
        <p>This is genuine body text of the article.</p>
      </body>
    </html>
    """
    cleaned, is_cam, reasons = strip_ignored_elements(html)
    assert "<credence-badge" not in cleaned
    assert "Article Headline" in cleaned
    assert "genuine body text" in cleaned
    assert not is_cam


def test_rescore_immunity_invariant():
    """Verify that adding or modifying <credence-badge> does not alter content_sha256."""
    raw_html_without_badge = """
    <html>
      <body>
        <h1>The Truth About Solar Flares</h1>
        <p>Solar flares release massive bursts of electromagnetic radiation into the heliosphere.</p>
      </body>
    </html>
    """
    raw_html_with_badge = """
    <html>
      <body>
        <credence-badge url="https://example.com/solar" receipt="abc123xyz"></credence-badge>
        <h1>The Truth About Solar Flares</h1>
        <p>Solar flares release massive bursts of electromagnetic radiation into the heliosphere.</p>
      </body>
    </html>
    """

    res1 = extract_clean_content(raw_html_without_badge, url="https://example.com/solar")
    res2 = extract_clean_content(raw_html_with_badge, url="https://example.com/solar")

    hash1 = compute_content_sha256(res1.clean_text)
    hash2 = compute_content_sha256(res2.clean_text)

    assert hash1 == hash2, "Adding a credence-badge altered the canonical content_sha256!"


def test_sec11_dom_camouflage_detection():
    """Verify that large text blocks hidden in [data-credence-ignore] trigger SEC-1.1 camouflage penalty."""
    deceptive_html = """
    <html>
      <body>
        <h1>Headline</h1>
        <p>Innocuous visible paragraph.</p>
        <div data-credence-ignore="true">
          This is a covert deceptive claim designed to evade fact-checking algorithms by being hidden inside an ignored container. It exceeds the 150-character threshold to test our adversarial defenses.
        </div>
      </body>
    </html>
    """
    cleaned, is_cam, reasons = strip_ignored_elements(deceptive_html)
    assert is_cam is True
    assert len(reasons) > 0
    assert "SEC-1.1: Intentional DOM Camouflage" in reasons[0]


def test_extract_editorial_notices():
    html = """
    <div class="article-body">
      <h1>Study on Ocean Currents</h1>
      <div class="correction">
        Correction: An earlier version of this report misstated the baseline year for temperature readings. The correct baseline is 1990.
      </div>
      <p>Ocean currents transport heat globally.</p>
    </div>
    """
    notices = extract_editorial_notices(html)
    assert len(notices) == 1
    assert "Correction: An earlier version" in notices[0]
