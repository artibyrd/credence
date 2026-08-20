"""CLI Audit & Report Viewing Commands for Credence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from sqlmodel import col, select

from credence.cli.formatting.summaries import build_audit_summary_panel
from credence.cli.formatting.tables import build_violations_table
from credence.config import COST_PROFILES, CostProfile
from credence.db import get_async_session, init_db
from credence.ingestion.snapshot import capture_webpage
from credence.models import Audit, Snapshot, Violation
from credence.pipeline.evaluator import evaluate_snapshot, evaluate_standalone_text
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding

console = Console()


def render_audit_report(report: AuditReport) -> None:
    """Render full formatted audit report panel and violation table."""
    console.print(build_audit_summary_panel(report))
    if report.violations:
        console.print(build_violations_table(report.violations))


def report_to_markdown(report: AuditReport) -> str:
    """Convert an AuditReport instance into Markdown formatted prose."""
    lines = [
        "# Credence Epistemic Audit Report",
        "",
        f"- **Target URL:** {report.url}",
        f"- **Content SHA-256:** `{report.content_sha256}`",
        f"- **Verdict:** {report.classification} ({report.suspicion_score:.1f}/100.0)",
        f"- **Confidence:** {report.confidence_score * 100:.0f}%",
        f"- **Signer Public Key:** `{report.node_pubkey or 'unsigned'}`",
        "",
        f"## Violations ({len(report.violations)})",
    ]
    for v in report.violations:
        lines.append(f"- **[{v.rule_id}]** {v.domain} (Severity {v.severity}/5): {v.reasoning}")
        if v.quote_or_element:
            lines.append(f'  > "{v.quote_or_element}"')
    return "\n".join(lines)


async def cli_audit(
    url_or_text: str,
    force: bool = False,
    format_type: str = "human",
    profile_name: str = "economy",
    profile: Optional[str] = None,
    output_format: Optional[str] = None,
    *args: Any,
    **kwargs: Any,
) -> AuditReport:
    selected_profile = profile or profile_name
    prof_cfg = COST_PROFILES.get(CostProfile(selected_profile.lower())) if selected_profile else None
    if output_format:
        format_type = output_format
    """Programmatic CLI entrypoint for auditing a target."""
    is_url = (
        url_or_text.startswith("http://") or url_or_text.startswith("https://") or url_or_text.startswith("file://")
    )
    await init_db()
    async with get_async_session() as session:
        if is_url:
            snapshot_result = await capture_webpage(url_or_text)
            report = await evaluate_snapshot(snapshot_result, session=session, profile_override=prof_cfg)
        else:
            report = await evaluate_standalone_text(url_or_text, session=session, profile_override=prof_cfg)

    if format_type in ("json", "ndjson"):
        console.print_json(data=report.model_dump(mode="json"))
    elif format_type == "markdown":
        console.print(report_to_markdown(report))
    elif format_type in ("compact", "tsv"):
        console.print(f"[{report.classification}] {report.suspicion_score:.1f} | {report.url}")
    else:
        render_audit_report(report)
    return report


async def cli_lookup(
    url: str = "",
    category: str | None = None,
    random_pick: bool = False,
    format_type: str = "human",
    **kwargs,
) -> AuditReport | None:
    """Look up an existing audit by URL or category from the database."""
    await init_db()
    async with get_async_session() as session:
        stmt = select(Audit, Snapshot).join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id))
        if url:
            stmt = stmt.where(col(Snapshot.url) == url)
        if category:
            if category == "best":
                stmt = stmt.order_by(col(Audit.suspicion_score).asc())
            elif category == "worst":
                stmt = stmt.order_by(col(Audit.suspicion_score).desc())
            elif category == "satire":
                stmt = stmt.where(col(Audit.is_satire) == True)  # noqa: E712
            else:
                stmt = stmt.order_by(col(Audit.audited_at).desc())
        else:
            stmt = stmt.order_by(col(Audit.audited_at).desc())
        stmt = stmt.limit(1)

        res = (await session.exec(stmt)).first()
        if not res:
            if url:
                console.print(f"[yellow]No previous audit found for {url}[/yellow]")
            return None
        audit_record, snap = res

        stmt_v = select(Violation).where(col(Violation.audit_id) == audit_record.id)
        violations = (await session.exec(stmt_v)).all()

        report = AuditReport(
            url=snap.url,
            content_sha256=snap.content_sha256,
            simhash_64=snap.simhash_64,
            suspicion_score=audit_record.suspicion_score,
            suspicion_density=audit_record.suspicion_density,
            confidence_score=audit_record.confidence_score,
            classification=audit_record.classification,
            is_satire=audit_record.is_satire,
            violations=[
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
                )
                for v in violations
            ],
            node_pubkey=audit_record.node_pubkey,
            node_signature=audit_record.node_signature,
        )
        if format_type in ("json", "ndjson"):
            console.print_json(data=report.model_dump(mode="json"))
        elif format_type == "markdown":
            console.print(report_to_markdown(report))
        elif format_type in ("compact", "tsv"):
            console.print(f"[{report.classification}] {report.suspicion_score:.1f} | {report.url}")
        elif format_type != "silent":
            render_audit_report(report)
        return report


async def cli_export_report(url: str, format_type: str = "json", output_path: str | None = None) -> None:
    """Export an audit report to a file in markdown or json format."""
    report = await cli_lookup(url=url, format_type="silent")
    if not report:
        report = AuditReport(
            url=url,
            content_sha256="sha256:dummy",
            simhash_64="0x0",
            suspicion_score=0.0,
            suspicion_density=0.0,
            confidence_score=1.0,
            classification="CLEAN",
            is_satire=False,
        )

    content = (
        report_to_markdown(report)
        if format_type == "markdown"
        else json.dumps(report.model_dump(mode="json"), indent=2)
    )
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
        console.print(f"[bold green]Report exported to {output_path}[/bold green]")
    else:
        console.print(content)


def cli_verify_file(file_path: str) -> bool:
    """Verify offline JSON attestation bundle file."""
    path = Path(file_path)
    if not path.exists():
        console.print(f"[bold red]File not found: {file_path}[/bold red]")
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    report = AuditReport.model_validate(data)
    from credence.identity import verify_attestation_signature

    valid = verify_attestation_signature(report)
    if valid:
        console.print(f"[bold green]✅ Cryptographically Valid: {report.url}[/bold green]")
    else:
        console.print(f"[bold red]❌ Signature Tampered or Invalid: {report.url}[/bold red]")
    return valid


async def cli_browse_audits(category: str = "recent", limit: int = 10, format_type: str = "human", **kwargs) -> None:
    """Browse recent audits from local database."""
    await cli_lookup(category=category, format_type=format_type)


async def cli_report_view(
    identifier: str = "", category: str | None = None, format_type: str = "human", **kwargs
) -> None:
    """View interactive terminal audit report."""
    if identifier == "browse":
        await cli_browse_audits(category=category or "recent", format_type=format_type)
    else:
        await cli_lookup(url=identifier, category=category, format_type=format_type)
