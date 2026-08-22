"""CLI Boredom Engine Command Handlers for Credence."""

from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Console
from rich.table import Table
from sqlmodel import col, func, select

from credence.db import get_async_session, init_db
from credence.feeds.boredom import compute_curiosity_excitement, run_boredom_cycle
from credence.models import Audit
from credence.pipeline.governor import get_token_headroom_status

console = Console()


async def run_boredom_command(force: bool = False, *args: Any, **kwargs: Any) -> int:
    """Inspect local node boredom quotient, excitement level, and autonomous heartbeat cadence."""
    await init_db()
    async with get_async_session() as session:
        # 1. Check volume and headroom
        stmt_a = select(func.count(col(Audit.id)))
        total_audits = (await session.exec(stmt_a)).first() or 0
        headroom = await get_token_headroom_status(session)

        stmt_latest = select(Audit).order_by(col(Audit.audited_at).desc()).limit(1)
        latest_audit = (await session.exec(stmt_latest)).first()
        last_time = latest_audit.audited_at if latest_audit else None

        # 2. Compute dynamic excitement decision
        decision = compute_curiosity_excitement(
            total_audits=total_audits,
            daily_headroom_pct=headroom.daily_headroom_pct,
            last_audit_time=last_time,
        )

        table = Table(title="🌀 Credence Epistemic Excitement & Heartbeat Status", box=box.ROUNDED)
        table.add_column("Telemetry Metric", style="cyan", no_wrap=True)
        table.add_column("Current Value", style="bold")
        table.add_column("Architectural Notes", style="dim")

        mode_badge = (
            f"[bold yellow]🔥 {decision.mode}[/]"
            if decision.mode == "HYPER_EXCITED"
            else (
                f"[bold green]⚡ {decision.mode}[/]"
                if decision.mode == "ACTIVE_BURST"
                else (
                    f"[bold blue]🌱 {decision.mode}[/]"
                    if decision.mode == "STEADY_MAINTENANCE"
                    else (
                        f"[dim]💤 {decision.mode}[/]"
                        if decision.mode == "ADAPTIVE_BACKOFF"
                        else f"[bold red]🛑 {decision.mode}[/]"
                    )
                )
            )
        )

        table.add_row("Excitement Mode", mode_badge, decision.reason)
        table.add_row("Excitement Score (E)", f"{decision.excitement_score:.2f}", "E = Headroom% × (1 - Audits/250)")
        table.add_row(
            "Burst Capacity",
            f"{decision.audit_burst} audits / tick",
            f"+ {decision.expand_roots_appetite} root expansions",
        )
        table.add_row(
            "Autonomous Heartbeat", "10 Minutes (Cloud Scheduler)", "Triggers /cron/boredom (Scale-to-Zero: $0.00 Idle)"
        )
        table.add_row(
            "Daily Headroom",
            f"{headroom.daily_headroom_pct:.1f}%",
            f"${headroom.daily_spend_usd:.2f} spent today (Safety floor: 30%)",
        )
        table.add_row("Total Audits in DB", f"{total_audits} audits", "SQLite WAL Storage Gravity")

        console.print(table)

        if force:
            console.print("[yellow]Triggering forced curiosity cycle...[/yellow]")
            summary = await run_boredom_cycle(session, audit_burst=max(1, decision.audit_burst))
            console.print(
                f"[bold green]Cycle complete:[/] Audited {summary.pending_items_audited} items, adopted {summary.mesh_attestations_adopted} from mesh."
            )

    return 0
