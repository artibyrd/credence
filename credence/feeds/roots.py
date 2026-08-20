"""Epistemic Root Expansion Engine for Credence.

Analyzes verified high-integrity articles, extracts cited external domains from HTML/markdown,
filters out noise/SSRF/social endpoints, discovers candidate RSS/Atom/JSON feeds,
and autonomously expands the node's subscription roots.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import httpx
from rich.console import Console
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.discovery import DiscoveredFeedCandidate, discover_feed_endpoints
from credence.feeds.parser import fetch_and_parse_feed
from credence.ingestion.extractor import extract_outbound_links
from credence.ingestion.security import is_safe_url
from credence.models import AuditRecord, FeedItemRecord, FeedSubscriptionRecord, SnapshotRecord, utc_now
from credence.subjects.registry import classify_subject

console = Console()

# Domains excluded from autonomous feed subscription (social networks, CDNs, search engines, shorteners)
EXCLUDED_CANDIDATE_DOMAINS: Set[str] = {
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "youtu.be",
    "t.co",
    "bit.ly",
    "tinyurl.com",
    "google.com",
    "bing.com",
    "yahoo.com",
    "duckduckgo.com",
    "linkedin.com",
    "reddit.com",
    "tiktok.com",
    "pinterest.com",
    "cloudflare.com",
    "gravatar.com",
    "w3.org",
    "schema.org",
    "github.com",
    "gitlab.com",
    "apple.com",
    "amazon.com",
    "doubleclick.net",
    "googletagmanager.com",
    "google-analytics.com",
    "ampproject.org",
    "cdn.ampproject.org",
    "wordpress.org",
    "medium.com",
    "substack.com",
}


@dataclass
class RootCandidate:
    """Discovered candidate root domain extracted from verified citations."""

    domain: str
    citation_count: int = 1
    citing_articles: List[str] = field(default_factory=list)
    avg_parent_trust: float = 100.0  # 100.0 - suspicion_score
    discovered_feed_urls: List[str] = field(default_factory=list)
    primary_subject: str = "journalism.news"
    validation_status: str = "discovered"  # discovered, verified, subscribed, skipped, no_feed_found


@dataclass
class RootExpansionSummary:
    """Summary of an autonomous root expansion cycle."""

    candidates_scanned: int = 0
    candidate_domains_evaluated: int = 0
    new_feeds_discovered: int = 0
    new_feeds_subscribed: int = 0
    initial_items_harvested: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)


def _normalize_domain(url_or_domain: str) -> str:
    """Normalize URL or domain string to lowercased netloc."""
    if not url_or_domain:
        return ""
    if not url_or_domain.startswith(("http://", "https://")):
        url_or_domain = f"https://{url_or_domain}"
    try:
        netloc = urlparse(url_or_domain).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def _is_candidate_eligible(domain: str, allow_local: bool = False) -> bool:
    """Check whether a domain is eligible for autonomous root expansion."""
    if not domain or len(domain) < 4 or "." not in domain:
        return False
    if domain in EXCLUDED_CANDIDATE_DOMAINS:
        return False
    # Check if domain ends with any excluded base domain
    for excluded in EXCLUDED_CANDIDATE_DOMAINS:
        if domain == excluded or domain.endswith(f".{excluded}"):
            return False
    # SSRF guard check
    test_url = f"https://{domain}"
    return is_safe_url(test_url, allow_local=allow_local)


async def extract_root_candidates(
    session: AsyncSession,
    min_parent_score: float = 75.0,  # Min parent trust for clean soil (100 - suspicion_score)
    limit: int = 20,
    allow_local: bool = False,
    soil_type: str = "clean",  # clean, adversarial, or all
) -> List[RootCandidate]:
    """Extract candidate external domains cited by verified articles from clean or adversarial soil."""
    max_suspicion = 100.0 - min_parent_score

    # 1. Fetch active subscriptions to exclude existing root sources
    stmt_subs = select(FeedSubscriptionRecord)
    subs = (await session.exec(stmt_subs)).all()
    subscribed_domains = {_normalize_domain(s.feed_url) for s in subs}

    # 2. Fetch audit records based on requested soil_type
    stmt_audits = (
        select(AuditRecord, SnapshotRecord)
        .join(SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id))
    )
    if soil_type == "clean":
        stmt_audits = stmt_audits.where(AuditRecord.suspicion_score <= max_suspicion)
    elif soil_type == "adversarial":
        stmt_audits = stmt_audits.where(AuditRecord.suspicion_score >= 50.0)

    stmt_audits = stmt_audits.order_by(col(AuditRecord.audited_at).desc()).limit(100)
    results = (await session.exec(stmt_audits)).all()

    candidates_map: Dict[str, RootCandidate] = {}

    for audit, snap in results:
        parent_url = snap.url or ""
        parent_domain = _normalize_domain(parent_url)
        parent_trust = round(100.0 - audit.suspicion_score, 1)

        # Extract links from stored DOM or HTML snapshot
        links: List[str] = []
        if snap.dom_file_path and Path(snap.dom_file_path).exists():
            try:
                html_text = Path(snap.dom_file_path).read_text(encoding="utf-8", errors="ignore")
                links = extract_outbound_links(html_text)
            except Exception:
                pass

        # If no DOM file, check if links exist in snapshot url or title
        for link in links:
            cand_domain = _normalize_domain(link)
            if not cand_domain or cand_domain == parent_domain:
                continue
            if cand_domain in subscribed_domains:
                continue
            if not _is_candidate_eligible(cand_domain, allow_local=allow_local):
                continue

            if cand_domain not in candidates_map:
                classified_subject, _ = classify_subject(cand_domain)
                candidates_map[cand_domain] = RootCandidate(
                    domain=cand_domain,
                    citation_count=1,
                    citing_articles=[parent_url] if parent_url else [],
                    avg_parent_trust=parent_trust,
                    primary_subject=classified_subject,
                )
            else:
                c = candidates_map[cand_domain]
                c.citation_count += 1
                if parent_url and parent_url not in c.citing_articles:
                    c.citing_articles.append(parent_url)
                c.avg_parent_trust = round((c.avg_parent_trust + parent_trust) / 2.0, 1)

    # Rank candidates: clean soil prefers higher trust; adversarial soil prefers higher citation frequency
    if soil_type == "adversarial":
        ranked = sorted(
            candidates_map.values(),
            key=lambda c: (c.citation_count, -c.avg_parent_trust),
            reverse=True,
        )
    else:
        ranked = sorted(
            candidates_map.values(),
            key=lambda c: (c.citation_count, c.avg_parent_trust),
            reverse=True,
        )
    return ranked[:limit]


async def expand_roots(
    session: AsyncSession,
    max_new_sources: int = 5,
    min_citation_count: int = 1,
    dry_run: bool = False,
    allow_local: bool = False,
    client: Optional[httpx.AsyncClient] = None,
) -> RootExpansionSummary:
    """Autonomously discover and subscribe to new high-value feeds from cited candidate roots."""
    summary = RootExpansionSummary()
    candidates = await extract_root_candidates(session, limit=30, allow_local=allow_local)
    summary.candidates_scanned = len(candidates)

    eligible_candidates = [c for c in candidates if c.citation_count >= min_citation_count][:max_new_sources]
    summary.candidate_domains_evaluated = len(eligible_candidates)

    for cand in eligible_candidates:
        target_url = f"https://{cand.domain}"
        try:
            # 1. Discover feed endpoints
            discovered = await discover_feed_endpoints(target_url, client=client, timeout_sec=8.0)
            if not discovered:
                cand.validation_status = "no_feed_found"
                summary.details.append(
                    {
                        "domain": cand.domain,
                        "status": "no_feed_found",
                        "citation_count": cand.citation_count,
                    }
                )
                continue

            # Pick the primary/highest-priority discovered feed candidate
            feed_cand: DiscoveredFeedCandidate = discovered[0]
            cand.discovered_feed_urls = [d.feed_url for d in discovered]
            summary.new_feeds_discovered += len(discovered)

            if dry_run:
                cand.validation_status = "dry_run_discovered"
                summary.details.append(
                    {
                        "domain": cand.domain,
                        "feed_url": feed_cand.feed_url,
                        "title": feed_cand.title,
                        "status": "dry_run_discovered",
                        "feed_type": feed_cand.feed_type,
                    }
                )
                continue

            # 2. Check if already subscribed to this exact feed URL
            stmt_existing = select(FeedSubscriptionRecord).where(FeedSubscriptionRecord.feed_url == feed_cand.feed_url)
            existing_sub = (await session.exec(stmt_existing)).first()
            if existing_sub:
                cand.validation_status = "already_subscribed"
                continue

            # 3. Verify feed content validity
            parsed = await fetch_and_parse_feed(feed_cand.feed_url)
            title = parsed.title or feed_cand.title or f"{cand.domain} Feed"

            # 4. Auto-register new FeedSubscriptionRecord
            new_sub = FeedSubscriptionRecord(
                feed_url=feed_cand.feed_url,
                title=title,
                feed_format=parsed.feed_format,
                subject_tag=cand.primary_subject,
                priority_tier=2,  # Discovered roots default to Tier 2 News
                etag=parsed.etag,
                last_modified=parsed.last_modified,
                last_polled_at=utc_now(),
                is_active=True,
            )
            session.add(new_sub)
            await session.commit()
            await session.refresh(new_sub)

            summary.new_feeds_subscribed += 1
            cand.validation_status = "subscribed"

            # 5. Harvest initial entries into FeedItemRecord queue
            harvested_count = 0
            for entry in parsed.entries[:10]:
                stmt_item = select(FeedItemRecord).where(FeedItemRecord.item_url == entry.url)
                if (await session.exec(stmt_item)).first():
                    continue

                item_subject, _ = classify_subject(f"{entry.title} {entry.summary or ''}")
                item_record = FeedItemRecord(
                    item_url=entry.url,
                    feed_id=new_sub.id,
                    title=entry.title,
                    subject_id=item_subject or cand.primary_subject,
                    published_at=entry.published_at,
                    discovered_at=utc_now(),
                    processing_status="pending",
                )
                session.add(item_record)
                harvested_count += 1

            if harvested_count > 0:
                await session.commit()
                summary.initial_items_harvested += harvested_count

            summary.details.append(
                {
                    "domain": cand.domain,
                    "feed_url": new_sub.feed_url,
                    "title": new_sub.title,
                    "status": "subscribed",
                    "items_harvested": harvested_count,
                    "subject": new_sub.subject_tag,
                }
            )
            console.print(
                f"[bold green]🌱 Root Expanded:[/] Subscribed to [bold]{new_sub.title}[/] ({new_sub.feed_url}) "
                f"[{harvested_count} initial items queued]"
            )

        except Exception as e:
            cand.validation_status = "error"
            summary.details.append(
                {
                    "domain": cand.domain,
                    "status": "error",
                    "error": str(e),
                }
            )

    return summary


async def get_root_tree(session: AsyncSession) -> Dict[str, Any]:
    """Compute the hierarchical tree of subscriptions, active roots, and citation branches."""
    from sqlmodel import func

    # Active subscriptions
    stmt_subs = select(FeedSubscriptionRecord).order_by(col(FeedSubscriptionRecord.priority_tier).asc())
    subs = (await session.exec(stmt_subs)).all()

    # Total feed items per feed
    tree_nodes = []
    total_items = 0

    for sub in subs:
        stmt_count = select(func.count(col(FeedItemRecord.id))).where(FeedItemRecord.feed_id == sub.id)
        count = (await session.exec(stmt_count)).first() or 0
        total_items += count

        domain = _normalize_domain(sub.feed_url)
        tree_nodes.append(
            {
                "id": sub.id,
                "title": sub.title or sub.feed_url,
                "feed_url": sub.feed_url,
                "domain": domain,
                "subject": sub.subject_tag,
                "priority_tier": sub.priority_tier,
                "is_active": sub.is_active,
                "items_count": count,
                "last_polled_at": sub.last_polled_at.isoformat() if sub.last_polled_at else None,
            }
        )

    # Unsubscribed candidates waiting in citation soil
    candidates = await extract_root_candidates(session, limit=10)
    candidate_list = [
        {
            "domain": c.domain,
            "citation_count": c.citation_count,
            "avg_parent_trust": c.avg_parent_trust,
            "primary_subject": c.primary_subject,
            "citing_articles_count": len(c.citing_articles),
        }
        for c in candidates
    ]

    return {
        "total_active_roots": len(subs),
        "total_harvested_items": total_items,
        "active_roots": tree_nodes,
        "pending_citation_candidates": candidate_list,
        "generated_at": utc_now().isoformat(),
    }
