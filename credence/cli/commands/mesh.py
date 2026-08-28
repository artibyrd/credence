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


async def run_mesh_audit_feed_command(
    feed_or_domain: str,
    node: str | None = None,
    limit: int = 10,
    profile: str = "balanced",
    json_output: bool = False,
) -> int:
    """Routinely audit RSS feed entries and contribute signed attestations to local node and/or remote mesh."""
    import json

    import httpx

    from credence.config import COST_PROFILES, CostProfile, settings
    from credence.db import init_db
    from credence.feeds.parser import fetch_and_parse_feed
    from credence.pipeline.evaluator import audit_url

    # 1. Normalize feed target
    target = (feed_or_domain or "").strip()
    if not target or target in ("inmaricopa", "inmaricopa.com"):
        feed_url = "https://inmaricopa.com/feed/"
    elif target.startswith("http://") or target.startswith("https://"):
        feed_url = target
    else:
        feed_url = f"https://{target.rstrip('/')}/feed/"

    # 2. Fetch and parse feed
    try:
        parsed = await fetch_and_parse_feed(feed_url)
    except Exception as e:
        console.print(f"[bold red]Failed to fetch or parse feed '{feed_url}': {e}[/bold red]")
        return 1

    if not parsed.entries:
        console.print(f"[yellow]No entries discovered in feed '{feed_url}'.[/yellow]")
        return 0

    entries_to_audit = parsed.entries[:limit]
    console.print(
        f"[cyan]Found {len(parsed.entries)} entries; auditing up to {len(entries_to_audit)} entries with profile '{profile}'...[/cyan]\n"
    )

    await init_db()

    cost_prof = (
        CostProfile(profile.lower()) if profile.lower() in [p.value for p in CostProfile] else CostProfile.BALANCED
    )
    prof_cfg = COST_PROFILES.get(cost_prof)

    audited_reports: list[dict] = []

    for idx, entry in enumerate(entries_to_audit):
        console.print(
            f"[[bold cyan]{idx + 1}/{len(entries_to_audit)}[/bold cyan]] Auditing: [bold white]{entry.title}[/bold white] ({entry.url})..."
        )
        try:
            report = await audit_url(entry.url, profile_override=prof_cfg)
            score = report.suspicion_score
            viols_count = (
                len(report.findings)
                if hasattr(report, "findings") and report.findings
                else (len(report.violations) if hasattr(report, "violations") and report.violations else 0)
            )

            score_color = "green" if score <= 15.0 else ("yellow" if score < 60.0 else "red")
            console.print(
                f"   ↳ Score: [{score_color}]{score:.1f}[/{score_color}] | Violations: {viols_count} | SHA: {report.content_sha256[:16]}..."
            )
            audited_reports.append(report.model_dump(mode="json"))
        except Exception as e:
            console.print(f"   [bold red]↳ Evaluation failed: {e}[/bold red]")

    if not audited_reports:
        console.print("[yellow]No articles were successfully audited.[/yellow]")
        return 1

    # 2. Remote mesh node submission if specified
    remote_endpoint = node or settings.CREDENCE_SENTINEL_NODE_URL
    if remote_endpoint:
        submit_url = f"{remote_endpoint.rstrip('/')}/api/mesh/submit-batch"
        console.print(
            f"\n[cyan]Submitting {len(audited_reports)} signed attestation(s) to mesh node: {submit_url}...[/cyan]"
        )
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(submit_url, json={"attestations": audited_reports})
                if resp.status_code in (200, 207):
                    res_data = resp.json()
                    console.print(
                        f"[bold green]✓ Remote Mesh Submission Accepted![/bold green] Status: {res_data.get('status', 'OK')} (Accepted: {res_data.get('accepted', len(audited_reports))})"
                    )
                else:
                    console.print(f"[yellow]Remote Mesh Submission Status ({resp.status_code}): {resp.text}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Remote mesh submission note: {e}[/yellow]")

    if json_output:
        console.print(json.dumps(audited_reports, indent=2))
    else:
        console.print(
            f"\n[bold green]✓ Feed Audit Completed successfully ({len(audited_reports)} articles audited).[/bold green]"
        )

    return 0
