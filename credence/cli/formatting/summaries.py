"""Executive Takeaways and Summary Panels for Credence CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from credence.cli.formatting.badges import get_verdict_badge
from credence.pipeline.schemas import AuditReport


def build_audit_summary_panel(report: AuditReport) -> Panel:
    """Construct a comprehensive executive summary panel for an audit report."""
    verdict_badge = get_verdict_badge(report.classification, report.suspicion_score, report.is_satire)
    summary_text = Text()
    summary_text.append(f"Target URL: {report.url}\n", style="bold cyan")
    summary_text.append(f"Content SHA-256: {report.content_sha256[:16]}...\n", style="dim")
    summary_text.append("Verdict: ", style="bold")
    summary_text.append_text(verdict_badge)
    summary_text.append(f"\nSuspicion Density: {report.suspicion_density:.2f} violations/1k words\n")
    summary_text.append(f"Confidence: {report.confidence_score * 100:.0f}%\n")

    if report.evaluation_model:
        summary_text.append(f"Cognitive Engine: {report.evaluation_model}\n", style="cyan")
    if report.taxonomy_root_hash:
        summary_text.append(f"Taxonomy Root: {report.taxonomy_root_hash[:16]}...\n", style="dim")

    if report.sourcing_ratios:
        r_byline = report.sourcing_ratios.get("r_byline", 0.0)
        r_single = report.sourcing_ratios.get("r_single", 0.0)
        asi = report.sourcing_ratios.get("asi", 100.0)
        summary_text.append(
            f"Sourcing Forensics: Byline {r_byline:.0f}% | Single-Source {r_single:.0f}% | ASI {asi:.0f}/100\n",
            style="magenta",
        )

    if report.is_taxonomy_stale:
        summary_text.append(
            "⚠️  TAXONOMY STALE: Catalogs have expanded since this audit. Use --force to re-evaluate.\n",
            style="bold yellow",
        )

    if report.node_pubkey:
        summary_text.append(f"Signed By Node: {report.node_pubkey[:16]}... (Ed25519 Verified)\n", style="green")

    return Panel(
        summary_text,
        title="[bold blue]Credence Epistemic Audit Report[/bold blue]",
        border_style="blue",
    )


def render_audit_report(report: AuditReport) -> None:
    """Render full formatted audit report to Rich console."""
    console = Console()
    console.print(build_audit_summary_panel(report))


def report_to_markdown(report: AuditReport) -> str:
    """Export audit report to Markdown string."""
    return f"# Credence Epistemic Audit Report\n\n**Target URL**: {report.url}\n**Suspicion Score**: {report.suspicion_score}\n**Classification**: {report.classification}\n"
