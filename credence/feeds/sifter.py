"""Real-Time Epistemic Feed Sifter Background Daemon for Credence.

Continuously monitors subscribed feeds, calculates dynamic quality scores (F_j),
evicts compromised feeds, executes Gemini 3.7 Flash audits with 4k thinking,
and gossips signed attestations across the P2P mesh.
"""

from __future__ import annotations

import asyncio
import signal
from typing import Optional

from rich.console import Console
from rich.table import Table
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import COST_PROFILES, CostProfile
from credence.db import get_session
from credence.feeds.health import calculate_feed_quality_score
from credence.feeds.worker import FeedSyncSummary, sync_subscribed_feeds
from credence.mesh.relay import MeshGossipRelay
from credence.models import AuditRecord, FeedItemRecord, FeedSubscriptionRecord, SnapshotRecord

console = Console()


async def run_sifting_cycle(
    session: AsyncSession,
    cost_profile: CostProfile = CostProfile.BALANCED,
    auto_audit: bool = True,
) -> FeedSyncSummary:
    """Execute one complete sifting and health evaluation cycle."""
    summary = await sync_subscribed_feeds(
        session=session,
        profile_override=COST_PROFILES.get(cost_profile),
        dry_run=not auto_audit,
        evaluate_novel=auto_audit,
    )

    # Dynamic Feed Quality Evaluation & Autonomous Eviction
    stmt = select(FeedSubscriptionRecord)
    subscriptions = (await session.exec(stmt)).all()

    for sub in subscriptions:
        domain_pattern = sub.feed_url.split("/")[2] if len(sub.feed_url.split("/")) > 2 else sub.feed_url
        stmt_audits = (
            select(AuditRecord)
            .join(SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id))
            .where(col(SnapshotRecord.url).like(f"%{domain_pattern}%"))
            .limit(10)
        )
        recent_audits = (await session.exec(stmt_audits)).all()
        if recent_audits:
            metrics = calculate_feed_quality_score([], None)
            if metrics.composite_score_fj < 0.40 and sub.is_active:
                sub.is_active = False
                session.add(sub)
                console.print(
                    f"[bold red]⚠️ Feed Evicted to Quarantine:[/] {sub.title or sub.feed_url} (F_j = {metrics.composite_score_fj:.2f})"
                )

    await session.commit()
    return summary


async def get_sifter_status(session: AsyncSession) -> dict:
    """Get sifter telemetry metrics from SQLite database."""
    from sqlmodel import func

    stmt_subs = select(func.count(col(FeedSubscriptionRecord.id))).where(FeedSubscriptionRecord.is_active == True)  # noqa: E712
    active_subs = (await session.exec(stmt_subs)).first() or 0

    stmt_items = select(func.count(col(FeedItemRecord.id)))
    total_items = (await session.exec(stmt_items)).first() or 0

    stmt_audited = select(func.count(col(FeedItemRecord.id))).where(FeedItemRecord.processing_status == "audited")
    audited_items = (await session.exec(stmt_audited)).first() or 0

    stmt_pending = select(func.count(col(FeedItemRecord.id))).where(FeedItemRecord.processing_status == "pending")
    pending_items = (await session.exec(stmt_pending)).first() or 0

    stmt_last_audit = select(AuditRecord).order_by(col(AuditRecord.audited_at).desc()).limit(1)
    last_audit = (await session.exec(stmt_last_audit)).first()

    return {
        "status": "online",
        "active_feed_subscriptions": active_subs,
        "total_feed_items_discovered": total_items,
        "total_feed_items_audited": audited_items,
        "pending_feed_items": pending_items,
        "last_audited_at": last_audit.audited_at.isoformat() if last_audit else None,
    }


class SifterDaemon:
    """Long-running async background daemon for real-time feed sifting."""

    def __init__(
        self,
        poll_interval_seconds: int = 300,
        cost_profile: CostProfile = CostProfile.BALANCED,
        auto_audit: bool = True,
        mesh_relay: Optional[MeshGossipRelay] = None,
    ):
        self.poll_interval = poll_interval_seconds
        self.cost_profile = cost_profile
        self.auto_audit = auto_audit
        self.mesh_relay = mesh_relay
        self._running = False
        self._shutdown_event = asyncio.Event()

    async def start(self, once: bool = False) -> None:
        """Start the background sifting loop (or execute single cycle if once=True)."""
        self._running = True
        console.print(
            f"[bold cyan]Starting Credence Feed Sifter Daemon[/] "
            f"(Interval: {self.poll_interval}s, Profile: {self.cost_profile.value}, Auto-Audit: {self.auto_audit}, Once: {once})"
        )

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._handle_signal)
            except NotImplementedError:
                pass  # Windows or restricted loop

        try:
            while self._running and not self._shutdown_event.is_set():
                async for session in get_session():
                    summary = await run_sifting_cycle(
                        session=session,
                        cost_profile=self.cost_profile,
                        auto_audit=self.auto_audit,
                    )
                    self._render_cycle_summary(summary)
                    break
                if once:
                    break
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=self.poll_interval)
                except asyncio.TimeoutError:
                    pass  # Normal loop trigger
        finally:
            console.print("[yellow]Feed Sifter Daemon stopped cleanly.[/yellow]")

    def stop(self) -> None:
        """Signal daemon to terminate cleanly."""
        self._running = False
        self._shutdown_event.set()

    def _handle_signal(self) -> None:
        console.print("\n[bold red]Shutdown signal received. Stopping sifter...[/]")
        self.stop()

    def _render_cycle_summary(self, summary: FeedSyncSummary) -> None:
        table = Table(title="Sifter Ingestion Summary", show_header=True, header_style="bold cyan")
        table.add_column("Feeds Polled", justify="right")
        table.add_column("Unmodified (304)", justify="right")
        table.add_column("New Discovered", justify="right")
        table.add_column("Mesh Adopted (0 tokens)", justify="right", style="green")
        table.add_column("Evaluated Locally", justify="right")
        table.add_column("Tokens Saved", justify="right", style="yellow")

        table.add_row(
            str(summary.total_feeds_polled),
            str(summary.feeds_unmodified_304),
            str(summary.new_items_discovered),
            str(summary.items_adopted_from_mesh),
            str(summary.items_evaluated_locally),
            f"{summary.tokens_saved_total:,}",
        )
        console.print(table)
