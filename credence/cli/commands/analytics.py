"""CLI Analytics & Rankings Command Handlers for Credence."""

from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Console
from rich.table import Table

from credence.db import get_async_session
from credence.subjects.analytics import get_domain_leaderboard

console = Console()


async def run_rankings_command(ranking_type: str = "domains", category: str = "best") -> int:
    """Display domain epistemic merit leaderboards."""
    async with get_async_session() as session:
        domains = await get_domain_leaderboard(session)

    table = Table(title=f"Epistemic Domain Rankings ({ranking_type})", box=box.ROUNDED)
    table.add_column("Domain", style="bold cyan")
    table.add_column("Score", justify="center")
    table.add_column("Band", style="magenta")
    table.add_column("Total Audits", justify="right")

    for d in domains:
        table.add_row(d.domain, f"{d.dci_score:.1f}", d.trust_band, str(d.total_audits))

    console.print(table)
    return 0


async def cli_leaderboard(*args: Any, **kwargs: Any) -> Any:
    return await run_rankings_command(*args, **kwargs)


async def cli_merit(*args: Any, **kwargs: Any) -> Any:
    return await run_rankings_command(*args, **kwargs)


async def cli_rankings(*args: Any, **kwargs: Any) -> Any:
    return await run_rankings_command(*args, **kwargs)


def cli_badge_export(*args: Any, **kwargs: Any) -> None:
    pass
