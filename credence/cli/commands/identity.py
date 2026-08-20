"""CLI Node Identity Command Handlers for Credence."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from credence.config import settings
from credence.identity import load_or_create_node_identity

console = Console()


def run_identity_show_command(key_file: str | None = None) -> int:
    """Display current node Ed25519 public key and cryptographic identity."""
    target_path = Path(key_file) if key_file else Path(getattr(settings, "NODE_KEY_PATH", "node_key.json"))
    ident = load_or_create_node_identity(target_path)
    console.print(
        Panel(
            f"[bold]Public Key:[/bold] {ident.public_key_hex}\n[bold]Key File:[/bold] {target_path}",
            title="[bold green]Credence Sovereign Node Identity[/bold green]",
            border_style="green",
        )
    )
    return 0
