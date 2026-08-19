"""Autonomous Epistemic Boredom Engine and Opportunistic Ingestion Daemon for Credence.

Monitors node idle state and token budget headroom. When the node gets bored (idling with healthy
token headroom >= 30%), it opportunistically digests pending feed queues, verifies breaking claims,
expands subscription roots from cited references, and relays signed attestations across the P2P mesh.
"""

from __future__ import annotations

import asyncio
import signal
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import COST_PROFILES, CostProfile
from credence.db import get_session
from credence.feeds.dedup import check_mesh_effort_avoidance
from credence.feeds.roots import RootExpansionSummary, expand_roots
from credence.mesh.relay import MeshGossipRelay
from credence.models import FeedItemRecord, FeedSubscriptionRecord, utc_now
from credence.pipeline.governor import get_token_headroom_status

console = Console()


@dataclass
class BoredomCycleSummary:
    """Telemetry metrics from an autonomous boredom execution cycle."""

    timestamp: datetime = field(default_factory=utc_now)
    headroom_daily_pct: float = 100.0
    headroom_hourly_pct: float = 100.0
    circuit_breaker_tripped: bool = False
    pending_items_scanned: int = 0
    pending_items_audited: int = 0
    mesh_attestations_adopted: int = 0
    items_deferred_budget: int = 0
    tokens_saved_mesh: int = 0
    new_roots_subscribed: int = 0
    initial_items_harvested: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)


async def run_boredom_cycle(
    session: AsyncSession,
    audit_burst: int = 3,
    expand_roots_enabled: bool = True,
    mesh_relay: Optional[MeshGossipRelay] = None,
    cost_profile: CostProfile = CostProfile.BALANCED,
    profile_override: Any = None,
    allow_local: bool = False,
    client: Optional[Any] = None,
) -> BoredomCycleSummary:
    """Execute one complete opportunistic boredom cycle."""
    summary = BoredomCycleSummary()
    prof_cfg = profile_override or COST_PROFILES.get(cost_profile)

    # 1. Check Token Safety Governor Headroom
    headroom = await get_token_headroom_status(session, profile_override=prof_cfg)
    summary.headroom_daily_pct = headroom.daily_headroom_pct
    summary.headroom_hourly_pct = headroom.hourly_headroom_pct
    summary.circuit_breaker_tripped = headroom.circuit_breaker_tripped

    # 2. Opportunistic Pending Feed Item Ingestion
    stmt_pending = (
        select(FeedItemRecord, FeedSubscriptionRecord)
        .join(FeedSubscriptionRecord, col(FeedItemRecord.feed_id) == col(FeedSubscriptionRecord.id), isouter=True)
        .where(FeedItemRecord.processing_status == "pending")
        .order_by(col(FeedSubscriptionRecord.priority_tier).asc(), col(FeedItemRecord.discovered_at).asc())
        .limit(audit_burst * 2)
    )
    pending_pairs = (await session.exec(stmt_pending)).all()
    summary.pending_items_scanned = len(pending_pairs)

    audited_in_this_cycle = 0

    for item, _sub in pending_pairs:
        if audited_in_this_cycle >= audit_burst:
            break

        # A. Mesh Effort Avoidance Check (Zero-Token Adoption)
        dedup = await check_mesh_effort_avoidance(session, item.item_url)
        if dedup.status in ("local_cached", "mesh_adopted"):
            item.processing_status = "mesh_adopted"
            item.adopted_from_node = str(dedup.adopted_from_node or "local")
            item.tokens_saved = dedup.tokens_saved
            session.add(item)
            await session.commit()

            summary.mesh_attestations_adopted += 1
            summary.tokens_saved_mesh += dedup.tokens_saved
            summary.details.append(
                {
                    "url": item.item_url,
                    "status": "mesh_adopted",
                    "tokens_saved": dedup.tokens_saved,
                    "node": str(dedup.adopted_from_node or "local"),
                }
            )
            continue

        # B. Token Safety Guard Check
        if summary.circuit_breaker_tripped or summary.headroom_daily_pct < 30.0:
            summary.items_deferred_budget += 1
            summary.details.append(
                {
                    "url": item.item_url,
                    "status": "deferred_budget_headroom",
                }
            )
            continue

        # C. Novel Item Live Audit
        try:
            from credence.pipeline.evaluator import audit_url

            report = await audit_url(
                item.item_url,
                force_refresh=False,
                profile_override=prof_cfg,
            )
            item.processing_status = "audited"
            session.add(item)
            await session.commit()

            summary.pending_items_audited += 1
            audited_in_this_cycle += 1
            summary.details.append(
                {
                    "url": item.item_url,
                    "status": "audited_opportunistically",
                    "score": f"{report.suspicion_score:.1f}",
                    "classification": report.classification,
                    "violations_count": len(report.violations),
                }
            )

            # D. Broadcast newly minted signed attestation across P2P Mesh
            if mesh_relay:
                try:
                    await mesh_relay.broadcast_attestation(report)
                except Exception as ex:
                    console.print(f"[dim yellow]Mesh gossip relay warning: {ex}[/dim yellow]")

        except Exception as e:
            item.processing_status = "error"
            session.add(item)
            await session.commit()
            summary.details.append(
                {
                    "url": item.item_url,
                    "status": "audit_error",
                    "error": str(e),
                }
            )

    # 3. Autonomous Root Expansion (Expanding Roots from Clean Citations)
    if expand_roots_enabled:
        try:
            root_summary: RootExpansionSummary = await expand_roots(
                session=session,
                max_new_sources=3,
                min_citation_count=1,
                dry_run=False,
                allow_local=allow_local,
                client=client,
            )
            summary.new_roots_subscribed = root_summary.new_feeds_subscribed
            summary.initial_items_harvested = root_summary.initial_items_harvested
            for detail in root_summary.details:
                summary.details.append({"root_expansion": detail})
        except Exception as e:
            summary.details.append({"root_expansion_error": str(e)})

    return summary


