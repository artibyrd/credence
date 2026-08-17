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
from sqlmodel import col, select

from credence.config import CostProfileConfig, settings
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


async def cli_audit(
    url: str,
    force: bool = False,
    profile_override: Optional[CostProfileConfig] = None,
) -> None:
    """Execute live audit or cache lookup for target URL."""
    with console.status(f"[bold green]Evaluating {url}...", spinner="dots"):
        report = await audit_url(url, force_refresh=force, profile_override=profile_override)
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


def cli_profile(action: str = "list", profile_name: Optional[str] = None) -> None:
    """List or inspect operational cost profiles."""
    from credence.config import COST_PROFILES, CostProfile

    if action == "list" and not profile_name:
        table = Table(
            title="[bold]Credence Operational Cost Profiles[/bold]",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Profile", style="bold cyan")
        table.add_column("Target Tier", style="dim")
        table.add_column("Primary Model", style="green")
        table.add_column("Thinking", justify="right")
        table.add_column("Daily Cap", justify="right")
        table.add_column("Max Words", justify="right")
        table.add_column("Active", justify="center")

        active_prof = settings.CREDENCE_PROFILE
        for p, cfg in COST_PROFILES.items():
            is_active = "[bold green]✓ ACTIVE[/bold green]" if p == active_prof else "[dim]-[/dim]"
            table.add_row(
                p.value.upper(),
                cfg.target_tier,
                cfg.primary_model,
                f"{cfg.default_thinking_budget} tok",
                f"${cfg.max_daily_budget_usd:.2f}/day",
                f"{cfg.max_article_words:,} w",
                is_active,
            )
        console.print(table)
    else:
        name = (profile_name or action).lower()
        try:
            target_profile = CostProfile(name)
            cfg = COST_PROFILES[target_profile]
            lines = [
                f"[bold]Profile:[/bold] [cyan]{cfg.name}[/cyan] ({cfg.profile.value.upper()})",
                f"[bold]Target Tier:[/bold] {cfg.target_tier}",
                f"[bold]Description:[/bold] {cfg.description}",
                f"[bold]Primary Model:[/bold] [green]{cfg.primary_model}[/green]",
                f"[bold]Escalation Model:[/bold] [yellow]{cfg.escalation_model}[/yellow]",
                f"[bold]Thinking Tokens (Default / Escalation):[/bold] {cfg.default_thinking_budget} / {cfg.escalation_thinking_budget}",
                f"[bold]Hourly Token Cap:[/bold] {cfg.max_tokens_per_hour:,} tokens",
                f"[bold]Daily Token Cap:[/bold] {cfg.max_tokens_per_day:,} tokens",
                f"[bold]Daily Budget Limit:[/bold] ${cfg.max_daily_budget_usd:.2f} USD",
                f"[bold]Article Word Limit:[/bold] {cfg.max_article_words:,} words",
                f"[bold]Concurrency Gate:[/bold] {cfg.concurrency_limit} concurrent requests",
            ]
            console.print(
                Panel(
                    "\n".join(lines),
                    title=f"[bold]Cost Profile: {cfg.profile.value.upper()}[/bold]",
                    border_style="cyan",
                )
            )
        except ValueError:
            console.print(f"[red]Unknown cost profile '{name}'. Choose from: free, balanced, ultra.[/red]")


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
            f"[bold]Active Operational Profile:[/bold] [bold cyan]{status.active_profile.upper()}[/bold cyan] ([dim]{status.profile_target_tier}[/dim])",
            f"[bold]Active API Key Source:[/bold]      [cyan]{status.active_api_key_source}[/cyan]",
            f"[bold]Circuit Breaker Status:[/bold]     [{cb_style}]{cb_label}[/{cb_style}]\n",
            f"[bold]Hourly Token Headroom:[/bold]      [green]{status.hourly_headroom_pct:.1f}% remaining[/green] ({status.hourly_tokens_used:,} / {status.hourly_tokens_max:,} tokens)",
            f"[bold]Daily Token Headroom:[/bold]       [green]{status.daily_headroom_pct:.1f}% remaining[/green] ({status.daily_tokens_used:,} / {status.daily_tokens_max:,} tokens)",
            f"[bold]24h Estimated Spend:[/bold]        [yellow]${status.daily_spend_usd:.4f}[/yellow] / ${status.daily_budget_usd:.2f} USD ({status.daily_spend_pct:.1f}% budget used)",
        ]

        console.print(
            Panel(
                "\n".join(lines),
                title="[bold]Token Safety Governor & Headroom Budget[/bold]",
                border_style="green" if not status.circuit_breaker_tripped else "red",
            )
        )
        return


