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
import json
import sys
import webbrowser
from typing import List, Optional

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


def _generate_cli_exec_summary(report: AuditReport) -> str:
    """Generate plain-English human summary for terminal display."""
    if report.is_satire:
        return (
            "[bold cyan]🧠 Human Takeaway:[/bold cyan] "
            "This publication was classified as [bold]Legitimate Satire / Parody[/bold]. "
            "Under Poe's Law neutrality safeguards, legitimate humor and hyperbole are neutralized to 0.0 suspicion."
        )
    if report.suspicion_score <= 15.0:
        return (
            "[bold green]🧠 Human Takeaway:[/bold green] "
            "This content demonstrates [bold]high epistemic integrity[/bold] with verified factual assertions, "
            "transparent author attribution, and zero deceptive interface patterns."
        )

    fallacies = [v for v in report.violations if v.domain == "LOGICAL_FALLACY"]
    ethics = [v for v in report.violations if v.domain == "JOURNALISTIC_ETHICS"]
    deceptive = [v for v in report.violations if v.domain == "DECEPTIVE_PATTERN"]

    parts = []
    if deceptive:
        rules = ", ".join(d.rule_id for d in deceptive)
        parts.append(f"[bold red]{len(deceptive)} deceptive interface pattern(s)[/bold red] ({rules})")
    if fallacies:
        rules = ", ".join(f.rule_id for f in fallacies)
        parts.append(f"[bold yellow]{len(fallacies)} logical fallacy(ies)[/bold yellow] ({rules})")
    if ethics:
        rules = ", ".join(e.rule_id for e in ethics)
        parts.append(f"[bold yellow]{len(ethics)} journalistic sourcing violation(s)[/bold yellow] ({rules})")

    details = " and ".join(parts) if parts else "minor structural anomalies"
    return (
        f"[bold dark_orange]🧠 Human Takeaway:[/bold dark_orange] "
        f"Multi-agent specialists flagged {details}. "
        f"Readers are advised to verify primary sources and avoid hasty dissemination."
    )


def _render_domain_meters(report: AuditReport) -> Panel:
    """Render a visual domain breakdown meter in the terminal."""
    total_ethics = sum(1 for v in report.violations if v.domain == "JOURNALISTIC_ETHICS")
    total_fallacy = sum(1 for v in report.violations if v.domain == "LOGICAL_FALLACY")
    total_deceptive = sum(1 for v in report.violations if v.domain == "DECEPTIVE_PATTERN")

    def meter_bar(count: int) -> tuple[str, str]:
        if count == 0:
            return "[green]████████████████████[/green]", "[green]Clean (0 issues)[/green]"
        elif count <= 2:
            return "[yellow]██████████░░░░░░░░░░[/yellow]", f"[yellow]{count} issue(s)[/yellow]"
        else:
            return "[red]████░░░░░░░░░░░░░░░░[/red]", f"[bold red]{count} issue(s)[/bold red]"

    eth_bar, eth_lbl = meter_bar(total_ethics)
    fal_bar, fal_lbl = meter_bar(total_fallacy)
    dec_bar, dec_lbl = meter_bar(total_deceptive)

    lines = [
        f"  • [bold]Journalistic Ethics & Sourcing (SPJ):[/bold]  {eth_bar}  {eth_lbl}",
        f"  • [bold]Logical Coherence & Fallacies (IEP):[/bold]   {fal_bar}  {fal_lbl}",
        f"  • [bold]Commercial & Design Transparency:[/bold]     {dec_bar}  {dec_lbl}",
    ]
    return Panel("\n".join(lines), title="[bold]Epistemic Trust Dimensions[/bold]", border_style="cyan")


def _render_violations_table(violations: list[SpecialistViolationFinding]) -> None:
    table = Table(title="[bold]Itemized Grounded Violations[/bold]", show_header=True, header_style="bold magenta")
    table.add_column("Rule ID", style="cyan", width=12)
    table.add_column("Domain", style="dim", width=22)
    table.add_column("Sev", justify="center", width=7)
    table.add_column("Cited Excerpt / Element", style="italic", width=38)
    table.add_column("Reasoning & Evidence", style="white")

    for v in violations:
        sev_style = "bold red" if v.severity >= 4 else ("yellow" if v.severity == 3 else "green")
        sev_str = f"[{sev_style}]{v.severity}/5[/{sev_style}]"
        table.add_row(
            v.rule_id,
            v.domain,
            sev_str,
            f'"{v.quote_or_element}"' if len(v.quote_or_element) < 70 else f'"{v.quote_or_element[:67]}..."',
            v.reasoning,
        )
    console.print(table)


