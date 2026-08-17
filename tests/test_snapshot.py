"""Unit tests for HTML Ingestion, Trafilatura Extraction, and Satire Detection."""

from pathlib import Path

import pytest

from credence.ingestion.extractor import detect_satire_cues, extract_clean_content, extract_outbound_links
from credence.ingestion.snapshot import capture_webpage


@pytest.mark.unit
def test_clean_article_extraction(clean_html: str) -> None:
    """Verify clean HTML fixture extracts prose, byline, title, and citations correctly."""
    result = extract_clean_content(clean_html, url="https://example.org/renewable-energy")

    assert result.title == "Global Renewable Energy Adoption Reaches New Record in 2025"
    assert "Sarah Jenkins" in (result.byline or "")
    assert "Global Science Journal" in (result.site_name or "")
    assert "solar photovoltaic" in result.clean_text.lower()
    assert result.word_count > 50
    assert result.is_satire_cue is False
    assert len(result.outbound_links) >= 1
    assert "https://example.org/iea-report-2025" in result.outbound_links


@pytest.mark.unit
def test_satire_article_detection(satire_html: str) -> None:
    """Verify satirical publication metadata and badges are detected."""
    result = extract_clean_content(satire_html, url="https://theonion.com/moon-cheese")

    assert result.is_satire_cue is True
    assert len(result.satire_cue_reasons) > 0
    assert any("satire" in reason.lower() or "parody" in reason.lower() for reason in result.satire_cue_reasons)
    assert "NASA" in result.clean_text


@pytest.mark.unit
def test_detect_satire_cues_patterns() -> None:
    """Verify custom satire patterns like Schema.org and disclaimers."""
    # Test Schema.org SatiricalArticle
    html_schema = '<div itemscope itemtype="https://schema.org/SatiricalArticle">Article</div>'
    is_satire, reasons = detect_satire_cues(html_schema)
    assert is_satire is True
    assert len(reasons) > 0

    # Test explicit fictitious disclaimer
    html_disclaimer = "<footer>All stories and articles are satirical and fictitious.</footer>"
    is_satire, reasons = detect_satire_cues(html_disclaimer)
    assert is_satire is True
    assert len(reasons) > 0


@pytest.mark.unit
def test_extract_outbound_links() -> None:
    """Verify extraction of external links."""
    html = """
    <div>
        <a href="https://reuters.com/news/123">Reuters</a>
        <a href="https://apnews.com/article/456">AP News</a>
        <a href="/local-path">Local link</a>
    </div>
    """
    links = extract_outbound_links(html)
    assert "https://reuters.com/news/123" in links
    assert "https://apnews.com/article/456" in links
    assert "/local-path" not in links


@pytest.mark.unit
async def test_capture_webpage_local_file(fixtures_dir: Path, tmp_path: Path) -> None:
    """Verify Playwright captures rendered HTML and screenshot from a local HTML file."""
    file_url = f"file://{fixtures_dir / 'clean_article.html'}"
    result = await capture_webpage(file_url, output_dir=tmp_path, save_artifacts=True)

    assert result.url == file_url
    assert result.extracted.title is not None
    assert "Global Renewable Energy Adoption" in result.extracted.title
    assert result.dom_file_path is not None
    assert Path(result.dom_file_path).exists()
    assert result.screenshot_file_path is not None
    assert Path(result.screenshot_file_path).exists()
    assert result.screenshot_bytes is not None
    assert len(result.screenshot_bytes) > 1000