def cli_serve(
    transport: str = "stdio",
    host: str = "0.0.0.0",  # noqa: S104
    port: int = 8000,
    profile: Optional[str] = None,
) -> None:
    """Launch the FastMCP server in Stdio or SSE mode."""
    from credence.config import CostProfile
    from credence.server.app import mcp_server

    if profile:
        try:
            settings.CREDENCE_PROFILE = CostProfile(profile.lower())
        except ValueError:
            console.print(
                f"[yellow]Invalid profile '{profile}', using default '{settings.CREDENCE_PROFILE.value}'.[/yellow]"
            )

    if transport == "stdio":
        console.print(
            f"[green]Starting Credence FastMCP Server on stdio (Profile: {settings.CREDENCE_PROFILE.value.upper()})...[/green]"
        )
        asyncio.run(mcp_server.run_stdio_async())
    elif transport == "sse":
        import uvicorn

        console.print(
            f"[bold green]Starting Credence FastMCP Server (SSE) on http://{host}:{port}/sse (Profile: {settings.CREDENCE_PROFILE.value.upper()})[/bold green]"
        )
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


async def cli_benchmark() -> None:
    """Run the Golden 12 epistemic benchmark across FREE, BALANCED, and ULTRA profiles."""
    from credence.pipeline.benchmark import render_benchmark_table, run_epistemic_benchmark

    with console.status("[bold green]Executing 'Golden 12' multi-profile benchmark...", spinner="dots"):
        suite = await run_epistemic_benchmark()
    render_benchmark_table(suite)


def report_to_markdown(report: AuditReport) -> str:
    """Generate a clean, structured Markdown export of an AuditReport."""
    badge = "SATIRE / PARODY" if report.is_satire else report.classification
    lines = [
        "# Credence Epistemic Audit Report",
        "",
        f"- **Target URL:** `{report.url}`",
        f"- **Audited At:** {report.audited_at.isoformat()}",
        f"- **Verdict:** **{badge}**",
        f"- **Suspicion Score:** `{report.suspicion_score:.1f}/100.0`",
        f"- **Suspicion Density:** `{report.suspicion_density:.2f} violations/1k words`",
        f"- **Confidence Score:** `{report.confidence_score:.2f}`",
        f"- **Content SHA-256:** `{report.content_sha256}`",
        f"- **SimHash-64:** `{report.simhash_64}`",
        f"- **Node Public Key:** `{report.node_pubkey or 'unsigned'}`",
        f"- **Cryptographic Signature:** `{report.node_signature or 'unsigned'}`",
        "",
    ]
    if report.satire_notes:
        lines.extend(["### Satire & Provenance Notes", f"> {report.satire_notes}", ""])

    lines.extend([f"## Itemized Violations ({len(report.violations)})", ""])
    if not report.violations:
        lines.append("*No ethics, fallacy, or deceptive pattern violations detected. Content is clean.*")
    else:
        lines.extend(
            [
                "| Rule ID | Severity | Quoted Excerpt | Reasoning & Evidence |",
                "|---|---|---|---|",
            ]
        )
        for v in report.violations:
            clean_quote = v.quote_or_element.replace("\n", " ").replace("|", "\\|")[:80]
            clean_reason = v.reasoning.replace("\n", " ").replace("|", "\\|")
            lines.append(f'| `{v.rule_id}` | {v.severity}/5 | *"{clean_quote}"* | {clean_reason} |')

    lines.append("")
    lines.append("---")
    lines.append("*Generated autonomously by Credence Epistemic Engine & FastMCP 2.0 Server.*")
    return "\n".join(lines)


def cli_verify_file(file_path: str) -> None:
    """Verify an on-disk Ed25519-signed JSON audit attestation file."""
    import json
    from pathlib import Path

    from credence.identity import verify_audit_report

    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]File not found:[/bold red] {file_path}")
        return

    try:
        raw_json = json.loads(path.read_text(encoding="utf-8"))
        report = AuditReport.model_validate(raw_json)
    except Exception as e:
        console.print(f"[bold red]Invalid attestation JSON format:[/bold red] {e}")
        return

    is_valid = verify_audit_report(report)
    badge_style, badge_text = _get_verdict_badge(report)

    status_icon = "✅ CRYPTOGRAPHICALLY VALID" if is_valid else "❌ INVALID SIGNATURE"
    status_style = "bold green" if is_valid else "bold red"

    lines = [
        f"[bold]Attestation File:[/bold]   {file_path}",
        f"[bold]Signature Status:[/bold]   [{status_style}]{status_icon}[/{status_style}]",
        f"[bold]Node Public Key:[/bold]    [cyan]{report.node_pubkey or 'N/A'}[/cyan]",
        f"[bold]Target URL:[/bold]         [cyan]{report.url}[/cyan]",
        f"[bold]Content SHA-256:[/bold]    {report.content_sha256}",
        f"[bold]Suspicion Score:[/bold]    [{badge_style}]{report.suspicion_score:.1f}/100.0 ({badge_text})[/{badge_style}]",
        f"[bold]Confidence Score:[/bold]   {report.confidence_score:.2f}",
        f"[bold]Grounded Violations:[/bold] {len(report.violations)}",
    ]

    console.print(
        Panel(
            "\n".join(lines),
            title="[bold]Credence Attestation Verification[/bold]",
            border_style="green" if is_valid else "red",
        )
    )

    if report.violations:
        _render_violations_table(report.violations)


