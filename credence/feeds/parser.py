"""Lightweight, zero-dependency Syndicated Feed Parser for Credence.

Supports RSS 2.0, Atom 1.0, and JSON Feed 1.1 formats with HTTP conditional
ETag and Last-Modified (304 Not Modified) bandwidth optimization.
"""

import email.utils
import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field


class FeedEntry(BaseModel):
    """Normalized syndicated article item extracted from a feed."""

    url: str = Field(..., description="Canonical article URL")
    title: str = Field(default="", description="Article headline title")
    summary: Optional[str] = Field(default=None, description="Article summary or excerpt")
    author: Optional[str] = Field(default=None, description="Author byline if provided")
    published_at: Optional[datetime] = Field(default=None, description="Publication timestamp")
    guid: Optional[str] = Field(default=None, description="Unique item identifier")


class ParsedFeed(BaseModel):
    """Result of parsing an RSS/Atom/JSON feed."""

    title: str = Field(default="", description="Feed channel title")
    feed_format: str = Field(default="rss", description="Format detected: rss, atom, json")
    etag: Optional[str] = Field(default=None, description="HTTP ETag header received")
    last_modified: Optional[str] = Field(default=None, description="HTTP Last-Modified header received")
    is_modified: bool = Field(default=True, description="False if server returned HTTP 304 Not Modified")
    entries: List[FeedEntry] = Field(default_factory=list, description="Extracted feed entries")


def _get_elem_text(elem: Optional[ET.Element]) -> Optional[str]:
    """Extract all inner text from an XML element including any child elements."""
    if elem is None:
        return None
    return "".join(elem.itertext()).strip()


def _strip_html_tags(text: Optional[str]) -> Optional[str]:
    """Strip HTML markup and unescape HTML entities from feed text."""
    if not text:
        return None
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = html.unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean or None


def _parse_rfc822_date(date_str: str) -> Optional[datetime]:
    """Parse RFC 822 / 2822 date string into UTC datetime."""
    try:
        parsed_tuple = email.utils.parsedate_tz(date_str)
        if parsed_tuple:
            timestamp = email.utils.mktime_tz(parsed_tuple)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except Exception:  # noqa: S110
        pass
    return None


def _parse_iso_date(date_str: str) -> Optional[datetime]:
    """Parse ISO 8601 / RFC 3339 date string into UTC datetime."""
    try:
        clean = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:  # noqa: S110
        pass
    return None


