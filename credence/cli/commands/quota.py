"""CLI Quota & Cost Profile Command Handlers for Credence."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel

from credence.db import get_async_session, init_db
from credence.pipeline.governor import get_token_headroom_status

console = Console()


async def run_quota_command(session: Any = None) -> int:
    """Display real-time token consumption, daily spend, and circuit breaker status."""
    if session is not None:
        status = await get_token_headroom_status(session)
    else:
        await init_db()
        async with get_async_session() as s:
            status = await get_token_headroom_status(s)

    console.print(
        Panel(
            f"[bold]Active Profile:[/bold] {status.active_profile}\n"
            f"[bold]Hourly Tokens:[/bold] {status.hourly_tokens_used:,} / {status.hourly_tokens_max:,} ({status.hourly_headroom_pct:.1f}% headroom)\n"
            f"[bold]Daily Spend:[/bold] ${status.daily_spend_usd:.4f} / ${status.daily_budget_usd:.2f}\n"
            f"[bold]Circuit Breaker:[/bold] {'🚨 TRIPPED' if status.circuit_breaker_tripped else '🛡️ HEALTHY'}",
            title="Token Safety & Cost Headroom",
            border_style="green" if not status.circuit_breaker_tripped else "red",
        )
    )
    return 0
