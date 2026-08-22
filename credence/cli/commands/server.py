"""CLI Server Launch Command Handlers for Credence."""

from __future__ import annotations

import uvicorn
from rich.console import Console

from credence.config import settings

console = Console()


def run_server_command(
    transport: str = "sse",
    host: str = "0.0.0.0",  # noqa: S104
    port: int = 8000,
    name: str | None = None,
) -> int:
    """Launch the Credence FastAPI + FastMCP multi-plane server engine."""
    if name:
        settings.NODE_ALIAS = name
    alias_display = settings.effective_node_alias
    console.print(
        f"[bold green]Starting Credence Server [{transport.upper()}] on {host}:{port} (Node: {alias_display})...[/bold green]"
    )
    uvicorn.run("credence.server.app:app", host=host, port=port, reload=False)
    return 0
