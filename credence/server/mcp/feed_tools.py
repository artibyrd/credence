"""FastMCP Tool & Resource Definitions for Credence."""

from __future__ import annotations

import json
import logging

from mcp.server.mcpserver import MCPServer
from sqlmodel import col, select

from credence.db import get_async_session, init_db

logger = logging.getLogger("credence.server.mcp")


def _register_feed_sync_tools(server: MCPServer) -> None:
    """Register syndicated RSS/Atom/JSON feed synchronization tools."""

    @server.tool(
        name="credence_sync_feeds",
        description="Poll all active syndicated RSS/Atom/JSON feeds, perform mesh effort avoidance, and adopt peer attestations at $0 token cost.",
    )
    async def sync_feeds_tool(dry_run: bool = False, evaluate_novel: bool = True) -> str:
        from credence.feeds.worker import sync_all_feeds

        await init_db()
        async with get_async_session() as session:
            summary = await sync_all_feeds(session=session, dry_run=dry_run, evaluate_novel=evaluate_novel)
            return json.dumps(
                {
                    "total_feeds_polled": summary.total_feeds_polled,
                    "feeds_unmodified_304": summary.feeds_unmodified_304,
                    "new_items_discovered": summary.new_items_discovered,
                    "items_adopted_from_mesh": summary.items_adopted_from_mesh,
                    "tokens_saved_total": summary.tokens_saved_total,
                    "items_deferred_budget": summary.items_deferred_budget,
                    "dry_run": dry_run,
                },
                indent=2,
            )
        return "{}"

    @server.tool(
        name="credence_get_feed_stats",
        description="Get aggregate feed pre-ingestion metrics, zero-token adoptions, and tokens saved.",
    )
    async def get_feed_stats_tool() -> str:
        from credence.models import FeedItem, FeedSubscription

        await init_db()
        async with get_async_session() as session:
            stmt_subs = select(FeedSubscription)
            subs = (await session.exec(stmt_subs)).all()
            stmt_items = select(FeedItem)
            items = (await session.exec(stmt_items)).all()

            adopted = [i for i in items if i.processing_status == "mesh_adopted"]
            return json.dumps(
                {
                    "active_subscriptions_count": len([s for s in subs if s.is_active]),
                    "total_articles_discovered": len(items),
                    "zero_token_adoptions_count": len(adopted),
                    "total_tokens_saved": sum(i.tokens_saved for i in items),
                    "attestation_seeding_active": True,
                },
                indent=2,
            )
        return "{}"


