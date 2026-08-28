"""CLI Model Comparison Matrix Command Handler for Credence."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from credence.db import get_async_session, init_db
from credence.storage.revisions import get_model_comparison_matrix

console = Console()


async def run_model_compare_command(
    url: str,
    json_output: bool = False,
) -> int:
    """Compare multiple model evaluation passes (e.g. Heuristics vs Gemini vs Claude) for a URL."""
    await init_db()

    async with get_async_session() as session:
        matrix = await get_model_comparison_matrix(session, url)

    if not matrix.passes:
        console.print(f"[yellow]No evaluation history found for: {url}[/yellow]")
        return 1

    if json_output:
        console.print(matrix.model_dump_json(indent=2))
        return 0

    console.print("\n[bold cyan]⚡ Multi-Model Evaluation Comparison Matrix[/bold cyan]")
    console.print(f"[dim]Target: {url}[/dim]\n")

    # Table of Evaluation Passes
    pass_table = Table(title="Evaluation Passes (Provenance & Scores)")
    pass_table.add_column("Engine / Model", style="cyan", no_wrap=True)
    pass_table.add_column("Audited At", style="dim")
    pass_table.add_column("Score", justify="right")
    pass_table.add_column("Confidence", justify="right")
    pass_table.add_column("Classification", style="bold")
    pass_table.add_column("Violations", justify="center")
    pass_table.add_column("Quota Preserved", justify="center")

    for p in matrix.passes:
        score_color = "green" if p.suspicion_score < 25 else "yellow" if p.suspicion_score < 60 else "red"
        pass_table.add_row(
            p.evaluation_method or "unknown",
            p.captured_at[:19] if p.captured_at else "N/A",
            f"[{score_color}]{p.suspicion_score:.1f}[/{score_color}]",
            f"{p.confidence_score:.0%}",
            f"[{score_color}]{p.classification}[/{score_color}]",
            str(len(p.violations)),
            "✓" if p.quota_preserved else "-",
        )

    console.print(pass_table)

    if matrix.pairwise_diffs:
        console.print("\n[bold]Pairwise Model Score & Violation Discrepancies:[/bold]")
        diff_table = Table()
        diff_table.add_column("Baseline Model", style="blue")
        diff_table.add_column("Comparison Model", style="magenta")
        diff_table.add_column("Score Delta", justify="right")
        diff_table.add_column("Violations Delta")
        diff_table.add_column("Discrepancy Notes")

        for d in matrix.pairwise_diffs:
            delta_str = f"{d.score_delta:+.1f} pts"
            d_color = "green" if abs(d.score_delta) < 10 else "yellow" if abs(d.score_delta) < 25 else "red"
            diff_table.add_row(
                d.baseline_model,
                d.comparison_model,
                f"[{d_color}]{delta_str}[/{d_color}]",
                f"+{len(d.violations_added)} / -{len(d.violations_removed)}",
                d.discrepancy_summary,
            )

        console.print(diff_table)

    if matrix.heuristic_baseline_used:
        console.print(
            Panel.fit(
                "[bold yellow]⚠️ Grounding Advisory:[/bold yellow] Heuristic fallback evaluation is bounded at 25% max confidence.\n"
                "Multi-agent LLM evaluations provide deep epistemic nuance with 100% taxonomy coverage.",
                border_style="yellow",
            )
        )

    return 0
