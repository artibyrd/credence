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


async def run_mesh_submit_command(
    target: str,
    node: str | None = None,
    batch: bool = False,
    json_output: bool = False,
) -> int:
    """Submit locally-evaluated signed audit reports to a remote Credence node."""
    import json
    from pathlib import Path

    import httpx

    from credence.config import settings
    from credence.db import init_db
    from credence.pipeline.evaluator import audit_url

    endpoint = node or settings.CREDENCE_SENTINEL_NODE_URL or "http://127.0.0.1:8000"
    target_path = Path(target)

    reports_to_send: list[dict] = []

    if target_path.exists() and target_path.is_file():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            if isinstance(raw_data, list):
                reports_to_send = raw_data
            elif isinstance(raw_data, dict):
                if "attestations" in raw_data or "reports" in raw_data:
                    reports_to_send = raw_data.get("attestations") or raw_data.get("reports") or []
                else:
                    reports_to_send = [raw_data]
        except Exception as e:
            console.print(f"[bold red]Failed to load JSON file {target}: {e}[/bold red]")
            return 1
    else:
        # Target is a URL to evaluate and submit
        console.print(f"[cyan]Evaluating URL locally before submission: {target}...[/cyan]")
        await init_db()
        report = await audit_url(target)
        reports_to_send = [report.model_dump(mode="json")]

    if not reports_to_send:
        console.print("[yellow]No audit reports found to submit.[/yellow]")
        return 1

    submit_url = (
        f"{endpoint.rstrip('/')}/api/mesh/submit-batch"
        if (len(reports_to_send) > 1 or batch)
        else f"{endpoint.rstrip('/')}/api/mesh/submit-attestation"
    )
    payload = {"attestations": reports_to_send} if (len(reports_to_send) > 1 or batch) else reports_to_send[0]

    console.print(f"[cyan]Submitting {len(reports_to_send)} report(s) to mesh node: {submit_url}...[/cyan]")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(submit_url, json=payload)
            if resp.status_code in (200, 207):
                res_data = resp.json()
                if json_output:
                    console.print(json.dumps(res_data, indent=2))
                else:
                    console.print(
                        f"[bold green]✓ Submission Accepted![/bold green] Status: {res_data.get('status', 'OK')}"
                    )
                    if "accepted" in res_data:
                        console.print(
                            f"  Accepted: [green]{res_data.get('accepted')}[/green] | Rejected: [red]{res_data.get('rejected')}[/red]"
                        )
                return 0
            else:
                console.print(f"[bold red]Submission Rejected ({resp.status_code}):[/bold red] {resp.text}")
                return 1
    except Exception as e:
        console.print(f"[bold red]Network error contacting mesh node {endpoint}: {e}[/bold red]")
        return 1
