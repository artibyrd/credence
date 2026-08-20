"""CLI Boredom Engine Command Handlers for Credence."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from credence.db import get_async_session, init_db
from credence.feeds.boredom import run_boredom_cycle

console = Console()


async def run_boredom_command(force: bool = False, *args: Any, **kwargs: Any) -> int:
    """Inspect local node boredom quotient and idle activity metrics."""
    await init_db()
    async with get_async_session() as session:
        summary = await run_boredom_cycle(session)

    console.print(f"[bold]Daily Headroom:[/bold] {summary.headroom_daily_pct:.1f}%")
    console.print(f"[bold]Hourly Headroom:[/bold] {summary.headroom_hourly_pct:.1f}%")
    console.print(f"[bold]Items Audited:[/bold] {summary.pending_items_audited}")
    console.print(f"[bold]Roots Discovered:[/bold] {summary.new_roots_subscribed}")
    return 0
