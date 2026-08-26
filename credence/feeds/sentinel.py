"""Sentinel Mode Engine and High-Priority Source Scheduler for Credence.

Governed by Invariants:
- inv-untrusted-ingestion (SSRF & network boundary validation)
- inv-topic-entropy-defense (Astroturfing & spam demotion)
- inv-cart-before-horse & 500 LOC Ceiling Law (<180 LOC)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain
from credence.ingestion.security import is_safe_url
from credence.models import FeedSubscription, utc_now

MAX_ACTIVE_SENTINELS: int = 10
MIN_SENTINEL_INTERVAL_SECONDS: int = 60
DEFAULT_SENTINEL_INTERVAL_SECONDS: int = 300
MAX_SENTINEL_BURST_RATIO: float = 0.50


def compute_sentinel_poll_due(subscription: FeedSubscription, now: Optional[datetime] = None) -> bool:
    """Determine whether a sentinel feed is due for prioritized polling."""
    if not subscription.is_sentinel or not subscription.is_active:
        return False
    if subscription.last_polled_at is None:
        return True
    current_time = now or utc_now()
    if subscription.last_polled_at.tzinfo is None:
        last_poll = subscription.last_polled_at.replace(tzinfo=timezone.utc)
    else:
        last_poll = subscription.last_polled_at
    interval = max(MIN_SENTINEL_INTERVAL_SECONDS, subscription.sentinel_interval_seconds)
    return (current_time - last_poll).total_seconds() >= interval


def partition_ingestion_burst(
    sentinel_items: List[Any],
    organic_items: List[Any],
    total_burst: int,
    max_sentinel_ratio: float = MAX_SENTINEL_BURST_RATIO,
) -> List[Any]:
    """Partition ingestion burst enforcing the Guaranteed Organic Soil Floor (>= 50%)."""
    if total_burst <= 0:
        return []
    max_sentinels = max(0, int(total_burst * max_sentinel_ratio))
    selected: List[Any] = []

    # 1. Take up to max_sentinels from sentinel items
    sentinel_picks = sentinel_items[:max_sentinels]
    selected.extend(sentinel_picks)

    # 2. Fill remaining slots from organic items (guaranteeing at least 50% capacity)
    remaining_slots = total_burst - len(selected)
    organic_picks = organic_items[:remaining_slots]
    selected.extend(organic_picks)

    # 3. If organic queue is starved, fall back to remaining sentinel items
    if len(selected) < total_burst:
        extra_slots = total_burst - len(selected)
        selected.extend(sentinel_items[max_sentinels : max_sentinels + extra_slots])

    return selected


async def set_feed_sentinel_mode(
    session: AsyncSession,
    target: str,
    enabled: bool = True,
    interval_seconds: int = DEFAULT_SENTINEL_INTERVAL_SECONDS,
    allow_local: bool = False,
) -> Dict[str, Any]:
    """Enable or disable Sentinel Mode for a specific feed URL or domain."""
    if not target or not target.strip():
        raise ValueError("Target feed URL or domain must not be empty.")

    target_clean = target.strip()
    if not target_clean.startswith(("http://", "https://")):
        feed_url = f"https://{target_clean}/feed/"
        domain = normalize_domain(target_clean)
    else:
        feed_url = target_clean
        domain = normalize_domain(target_clean)

    # SSRF & Network Security Validation
    if not is_safe_url(feed_url, allow_local=allow_local):
        raise ValueError(f"Security Rejection: Target URL '{feed_url}' violates untrusted ingestion boundaries (SSRF).")

    interval = max(MIN_SENTINEL_INTERVAL_SECONDS, int(interval_seconds))

    from sqlmodel import or_

    # Find subscription by feed_url or matching domain
    stmt = select(FeedSubscription).where(
        or_(col(FeedSubscription.feed_url) == feed_url, col(FeedSubscription.feed_url).like(f"%{domain}%"))
    )
    sub = (await session.exec(stmt)).first()

    if enabled:
        # Check active capacity ceiling
        stmt_active = select(FeedSubscription).where(
            FeedSubscription.is_sentinel == True,  # noqa: E712
            FeedSubscription.is_active == True,  # noqa: E712
        )
        active_sentinels = (await session.exec(stmt_active)).all()
        if len(active_sentinels) >= MAX_ACTIVE_SENTINELS and (not sub or not sub.is_sentinel):
            raise ValueError(
                f"Sentinel capacity ceiling reached: maximum of {MAX_ACTIVE_SENTINELS} active sentinels allowed."
            )

        if not sub:
            sub = FeedSubscription(
                feed_url=feed_url,
                title=f"{domain} (Sentinel)",
                priority_tier=1,
                is_active=True,
                is_sentinel=True,
                sentinel_interval_seconds=interval,
            )
            session.add(sub)
        else:
            sub.is_sentinel = True
            sub.sentinel_interval_seconds = interval
            sub.is_active = True
            session.add(sub)

        # Update domain reputation record sentinel flag (preserves quarantine status)
        rep = await get_or_create_domain_reputation(session, domain)
        rep.is_sentinel = True
        session.add(rep)
        await session.commit()
        await session.refresh(sub)

        return {
            "status": "enabled",
            "domain": domain,
            "feed_url": sub.feed_url,
            "interval_seconds": sub.sentinel_interval_seconds,
            "is_sentinel": True,
            "priority_tier": sub.priority_tier,
            "quarantine_status": rep.status,
        }
    else:
        if sub:
            sub.is_sentinel = False
            session.add(sub)
        rep = await get_or_create_domain_reputation(session, domain)
        rep.is_sentinel = False
        session.add(rep)
        await session.commit()
        if sub:
            await session.refresh(sub)

        return {
            "status": "disabled",
            "domain": domain,
            "feed_url": sub.feed_url if sub else feed_url,
            "is_sentinel": False,
            "quarantine_status": rep.status,
        }


async def list_sentinel_sources(session: AsyncSession) -> List[Dict[str, Any]]:
    """Retrieve all active Sentinel feeds and their high-frequency telemetry."""
    stmt = (
        select(FeedSubscription)
        .where(FeedSubscription.is_sentinel == True, FeedSubscription.is_active == True)  # noqa: E712
        .order_by(col(FeedSubscription.priority_tier).asc(), col(FeedSubscription.last_polled_at).asc())
    )
    subs = (await session.exec(stmt)).all()
    results = []
    for s in subs:
        dom = normalize_domain(s.feed_url)
        rep = await get_or_create_domain_reputation(session, dom)
        results.append(
            {
                "id": s.id,
                "domain": dom,
                "title": s.title or dom,
                "feed_url": s.feed_url,
                "interval_seconds": s.sentinel_interval_seconds,
                "is_sentinel": s.is_sentinel,
                "priority_tier": s.priority_tier,
                "last_polled_at": s.last_polled_at.isoformat() if s.last_polled_at else None,
                "quarantine_status": rep.status,
                "reputation_score": rep.reputation_score,
            }
        )
    return results