class BoredomDaemon:
    """Background async daemon that triggers opportunistic boredom cycles when the node is idle."""

    def __init__(
        self,
        idle_interval_seconds: int = 120,
        audit_burst: int = 3,
        expand_roots_enabled: bool = True,
        cost_profile: CostProfile = CostProfile.BALANCED,
        mesh_relay: Optional[MeshGossipRelay] = None,
    ):
        self.idle_interval = idle_interval_seconds
        self.audit_burst = audit_burst
        self.expand_roots_enabled = expand_roots_enabled
        self.cost_profile = cost_profile
        self.mesh_relay = mesh_relay
        self._running = False
        self._shutdown_event = asyncio.Event()

    async def start(self, once: bool = False) -> None:
        """Start the opportunistic boredom loop (or execute single cycle if once=True)."""
        self._running = True
        console.print(
            f"[bold cyan]🧠 Starting Credence Autonomous Boredom Engine[/] "
            f"(Interval: {self.idle_interval}s, Burst: {self.audit_burst}, Roots: {self.expand_roots_enabled}, Once: {once})"
        )

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._handle_signal)
            except NotImplementedError:
                pass

        try:
            while self._running and not self._shutdown_event.is_set():
                async for session in get_session():
                    summary = await run_boredom_cycle(
                        session=session,
                        audit_burst=self.audit_burst,
                        expand_roots_enabled=self.expand_roots_enabled,
                        mesh_relay=self.mesh_relay,
                        cost_profile=self.cost_profile,
                    )
                    self._render_cycle_summary(summary)
                    break
                if once:
                    break
                try:
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=self.idle_interval)
                except asyncio.TimeoutError:
                    pass  # Normal loop trigger
        finally:
            console.print("[yellow]Autonomous Boredom Engine stopped cleanly.[/yellow]")

    def stop(self) -> None:
        """Signal daemon to terminate cleanly."""
        self._running = False
        self._shutdown_event.set()

    def _handle_signal(self) -> None:
        console.print("\n[bold red]Shutdown signal received. Stopping boredom engine...[/]")
        self.stop()

    def _render_cycle_summary(self, summary: BoredomCycleSummary) -> None:
        table = Table(title="Autonomous Boredom Exploration Summary", show_header=True, header_style="bold cyan")
        table.add_column("Pending Scanned", justify="right")
        table.add_column("Audited Novel", justify="right", style="green")
        table.add_column("Mesh Adopted (0 tokens)", justify="right", style="cyan")
        table.add_column("Tokens Saved", justify="right", style="yellow")
        table.add_column("Roots Subscribed", justify="right", style="bold magenta")
        table.add_column("Headroom Daily", justify="right")

        table.add_row(
            str(summary.pending_items_scanned),
            str(summary.pending_items_audited),
            str(summary.mesh_attestations_adopted),
            f"{summary.tokens_saved_mesh:,}",
            str(summary.new_roots_subscribed),
            f"{summary.headroom_daily_pct:.1f}%",
        )
        console.print(table)