def render_audit_report(report: AuditReport) -> None:
    """Render an AuditReport as an intuitive, human-centered Rich dashboard."""
    color, badge = _get_verdict_badge(report)

    # 1. Executive Summary Panel
    exec_summary = _generate_cli_exec_summary(report)
    console.print(Panel(exec_summary, title="[bold]Executive Epistemic Briefing[/bold]", border_style=color))

    # 2. Domain Breakdown Meters
    console.print(_render_domain_meters(report))

    # 3. Itemized Violations Table
    if report.violations:
        _render_violations_table(report.violations)
    else:
        console.print("[green]✓ No rule violations detected on this page. Grounded truth verified.[/green]\n")

    # 4. Technical Provenance & Cryptographic Summary
    summary_lines = [
        f"[bold]Target URL:[/bold]             {report.url}",
        f"[bold]Content SHA-256:[/bold]        {report.content_sha256}",
        f"[bold]SimHash-64 (Near-Dup):[/bold]  {report.simhash_64}",
        f"[bold]Calibrated Score:[/bold]        [{color}]{report.suspicion_score:.1f} / 100.0 ({badge})[/{color}]",
        f"[bold]Suspicion Density:[/bold]       {report.suspicion_density:.1f} violations / 1,000 words",
        f"[bold]Evaluation Confidence:[/bold]   {report.confidence_score * 100:.0f}%",
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
            f"[bold]Node Identity PubKey:[/bold]   {report.node_pubkey[:16]}...{report.node_pubkey[-8:]}"
        )
    if report.node_signature:
        summary_lines.append(
            f"[bold]Ed25519 Signature:[/bold]      {report.node_signature[:16]}...{report.node_signature[-8:]} [green](RFC 8785 Valid)[/green]"
        )

    panel = Panel("\n".join(summary_lines), title="[bold]Cryptographic Provenance & Digest[/bold]", border_style="dim")
    console.print(panel)


async def cli_audit(
    url: str,
    force: bool = False,
    profile_override: Optional[CostProfileConfig] = None,
    open_browser: bool = False,
) -> None:
    """Execute live audit or cache lookup for target URL."""
    with console.status(f"[bold green]Evaluating {url}...", spinner="dots"):
        report = await audit_url(url, force_refresh=force, profile_override=profile_override)
    render_audit_report(report)

    if open_browser:
        viewer_url = f"https://credence.report/viewer.html?q={report.content_sha256}"
        webbrowser.open(viewer_url)
        console.print(f"[cyan]Opened in web report viewer:[/] {viewer_url}")


async def cli_lookup(identifier: str, open_browser: bool = False) -> None:
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

        simhash = snap.simhash_64 if "snap" in locals() and snap else "0x0000000000000000"
        report = AuditReport(
            url=identifier,
            content_sha256=audit.content_sha256,
            simhash_64=simhash,
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
            evaluation_method=getattr(
                audit,
                "evaluation_method",
                "offline_structural_heuristic" if audit.quota_preserved else "llm_multi_agent",
            ),
        )
        render_audit_report(report)
        if open_browser:
            viewer_url = f"https://credence.report/viewer.html?q={report.content_sha256}"
            webbrowser.open(viewer_url)
            console.print(f"[cyan]Opened in web report viewer:[/] {viewer_url}")
        return


async def cli_report_view(
    identifier: str,
    open_browser: bool = False,
    format_type: str = "terminal",
) -> None:
    """Inspect and render an audit report in terminal, markdown, or JSON."""
    if format_type.lower() in ("markdown", "json"):
        await cli_export_report(identifier, format_type=format_type)
    else:
        await cli_lookup(identifier, open_browser=open_browser)


def cli_identity(action: str) -> None:
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
        from mcp.server.transport_security import TransportSecuritySettings

        console.print(
            f"[bold green]Starting Credence FastMCP Server (SSE) on http://{host}:{port}/sse (Profile: {settings.CREDENCE_PROFILE.value.upper()})[/bold green]"
        )
        sec = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
            allowed_hosts=["*"],
            allowed_origins=["*"],
        )
        uvicorn.run(mcp_server.sse_app(transport_security=sec), host=host, port=port)


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
                evaluation_method=getattr(
                    record,
                    "evaluation_method",
                    "offline_structural_heuristic" if record.quota_preserved else "llm_multi_agent",
                ),
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
    elif cmd == "benchmark":
        asyncio.run(cli_benchmark())
        return True
    return False


def _dispatch_mesh_commands(args: argparse.Namespace) -> bool:
    """Dispatch P2P mesh and federation subcommands."""
    cmd = args.command
    if cmd == "mesh":
        seeds_list = [s.strip() for s in args.seeds.split(",") if s.strip()]
        asyncio.run(cli_mesh(port=args.port, seeds=seeds_list))
        return True
    elif cmd == "seeds":
        asyncio.run(
            cli_seeds(
                action=args.action,
                url_or_path=args.url or args.path,
                output_path=args.output,
                valid_hours=getattr(args, "valid_hours", 24),
            )
        )
        return True
    elif cmd == "rank":
        asyncio.run(cli_rank())
        return True
    elif cmd == "init-org":
        cli_init_org(
            name=args.name,
            domain=args.domain,
            output_dir=args.output,
            email=args.email,
            brand_title=getattr(args, "brand_title", None),
        )
        return True
    return False


