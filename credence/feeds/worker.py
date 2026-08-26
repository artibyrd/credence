"""Rate-Governed Feed Synchronization Worker and Ingestion Scheduler.

Orchestrates HTTP conditional polling, priority triage, mesh-aware effort avoidance,
and generous attestation seeding with strict token budget headroom protection.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.dedup import check_mesh_effort_avoidance
from credence.feeds.parser import fetch_and_parse_feed
from credence.models import Audit, FeedItem, FeedSubscription, Snapshot, utc_now
from credence.pipeline.governor import get_token_headroom_status
from credence.subjects.registry import classify_subject


@dataclass
class FeedSyncSummary:
    """Summary of a feed synchronization cycle."""

    total_feeds_polled: int = 0
    feeds_unmodified_304: int = 0
    new_items_discovered: int = 0
    items_adopted_from_mesh: int = 0
    items_evaluated_locally: int = 0
    items_deferred_budget: int = 0
    tokens_saved_total: int = 0
    details: List[Dict[str, str]] = field(default_factory=list)


# Per-domain outbound HTTP concurrency semaphore (Max 2 concurrent per domain)
_DOMAIN_SEMAPHORES: Dict[str, asyncio.Semaphore] = {}


def _get_domain_semaphore(url: str) -> asyncio.Semaphore:
    """Get or create per-domain rate limiting semaphore."""
    domain = urlparse(url).netloc.lower()
    if domain not in _DOMAIN_SEMAPHORES:
        _DOMAIN_SEMAPHORES[domain] = asyncio.Semaphore(2)
    return _DOMAIN_SEMAPHORES[domain]


async def _process_single_entry(
    session: AsyncSession,
    entry: Any,
    subscription: FeedSubscription,
    summary: FeedSyncSummary,
    dry_run: bool,
    now: datetime,
    evaluate_novel: bool = True,
    profile_override: Any = None,
) -> None:
    """Process an individual feed entry with effort avoidance, headroom checks, and live audit."""
    stmt_item = select(FeedItem).where(FeedItem.item_url == entry.url)
    existing = (await session.exec(stmt_item)).first()
    if existing:
        if not evaluate_novel or existing.processing_status == "audited":
            return

        stmt_audit_exists = (
            select(Audit).join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id)).where(Snapshot.url == entry.url)
        )
        if (await session.exec(stmt_audit_exists)).first():
            existing.processing_status = "audited"
            session.add(existing)
            await session.commit()
            return
        item_record = existing
    else:
        summary.new_items_discovered += 1
        classified_subject, _ = classify_subject(f"{entry.title} {entry.summary or ''}")

        if dry_run:
            summary.details.append(
                {
                    "url": entry.url,
                    "title": entry.title,
                    "subject": classified_subject,
                    "action": "dry_run_discovered",
                }
            )
            return

        item_record = FeedItem(
            item_url=entry.url,
            feed_id=subscription.id,
            title=entry.title,
            subject_id=classified_subject,
            published_at=entry.published_at,
            discovered_at=now,
            processing_status="pending",
        )
        session.add(item_record)
        await session.commit()
        await session.refresh(item_record)

    # Effort Avoidance Check
    dedup_result = await check_mesh_effort_avoidance(session, entry.url)
    if dedup_result.status in ("local_cached", "mesh_adopted"):
        summary.items_adopted_from_mesh += 1
        summary.tokens_saved_total += dedup_result.tokens_saved
        summary.details.append(
            {
                "url": entry.url,
                "status": "mesh_adopted",
                "node": str(dedup_result.adopted_from_node or "local"),
                "tokens_saved": str(dedup_result.tokens_saved),
            }
        )
        return

    # Check Token Budget Governor Headroom
    headroom = await get_token_headroom_status(session, profile_override=profile_override)
    if headroom.circuit_breaker_tripped or headroom.daily_headroom_pct < 30.0:
        item_record.processing_status = "skipped"
        await session.commit()
        summary.items_deferred_budget += 1
        summary.details.append(
            {
                "url": entry.url,
                "status": "deferred_budget_headroom",
            }
        )
        return

    if evaluate_novel:
        try:
            from credence.pipeline.evaluator import audit_url

            report = await audit_url(
                entry.url,
                force_refresh=False,
                profile_override=profile_override,
            )
            item_record.processing_status = "audited"
            await session.commit()
            summary.items_evaluated_locally += 1
            summary.details.append(
                {
                    "url": entry.url,
                    "status": "audited_locally",
                    "score": f"{report.suspicion_score:.1f}",
                    "classification": report.classification,
                }
            )
        except Exception as e:
            item_record.processing_status = "error"
            await session.commit()
            summary.details.append(
                {
                    "url": entry.url,
                    "status": "audit_error",
                    "error": str(e),
                }
            )
    else:
        summary.details.append(
            {
                "url": entry.url,
                "status": "pending_local_audit",
                "subject": classified_subject,
            }
        )


async def sync_single_feed(
    session: AsyncSession,
    subscription: FeedSubscription,
    dry_run: bool = False,
    evaluate_novel: bool = True,
    profile_override: Any = None,
    force_refresh: bool = False,
) -> FeedSyncSummary:
    """Synchronize a single syndicated feed subscription."""
    summary = FeedSyncSummary(total_feeds_polled=1)
    sem = _get_domain_semaphore(subscription.feed_url)

    async with sem:
        try:
            parsed = await fetch_and_parse_feed(
                feed_url=subscription.feed_url,
                etag=None if force_refresh else subscription.etag,
                last_modified=None if force_refresh else subscription.last_modified,
            )
        except Exception as e:
            summary.details.append({"feed": subscription.feed_url, "error": str(e)})
            return summary

    now = utc_now()
    if not parsed.is_modified and not force_refresh:
        summary.feeds_unmodified_304 = 1
        if not dry_run:
            subscription.last_polled_at = now
            await session.commit()
    else:
        # Update subscription metadata
        if not dry_run:
            subscription.etag = parsed.etag
            subscription.last_modified = parsed.last_modified
            subscription.last_polled_at = now
            if parsed.title and not subscription.title:
                subscription.title = parsed.title
            await session.commit()

        # Process discovered feed items
        for entry in parsed.entries:
            await _process_single_entry(
                session=session,
                entry=entry,
                subscription=subscription,
                summary=summary,
                dry_run=dry_run,
                now=now,
                evaluate_novel=evaluate_novel,
                profile_override=profile_override,
            )

    return summary


async def sync_all_feeds(
    session: AsyncSession,
    dry_run: bool = False,
    evaluate_novel: bool = True,
    profile_override: Any = None,
) -> FeedSyncSummary:
    """Synchronize all active feed subscriptions ordered by sentinel priority and priority tier."""
    stmt = (
        select(FeedSubscription)
        .where(FeedSubscription.is_active == True)  # noqa: E712
        .order_by(col(FeedSubscription.is_sentinel).desc(), col(FeedSubscription.priority_tier).asc())
    )
    subscriptions = (await session.exec(stmt)).all()

    # Auto-bootstrap presets if subscription catalog is empty
    if not subscriptions and not dry_run:
        await bootstrap_preset_feeds(session)
        subscriptions = (await session.exec(stmt)).all()

    aggregate = FeedSyncSummary()
    for sub in subscriptions:
        sub_summary = await sync_single_feed(
            session=session,
            subscription=sub,
            dry_run=dry_run,
            evaluate_novel=evaluate_novel,
            profile_override=profile_override,
        )
        aggregate.total_feeds_polled += sub_summary.total_feeds_polled
        aggregate.feeds_unmodified_304 += sub_summary.feeds_unmodified_304
        aggregate.new_items_discovered += sub_summary.new_items_discovered
        aggregate.items_adopted_from_mesh += sub_summary.items_adopted_from_mesh
        aggregate.items_evaluated_locally += sub_summary.items_evaluated_locally
        aggregate.items_deferred_budget += sub_summary.items_deferred_budget
        aggregate.tokens_saved_total += sub_summary.tokens_saved_total
        aggregate.details.extend(sub_summary.details)

    return aggregate


# Convenient alias for sifter daemon
sync_subscribed_feeds = sync_all_feeds


# ============================================================================
# Categorized Diverse Feed Presets & Rendezvous Hashing Partitioning
# ============================================================================

PRESET_FEED_CATALOGS = {
    "core-news": [
        ("AP News: Top Stories", "https://apnews.com/rss", 1),
        ("Reuters: World News", "https://www.reutersagency.com/feed/?best-topics=world", 1),
        ("NPR News: Headlines", "https://feeds.npr.org/1001/rss.xml", 2),
        ("BBC News: World", "https://feeds.bbci.co.uk/news/world/rss.xml", 2),
        ("The Guardian: World News", "https://www.theguardian.com/world/rss", 2),
    ],
    "investigative-tech": [
        ("ProPublica: Main Feeds", "https://www.propublica.org/feeds/propublica/main", 1),
        ("The Markup: Investigations", "https://themarkup.org/feeds/rss.xml", 1),
        ("Ars Technica: Technology Lab", "https://feeds.arstechnica.com/arstechnica/technology-lab", 2),
        ("Krebs on Security", "https://krebsonsecurity.com/feed/", 2),
        ("404 Media", "https://www.404media.co/rss/", 2),
        ("EFF Deeplinks", "https://www.eff.org/rss/updates.xml", 2),
    ],
    "science-preprints": [
        ("Nature: Latest Research", "https://www.nature.com/nature.rss", 1),
        ("arXiv: Artificial Intelligence", "https://rss.arxiv.org/rss/cs.AI", 2),
        ("ScienceDaily: Top Science", "https://www.sciencedaily.com/rss/top/science.xml", 2),
        ("Retraction Watch", "https://retractionwatch.com/feed/", 2),
        ("NIH News Releases", "https://www.nih.gov/news-events/news-releases/feed.xml", 2),
    ],
    "regional-civic": [
        ("InMaricopa: Local News & Civic", "https://inmaricopa.com/feed/", 1),
        ("CalMatters: California Policy", "https://calmatters.org/feed/", 2),
        ("The Texas Tribune", "https://www.texastribune.org/feeds/main/", 2),
        ("Spotlight PA", "https://www.spotlightpa.org/feeds/rss.xml", 2),
        ("Voice of San Diego", "https://voiceofsandiego.org/feed/", 2),
    ],
    "financial-corporate": [
        ("MarketWatch: Top Stories", "https://feeds.content.dowjones.io/public/rss/mw_topstories", 2),
        ("SEC Press Releases", "https://www.sec.gov/news/pressreleases.rss", 2),
        ("FTC Press Releases", "https://www.ftc.gov/news-events/news/press-releases/feed", 2),
    ],
    "satire-commentary": [
        ("The Onion: American Finest News", "https://www.theonion.com/rss", 3),
        ("The Babylon Bee", "https://babylonbee.com/feed", 3),
    ],
}


def compute_feed_affinity(node_pubkey: str, feed_url: str) -> float:
    """Calculate Rendezvous Hash (HRW) affinity score between node pubkey and feed URL."""
    import hashlib

    combined = f"{node_pubkey}:{feed_url}".encode("utf-8")
    digest = hashlib.sha256(combined).hexdigest()
    # Normalize hex hash to a deterministic float in [0.0, 1.0]
    return int(digest[:8], 16) / 0xFFFFFFFF


async def bootstrap_preset_feeds(
    session: AsyncSession,
    category: Optional[str] = None,
    node_pubkey: Optional[str] = None,
) -> int:
    """Populate initial diverse feed subscriptions."""
    added_count = 0
    categories = [category] if category and category in PRESET_FEED_CATALOGS else list(PRESET_FEED_CATALOGS.keys())

    for cat in categories:
        for title, url, priority in PRESET_FEED_CATALOGS[cat]:
            try:
                stmt = select(FeedSubscription).where(FeedSubscription.feed_url == url)
                existing = (await session.exec(stmt)).first()
                if not existing:
                    sub = FeedSubscription(
                        feed_url=url,
                        title=title,
                        priority_tier=priority,
                        is_active=True,
                        is_sentinel=False,
                        sentinel_interval_seconds=300,
                    )
                    session.add(sub)
                    await session.commit()
                    added_count += 1
            except Exception:
                await session.rollback()

    return added_count