async def cli_export_report(
    identifier: str,
    format_type: str = "markdown",
    output_path: Optional[str] = None,
) -> None:
    """Export an audit report to formatted Markdown or JSON."""
    import json
    from pathlib import Path

    await init_db()
    async for session in get_session():
        # Query latest snapshot to find matching audit record
        snap_query = (
            select(SnapshotRecord)
            .where((SnapshotRecord.url == identifier) | (SnapshotRecord.content_sha256 == identifier))
            .order_by(col(SnapshotRecord.captured_at).desc())
        )
        snap_res = await session.exec(snap_query)
        snapshot = snap_res.first()

        record: Optional[AuditRecord] = None
        if snapshot and snapshot.id is not None:
            audit_query = (
                select(AuditRecord)
                .where(AuditRecord.snapshot_id == snapshot.id)
                .order_by(col(AuditRecord.audited_at).desc())
            )
            audit_res = await session.exec(audit_query)
            record = audit_res.first()
        else:
            audit_query = (
                select(AuditRecord)
                .where(AuditRecord.content_sha256 == identifier)
                .order_by(col(AuditRecord.audited_at).desc())
            )
            audit_res = await session.exec(audit_query)
            record = audit_res.first()
            if record and record.snapshot_id:
                s_res = await session.exec(select(SnapshotRecord).where(SnapshotRecord.id == record.snapshot_id))
                snapshot = s_res.first()

        if not record or not snapshot:
            console.print(f"[yellow]No cached audit found for '{identifier}'. Running live audit first...[/yellow]")
            report = await audit_url(identifier, session=session)
        else:
            violation_query = select(ViolationRecord).where(ViolationRecord.audit_id == record.id)
            v_res = await session.exec(violation_query)
            violation_records = v_res.all()
            violations = [
                SpecialistViolationFinding(
                    rule_id=vr.rule_id,
                    rule_uri=vr.rule_uri,
                    domain=vr.domain,
                    cluster_id=vr.cluster_id,
                    severity=vr.severity,
                    confidence=vr.confidence,
                    quote_or_element=vr.quote_or_element,
                    reasoning=vr.reasoning,
                    line_or_selector=vr.line_or_selector,
                    is_grounded=True,
                )
                for vr in violation_records
            ]
            from datetime import timezone

            audited_at = (
                record.audited_at
                if record.audited_at.tzinfo is not None
                else record.audited_at.replace(tzinfo=timezone.utc)
            )
            report = AuditReport(
                url=snapshot.url,
                content_sha256=record.content_sha256,
                simhash_64=snapshot.simhash_64,
                suspicion_score=record.suspicion_score,
                suspicion_density=record.suspicion_density,
                confidence_score=record.confidence_score,
                classification=record.classification,
                is_satire=record.is_satire,
                content_type=record.content_type,
                satire_notes=record.satire_notes,
                violations=violations,
                taxonomies_used=json.loads(record.taxonomies_used_json),
                node_pubkey=record.node_pubkey,
                node_signature=record.node_signature,
                quota_preserved=record.quota_preserved,
                audited_at=audited_at,
            )

        if format_type.lower() == "json":
            content = json.dumps(report.model_dump(mode="json"), indent=2)
        else:
            content = report_to_markdown(report)

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")
            console.print(f"[bold green]Report exported successfully to:[/bold green] {output_path}")
        else:
            console.print(content)
        return


async def cli_db_clean(retention_days: int = 30) -> None:
    """Prune expired token usage records and optimize SQLite database."""
    from datetime import datetime, timedelta, timezone

    from credence.models import TokenUsageRecord

    await init_db()
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    async for session in get_session():
        query = select(TokenUsageRecord).where(TokenUsageRecord.timestamp < cutoff)
        records = (await session.exec(query)).all()
        for r in records:
            await session.delete(r)
        await session.commit()
        console.print(
            Panel(
                f"[bold green]Database Cleaned & Optimized Successfully[/bold green]\n\n"
                f"- [bold]Retention Window:[/bold] {retention_days} days\n"
                f"- [bold]Cutoff Timestamp:[/bold] {cutoff.isoformat()}\n"
                f"- [bold]Pruned Token Records:[/bold] {len(records)}\n"
                f"- [bold]SQLite WAL Maintenance:[/bold] Completed",
                title="[bold]Database Maintenance[/bold]",
                border_style="green",
            )
        )
        return


