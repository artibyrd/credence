"""CLI Feed Sifter & Syndication Command Handlers for Credence."""

from __future__ import annotations

from typing import Any, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlmodel import col, select

from credence.db import get_async_session
from credence.feeds.sentinel import list_sentinel_sources, set_feed_sentinel_mode
from credence.feeds.sifter import run_sifting_cycle
from credence.models import FeedSubscription

console = Console()


async def run_feeds_list_command() -> int:
    """List syndicated RSS/Atom feed subscriptions with Sentinel status."""
    async with get_async_session() as session:
        stmt = select(FeedSubscription).order_by(
            col(FeedSubscription.is_sentinel).desc(),
            col(FeedSubscription.priority_tier).asc(),
        )
        feeds = (await session.exec(stmt)).all()

    table = Table(title="Syndicated RSS/Atom Feed Subscriptions", box=box.ROUNDED)
    table.add_column("Feed URL / Source", style="cyan")
    table.add_column("Sentinel Mode", justify="center")
    table.add_column("Tier", justify="center")
    table.add_column("Active", justify="center")
    table.add_column("Last Polled", style="dim")

    for f in feeds:
        sentinel_tag = (
            f"[bold green]🛡️ SENTINEL ({f.sentinel_interval_seconds}s)[/]" if f.is_sentinel else "[dim]STANDARD[/]"
        )
        table.add_row(
            f.feed_url,
            sentinel_tag,
            f"T{f.priority_tier}",
            "✅" if f.is_active else "❌",
            str(f.last_polled_at or "Never"),
        )

    console.print(table)
    return 0


async def run_feeds_sentinel_command(
    action: str = "list",
    target: Optional[str] = None,
    interval: int = 300,
) -> int:
    """Manage high-priority Sentinel Mode feed subscriptions."""
    async with get_async_session() as session:
        if action == "list":
            sentinels = await list_sentinel_sources(session)
            if not sentinels:
                console.print(
                    Panel(
                        "[dim]No active Sentinel sources configured.[/dim]\n"
                        "Enable with: [bold cyan]credence feeds sentinel enable <url_or_domain>[/bold cyan]",
                        title="🛡️ Active Sentinel Sources (0/10)",
                        border_style="yellow",
                    )
                )
                return 0

            table = Table(title=f"🛡️ Active Sentinel Sources ({len(sentinels)}/10 Max)", box=box.ROUNDED)
            table.add_column("Domain", style="bold cyan")
            table.add_column("Cadence", justify="center", style="bold green")
            table.add_column("Quarantine Status", justify="center")
            table.add_column("Reputation", justify="center")
            table.add_column("Last Polled", style="dim")
            table.add_column("Feed Endpoint", style="dim")

            for s in sentinels:
                status_style = (
                    "green"
                    if s["quarantine_status"] == "TRUSTED"
                    else ("red" if "QUARANTINE" in s["quarantine_status"] else "yellow")
                )
                table.add_row(
                    s["domain"],
                    f"{s['interval_seconds']}s (5m)" if s["interval_seconds"] == 300 else f"{s['interval_seconds']}s",
                    f"[{status_style}]{s['quarantine_status']}[/]",
                    f"{s['reputation_score']:.1f}",
                    str(s["last_polled_at"] or "Pending first poll"),
                    s["feed_url"],
                )
            console.print(table)
            return 0

        if not target:
            console.print("[bold red]Error:[/] Missing target feed URL or domain for sentinel command.")
            return 1

        try:
            if action in ("enable", "set-interval"):
                res = await set_feed_sentinel_mode(
                    session=session,
                    target=target,
                    enabled=True,
                    interval_seconds=interval,
                )
                console.print(
                    Panel(
                        f"[bold green]✅ Sentinel Mode Active for:[/] [cyan]{res['domain']}[/cyan]\n"
                        f"• [bold]Feed Endpoint:[/] {res['feed_url']}\n"
                        f"• [bold]Polling Cadence:[/] Every {res['interval_seconds']}s (Priority Tier {res['priority_tier']})\n"
                        f"• [bold]Quarantine Status:[/] {res['quarantine_status']}",
                        title="🛡️ Sentinel Configuration Updated",
                        border_style="green",
                    )
                )
                return 0
            elif action == "disable":
                res = await set_feed_sentinel_mode(
                    session=session,
                    target=target,
                    enabled=False,
                )
                console.print(
                    Panel(
                        f"[bold yellow]⚠️ Sentinel Mode Disabled for:[/] [cyan]{res['domain']}[/cyan]\n"
                        f"Feed restored to standard polling rotation.",
                        title="🛡️ Sentinel Disabled",
                        border_style="yellow",
                    )
                )
                return 0
            else:
                console.print(
                    f"[bold red]Unknown sentinel action:[/] {action}. Use 'list', 'enable', 'disable', or 'set-interval'."
                )
                return 1
        except Exception as e:
            console.print(f"[bold red]Sentinel Error:[/] {e}")
            return 1


async def run_sifter_command(burst: bool = False, once: bool = True, *args: Any, **kwargs: Any) -> int:
    """Execute feed sifter ingestion pass."""
    async with get_async_session() as session:
        summary = await run_sifting_cycle(session)
    console.print(
        f"[bold green]Sifter pass complete:[/bold green] Ingested {summary.new_items_discovered} new articles, audited {summary.items_evaluated_locally}."
    )
    return 0
