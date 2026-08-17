"""Rate-Governed Feed Synchronization Worker and Ingestion Scheduler.

Orchestrates HTTP conditional polling, priority triage, mesh-aware effort avoidance,
and generous attestation seeding with strict token budget headroom protection.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.dedup import check_mesh_effort_avoidance
from credence.feeds.parser import fetch_and_parse_feed
from credence.models import FeedItemRecord, FeedSubscriptionRecord, utc_now
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
    subscription: FeedSubscriptionRecord,
    summary: FeedSyncSummary,
    dry_run: bool,
    now: datetime,
) -> None:
    """Process an individual feed entry with effort avoidance and headroom checks."""
    stmt_item = select(FeedItemRecord).where(FeedItemRecord.item_url == entry.url)
    existing = (await session.exec(stmt_item)).first()
    if existing:
        return

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

    item_record = FeedItemRecord(
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
    headroom = await get_token_headroom_status(session)
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

    summary.details.append(
        {
            "url": entry.url,
            "status": "pending_local_audit",
            "subject": classified_subject,
        }
    )


async def sync_single_feed(
    session: AsyncSession,
    subscription: FeedSubscriptionRecord,
    dry_run: bool = False,
    evaluate_novel: bool = True,
) -> FeedSyncSummary:
    """Synchronize a single syndicated feed subscription."""
    summary = FeedSyncSummary(total_feeds_polled=1)
    sem = _get_domain_semaphore(subscription.feed_url)

    async with sem:
        try:
            parsed = await fetch_and_parse_feed(
                feed_url=subscription.feed_url,
                etag=subscription.etag,
                last_modified=subscription.last_modified,
            )
        except Exception as e:
            summary.details.append({"feed": subscription.feed_url, "error": str(e)})
            return summary

    now = utc_now()
    if not parsed.is_modified:
        summary.feeds_unmodified_304 = 1
        if not dry_run:
            subscription.last_polled_at = now
            await session.commit()
        return summary

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
        )

    return summary


async def sync_all_feeds(
    session: AsyncSession,
    dry_run: bool = False,
    evaluate_novel: bool = True,
) -> FeedSyncSummary:
    """Synchronize all active feed subscriptions ordered by priority tier."""
    stmt = (
        select(FeedSubscriptionRecord)
        .where(FeedSubscriptionRecord.is_active == True)  # noqa: E712
        .order_by(col(FeedSubscriptionRecord.priority_tier).asc())
    )
    subscriptions = (await session.exec(stmt)).all()

    aggregate = FeedSyncSummary()
    for sub in subscriptions:
        sub_summary = await sync_single_feed(
            session=session,
            subscription=sub,
            dry_run=dry_run,
            evaluate_novel=evaluate_novel,
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
