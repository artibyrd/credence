"""Integration & Security tests asserting Red Team / Blue Team badge protections."""

import pytest

from credence.ingestion.extractor import extract_clean_content, strip_ignored_elements
from credence.ingestion.hasher import compute_content_sha256

pytestmark = pytest.mark.integration


def test_redteam_bait_and_switch_detection():
    """Verify that mutating DOM text after initial hashing produces a different content_sha256."""
    pristine_article = "<p>Standard verified reporting with grounded sources.</p>"
    poisoned_article = "<p>Defamatory libel replacing previous article text.</p>"

    h1 = compute_content_sha256(extract_clean_content(pristine_article).clean_text)
    h2 = compute_content_sha256(extract_clean_content(poisoned_article).clean_text)

    assert h1 != h2, "Mutated DOM produced colliding hash; Bait-and-Switch defense failed!"


def test_redteam_scrubber_camouflage_defense():
    """Verify that attempting to cloak payload inside [data-credence-ignore] is detected."""
    attack_payload = (
        """
    <html>
      <body>
        <p>Clean text seen by scanner.</p>
        <aside data-credence-ignore="true">
          """
        + ("A" * 300)
        + """
        </aside>
      </body>
    </html>
    """
    )
    cleaned, is_cam, reasons = strip_ignored_elements(attack_payload)
    assert is_cam is True
    assert any("SEC-1.1" in r for r in reasons)
