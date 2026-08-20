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
from urllib.parse import urlparse

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
    is_editorial_update: bool = Field(
        default=False, description="Detected explicit correction or editorial update notice"
    )
    editorial_notices: List[str] = Field(default_factory=list, description="Extracted correction or retraction notices")
    is_dom_camouflage: bool = Field(
        default=False, description="Detected adversarial text hidden inside ignored elements"
    )
    camouflage_reasons: List[str] = Field(default_factory=list, description="Reasons for DOM camouflage detection")


# Regex patterns for detecting explicit satire cues in HTML, mastheads, or metadata
_SATIRE_META_PATTERNS = [
    re.compile(r'itemtype=["\']https?://schema\.org/(SatiricalArticle|Humor)["\']', re.IGNORECASE),
    re.compile(r'["\'](@type|genre)["\']\s*:\s*["\'](SatiricalArticle|Humor|Satire|Parody)["\']', re.IGNORECASE),
    re.compile(
        r"<meta\s+[^>]*\b(satire|parody|satirical|humor\s+site|fake\s+news)\b[^>]*>",
        re.IGNORECASE,
    ),
    re.compile(
        r"<title>[^<]*\b(satire|parody|satirical|fake\s+news\s+you\s+can\s+trust)\b[^<]*</title>",
        re.IGNORECASE,
    ),
    re.compile(
        r'class=["\'][^"\']*\b(satire-tag|badge-satire|humor-category|satire-indicator)\b[^"\']*["\']',
        re.IGNORECASE,
    ),
    re.compile(r'href=["\'][^"\']*/(satire|humor|parody|comedy)/?["\']', re.IGNORECASE),
    re.compile(
        r"<footer>.*?\b(satirical|parody|fictitious|satire)\b.*?</footer>",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"<(div|section|p)[^>]*\b(disclaimer|about-us|site-description)\b[^>]*>.*?\b(satire|satirical|parody|fictitious|humor\s+publication)\b.*?</\1>",
        re.IGNORECASE | re.DOTALL,
    ),
]

_EDITORIAL_NOTICE_PATTERNS = [
    re.compile(
        r"<(div|section|aside|p)[^>]*\b(correction|update-notice|retraction|editor-note|clarification)\b[^>]*>(.*?)</\1>",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"<(div|section|p)[^>]*>.*?\b(Correction:\s|Editor's Note:\s|Updated:\sAn earlier version|Clarification:\s).*?</\1>",
        re.IGNORECASE | re.DOTALL,
    ),
]


