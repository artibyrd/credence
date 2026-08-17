"""HTML parsing and clean text/markdown extraction using Trafilatura.

Extracts:
- Clean prose and structured markdown.
- Metadata: title, author/byline, publication date, site name.
- Satire and parody cues from meta tags, Schema.org types, and masthead keywords.
- Outbound hyperlinks for citation verification.
"""

from __future__ import annotations

import re
from typing import List, Optional

import trafilatura
from pydantic import BaseModel, Field
from trafilatura.settings import use_config

# Configure Trafilatura for rigorous extraction
_traf_config = use_config()
_traf_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "10")


class ExtractedContent(BaseModel):
    """Structured extraction result from HTML markup."""

    url: str = Field(default="", description="Source URL")
    title: Optional[str] = Field(default=None, description="Extracted article/page title")
    byline: Optional[str] = Field(default=None, description="Author or organization byline")
    site_name: Optional[str] = Field(default=None, description="Publisher or domain title")
    date: Optional[str] = Field(default=None, description="Publication timestamp string")
    clean_text: str = Field(default="", description="Cleaned, unformatted plain text")
    clean_markdown: str = Field(default="", description="Structured markdown representation")
    word_count: int = Field(default=0, description="Total word count in clean text")
    char_count: int = Field(default=0, description="Total character count in clean text")
    is_satire_cue: bool = Field(default=False, description="Detected explicit satire or humor metadata/badges")
    satire_cue_reasons: List[str] = Field(default_factory=list, description="Specific satire indicators detected")
    outbound_links: List[str] = Field(default_factory=list, description="External URLs cited in the content")


# Regex patterns for detecting explicit satire cues in HTML, mastheads, or metadata
_SATIRE_META_PATTERNS = [
    re.compile(r'itemtype=["\']https?://schema\.org/(SatiricalArticle|Humor)["\']', re.IGNORECASE),
    re.compile(r'content=["\'][^"\']*\b(satire|parody|humor|satirical)\b[^"\']*["\']', re.IGNORECASE),
    re.compile(
        r'class=["\'][^"\']*\b(satire-tag|badge-satire|humor-category|parody-disclaimer)\b[^"\']*["\']', re.IGNORECASE
    ),
    re.compile(r'href=["\'][^"\']*/(satire|humor|parody|comedy)/?["\']', re.IGNORECASE),
    re.compile(
        r"(about\s+us|disclaimer)[^>]*>[^<]*\b(satire|satirical|parody|fictional|humor|comedy\s+publication)\b",
        re.IGNORECASE,
    ),
    re.compile(r"<(footer|div|p)[^>]*>.*?\b(satirical|parody|fictitious)\b.*?</\1>", re.IGNORECASE | re.DOTALL),
]


def detect_satire_cues(html: str) -> tuple[bool, List[str]]:
    """Scan raw HTML markup for explicit satire/parody declarations and metadata."""
    if not html:
        return False, []

    reasons: List[str] = []
    for pattern in _SATIRE_META_PATTERNS:
        match = pattern.search(html)
        if match:
            matched_str = match.group(0)[:100].replace("\n", " ").strip()
            reasons.append(f"Found satire marker: {matched_str}")

    # Check for general satirical phrases
    if re.search(r"\b(satirical|parody|fictitious)\b", html, re.IGNORECASE):
        if not reasons:
            reasons.append("Detected satire/parody keywords in document markup.")

    return len(reasons) > 0, reasons


def extract_outbound_links(html: str) -> List[str]:
    """Extract unique outbound HTTP/HTTPS links from HTML body."""
    links = set(re.findall(r'href=["\'](https?://[^"\'\s>]+)["\']', html, re.IGNORECASE))
    return sorted(links)


def extract_clean_content(html: str, url: str = "") -> ExtractedContent:
    """Extract clean text, markdown, and rich metadata from an HTML document."""
    if not html or not html.strip():
        return ExtractedContent(url=url)

    # Use Trafilatura to extract structured metadata (JSON-LD, OpenGraph, Dublin Core)
    metadata = trafilatura.extract_metadata(html, default_url=url)

    # Extract clean markdown format
    clean_markdown = (
        trafilatura.extract(
            html,
            url=url,
            output_format="markdown",
            include_links=True,
            include_images=False,
            include_tables=True,
            config=_traf_config,
        )
        or ""
    )

    # Extract plain text
    clean_text = (
        trafilatura.extract(
            html,
            url=url,
            output_format="txt",
            include_links=False,
            include_tables=True,
            config=_traf_config,
        )
        or clean_markdown
    )

    # Detect satire cues
    is_satire_cue, satire_reasons = detect_satire_cues(html)

    # Extract links
    outbound_links = extract_outbound_links(html)

    # Compute word and character counts
    words = clean_text.split()
    word_count = len(words)
    char_count = len(clean_text)

    # Assemble metadata
    title = metadata.title if metadata and metadata.title else None
    byline = metadata.author if metadata and metadata.author else None
    site_name = metadata.sitename if metadata and metadata.sitename else None
    date = metadata.date if metadata and metadata.date else None

    # Fallback to HTML title tag if metadata is missing
    if not title:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()

    return ExtractedContent(
        url=url,
        title=title,
        byline=byline,
        site_name=site_name,
        date=date,
        clean_text=clean_text,
        clean_markdown=clean_markdown,
        word_count=word_count,
        char_count=char_count,
        is_satire_cue=is_satire_cue,
        satire_cue_reasons=satire_reasons,
        outbound_links=outbound_links,
    )