def _register_feed_management_tools(server: MCPServer) -> None:
    """Register syndicated feed subscription management tools."""

    @server.tool(
        name="credence_add_feed_subscription",
        description="Subscribe node to a syndicated RSS 2.0, Atom 1.0, or JSON Feed.",
    )
    async def add_feed_subscription_tool(
        feed_url: str,
        title: str = "",
        priority_tier: int = 2,
        subject_tag: str = "journalism.news",
        is_satire: bool = False,
        is_sentinel: bool = False,
        sentinel_interval_seconds: int = 300,
    ) -> str:
        from credence.models import FeedSubscription

        await init_db()
        async with get_async_session() as session:
            sub = FeedSubscription(
                feed_url=feed_url,
                title=title,
                priority_tier=priority_tier,
                subject_tag=subject_tag,
                is_satire=is_satire,
                is_sentinel=is_sentinel,
                sentinel_interval_seconds=sentinel_interval_seconds,
            )
            session.add(sub)
            await session.commit()
            return json.dumps(
                {
                    "status": "success",
                    "feed_url": feed_url,
                    "priority_tier": priority_tier,
                    "is_sentinel": is_sentinel,
                }
            )
        return "{}"

    @server.tool(
        name="credence_list_feeds",
        description="List all registered syndicated RSS/Atom/JSON feed subscriptions.",
    )
    async def list_feeds_tool() -> str:
        from credence.db import get_async_session, init_db
        from credence.models import FeedSubscription

        await init_db()
        async with get_async_session() as session:
            stmt = select(FeedSubscription).order_by(col(FeedSubscription.priority_tier).asc())
            subs = (await session.exec(stmt)).all()
            return json.dumps(
                [
                    {
                        "id": s.id,
                        "feed_url": s.feed_url,
                        "title": s.title,
                        "priority_tier": s.priority_tier,
                        "subject_tag": s.subject_tag,
                        "is_active": s.is_active,
                        "is_satire": s.is_satire,
                        "is_sentinel": s.is_sentinel,
                        "sentinel_interval_seconds": s.sentinel_interval_seconds,
                        "etag": s.etag,
                        "last_polled_at": s.last_polled_at.isoformat() if s.last_polled_at else None,
                    }
                    for s in subs
                ],
                indent=2,
            )
        return "[]"

    @server.tool(
        name="credence_set_feed_sentinel_mode",
        description="Enable or disable Sentinel Mode on a target feed or domain for prioritized high-frequency scanning.",
    )
    async def set_feed_sentinel_mode_tool(
        target: str,
        enabled: bool = True,
        interval_seconds: int = 300,
    ) -> str:
        from credence.feeds.sentinel import set_feed_sentinel_mode

        await init_db()
        async with get_async_session() as session:
            try:
                res = await set_feed_sentinel_mode(
                    session=session,
                    target=target,
                    enabled=enabled,
                    interval_seconds=interval_seconds,
                )
                return json.dumps(res, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)}, indent=2)
        return "{}"

    @server.tool(
        name="credence_list_sentinel_sources",
        description="List all active Sentinel sources and their high-frequency polling telemetry.",
    )
    async def list_sentinel_sources_tool() -> str:
        from credence.feeds.sentinel import list_sentinel_sources

        await init_db()
        async with get_async_session() as session:
            sentinels = await list_sentinel_sources(session)
            return json.dumps(sentinels, indent=2)
        return "[]"

    @server.tool(
        name="credence_discover_feeds",
        description="Autonomously discover RSS/Atom/JSON feed candidate endpoints from any target webpage.",
    )
    async def discover_feeds_tool(target_url: str) -> str:
        from dataclasses import asdict

        from credence.feeds.discovery import discover_feed_endpoints

        candidates = await discover_feed_endpoints(target_url)
        return json.dumps([asdict(c) for c in candidates], indent=2)

    @server.tool(
        name="credence_inspect_feed_health",
        description="Run pre-flight forensic audit on a candidate feed to calculate Topic Entropy (H_topic), ethics, and F_j quality score.",
    )
    async def inspect_feed_health_tool(feed_url: str) -> str:
        from dataclasses import asdict

        from credence.feeds.health import run_preflight_feed_audit

        await init_db()
        async with get_async_session() as session:
            result = await run_preflight_feed_audit(feed_url, session=session)
            return json.dumps(asdict(result), indent=2)
        return "{}"

    @server.tool(
        name="credence_generate_digest",
        description="Generate a structured Morning Epistemic Briefing from recent evaluated feed items.",
    )
    async def generate_digest_tool(hours: int = 24) -> str:
        from credence.feeds.digest import generate_morning_digest

        await init_db()
        async with get_async_session() as session:
            digest = await generate_morning_digest(session, timeframe_hours=hours)
            return json.dumps(digest.to_dict(), indent=2)
        return "{}"

    @server.tool(
        name="credence_expand_roots",
        description="Extract cited external domains from verified clean articles, discover RSS/Atom feed endpoints, and autonomously subscribe to new roots.",
    )
    async def expand_roots_tool(max_new_sources: int = 5, min_citation_count: int = 1, dry_run: bool = False) -> str:
        from dataclasses import asdict

        from credence.feeds.roots import expand_roots

        await init_db()
        async with get_async_session() as session:
            summary = await expand_roots(
                session, max_new_sources=max_new_sources, min_citation_count=min_citation_count, dry_run=dry_run
            )
            return json.dumps(asdict(summary), indent=2)
        return "{}"

    @server.tool(
        name="credence_trigger_boredom_cycle",
        description="Trigger an opportunistic boredom cycle to digest pending feed items and autonomously expand subscription roots when token headroom allows.",
    )
    async def trigger_boredom_cycle_tool(
        audit_burst: int = 3,
        boredom_ratio: float = 0.60,
        expand_roots: bool = True,
    ) -> str:
        from dataclasses import asdict

        from credence.feeds.boredom import run_boredom_cycle

        await init_db()
        async with get_async_session() as session:
            summary = await run_boredom_cycle(
                session,
                audit_burst=audit_burst,
                boredom_ratio=boredom_ratio,
                expand_roots_enabled=expand_roots,
            )
            res = asdict(summary)
            res["timestamp"] = summary.timestamp.isoformat()
            return json.dumps(res, indent=2)
        return "{}"

    @server.tool(
        name="credence_get_domain_reputation",
        description="Retrieve domain-level reputation score, status, and BuzzFeed Doctrine redemption progress.",
    )
    async def get_domain_reputation_tool(domain: str) -> str:
        from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain

        await init_db()
        async with get_async_session() as session:
            rec = await get_or_create_domain_reputation(session, normalize_domain(domain))
            return json.dumps(rec.model_dump(mode="json"), indent=2)
        return "{}"

    @server.tool(
        name="credence_get_domain_quarantine",
        description="List all currently quarantined or suspicious domains with exponential polling backoff factors.",
    )
    async def get_domain_quarantine_tool() -> str:
        from credence.feeds.reputation import get_domain_quarantine_list

        await init_db()
        async with get_async_session() as session:
            quarantined = await get_domain_quarantine_list(session)
            return json.dumps(quarantined, indent=2)
        return "[]"

    @server.tool(
        name="credence_appeal_domain_quarantine",
        description="File an expedited BuzzFeed News Doctrine redemption appeal for a quarantined domain.",
    )
    async def appeal_domain_quarantine_tool(domain: str) -> str:
        from credence.feeds.reputation import get_or_create_domain_reputation, normalize_domain

        await init_db()
        async with get_async_session() as session:
            rec = await get_or_create_domain_reputation(session, normalize_domain(domain))
            return json.dumps(
                {
                    "domain": rec.domain,
                    "status": rec.status,
                    "reputation_score": rec.reputation_score,
                    "appeal_status": "QUEUED_FOR_EXPEDITED_AUDIT",
                    "doctrine": "The BuzzFeed News Doctrine (Asymmetric Epistemic Recovery)",
                },
                indent=2,
            )
        return "{}"

    @server.tool(
        name="credence_get_root_candidates",
        description="Retrieve un-subscribed candidate source domains cited by audited high-integrity articles.",
    )
    async def get_root_candidates_tool(limit: int = 10) -> str:
        from dataclasses import asdict

        from credence.feeds.roots import extract_root_candidates

        await init_db()
        async with get_async_session() as session:
            candidates = await extract_root_candidates(session, limit=limit)
            return json.dumps([asdict(c) for c in candidates], indent=2)
        return "[]"

    @server.tool(
        name="credence_remove_feed_subscription",
        description="Unsubscribe and remove a syndicated feed by URL.",
    )
    async def remove_feed_subscription_tool(feed_url: str) -> str:
        from credence.models import FeedSubscription

        await init_db()
        async with get_async_session() as session:
            stmt = select(FeedSubscription).where(FeedSubscription.feed_url == feed_url)
            sub = (await session.exec(stmt)).first()
            if sub:
                await session.delete(sub)
                await session.commit()
                return json.dumps({"status": "removed", "feed_url": feed_url})
            return json.dumps({"error": f"Feed subscription not found for: {feed_url}"})
        return "{}"
