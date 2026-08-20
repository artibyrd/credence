"""CLI Genesis Roots Command Handlers for Credence."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from credence.config import settings

console = Console()


def run_roots_command(action: str = "tree", *args: Any, **kwargs: Any) -> int:
    """Display pinned Genesis seed roots and cryptographic trust anchors."""
    console.print(f"[bold]Genesis Root URL:[/bold] {settings.DEFAULT_SEED_URL}")
    console.print(f"[bold]Pinned Trust Root Key:[/bold] {settings.TRUSTED_ROOT_PUBKEY}")
    return 0
