"""Zero-Trust Dynamic Feed Autodiscovery Engine for Credence.

Autonomously extracts RSS 2.0, Atom, and JSON feed endpoints using
Python standard library html.parser (0 extra dependencies):
1. HTML <link rel="alternate"> tags
2. Standard protocol endpoints (/feed, /rss.xml, /atom.xml, /.well-known/epistemic-feeds.json)
3. Direct feed URLs
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import httpx


@dataclass
class DiscoveredFeedCandidate:
    """Discovered candidate feed endpoint metadata."""

    feed_url: str
    title: str
    feed_type: str  # 'rss', 'atom', 'json_feed', 'well_known'
    source_url: str
    base_domain: str
    is_verified: bool = False


# Well-known feed paths to probe if HTML autodiscovery yields no link tags
WELL_KNOWN_FEED_PATHS = [
    "/feed",
    "/rss",
    "/rss.xml",
    "/feed.xml",
    "/atom.xml",
    "/index.xml",
    "/.well-known/epistemic-feeds.json",
]


class _FeedLinkHTMLParser(HTMLParser):
    """Zero-dependency HTML parser for extracting alternate feed links."""

    def __init__(self, source_url: str):
        super().__init__()
        self.source_url = source_url
        self.candidates: List[DiscoveredFeedCandidate] = []
        self.domain = urlparse(source_url).netloc.lower()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]):
        if tag.lower() != "link":
            return

        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        rel = attr_dict.get("rel", "").lower()
        if "alternate" not in rel:
            return

        feed_type_attr = attr_dict.get("type", "").lower()
        href = attr_dict.get("href", "")
        if not href:
            return

        full_url = urljoin(self.source_url, href)
        title = attr_dict.get("title") or f"{self.domain} Feed"

        if "atom" in feed_type_attr:
            self.candidates.append(
                DiscoveredFeedCandidate(
                    feed_url=full_url,
                    title=title.strip(),
                    feed_type="atom",
                    source_url=self.source_url,
                    base_domain=self.domain,
                )
            )
        elif "json" in feed_type_attr:
            self.candidates.append(
                DiscoveredFeedCandidate(
                    feed_url=full_url,
                    title=title.strip(),
                    feed_type="json_feed",
                    source_url=self.source_url,
                    base_domain=self.domain,
                )
            )
        elif "rss" in feed_type_attr or "xml" in feed_type_attr:
            self.candidates.append(
                DiscoveredFeedCandidate(
                    feed_url=full_url,
                    title=title.strip(),
                    feed_type="rss",
                    source_url=self.source_url,
                    base_domain=self.domain,
                )
            )


def extract_feeds_from_html(html_text: str, source_url: str) -> List[DiscoveredFeedCandidate]:
    """Parse HTML DOM and extract all alternate feed links using standard library parser."""
    parser = _FeedLinkHTMLParser(source_url)
    try:
        parser.feed(html_text)
    except Exception:
        pass
    return parser.candidates


async def discover_feed_endpoints(
    target_url: str,
    client: Optional[httpx.AsyncClient] = None,
    timeout_sec: float = 10.0,
) -> List[DiscoveredFeedCandidate]:
    """Dynamically discover candidate feed endpoints from any target website or URL."""
    parsed = urlparse(target_url)
    if not parsed.scheme:
        target_url = f"https://{target_url}"
        parsed = urlparse(target_url)

    domain = parsed.netloc.lower()
    base_origin = f"{parsed.scheme}://{domain}"

    candidates: List[DiscoveredFeedCandidate] = []
    seen_urls: set[str] = set()

    should_close = False
    if client is None:
        client = httpx.AsyncClient(
            timeout=timeout_sec,
            follow_redirects=True,
            headers={"User-Agent": "Credence-Epistemic-Feed-Discoverer/1.0"},
        )
        should_close = True

    try:
        # Step 1: Fetch HTML and inspect <link> tags
        try:
            resp = await client.get(target_url)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "").lower()
                text = resp.text

                # Check if target_url itself is directly an XML/RSS/Atom feed
                if "xml" in content_type or text.strip().startswith("<?xml") or "<rss" in text or "<feed" in text:
                    candidates.append(
                        DiscoveredFeedCandidate(
                            feed_url=str(resp.url),
                            title=f"{domain} (Direct Feed)",
                            feed_type="atom" if "<feed" in text else "rss",
                            source_url=target_url,
                            base_domain=domain,
                            is_verified=True,
                        )
                    )
                    return candidates

                # Extract HTML <link> tags
                html_candidates = extract_feeds_from_html(text, str(resp.url))
                for c in html_candidates:
                    if c.feed_url not in seen_urls:
                        seen_urls.add(c.feed_url)
                        candidates.append(c)
        except Exception:
            pass

        # Step 2: Probe well-known paths if no feeds found in HTML
        if not candidates:
            for path in WELL_KNOWN_FEED_PATHS:
                candidate_url = urljoin(base_origin, path)
                if candidate_url in seen_urls:
                    continue
                seen_urls.add(candidate_url)

                try:
                    head_resp = await client.get(candidate_url)
                    if head_resp.status_code == 200:
                        ct = head_resp.headers.get("content-type", "").lower()
                        body = head_resp.text
                        if (
                            "xml" in ct
                            or "json" in ct
                            or body.strip().startswith("<?xml")
                            or "<rss" in body
                            or "<feed" in body
                        ):
                            feed_type = "atom" if "<feed" in body else ("json_feed" if "json" in ct else "rss")
                            candidates.append(
                                DiscoveredFeedCandidate(
                                    feed_url=candidate_url,
                                    title=f"{domain} {path.strip('/')}",
                                    feed_type=feed_type,
                                    source_url=target_url,
                                    base_domain=domain,
                                    is_verified=True,
                                )
                            )
                            # Stop on first match
                            break
                except Exception:
                    continue

    finally:
        if should_close:
            await client.aclose()

    return candidates
