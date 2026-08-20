"""CLI Mesh P2P Relay & Leaderboard Command Handlers for Credence."""

from __future__ import annotations

import asyncio

from rich.console import Console

from credence.mesh.relay import MeshGossipRelay

console = Console()


async def run_mesh_serve_command(port: int = 8765) -> int:
    """Launch local P2P Mesh Gossip Relay server."""
    console.print(f"[bold cyan]Starting Credence P2P Mesh Relay on port {port}...[/bold cyan]")
    relay = MeshGossipRelay(port=port)
    await relay.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await relay.stop()
    return 0
