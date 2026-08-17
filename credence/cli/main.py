"""Rich Terminal Command-Line Interface (CLI) for Credence.

Commands:
- credence audit <url> [--force]
- credence lookup <hash_or_url>
- credence identity [show|generate]
- credence taxonomy [list|show <catalog_id>]
- credence quota
- credence serve [--transport {stdio,sse}] [--host HOST] [--port PORT]
- credence mesh [--port PORT] [--seeds SEEDS]
- credence tui
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlmodel import select

from credence.config import settings
from credence.db import get_session, init_db
from credence.identity import load_or_create_node_identity
from credence.models import AuditRecord, SnapshotRecord, ViolationRecord
from credence.pipeline.evaluator import audit_url
from credence.pipeline.governor import get_token_headroom_status
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.taxonomy_loader import registry

console = Console()


def _get_verdict_badge(report: AuditReport) -> tuple[str, str]:
    if report.is_satire:
        return "cyan", "🎭 SATIRE / PARODY"
    if report.suspicion_score <= 15.0:
        return "green", "🛡️ CLEAN"
    if report.suspicion_score <= 40.0:
        return "yellow", "⚠️ LOW SUSPICION"
    if report.suspicion_score <= 70.0:
        return "dark_orange", "🚨 SUSPICIOUS"
    return "bold red", "🛑 HIGH DECEPTION"


def _render_violations_table(violations: list[SpecialistViolationFinding]) -> None:
    table = Table(title="[bold]Itemized Grounded Violations[/bold]", show_header=True, header_style="bold magenta")
    table.add_column("Rule ID", style="cyan", width=12)
    table.add_column("Domain", style="dim", width=22)
    table.add_column("Sev", justify="center", width=5)
    table.add_column("Cited Excerpt / Element", style="italic", width=40)
    table.add_column("Reasoning & Evidence", style="white")

    for v in violations:
        sev_style = "red" if v.severity >= 4 else ("yellow" if v.severity == 3 else "green")
        table.add_row(
            v.rule_id,
            v.domain,
            f"[{sev_style}]{v.severity}[/{sev_style}]",
            f'"{v.quote_or_element}"' if len(v.quote_or_element) < 80 else f'"{v.quote_or_element[:77]}..."',
            v.reasoning,
        )
    console.print(table)


def render_audit_report(report: AuditReport) -> None:
    """Render an AuditReport as a formatted Rich dashboard panel."""
    color, badge = _get_verdict_badge(report)

    summary_lines = [
        f"[bold]Target URL:[/bold] {report.url}",
        f"[bold]Content SHA-256:[/bold] {report.content_sha256}",
        f"[bold]SimHash-64:[/bold] {report.simhash_64}",
        f"[bold]Verdict:[/bold] [{color}]{badge} ({report.classification})[/{color}]",
        f"[bold]Suspicion Score:[/bold] [{color}]{report.suspicion_score:.1f} / 100.0[/{color}]",
        f"[bold]Suspicion Density:[/bold] {report.suspicion_density:.1f} violations / 1,000 words",
        f"[bold]Evaluation Confidence:[/bold] {report.confidence_score * 100:.0f}%",
    ]

    if report.quota_preserved:
        summary_lines.append(
            "[bold yellow]⚡ Quota Preserved:[/bold yellow] Offline heuristic mode executed to protect developer tokens."
        )

    if report.is_satire:
        summary_lines.append(
            f"[bold cyan]Satire Advisory:[/bold cyan] {report.satire_notes or 'Satire/Parody content'}"
        )

    if report.node_pubkey:
        summary_lines.append(
            f"[bold]Node Identity PubKey:[/bold] {report.node_pubkey[:16]}...{report.node_pubkey[-8:]}"
        )
    if report.node_signature:
        summary_lines.append(
            f"[bold]Ed25519 Signature:[/bold] {report.node_signature[:16]}...{report.node_signature[-8:]}"
        )

    panel = Panel("\n".join(summary_lines), title="[bold]Credence Audit Summary[/bold]", border_style=color)
    console.print(panel)

    if report.violations:
        _render_violations_table(report.violations)
    else:
        console.print("[green]✓ No rule violations detected on this page.[/green]\n")


async def cli_audit(url: str, force: bool = False) -> None:
    """Execute live audit or cache lookup for target URL."""
    with console.status(f"[bold green]Evaluating {url}...", spinner="dots"):
        report = await audit_url(url, force_refresh=force)
    render_audit_report(report)


async def cli_lookup(identifier: str) -> None:
    """Look up cached audit report by URL or content SHA-256."""
    await init_db()
    async for s in get_session():
        if identifier.startswith("sha256:") or len(identifier) == 64:
            clean_hash = identifier if identifier.startswith("sha256:") else f"sha256:{identifier}"
            stmt = select(AuditRecord).where(AuditRecord.content_sha256 == clean_hash)
        else:
            snap_stmt = select(SnapshotRecord).where(SnapshotRecord.url == identifier)
            snap = (await s.exec(snap_stmt)).first()
            if not snap:
                console.print(f"[red]No cached audit found for URL: {identifier}[/red]")
                return
            stmt = select(AuditRecord).where(AuditRecord.content_sha256 == snap.content_sha256)

        audit = (await s.exec(stmt)).first()
        if not audit:
            console.print(f"[red]No cached audit found matching: {identifier}[/red]")
            return

        v_stmt = select(ViolationRecord).where(ViolationRecord.audit_id == audit.id)
        violations = (await s.exec(v_stmt)).all()

        violations_schemas = [
            SpecialistViolationFinding(
                rule_id=v.rule_id,
                rule_uri=v.rule_uri,
                domain=v.domain,
                cluster_id=v.cluster_id,
                severity=v.severity,
                confidence=v.confidence,
                quote_or_element=v.quote_or_element,
                reasoning=v.reasoning,
                line_or_selector=v.line_or_selector,
                is_grounded=True,
            )
            for v in violations
        ]

        report = AuditReport(
            url=identifier,
            content_sha256=audit.content_sha256,
            simhash_64="0x0000000000000000",
            audited_at=audit.audited_at,
            suspicion_score=audit.suspicion_score,
            suspicion_density=audit.suspicion_density,
            confidence_score=audit.confidence_score,
            classification=audit.classification,
            is_satire=audit.is_satire,
            content_type=audit.content_type,
            satire_notes=audit.satire_notes,
            violations=violations_schemas,
            node_pubkey=audit.node_pubkey,
            node_signature=audit.node_signature,
            quota_preserved=audit.quota_preserved,
        )
        render_audit_report(report)
        return


def cli_identity(action: str) -> None:
    """Show or generate Ed25519 node identity keypair."""
    identity = load_or_create_node_identity()
    console.print(
        Panel(
            f"[bold]Node Public Key (Ed25519):[/bold] [cyan]{identity.public_key_hex}[/cyan]\n"
            f"[bold]Keyfile Path:[/bold] {identity.key_path}",
            title="[bold]Credence Node Identity[/bold]",
            border_style="cyan",
        )
    )


def cli_taxonomy(action: str, catalog_id: Optional[str] = None) -> None:
    """List or inspect registered taxonomy catalogs."""
    registry.load_all()

    if action == "list" or not catalog_id:
        table = Table(title="[bold]Registered Taxonomy Catalogs[/bold]", show_header=True, header_style="bold cyan")
        table.add_column("Catalog ID", style="bold")
        table.add_column("Domain", style="green")
        table.add_column("Version", style="dim")
        table.add_column("Weight", justify="right")
        table.add_column("Clusters", justify="right")
        table.add_column("Rules", justify="right")
        table.add_column("Catalog Hash (SHA-256)", style="dim")

        for cat in registry.list_catalogs():
            total_rules = sum(len(c.rules) for c in cat.clusters)
            table.add_row(
                cat.catalog_id,
                cat.domain,
                f"v{cat.version}",
                str(cat.default_weight),
                str(len(cat.clusters)),
                str(total_rules),
                cat.catalog_hash[:20] + "..." if cat.catalog_hash else "N/A",
            )
        console.print(table)
    else:
        target_cat = registry.get_catalog(catalog_id)
        if not target_cat:
            console.print(f"[red]Catalog '{catalog_id}' not found.[/red]")
            return
        checklist = registry.generate_prompt_checklist(catalog_id)
        console.print(checklist)


async def cli_quota() -> None:
    """Display real-time Token Headroom, spend metrics, and Circuit Breaker safety status."""
    await init_db()
    async for s in get_session():
        status = await get_token_headroom_status(s)

        cb_style = (
            "bold red"
            if status.circuit_breaker_tripped
            else ("bold yellow" if status.throttle_active else "bold green")
        )
        cb_label = (
            "🚨 TRIPPED (QUOTA_PRESERVED)"
            if status.circuit_breaker_tripped
            else ("⚠️ THROTTLED (High Usage)" if status.throttle_active else "🟢 HEALTHY (Normal Concurrency)")
        )

        lines = [
            f"[bold]Active API Key Source:[/bold] [cyan]{status.active_api_key_source}[/cyan]",
            f"[bold]Circuit Breaker Status:[/bold] [{cb_style}]{cb_label}[/{cb_style}]\n",
            f"[bold]Hourly Token Headroom:[/bold] [green]{status.hourly_headroom_pct:.1f}% remaining[/green] ({status.hourly_tokens_used:,} / {status.hourly_tokens_max:,} tokens)",
            f"[bold]Daily Token Headroom:[/bold]  [green]{status.daily_headroom_pct:.1f}% remaining[/green] ({status.daily_tokens_used:,} / {status.daily_tokens_max:,} tokens)",
            f"[bold]24h Estimated Spend:[/bold]    [yellow]${status.daily_spend_usd:.4f}[/yellow] / ${status.daily_budget_usd:.2f} USD ({status.daily_spend_pct:.1f}% budget used)",
        ]

        console.print(
            Panel(
                "\n".join(lines),
                title="[bold]Token Safety Governor & Headroom Budget[/bold]",
                border_style="green" if not status.circuit_breaker_tripped else "red",
            )
        )
        return


def cli_serve(transport: str = "stdio", host: str = "0.0.0.0", port: int = 8000) -> None:  # noqa: S104
    """Launch the FastMCP server in Stdio or SSE mode."""
    from credence.server.app import mcp_server

    if transport == "stdio":
        console.print("[green]Starting Credence FastMCP Server on stdio...[/green]")
        asyncio.run(mcp_server.run_stdio_async())
    elif transport == "sse":
        import uvicorn

        console.print(f"[bold green]Starting Credence FastMCP Server (SSE) on http://{host}:{port}/sse[/bold green]")
        uvicorn.run(mcp_server.sse_app(), host=host, port=port)


async def cli_mesh(port: int, seeds: list[str]) -> None:
    """Launch the P2P Mesh Relay node."""
    from credence.mesh.relay import MeshGossipRelay

    relay = MeshGossipRelay(port=port, peer_seeds=seeds)
    await relay.start()
    console.print(f"[bold cyan]Credence Mesh Relay active on ws://{settings.MESH_HOST}:{port}[/bold cyan]")
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        await relay.stop()


def main() -> None:
    """CLI argument parsing and router."""
    parser = argparse.ArgumentParser(
        prog="credence",
        description="Credence: Epistemic evaluation engine and decentralized trust network.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # audit command
    audit_parser = subparsers.add_parser("audit", help="Audit a webpage for epistemic suspicion.")
    audit_parser.add_argument("url", type=str, help="Target URL to snapshot and audit.")
    audit_parser.add_argument("--force", action="store_true", help="Force fresh audit, bypassing cache.")

    # lookup command
    lookup_parser = subparsers.add_parser("lookup", help="Lookup cached audit by URL or content hash.")
    lookup_parser.add_argument("identifier", type=str, help="URL or content SHA-256.")

    # identity command
    id_parser = subparsers.add_parser("identity", help="Manage node cryptographic identity.")
    id_parser.add_argument("action", choices=["show", "generate"], default="show", nargs="?")

    # quota command
    subparsers.add_parser("quota", help="Display token headroom, daily USD spend, and circuit breaker status.")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Launch FastMCP server.")
    serve_parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="MCP transport protocol.")
    serve_parser.add_argument("--host", default=settings.MCP_HOST, help="Bind host for SSE transport.")
    serve_parser.add_argument("--port", type=int, default=settings.MCP_PORT, help="Port for SSE transport.")

    # mesh command
    mesh_parser = subparsers.add_parser("mesh", help="Launch Credence P2P Mesh relay.")
    mesh_parser.add_argument("--port", type=int, default=settings.MESH_PORT, help="Port for Mesh WebSocket listener.")
    mesh_parser.add_argument("--seeds", default="", help="Comma-separated list of peer seed WebSocket URLs.")

    # tui command
    subparsers.add_parser("tui", help="Launch interactive Terminal User Interface (TUI) dashboard.")

    # taxonomy command
    tax_parser = subparsers.add_parser("taxonomy", help="Explore taxonomy catalogs and rules.")
    tax_parser.add_argument("action", choices=["list", "show"], default="list", nargs="?")
    tax_parser.add_argument("catalog_id", nargs="?", default=None)

    if len(sys.argv) == 1:
        # Default to launching TUI if no args provided in interactive terminal
        from credence.tui.app import run_tui

        run_tui()
        return

    args = parser.parse_args()

    if args.command == "tui":
        from credence.tui.app import run_tui

        run_tui()
    elif args.command == "audit":
        asyncio.run(cli_audit(args.url, force=args.force))
    elif args.command == "lookup":
        asyncio.run(cli_lookup(args.identifier))
    elif args.command == "identity":
        cli_identity(args.action)
    elif args.command == "quota":
        asyncio.run(cli_quota())
    elif args.command == "serve":
        cli_serve(transport=args.transport, host=args.host, port=args.port)
    elif args.command == "mesh":
        seeds_list = [s.strip() for s in args.seeds.split(",") if s.strip()]
        asyncio.run(cli_mesh(port=args.port, seeds=seeds_list))
    elif args.command == "taxonomy":
        cli_taxonomy(args.action, args.catalog_id)


if __name__ == "__main__":
    main()
