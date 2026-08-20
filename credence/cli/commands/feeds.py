"""CLI Feed Sifter & Syndication Command Handlers for Credence."""

from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Console
from rich.table import Table
from sqlmodel import select

from credence.db import get_async_session
from credence.feeds.sifter import run_sifting_cycle
from credence.models import FeedSubscription

console = Console()


async def run_feeds_list_command() -> int:
    """List syndicated RSS/Atom feed subscriptions."""
    async with get_async_session() as session:
        stmt = select(FeedSubscription)
        feeds = (await session.exec(stmt)).all()

    table = Table(title="Syndicated RSS/Atom Feed Subscriptions", box=box.ROUNDED)
    table.add_column("Feed URL", style="cyan")
    table.add_column("Active", justify="center")
    table.add_column("Last Polled", style="dim")

    for f in feeds:
        table.add_row(f.feed_url, "✅" if f.is_active else "❌", str(f.last_polled_at or "Never"))

    console.print(table)
    return 0


async def run_sifter_command(burst: bool = False, once: bool = True, *args: Any, **kwargs: Any) -> int:
    """Execute feed sifter ingestion pass."""
    async with get_async_session() as session:
        summary = await run_sifting_cycle(session)
    console.print(
        f"[bold green]Sifter pass complete:[/bold green] Ingested {summary.new_items_discovered} new articles, audited {summary.items_evaluated_locally}."
    )
    return 0