def strip_ignored_elements(html: str) -> tuple[str, bool, List[str]]:
    """Sanitize HTML by stripping score badges and ignored elements to prevent rescore loops.

    Enforces SEC-1.1 Camouflage Guard:
    - Strips <credence-badge> Web Components and .credence-badge classes.
    - Strips elements marked with data-credence-ignore='true' or data-credence-widget='true'.
    - If non-badge [data-credence-ignore] elements contain >150 chars of visible text, flags SEC-1.1 camouflage.
    """
    if not html:
        return "", False, []

    is_camouflage = False
    camouflage_reasons: List[str] = []

    # 1. Strip explicit <credence-badge> custom elements (self-closing or container)
    cleaned = re.sub(r"<credence-badge\b[^>]*>.*?</credence-badge>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<credence-badge\b[^>]*/>", " ", cleaned, flags=re.IGNORECASE)

    # 2. Check and strip elements with data-credence-ignore="true" or data-credence-widget="true"
    ignore_pattern = re.compile(
        r"<([a-zA-Z0-9_-]+)\s+[^>]*\b(data-credence-ignore|data-credence-widget)=[\"']true[\"'][^>]*>(.*?)</\1>",
        re.IGNORECASE | re.DOTALL,
    )

    def _sanitize_and_check(match: re.Match) -> str:
        nonlocal is_camouflage
        tag = match.group(1).lower()
        content = match.group(3)
        # Strip child HTML tags to inspect inner plain text length
        inner_text = re.sub(r"<[^>]+>", " ", content).strip()
        # If tag is not a standard badge class and contains substantial text, flag camouflage
        if tag not in ("credence-badge", "span") and len(inner_text) > 150:
            is_camouflage = True
            preview = inner_text[:80].replace("\n", " ")
            camouflage_reasons.append(
                f"SEC-1.1: Intentional DOM Camouflage detected in <{tag} data-credence-ignore> ({len(inner_text)} chars): '{preview}...'"
            )
        return " "

    cleaned = ignore_pattern.sub(_sanitize_and_check, cleaned)

    # 3. Strip .credence-badge and .credence-badge-container elements
    cleaned = re.sub(
        r"<([a-zA-Z0-9_-]+)\s+[^>]*\bclass=[\"'][^\"']*\b(credence-badge|credence-badge-container)\b[^\"']*[\"'][^>]*>(.*?)</\1>",
        " ",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return cleaned, is_camouflage, camouflage_reasons


def extract_editorial_notices(html: str) -> List[str]:
    """Extract explicit correction, update, or retraction notices from HTML markup."""
    if not html:
        return []

    raw_candidates: List[str] = []
    for pattern in _EDITORIAL_NOTICE_PATTERNS:
        for match in pattern.finditer(html):
            raw_text = re.sub(r"<[^>]+>", " ", match.group(0)).strip()
            clean_notice = re.sub(r"\s+", " ", raw_text)
            if clean_notice and len(clean_notice) > 10:
                raw_candidates.append(clean_notice[:500])

    if not raw_candidates and any(k in html for k in ["Correction:", "Editor's Note:", "Clarification:"]):
        for line in html.splitlines():
            s_line = re.sub(r"<[^>]+>", " ", line).strip()
            s_line = re.sub(r"\s+", " ", s_line)
            if any(k in s_line for k in ["Correction:", "Editor's Note:", "Clarification:"]) and len(s_line) > 10:
                raw_candidates.append(s_line[:500])

    # Deduplicate and prefer inner, more specific notices
    notices: List[str] = []
    for cand in sorted(raw_candidates, key=len):
        if not any(existing in cand for existing in notices):
            notices.append(cand)

    return notices


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

    return len(reasons) > 0, reasons


def extract_outbound_links(html: str) -> List[str]:
    """Extract unique outbound HTTP/HTTPS links from HTML body."""
    links = set(re.findall(r'href=["\'](https?://[^"\'\s>]+)["\']', html, re.IGNORECASE))
    return sorted(links)


def extract_clean_content(html: str, url: str = "") -> ExtractedContent:
    """Extract clean text, markdown, and rich metadata from an HTML document."""
    if not html or not html.strip():
        return ExtractedContent(url=url)

    # 1. Sanitize HTML against score badges & ignored elements (Rescore Avoidance Invariant)
    sanitized_html, is_dom_camouflage, camouflage_reasons = strip_ignored_elements(html)

    # 2. Extract editorial notices
    editorial_notices = extract_editorial_notices(html)
    is_editorial_update = len(editorial_notices) > 0

    # 3. Use Trafilatura to extract structured metadata
    metadata = trafilatura.extract_metadata(sanitized_html, default_url=url)

    # 4. Extract clean markdown format
    clean_markdown = (
        trafilatura.extract(
            sanitized_html,
            url=url,
            output_format="markdown",
            include_links=True,
            include_images=False,
            include_tables=True,
            config=_traf_config,
        )
        or ""
    )

    # 5. Extract plain text
    clean_text = (
        trafilatura.extract(
            sanitized_html,
            url=url,
            output_format="txt",
            include_links=False,
            include_tables=True,
            config=_traf_config,
        )
        or clean_markdown
    )

    # Snippet fallback if Trafilatura returned empty on short markup
    if not clean_text or not clean_text.strip():
        raw_stripped = re.sub(r"<[^>]+>", " ", sanitized_html)
        clean_text = re.sub(r"\s+", " ", raw_stripped).strip()
        clean_markdown = clean_markdown or clean_text

    # 6. Detect satire cues
    is_satire_cue, satire_reasons = detect_satire_cues(html)

    # 7. Extract links

    outbound_links = extract_outbound_links(sanitized_html)

    # 8. Compute word and character counts
    words = clean_text.split()
    word_count = len(words)
    char_count = len(clean_text)

    # 9. Assemble metadata
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
        is_editorial_update=is_editorial_update,
        editorial_notices=editorial_notices,
        is_dom_camouflage=is_dom_camouflage,
        camouflage_reasons=camouflage_reasons,
    )


def extract_root_domain(url: str) -> str:
    """Extract root domain from URL string."""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.split(":")[0].lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc or "unknown-domain"
    except Exception:
        return "unknown-domain"
