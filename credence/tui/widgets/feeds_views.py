"""Syndicated Feeds and Sentinel Mode rich view formatters for Credence TUI.

Architecture: Modular Rich Text Formatters (<120 LOC) per 500 LOC Ceiling Law.
"""

from __future__ import annotations

from typing import Any, Dict

from rich.panel import Panel
from rich.text import Text


def format_sentinel_status_badge(is_sentinel: bool, interval_sec: int = 300) -> str:
    """Format short text badge for feed status in data tables."""
    if is_sentinel:
        return f"🛡️ SENTINEL ({interval_sec}s)"
    return "STANDARD"


def format_feed_sentinel_panel(feed_dict: Dict[str, Any]) -> Panel:
    """Render rich dossier inspector panel for the highlighted feed in TUI."""
    title = feed_dict.get("title") or feed_dict.get("domain") or "Selected Feed"
    feed_url = feed_dict.get("feed_url") or "Unknown"
    is_sentinel = feed_dict.get("is_sentinel", False)
    interval = feed_dict.get("interval_seconds", 300)
    tier = feed_dict.get("priority_tier", 2)
    quarantine = feed_dict.get("quarantine_status", "TRUSTED")
    reputation = feed_dict.get("reputation_score", 98.5)
    last_polled = feed_dict.get("last_polled_at") or "Pending initial poll"

    content = Text()
    content.append(f"📡 {title}\n", style="bold cyan")
    content.append(f"• URL: {feed_url}\n", style="dim")
    content.append(f"• Priority Tier: T{tier}\n", style="white")

    if is_sentinel:
        content.append(f"• Mode: 🛡️ SENTINEL ACTIVE ({interval}s cadence)\n", style="bold green")
    else:
        content.append(f"• Mode: STANDARD POLLING ({interval}s cadence)\n", style="dim")

    q_color = "green" if quarantine == "TRUSTED" else ("red" if "QUARANTINE" in quarantine else "yellow")
    content.append(f"• Quarantine Status: {quarantine}\n", style=q_color)
    content.append(f"• Domain Reputation: {reputation:.1f} / 100.0\n", style="cyan")
    content.append(f"• Last Synchronized: {last_polled}\n\n", style="dim")

    content.append("─── Operator Keybindings ───\n", style="dim")
    content.append("Press [t] to Toggle Sentinel Mode on this feed\n", style="bold yellow")
    content.append("Press [s] to Trigger Immediate Sifter Cycle\n", style="bold cyan")

    border_color = "green" if is_sentinel else "cyan"
    return Panel(
        content,
        title="[bold]🛡️ Feed & Sentinel Inspector[/bold]",
        border_style=border_color,
    )
