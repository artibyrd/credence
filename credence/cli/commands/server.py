"""CLI Server Launch Command Handlers for Credence."""

from __future__ import annotations

import uvicorn
from rich.console import Console

console = Console()


def run_server_command(transport: str = "sse", host: str = "0.0.0.0", port: int = 8000) -> int:  # noqa: S104
    """Launch the Credence FastAPI + FastMCP multi-plane server engine."""
    console.print(f"[bold green]Starting Credence Server [{transport.upper()}] on {host}:{port}...[/bold green]")
    uvicorn.run("credence.server.app:app", host=host, port=port, reload=False)
    return 0
