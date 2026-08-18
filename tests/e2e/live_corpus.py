"""Dynamic Live Site Corpus & Stratified Mutation Engine for Credence E2E Testing.

Provides a diverse, rotating, and mutating catalog of live target websites and RSS feeds
across 5 epistemic categories:
1. Reference & Epistemic Authority (Wikipedia, Stanford Encyclopedia, Nature)
2. Verified Satire & Parody (The Onion, Babylon Bee, Daily Mash)
3. Investigative Journalism (AP News, BBC, Reuters, NPR, The Guardian)
4. Tech & Commercial Media (Hacker News, Ars Technica, The Verge)
5. Syndicated Live RSS Feeds (BBC RSS, Hacker News RSS, Ars Technica RSS, NPR RSS)

Supports deterministic daily rotation (YYYY-MM-DD seed) or customizable pseudo-random
mutation via CREDENCE_LIVE_SEED environment variable.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from credence.feeds.parser import fetch_and_parse_feed


@dataclass(frozen=True)
class LiveCorpusEntry:
    """Descriptor for a live website target used in E2E testing."""

    url: str
    category: str
    expected_classification: str
    is_satire: bool
    title: str
    description: str


# --- Master Corpus Catalog across 5 Epistemic Categories ---

LIVE_CORPUS: Dict[str, List[LiveCorpusEntry]] = {
    "reference": [
        LiveCorpusEntry(
            url="https://en.wikipedia.org/wiki/Epistemology",
            category="reference",
            expected_classification="CLEAN",
            is_satire=False,
            title="Wikipedia: Epistemology",
            description="Foundational branch of philosophy concerning knowledge and justified belief.",
        ),
        LiveCorpusEntry(
            url="https://en.wikipedia.org/wiki/Scientific_method",
            category="reference",
            expected_classification="CLEAN",
            is_satire=False,
            title="Wikipedia: Scientific Method",
            description="Empirical method of knowledge acquisition characterizing natural sciences.",
        ),
        LiveCorpusEntry(
            url="https://plato.stanford.edu/entries/epistemology/",
            category="reference",
            expected_classification="CLEAN",
            is_satire=False,
            title="Stanford Encyclopedia: Epistemology",
            description="Peer-reviewed scholarly reference on epistemic justification.",
        ),
        LiveCorpusEntry(
            url="https://en.wikipedia.org/wiki/Peer_review",
            category="reference",
            expected_classification="CLEAN",
            is_satire=False,
            title="Wikipedia: Peer Review",
            description="Scholarly evaluation process of work by experts in the same field.",
        ),
    ],
    "satire": [
        LiveCorpusEntry(
            url="https://theonion.com",
            category="satire",
            expected_classification="SATIRE_PARODY",
            is_satire=True,
            title="The Onion",
            description="Prominent American satirical digital media and news satire organization.",
        ),
        LiveCorpusEntry(
            url="https://babylonbee.com",
            category="satire",
            expected_classification="SATIRE_PARODY",
            is_satire=True,
            title="The Babylon Bee",
            description="Satirical news website covering politics, religion, and current affairs.",
        ),
        LiveCorpusEntry(
            url="https://www.thedailymash.co.uk",
            category="satire",
            expected_classification="SATIRE_PARODY",
            is_satire=True,
            title="The Daily Mash",
            description="British satirical publication featuring humorous and absurd fabricated stories.",
        ),
        LiveCorpusEntry(
            url="https://waterfordwhispersnews.com",
            category="satire",
            expected_classification="SATIRE_PARODY",
            is_satire=True,
            title="Waterford Whispers News",
            description="Irish satirical news website publishing humorous articles and social commentary.",
        ),
    ],
    "journalism": [
        LiveCorpusEntry(
            url="https://apnews.com",
            category="journalism",
            expected_classification="LOW_SUSPICION",
            is_satire=False,
            title="Associated Press News",
            description="Independent global investigative wire service following strict SPJ standards.",
        ),
        LiveCorpusEntry(
            url="https://www.bbc.com/news",
            category="journalism",
            expected_classification="LOW_SUSPICION",
            is_satire=False,
            title="BBC News",
            description="Public service broadcaster international news desk.",
        ),
        LiveCorpusEntry(
            url="https://www.reuters.com",
            category="journalism",
            expected_classification="LOW_SUSPICION",
            is_satire=False,
            title="Reuters",
            description="International news agency and investigative wire service.",
        ),
        LiveCorpusEntry(
            url="https://www.npr.org/sections/news/",
            category="journalism",
            expected_classification="LOW_SUSPICION",
            is_satire=False,
            title="NPR News",
            description="National Public Radio primary coverage desk.",
        ),
    ],
    "tech_media": [
        LiveCorpusEntry(
            url="https://news.ycombinator.com",
            category="tech_media",
            expected_classification="LOW_SUSPICION",
            is_satire=False,
            title="Hacker News",
            description="Community-curated tech, science, and engineering aggregator.",
        ),
        LiveCorpusEntry(
            url="https://arstechnica.com",
            category="tech_media",
            expected_classification="LOW_SUSPICION",
            is_satire=False,
            title="Ars Technica",
            description="Technology publication covering science, policy, and engineering.",
        ),
        LiveCorpusEntry(
            url="https://www.theverge.com",
            category="tech_media",
            expected_classification="LOW_SUSPICION",
            is_satire=False,
            title="The Verge",
            description="Technology, science, and culture digital publication.",
        ),
    ],
    "rss_feeds": [
        LiveCorpusEntry(
            url="https://feeds.bbci.co.uk/news/rss.xml",
            category="rss_feeds",
            expected_classification="FEED_ACTIVE",
            is_satire=False,
            title="BBC News World RSS",
            description="Syndicated XML feed for BBC World News top stories.",
        ),
        LiveCorpusEntry(
            url="https://news.ycombinator.com/rss",
            category="rss_feeds",
            expected_classification="FEED_ACTIVE",
            is_satire=False,
            title="Hacker News RSS Feed",
            description="Syndicated top submissions feed from Hacker News.",
        ),
        LiveCorpusEntry(
            url="https://feeds.arstechnica.com/arstechnica/index",
            category="rss_feeds",
            expected_classification="FEED_ACTIVE",
            is_satire=False,
            title="Ars Technica Main RSS Feed",
            description="Syndicated technology and scientific journalism feed.",
        ),
        LiveCorpusEntry(
            url="https://feeds.npr.org/1001/rss.xml",
            category="rss_feeds",
            expected_classification="FEED_ACTIVE",
            is_satire=False,
            title="NPR News RSS Feed",
            description="Syndicated national public radio top stories feed.",
        ),
    ],
}


def get_active_seed(custom_seed: Optional[str] = None) -> str:
    """Return the deterministic rotation seed (defaults to date YYYY-MM-DD or env var)."""
    if custom_seed:
        return custom_seed
    env_seed = os.getenv("CREDENCE_LIVE_SEED")
    if env_seed:
        return env_seed
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_rotating_sample(
    category: str,
    seed: Optional[str] = None,
    count: int = 1,
) -> List[LiveCorpusEntry]:
    """Deterministically sample N targets from a category based on the current seed."""
    candidates = LIVE_CORPUS.get(category, [])
    if not candidates:
        raise ValueError(f"Unknown category '{category}'. Valid: {list(LIVE_CORPUS.keys())}")

    active_seed = get_active_seed(seed)
    # Compute deterministic offset hash
    seed_hash = hashlib.sha256(f"{active_seed}:{category}".encode("utf-8")).hexdigest()
    start_idx = int(seed_hash, 16) % len(candidates)

    selected: List[LiveCorpusEntry] = []
    for i in range(min(count, len(candidates))):
        idx = (start_idx + i) % len(candidates)
        selected.append(candidates[idx])
    return selected


def get_full_stratified_rotation(
    seed: Optional[str] = None,
    count_per_category: int = 1,
) -> Dict[str, List[LiveCorpusEntry]]:
    """Return a complete stratified rotating sample covering all 5 categories."""
    result: Dict[str, List[LiveCorpusEntry]] = {}
    for cat in LIVE_CORPUS:
        result[cat] = get_rotating_sample(cat, seed=seed, count=count_per_category)
    return result


async def extract_dynamic_feed_articles(feed_url: str, max_articles: int = 2) -> List[str]:
    """Fetch live RSS feed and dynamically extract fresh article URLs published in real-time."""
    parsed = await fetch_and_parse_feed(feed_url)
    article_urls: List[str] = []
    for entry in parsed.entries:
        if entry.url and entry.url.startswith("http") and entry.url not in article_urls:
            article_urls.append(entry.url)
        if len(article_urls) >= max_articles:
            break
    return article_urls