def _parse_flexible_date(date_str: Optional[str]) -> Optional[datetime]:
    """Robust date parser handling RFC 822, ISO 8601, and common date formats."""
    if not date_str or not date_str.strip():
        return None

    clean_str = date_str.strip()

    # 1. Try RFC 822 / 2822
    dt = _parse_rfc822_date(clean_str)
    if dt:
        return dt

    # 2. Try ISO 8601
    dt = _parse_iso_date(clean_str)
    if dt:
        return dt

    # 3. Try standard fallback date formats
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(clean_str, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def _find_first_elem(
    parent: ET.Element,
    tags: List[str],
    namespaces: Optional[Dict[str, str]] = None,
) -> Optional[ET.Element]:
    """Safely search for the first matching child element by tags list."""
    for tag in tags:
        elem = parent.find(tag, namespaces=namespaces) if namespaces and ":" in tag else parent.find(tag)
        if elem is not None:
            return elem
    return None


def parse_rss(root: ET.Element) -> ParsedFeed:
    """Parse RSS 2.0 XML element tree."""
    channel = root.find("channel")
    channel_elem = channel if channel is not None else root
    raw_title = _get_elem_text(_find_first_elem(channel_elem, ["title"])) or "RSS Feed"
    feed_title = _strip_html_tags(raw_title) or "RSS Feed"

    entries: List[FeedEntry] = []
    for item in channel_elem.findall("item"):
        link_elem = _find_first_elem(item, ["link", "guid"])
        url = _get_elem_text(link_elem) or ""
        url = url.strip()
        if not url or not url.startswith(("http://", "https://")):
            continue

        raw_item_title = _get_elem_text(_find_first_elem(item, ["title"])) or "Untitled"
        title = _strip_html_tags(raw_item_title) or "Untitled"
        summary = _strip_html_tags(_get_elem_text(_find_first_elem(item, ["description"])))
        author_elem = _find_first_elem(item, ["author", "{http://purl.org/dc/elements/1.1/}creator"])
        author = _strip_html_tags(_get_elem_text(author_elem))

        date_elem = _find_first_elem(item, ["pubDate", "{http://purl.org/dc/elements/1.1/}date"])
        pub_date_str = _get_elem_text(date_elem)
        pub_dt = _parse_flexible_date(pub_date_str)

        guid_elem = _find_first_elem(item, ["guid"])
        guid = _get_elem_text(guid_elem)

        entries.append(
            FeedEntry(
                url=url,
                title=title,
                summary=summary,
                author=author,
                published_at=pub_dt,
                guid=guid,
            )
        )

    return ParsedFeed(
        title=feed_title.strip(),
        feed_format="rss",
        is_modified=True,
        entries=entries,
    )


def parse_atom(root: ET.Element) -> ParsedFeed:
    """Parse Atom 1.0 XML element tree."""
    # Handle XML namespaces
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    raw_title = _get_elem_text(_find_first_elem(root, ["atom:title", "title"], namespaces=ns)) or "Atom Feed"
    feed_title = _strip_html_tags(raw_title) or "Atom Feed"

    entries: List[FeedEntry] = []
    for entry in root.findall("atom:entry", namespaces=ns) or root.findall("entry"):
        url = ""
        # Look for <link rel="alternate" href="..."> or first <link href="...">
        for link in entry.findall("atom:link", namespaces=ns) or entry.findall("link"):
            href = link.attrib.get("href", "").strip()
            rel = link.attrib.get("rel", "alternate")
            if href and rel == "alternate" and href.startswith(("http://", "https://")):
                url = href
                break
            elif href and not url and href.startswith(("http://", "https://")):
                url = href

        if not url:
            continue

        raw_title_str = _get_elem_text(_find_first_elem(entry, ["atom:title", "title"], namespaces=ns)) or "Untitled"
        title = _strip_html_tags(raw_title_str) or "Untitled"

        summary_elem = _find_first_elem(
            entry,
            ["atom:summary", "summary", "atom:content", "content"],
            namespaces=ns,
        )
        summary = _strip_html_tags(_get_elem_text(summary_elem))

        author_elem = _find_first_elem(entry, ["atom:author", "author"], namespaces=ns)
        author = None
        if author_elem is not None:
            author_name_elem = _find_first_elem(author_elem, ["atom:name", "name"], namespaces=ns)
            raw_author = _get_elem_text(author_name_elem)
            author = _strip_html_tags(raw_author)

        date_elem = _find_first_elem(
            entry,
            ["atom:published", "published", "atom:updated", "updated"],
            namespaces=ns,
        )
        pub_date_str = _get_elem_text(date_elem)
        pub_dt = _parse_flexible_date(pub_date_str)

        guid_elem = _find_first_elem(entry, ["atom:id", "id"], namespaces=ns)
        guid = _get_elem_text(guid_elem)

        entries.append(
            FeedEntry(
                url=url,
                title=title,
                summary=summary,
                author=author,
                published_at=pub_dt,
                guid=guid,
            )
        )

    return ParsedFeed(
        title=feed_title,
        feed_format="atom",
        is_modified=True,
        entries=entries,
    )


def parse_json_feed(data: Dict[str, Any]) -> ParsedFeed:
    """Parse JSON Feed 1.1 dictionary."""
    feed_title = data.get("title", "JSON Feed")
    entries: List[FeedEntry] = []

    for item in data.get("items", []):
        url = item.get("url") or item.get("id") or ""
        url = str(url).strip()
        if not url or not url.startswith(("http://", "https://")):
            continue

        title = item.get("title", "Untitled")
        summary = item.get("summary") or item.get("content_text")
        author_info = item.get("authors", [{}])[0] if item.get("authors") else item.get("author", {})
        author = author_info.get("name") if isinstance(author_info, dict) else str(author_info)
        pub_date_str = item.get("date_published") or item.get("date_modified")
        pub_dt = _parse_iso_date(pub_date_str) if pub_date_str else None

        entries.append(
            FeedEntry(
                url=url,
                title=str(title).strip(),
                summary=str(summary).strip() if summary else None,
                author=str(author).strip() if author else None,
                published_at=pub_dt,
                guid=str(item.get("id")),
            )
        )

    return ParsedFeed(
        title=str(feed_title).strip(),
        feed_format="json",
        is_modified=True,
        entries=entries,
    )


def safe_parse_xml(content: str, max_bytes: int = 10 * 1024 * 1024) -> ET.Element:
    """Safely parse XML content, strictly disallowing DTD entity expansion (Billion Laughs protection)."""
    if len(content.encode("utf-8")) > max_bytes:
        raise ValueError(f"XML payload exceeds maximum allowed size of {max_bytes} bytes.")

    content_upper = content.upper()
    if "<!DOCTYPE" in content_upper or "<!ENTITY" in content_upper:
        raise ValueError(
            "XML contains prohibited DTD entity or DOCTYPE declaration (rejected for entity expansion safety)."
        )

    return ET.fromstring(content)  # noqa: S314


def parse_feed_content(content: str) -> ParsedFeed:
    """Detect and parse raw XML/JSON feed content."""
    clean_content = content.strip()
    if clean_content.startswith("{"):
        try:
            data = json.loads(clean_content)
            return parse_json_feed(data)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON Feed: {e}") from e

    try:
        root = safe_parse_xml(clean_content)
        tag = root.tag.lower()
        if "rss" in tag or root.find("channel") is not None:
            return parse_rss(root)
        elif "feed" in tag:
            return parse_atom(root)
        else:
            # Fallback: check children
            if root.find("entry") is not None or root.find("{http://www.w3.org/2005/Atom}entry") is not None:
                return parse_atom(root)
            return parse_rss(root)
    except Exception as e:
        raise ValueError(f"Failed to parse XML Feed: {e}") from e


async def fetch_and_parse_feed(
    feed_url: str,
    etag: Optional[str] = None,
    last_modified: Optional[str] = None,
    timeout_seconds: float = 10.0,
) -> ParsedFeed:
    """Fetch and parse feed with HTTP conditional GET headers."""
    from credence.ingestion.security import validate_safe_url

    clean_url = validate_safe_url(feed_url)
    headers = {"User-Agent": "Credence-Epistemic-Feed-Ingester/1.0"}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        response = await client.get(clean_url, headers=headers)

        if response.status_code == 304:
            return ParsedFeed(
                title="",
                feed_format="unknown",
                etag=etag,
                last_modified=last_modified,
                is_modified=False,
                entries=[],
            )

        response.raise_for_status()

        parsed = parse_feed_content(response.text)
        parsed.etag = response.headers.get("ETag")
        parsed.last_modified = response.headers.get("Last-Modified")
        return parsed