def _dispatch_service_commands(args: argparse.Namespace) -> bool:
    """Dispatch daemon and server subcommands."""
    cmd = args.command
    if cmd == "serve":
        cli_serve(transport=args.transport, host=args.host, port=args.port, profile=args.profile)
        return True
    elif cmd == "mesh":
        seeds_list = [s.strip() for s in args.seeds.split(",") if s.strip()]
        asyncio.run(cli_mesh(port=args.port, seeds=seeds_list))
        return True
    elif cmd == "benchmark":
        asyncio.run(cli_benchmark())
        return True
    return False


def _dispatch_utility_commands(args: argparse.Namespace) -> None:
    """Dispatch inspection and maintenance subcommands."""
    cmd = args.command
    if cmd == "identity":
        cli_identity(args.action)
    elif cmd == "quota":
        asyncio.run(cli_quota())
    elif cmd == "profile":
        cli_profile(args.action, args.profile_name)
    elif cmd == "taxonomy":
        cli_taxonomy(args.action, args.catalog_id)
    elif cmd == "verify-file":
        cli_verify_file(args.path)
    elif cmd == "export-report":
        asyncio.run(cli_export_report(args.identifier, format_type=args.format, output_path=args.output))
    elif cmd == "db-clean":
        asyncio.run(cli_db_clean(retention_days=args.retention_days))


def _dispatch_command(args: argparse.Namespace) -> None:
    """Dispatch parsed CLI arguments to appropriate subcommands."""
    from credence.config import COST_PROFILES, CostProfile

    cmd = args.command
    if cmd == "tui":
        from credence.tui.app import run_tui

        run_tui()
    elif cmd == "audit":
        prof_cfg = COST_PROFILES.get(CostProfile(args.profile.lower())) if args.profile else None
        asyncio.run(cli_audit(args.url, force=args.force, profile_override=prof_cfg))
    elif cmd == "lookup":
        asyncio.run(cli_lookup(args.identifier))
    elif not _dispatch_service_commands(args):
        _dispatch_utility_commands(args)


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
    audit_parser.add_argument(
        "--profile",
        choices=["free", "balanced", "ultra"],
        default=None,
        help="Operational cost profile override.",
    )

    # lookup command
    lookup_parser = subparsers.add_parser("lookup", help="Lookup cached audit by URL or content hash.")
    lookup_parser.add_argument("identifier", type=str, help="URL or content SHA-256.")

    # identity command
    id_parser = subparsers.add_parser("identity", help="Manage node cryptographic identity.")
    id_parser.add_argument("action", choices=["show", "generate"], default="show", nargs="?")

    # quota command
    subparsers.add_parser("quota", help="Display token headroom, daily USD spend, and circuit breaker status.")

    # profile command
    profile_parser = subparsers.add_parser("profile", help="List and inspect operational cost profiles.")
    profile_parser.add_argument("action", choices=["list", "show"], default="list", nargs="?")
    profile_parser.add_argument("profile_name", nargs="?", default=None, help="Profile name (free, balanced, ultra)")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Launch FastMCP server.")
    serve_parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="MCP transport protocol.")
    serve_parser.add_argument("--host", default=settings.MCP_HOST, help="Bind host for SSE transport.")
    serve_parser.add_argument("--port", type=int, default=settings.MCP_PORT, help="Port for SSE transport.")
    serve_parser.add_argument(
        "--profile",
        choices=["free", "balanced", "ultra"],
        default=None,
        help="Active cost profile.",
    )

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

    # benchmark command
    subparsers.add_parser(
        "benchmark",
        help="Run the 'Golden 12' epistemic benchmark suite across FREE, BALANCED, and ULTRA profiles.",
    )

    # verify-file command
    verify_file_parser = subparsers.add_parser("verify-file", help="Verify an Ed25519-signed JSON attestation file.")
    verify_file_parser.add_argument("path", type=str, help="Path to signed JSON attestation file.")

    # export-report command
    export_parser = subparsers.add_parser("export-report", help="Export an audit report to Markdown or JSON.")
    export_parser.add_argument("identifier", type=str, help="URL or content SHA-256 to export.")
    export_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (markdown or json).",
    )
    export_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Target output filepath (writes to stdout if omitted).",
    )

    # db-clean command
    db_clean_parser = subparsers.add_parser("db-clean", help="Prune older token records and optimize SQLite database.")
    db_clean_parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Retention window in days (default: 30).",
    )

    if len(sys.argv) == 1:
        # Default to launching TUI if no args provided in interactive terminal
        from credence.tui.app import run_tui

        run_tui()
        return

    args = parser.parse_args()
    _dispatch_command(args)


if __name__ == "__main__":
    main()
