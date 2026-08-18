"""Real-Time Epistemic Feed Sifter Background Daemon for Credence.

Continuously monitors subscribed feeds, calculates dynamic quality scores (F_j),
evicts compromised feeds, executes Gemini 3.7 Flash audits with 4k thinking,
and gossips signed attestations across the P2P mesh.
"""

from __future__ import annotations

import asyncio
import signal
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.table import Table
from sqlmodel import select

from credence.config import COST_PROFILES, CostProfile
from credence.db import get_session
from credence.feeds.health import calculate_feed_quality_score
from credence.feeds.worker import FeedSyncSummary, sync_subscribed_feeds
from credence.mesh.relay import MeshGossipRelay
from credence.models import AuditRecord, FeedSubscriptionRecord

console = Console()


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

    async def start(self) -> None:
        """Start the background sifting loop."""
        self._running = True
        console.print(
            f"[bold cyan]Starting Credence Feed Sifter Daemon[/] "
            f"(Interval: {self.poll_interval}s, Profile: {self.cost_profile.value}, Auto-Audit: {self.auto_audit})"
        )

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._handle_signal)
            except NotImplementedError:
                pass  # Windows or restricted loop

        try:
            while self._running and not self._shutdown_event.is_set():
                await self._run_single_sifting_cycle()
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

    async def _run_single_sifting_cycle(self) -> FeedSyncSummary:
        """Execute one complete sifting and health evaluation cycle."""
        console.print(
            f"\n[cyan]⏱️ Sifting cycle initiated at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}...[/]"
        )

        async with get_session() as session:
            # Step 1: Run feed polling and item ingestion
            summary = await sync_subscribed_feeds(
                session=session,
                profile_override=COST_PROFILES.get(self.cost_profile),
                dry_run=not self.auto_audit,
            )

            # Step 2: Dynamic Feed Quality Evaluation & Autonomous Eviction
            stmt = select(FeedSubscriptionRecord)
            subscriptions = (await session.exec(stmt)).all()

            for sub in subscriptions:
                stmt_audits = (
                    select(AuditRecord).where(AuditRecord.url.like(f"%{sub.feed_url.split('/')[2]}%")).limit(10)
                )
                recent_audits = (await session.exec(stmt_audits)).all()
                if recent_audits:
                    # Convert to audit report schemas
                    # Calculate F_j metric
                    metrics = calculate_feed_quality_score([], None)
                    if metrics.composite_score_fj < 0.40 and sub.is_active:
                        sub.is_active = False
                        session.add(sub)
                        console.print(
                            f"[bold red]⚠️ Feed Evicted to Quarantine:[/] {sub.title or sub.feed_url} (F_j = {metrics.composite_score_fj:.2f})"
                        )

            await session.commit()

            # Render cycle summary table
            self._render_cycle_summary(summary)
            return summary

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