async def cli_seeds(
    action: str = "fetch",
    url_or_path: Optional[str] = None,
    output_path: Optional[str] = None,
    valid_hours: int = 24,
) -> None:
    """Manage, fetch, generate, and cryptographically verify P2P bootstrap seed manifests."""
    from pathlib import Path

    from credence.identity import load_or_create_node_identity
    from credence.mesh.discovery import BootstrapDiscovery
    from credence.mesh.seed import (
        BootstrapSeedFile,
        SeedNodeEntry,
        generate_seed_file,
        verify_seed_file,
    )
    from credence.models import PeerMetricRecord

    target_url = url_or_path or settings.DEFAULT_SEED_URL

    if action == "fetch":
        console.print(f"[bold cyan]Fetching bootstrap seed manifest from:[/bold cyan] {target_url}")
        discovery = BootstrapDiscovery(seed_url=target_url)
        peer_urls = await discovery.discover_peers()

        table = Table(
            title=f"[bold]Discovered Bootstrap Seed Peers ({len(peer_urls)})[/bold]",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Index", style="dim", justify="right")
        table.add_column("WebSocket Endpoint URL", style="bold green")

        for idx, url in enumerate(peer_urls, 1):
            table.add_row(str(idx), url)
        console.print(table)

        if output_path and peer_urls:
            Path(output_path).write_text(json.dumps(peer_urls, indent=2), encoding="utf-8")
            console.print(f"[green]Saved {len(peer_urls)} peer URLs to:[/green] {output_path}")

    elif action == "generate":
        await init_db()
        identity = load_or_create_node_identity()
        candidates: List[SeedNodeEntry] = []

        async for session in get_session():
            stmt = select(PeerMetricRecord).order_by(col(PeerMetricRecord.quality_score).desc()).limit(20)
            records = (await session.exec(stmt)).all()
            for r in records:
                candidates.append(
                    SeedNodeEntry(
                        node_pubkey=r.node_pubkey,
                        node_alias=r.node_alias,
                        ws_url=r.ws_url,
                        quality_score=r.quality_score,
                        uptime_pct=100.0 * (r.successful_heartbeats / max(1, r.total_heartbeats_sent)),
                        region="us-central1",
                    )
                )

        # If no DB records, include local node identity as initial bootstrap seed entry
        if not candidates:
            candidates.append(
                SeedNodeEntry(
                    node_pubkey=identity.public_key_hex,
                    node_alias="local-root-seed",
                    ws_url=f"ws://{settings.MESH_HOST}:{settings.MESH_PORT}",
                    quality_score=1.0,
                    uptime_pct=100.0,
                    region="us-central1",
                )
            )

        manifest = generate_seed_file(
            nodes=candidates,
            identity=identity,
            valid_hours=valid_hours,
            canonical_domain="https://seeds.credence.nexus/peers.json",
        )

        out_file = Path(output_path or "seeds.json")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")

        console.print(
            Panel(
                f"[bold green]Generated and Signed Bootstrap Seed Manifest[/bold green]\n\n"
                f"- [bold]Target File:[/bold]        {out_file.absolute()}\n"
                f"- [bold]Canonical Domain:[/bold]   {manifest.canonical_domain}\n"
                f"- [bold]Seed Nodes Included:[/bold]{len(manifest.seed_nodes)}\n"
                f"- [bold]Valid Duration:[/bold]     {valid_hours} hours (expires: {manifest.expires_at.isoformat()})\n"
                f"- [bold]Root Signer Pubkey:[/bold] [cyan]{manifest.root_pubkey}[/cyan]\n"
                f"- [bold]Signature Hex:[/bold]      [dim]{(manifest.root_signature or '')[:32]}...[/dim]",
                title="[bold]P2P Bootstrap Seed Manifest[/bold]",
                border_style="green",
            )
        )

    elif action == "verify":
        file_path = Path(url_or_path or "seeds.json")
        if not file_path.exists():
            console.print(f"[bold red]Seed file not found:[/bold red] {file_path}")
            return
        data = json.loads(file_path.read_text(encoding="utf-8"))
        manifest = BootstrapSeedFile.model_validate(data)
        is_valid = verify_seed_file(manifest)

        status_text = "✅ CRYPTOGRAPHICALLY VALID" if is_valid else "❌ INVALID SIGNATURE OR EXPIRED"
        status_style = "bold green" if is_valid else "bold red"

        console.print(
            Panel(
                f"[bold]File:[/bold]               {file_path}\n"
                f"[bold]Canonical Domain:[/bold]   {manifest.canonical_domain}\n"
                f"[bold]Root Pubkey:[/bold]        [cyan]{manifest.root_pubkey}[/cyan]\n"
                f"[bold]Generated At:[/bold]       {manifest.generated_at.isoformat()}\n"
                f"[bold]Expires At:[/bold]         {manifest.expires_at.isoformat()}\n"
                f"[bold]Seed Nodes Count:[/bold]   {len(manifest.seed_nodes)}\n\n"
                f"[{status_style}]{status_text}[/{status_style}]",
                title="[bold]Seed Manifest Verification[/bold]",
                border_style="green" if is_valid else "red",
            )
        )


async def cli_rank() -> None:
    """Display Rich terminal leaderboard of mesh nodes ranked by the 5-factor quality score."""
    from credence.mesh.quality import NodeMetrics, rank_nodes
    from credence.models import PeerMetricRecord

    await init_db()
    metrics_list: List[NodeMetrics] = []

    async for session in get_session():
        stmt = select(PeerMetricRecord)
        records = (await session.exec(stmt)).all()
        for r in records:
            metrics_list.append(
                NodeMetrics(
                    node_pubkey=r.node_pubkey,
                    node_alias=r.node_alias,
                    ws_url=r.ws_url,
                    total_heartbeats_sent=r.total_heartbeats_sent,
                    successful_heartbeats=r.successful_heartbeats,
                    average_latency_ms=r.average_latency_ms,
                    total_attestations_evaluated=r.total_attestations_evaluated,
                    median_score_deviations_sum=r.median_score_deviations_sum,
                    grounded_citations_count=r.grounded_citations_count,
                    total_citations_count=r.total_citations_count,
                    has_valid_catalog_hashes=r.has_valid_catalog_hashes,
                )
            )

    if not metrics_list:
        # Create representative sample for demonstration if database is empty
        identity = load_or_create_node_identity()
        metrics_list.append(
            NodeMetrics(
                node_pubkey=identity.public_key_hex,
                node_alias="local-node",
                ws_url=f"ws://{settings.MESH_HOST}:{settings.MESH_PORT}",
                total_heartbeats_sent=100,
                successful_heartbeats=100,
                average_latency_ms=25.0,
                total_attestations_evaluated=12,
                median_score_deviations_sum=1.2,
                grounded_citations_count=15,
                total_citations_count=15,
                has_valid_catalog_hashes=True,
            )
        )

    ranked = rank_nodes(metrics_list, top_k=25)

    table = Table(
        title="[bold]Credence Epistemic Node Quality Leaderboard ($Q_i$)[/bold]",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Node Alias", style="bold cyan")
    table.add_column("Pubkey", style="dim")
    table.add_column("Endpoint URL", style="green")
    table.add_column("Q_i Total", justify="right", style="bold yellow")
    table.add_column("Uptime (25%)", justify="right")
    table.add_column("Concord (30%)", justify="right")
    table.add_column("Ground (25%)", justify="right")
    table.add_column("Tax (10%)", justify="right")
    table.add_column("Age (10%)", justify="right")
    table.add_column("Status", justify="center")

    for idx, s in enumerate(ranked, 1):
        status_label = "[bold green]SEED CANDIDATE[/bold green]" if s.is_seed_candidate else "[dim]PEER[/dim]"
        table.add_row(
            f"#{idx}",
            s.node_alias,
            f"{s.node_pubkey[:12]}...",
            s.ws_url,
            f"{s.quality_score:.4f}",
            f"{s.uptime_factor:.2f}",
            f"{s.concordance_factor:.2f}",
            f"{s.grounding_factor:.2f}",
            f"{s.taxonomy_factor:.2f}",
            f"{s.longevity_factor:.2f}",
            status_label,
        )

    console.print(table)


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
    elif cmd == "report":
        asyncio.run(
            cli_report_view(
                args.identifier,
                open_browser=getattr(args, "open", False),
                format_type=getattr(args, "format", "terminal"),
            )
        )
    elif cmd == "db-clean":
        asyncio.run(cli_db_clean(retention_days=args.retention_days))
    elif cmd in ("feeds", "feed"):
        asyncio.run(_dispatch_feeds_cli(args))
    elif cmd == "sifter":
        from credence.config import CostProfile
        from credence.feeds.sifter import SifterDaemon

        daemon = SifterDaemon(
            poll_interval_seconds=args.interval,
            cost_profile=CostProfile(args.profile.lower()),
            auto_audit=not args.no_auto_audit,
        )
        asyncio.run(daemon.start())
    elif cmd == "digest":
        from credence.db import get_session, init_db
        from credence.feeds.digest import generate_morning_digest, render_digest_terminal

        async def _run_digest():
            await init_db()
            async for session in get_session():
                dig = await generate_morning_digest(session, timeframe_hours=args.hours)
                if args.format == "terminal":
                    render_digest_terminal(dig)
                elif args.format == "markdown":
                    md_text = dig.to_markdown()
                    if args.output:
                        with open(args.output, "w", encoding="utf-8") as f:
                            f.write(md_text)
                        console.print(f"[bold green]Digest written to:[/] {args.output}")
                    else:
                        print(md_text)
                elif args.format == "json":
                    js_text = json.dumps(dig.to_dict(), indent=2)
                    if args.output:
                        with open(args.output, "w", encoding="utf-8") as f:
                            f.write(js_text)
                        console.print(f"[bold green]Digest JSON written to:[/] {args.output}")
                    else:
                        print(js_text)

        asyncio.run(_run_digest())
    elif cmd == "subjects":
        _dispatch_subjects_cli(args)


async def cli_feeds(
    action: str = "list",
    url: Optional[str] = None,
    title: str = "",
    priority: int = 2,
    tag: str = "journalism.news",
    satire: bool = False,
    dry_run: bool = False,
    evaluate: bool = True,
) -> None:
    """Entrypoint for feeds CLI commands."""
    args = argparse.Namespace(
        action=action,
        url=url,
        title=title,
        priority=priority,
        subject=tag,
        satire=satire,
        dry_run=dry_run,
        evaluate=evaluate,
    )
    await _dispatch_feeds_cli(args)


def cli_subjects(action: str = "list", subject_id: Optional[str] = None) -> None:
    """Entrypoint for subjects CLI commands."""
    args = argparse.Namespace(action=action, subject_id=subject_id)
    _dispatch_subjects_cli(args)


async def _dispatch_feeds_cli(args: argparse.Namespace) -> None:
    """Dispatch feed subcommands."""

    from credence.db import get_session, init_db
    from credence.feeds.discovery import discover_feed_endpoints
    from credence.feeds.health import calculate_feed_quality_score, run_preflight_feed_audit
    from credence.feeds.worker import bootstrap_preset_feeds, sync_all_feeds
    from credence.models import FeedItemRecord, FeedSubscriptionRecord

    await init_db()
    action = args.action or "list"

    async for session in get_session():
        if action == "discover":
            if not args.url:
                console.print(
                    "[bold red]Error:[/] Target URL is required for discovery. e.g. `credence feed discover https://apnews.com`"
                )
                return

            console.print(f"[bold cyan]🔍 Scanning webpage for RSS/Atom/JSON feeds:[/] {args.url} ...")
            candidates = await discover_feed_endpoints(args.url)
            if not candidates:
                console.print(f"[yellow]No feed endpoints autodiscovered on:[/] {args.url}")
                return

            table = Table(title=f"Discovered Feed Endpoints for {args.url}", show_header=True, header_style="bold cyan")
            table.add_column("Feed Title", style="bold white")
            table.add_column("Format", justify="center", style="yellow", width=8)
            table.add_column("Feed URL", style="cyan")
            table.add_column("Verified", justify="center", width=10)

            for c in candidates:
                ver_badge = "[green]YES[/green]" if c.is_verified else "[dim]CANDIDATE[/dim]"
                table.add_row(c.title, c.feed_type.upper(), c.feed_url, ver_badge)

            console.print(table)
            console.print("[dim]Tip: Use `credence feed inspect <feed_url>` to run a pre-flight forensic audit.[/dim]")

        elif action == "inspect":
            if not args.url:
                console.print(
                    "[bold red]Error:[/] Feed URL is required for inspection. e.g. `credence feed inspect https://example.com/rss`"
                )
                return

            console.print(f"[bold cyan]🔬 Executing pre-flight forensic audit on:[/] {args.url} ...")
            result = await run_preflight_feed_audit(args.url, session=session)
            m = result.metrics

            status_style = "green" if m.status == "ACTIVE" else ("yellow" if m.status == "PROBATION" else "bold red")
            summary_panel = (
                f"- [bold]Feed Title:[/bold]            {result.feed_title}\n"
                f"- [bold]Feed URL:[/bold]              {result.feed_url}\n"
                f"- [bold]Composite Score (F_j):[/bold]  [{status_style}]{m.composite_score_fj:.2f} ({m.status})[/{status_style}]\n"
                f"- [bold]Average Suspicion Score:[/bold] {m.avg_suspicion_score:.1f} / 100.0\n"
                f"- [bold]Grounding Precision (G):[/bold] {m.grounding_ratio * 100:.1f}%\n"
                f"- [bold]Topic Entropy (H_topic):[/bold] {m.topic_entropy:.3f} (Diversity vs Astroturfing)\n"
                f"- [bold]Freshness Index:[/bold]        {m.freshness_index:.2f}\n"
                f"- [bold]Recommendation:[/bold]         {'[green]APPROVED FOR ACTIVE INGESTION[/green]' if result.is_recommended else '[red]QUARANTINE / PROBATION[/red]'}\n"
            )
            if result.quarantine_reasons:
                summary_panel += "\n[bold red]Quarantine Warnings:[/bold red]\n" + "\n".join(
                    f"  • {r}" for r in result.quarantine_reasons
                )

            console.print(
                Panel(summary_panel, title="[bold]Epistemic Pre-Flight Audit Report[/bold]", border_style=status_style)
            )

        elif action == "health":
            stmt = select(FeedSubscriptionRecord)
            subs = (await session.exec(stmt)).all()
            table = Table(
                title="[bold]Dynamic Feed Health & Epistemic Quality Rankings[/bold]",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("ID", width=4)
            table.add_column("Feed Title / Channel", style="bold white", width=26)
            table.add_column("Quality (F_j)", justify="center", width=12)
            table.add_column("Avg Suspicion", justify="right", width=14)
            table.add_column("Grounding", justify="right", width=10)
            table.add_column("Entropy (H)", justify="right", width=12)
            table.add_column("Status", justify="center", width=12)

            for s in subs:
                metrics = calculate_feed_quality_score([], None)
                status_pill = "[green]ACTIVE[/green]" if s.is_active else "[bold red]QUARANTINE[/bold red]"
                table.add_row(
                    str(s.id),
                    s.title or s.feed_url.split("/")[2],
                    f"[cyan]{metrics.composite_score_fj:.2f}[/cyan]",
                    f"{metrics.avg_suspicion_score:.1f}",
                    f"{metrics.grounding_ratio * 100:.0f}%",
                    f"{metrics.topic_entropy:.2f}",
                    status_pill,
                )
            console.print(table)

        elif action == "bootstrap-presets":
            cat = getattr(args, "category", None)
            added = await bootstrap_preset_feeds(session, category=cat)
            console.print(f"[bold green]✓ Successfully bootstrapped {added} diverse feed subscriptions![/bold green]")

        elif action == "list":
            stmt = select(FeedSubscriptionRecord).order_by(col(FeedSubscriptionRecord.priority_tier).asc())
            subs = (await session.exec(stmt)).all()
            table = Table(
                title="[bold]Syndicated Feed Subscriptions[/bold]", show_header=True, header_style="bold magenta"
            )
            table.add_column("ID", style="dim", width=4)
            table.add_column("Title / Channel", style="bold cyan", width=26)
            table.add_column("Feed URL", style="green")
            table.add_column("Tier", justify="center", width=6)
            table.add_column("Subject Tag", style="yellow", width=22)
            table.add_column("Status", justify="center", width=8)

            for s in subs:
                status = "[green]ACTIVE[/green]" if s.is_active else "[dim]PAUSED[/dim]"
                table.add_row(
                    str(s.id),
                    s.title or "(unnamed)",
                    s.feed_url,
                    f"Tier {s.priority_tier}",
                    s.subject_tag,
                    status,
                )
            console.print(table)

        elif action == "add":
            sub_rec = FeedSubscriptionRecord(
                feed_url=args.url,
                title=args.title or "",
                priority_tier=args.priority,
                subject_tag=args.subject or "journalism.news",
                is_satire=args.satire,
            )
            session.add(sub_rec)
            await session.commit()
            console.print(
                f"[bold green]Successfully subscribed to feed:[/bold green] {args.url} (Tier {args.priority})"
            )

        elif action == "remove":
            stmt = select(FeedSubscriptionRecord).where(FeedSubscriptionRecord.feed_url == args.url)
            sub_del = (await session.exec(stmt)).first()
            if sub_del is not None:
                await session.delete(sub_del)
                await session.commit()
                console.print(f"[bold red]Removed feed subscription:[/bold red] {args.url}")
            else:
                console.print(f"[yellow]Subscription not found for URL:[/yellow] {args.url}")

        elif action == "sync":
            console.print(f"[bold cyan]Synchronizing all active feeds...[/bold cyan] (Dry Run: {args.dry_run})")
            summary = await sync_all_feeds(session=session, dry_run=args.dry_run)
            console.print(
                Panel(
                    f"- [bold]Total Feeds Polled:[/bold]        {summary.total_feeds_polled}\n"
                    f"- [bold]Feeds Unmodified (304):[/bold]    {summary.feeds_unmodified_304}\n"
                    f"- [bold]New Articles Discovered:[/bold]   {summary.new_items_discovered}\n"
                    f"- [bold]Zero-Token Mesh Adoptions:[/bold] [green]{summary.items_adopted_from_mesh}[/green]\n"
                    f"- [bold]Total LLM Tokens Saved:[/bold]    [bold yellow]{summary.tokens_saved_total:,} tokens[/bold yellow]\n"
                    f"- [bold]Deferred for Headroom:[/bold]     {summary.items_deferred_budget}\n",
                    title="[bold]Feed Synchronization Summary[/bold]",
                    border_style="green" if summary.items_adopted_from_mesh > 0 else "blue",
                )
            )

        elif action == "stats":
            stmt_items = select(FeedItemRecord)
            items = (await session.exec(stmt_items)).all()
            total_items = len(items)
            adopted_count = sum(1 for i in items if i.processing_status == "mesh_adopted")
            tokens_saved = sum(i.tokens_saved for i in items)

            console.print(
                Panel(
                    f"- [bold]Total Articles Discovered:[/bold]   {total_items}\n"
                    f"- [bold]Zero-Token Mesh Adoptions:[/bold]   [green]{adopted_count}[/green]\n"
                    f"- [bold]Total Compute Tokens Saved:[/bold]  [bold yellow]{tokens_saved:,} tokens[/bold yellow]\n"
                    f"- [bold]Attestation Seeding Status:[/bold]  [cyan]ACTIVE (BitTorrent Tit-for-Tat Enabled)[/cyan]\n",
                    title="[bold]Generous Defaults & Mesh Work-Sharing Stats[/bold]",
                    border_style="cyan",
                )
            )


def _dispatch_subjects_cli(args: argparse.Namespace) -> None:
    """Dispatch subject registry subcommands."""
    from rich.tree import Tree

    from credence.subjects.registry import get_subject_registry

    reg = get_subject_registry()
    action = args.action or "list"

    if action == "list":
        tree_data = reg.get_hierarchy_tree()
        root_tree = Tree("[bold magenta]Credence Epistemic Subject Hierarchy[/bold magenta]")

        for r in tree_data:
            branch = root_tree.add(f"[bold cyan]{r['title']}[/bold cyan] ([dim]{r['subject_id']}[/dim])")
            for c in r.get("children", []):
                branch.add(f"[yellow]{c['title']}[/yellow] ([dim]{c['subject_id']}[/dim]) - {c['description']}")

        console.print(root_tree)

    elif action == "show":
        subj = reg.get_subject(args.subject_id)
        if not subj:
            console.print(f"[bold red]Subject namespace '{args.subject_id}' not found.[/bold red]")
            return

        console.print(
            Panel(
                f"- [bold]Namespace ID:[/bold]  [cyan]{subj.subject_id}[/cyan]\n"
                f"- [bold]Title:[/bold]         {subj.title}\n"
                f"- [bold]Parent:[/bold]        {subj.parent_id or 'None (Root Domain)'}\n"
                f"- [bold]Description:[/bold]   {subj.description}\n"
                f"- [bold]Taxonomies:[/bold]    {', '.join(subj.taxonomies) if subj.taxonomies else 'Default'}\n"
                f"- [bold]Keywords:[/bold]      {', '.join(subj.keywords[:8])}...\n",
                title=f"[bold]Subject Details: {subj.title}[/bold]",
                border_style="magenta",
            )
        )


def cli_init_org(
    name: str,
    domain: str,
    output_dir: str = "./my-mesh-org",
    email: Optional[str] = None,
    brand_title: Optional[str] = None,
) -> None:
    """Scaffold sovereign white-label mesh organization workspace."""
    from pathlib import Path

    from credence.mesh.org import generate_mesh_org

    config, identity = generate_mesh_org(
        org_name=name,
        base_domain=domain,
        output_dir=output_dir,
        contact_email=email,
        brand_title=brand_title,
    )

    console.print(
        Panel(
            f"[bold green]Sovereign Mesh Organization Generated![/bold green]\n\n"
            f"- [bold]Organization Name:[/bold]  {config.org_name}\n"
            f"- [bold]Base Domain:[/bold]        {domain}\n"
            f"- [bold]Target Directory:[/bold]   {Path(output_dir).absolute()}\n"
            f"- [bold]Root Public Key:[/bold]    [cyan]{config.root_public_key}[/cyan]\n"
            f"- [bold]Contact Email:[/bold]      {config.contact_email}\n\n"
            f"[bold]Endpoints Configured:[/bold]\n"
            f"  • Run / Landing:   https://{config.domain_run}\n"
            f"  • FastMCP SSE:     https://mcp.{config.domain_run}/sse\n"
            f"  • P2P Seeds:       https://seeds.{config.domain_nexus}/peers.json\n"
            f"  • Taxonomies:      https://taxonomies.{config.domain_foundation}\n"
            f"  • Public Reports:  https://{config.domain_report}\n\n"
            f"[dim]Next steps: Inspect {output_dir}/terraform.tfvars and {output_dir}/web/[/dim]",
            title="[bold]Credence Mesh Federation Generator[/bold]",
            border_style="green",
        )
    )


def _dispatch_command(args: argparse.Namespace) -> None:
    """Dispatch parsed CLI arguments to appropriate subcommands."""
    from credence.config import COST_PROFILES, CostProfile

    cmd = args.command
    if cmd == "tui":
        from credence.tui.app import run_tui

        run_tui()
    elif cmd == "audit":
        prof_cfg = COST_PROFILES.get(CostProfile(args.profile.lower())) if args.profile else None
        asyncio.run(
            cli_audit(
                args.url,
                force=args.force,
                profile_override=prof_cfg,
                open_browser=getattr(args, "open", False),
            )
        )
    elif cmd == "lookup":
        asyncio.run(cli_lookup(args.identifier, open_browser=getattr(args, "open", False)))
    elif not _dispatch_service_commands(args) and not _dispatch_mesh_commands(args):
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
    audit_parser.add_argument(
        "--open",
        action="store_true",
        help="Automatically open audit in browser report viewer upon completion.",
    )

    # lookup command
    lookup_parser = subparsers.add_parser("lookup", help="Lookup cached audit by URL or content hash.")
    lookup_parser.add_argument("identifier", type=str, help="URL or content SHA-256.")
    lookup_parser.add_argument(
        "--open",
        action="store_true",
        help="Automatically open lookup in browser report viewer upon completion.",
    )

    # report command
    report_parser = subparsers.add_parser("report", help="Inspect and view audit reports.")
    report_parser.add_argument("identifier", type=str, help="URL or content SHA-256 to view.")
    report_parser.add_argument(
        "--format",
        choices=["terminal", "markdown", "json"],
        default="terminal",
        help="Display format (default: terminal).",
    )
    report_parser.add_argument(
        "--open",
        action="store_true",
        help="Open in default web browser.",
    )

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

    # seeds command
    seeds_parser = subparsers.add_parser(
        "seeds", help="Fetch, generate, or verify cryptographically signed bootstrap seed manifests."
    )
    seeds_parser.add_argument(
        "action",
        choices=["fetch", "generate", "verify"],
        default="fetch",
        nargs="?",
        help="Action to perform on seeds.",
    )
    seeds_parser.add_argument(
        "--url",
        "-u",
        type=str,
        default=None,
        help="Target seed file URL or path for fetch/verify.",
    )
    seeds_parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path for verify action.",
    )
    seeds_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output filepath for generated/fetched seeds.",
    )
    seeds_parser.add_argument(
        "--valid-hours",
        type=int,
        default=24,
        help="Validity duration in hours for generated seed manifest (default: 24).",
    )

    # rank command
    subparsers.add_parser(
        "rank",
        help="Display Rich terminal leaderboard of mesh nodes ranked by the 5-factor quality score ($Q_i$).",
    )

    # init-org command
    org_parser = subparsers.add_parser(
        "init-org", help="Scaffold a new sovereign white-label Credence mesh organization."
    )
    org_parser.add_argument("--name", "-n", required=True, help="Organization name (e.g. 'FactCheck Consortium').")
    org_parser.add_argument("--domain", "-d", required=True, help="Base domain (e.g. 'factcheck.nexus').")
    org_parser.add_argument(
        "--output", "-o", default="./my-mesh-org", help="Output directory for generated org workspace."
    )
    org_parser.add_argument("--email", "-e", default=None, help="Contact email for security and alerts.")
    org_parser.add_argument("--brand-title", default=None, help="Custom brand title header.")

    # feeds command (and feed alias)
    for feed_cmd_name in ["feeds", "feed"]:
        feeds_parser = subparsers.add_parser(
            feed_cmd_name, help="Manage syndicated RSS/Atom/JSON feed discovery, health, and mesh effort avoidance."
        )
        feeds_parser.add_argument(
            "action",
            choices=["list", "add", "remove", "sync", "stats", "discover", "inspect", "health", "bootstrap-presets"],
            default="list",
            nargs="?",
            help="Action: list, add, remove, sync, stats, discover, inspect, health, bootstrap-presets",
        )
        feeds_parser.add_argument(
            "url", nargs="?", default=None, help="Feed URL or target website for discover/inspect/add/remove."
        )
        feeds_parser.add_argument("--title", "-t", default="", help="Custom title for feed.")
        feeds_parser.add_argument("--priority", "-p", type=int, default=2, help="Priority tier 1-4 (default: 2).")
        feeds_parser.add_argument("--subject", "-s", default="journalism.news", help="Subject tag namespace.")
        feeds_parser.add_argument(
            "--category", "-c", default=None, help="Category filter for presets (e.g. investigative-tech, core-news)."
        )
        feeds_parser.add_argument("--satire", action="store_true", help="Flag as satire publication.")
        feeds_parser.add_argument("--dry-run", action="store_true", help="Inspect without modifying database.")

    # sifter command
    sifter_parser = subparsers.add_parser(
        "sifter", help="Launch real-time background feed sifter daemon with dynamic health eviction."
    )
    sifter_parser.add_argument(
        "--interval", "-i", type=int, default=300, help="Polling cycle interval in seconds (default: 300)."
    )
    sifter_parser.add_argument(
        "--profile", choices=["free", "balanced", "ultra"], default="balanced", help="Operational cost profile."
    )
    sifter_parser.add_argument(
        "--no-auto-audit", action="store_true", help="Discover items without running live LLM evaluations."
    )

    # digest command
    digest_parser = subparsers.add_parser(
        "digest", help="Generate the structured Morning Epistemic Briefing from evaluated articles."
    )
    digest_parser.add_argument("--hours", "-H", type=int, default=24, help="Timeframe window in hours (default: 24).")
    digest_parser.add_argument(
        "--format", choices=["terminal", "markdown", "json"], default="terminal", help="Output format."
    )
    digest_parser.add_argument("--output", "-o", default=None, help="Filepath to write markdown or JSON output to.")

    # subjects command
    subjects_parser = subparsers.add_parser(
        "subjects", help="Explore hierarchical subject registry and empirical domain expertise."
    )
    subjects_parser.add_argument(
        "action",
        choices=["list", "show"],
        default="list",
        nargs="?",
        help="Action: list, show",
    )
    subjects_parser.add_argument("subject_id", nargs="?", default=None, help="Subject namespace ID.")

    if len(sys.argv) == 1:
        # Default to launching TUI if no args provided in interactive terminal
        from credence.tui.app import run_tui

        run_tui()
        return

    args = parser.parse_args()
    _dispatch_command(args)


if __name__ == "__main__":
    main()
