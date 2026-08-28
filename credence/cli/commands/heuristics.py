"""CLI Heuristics Benchmark & Calibration Corpus Management Handlers."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from credence.pipeline.heuristics.benchmark import (
    add_sample_to_corpus,
    run_empirical_heuristic_calibration,
)

console = Console()


async def run_heuristics_benchmark_command(
    corpus: str | None = None,
    json_output: bool = False,
) -> int:
    """Run empirical calibration benchmark over the N=100+ static anchor corpus."""
    corpus_path = Path(corpus) if corpus else None

    console.print("[bold cyan]🔬 Running Empirical Heuristic Calibration Benchmark...[/bold cyan]\n")
    result = run_empirical_heuristic_calibration(corpus_path=corpus_path)

    if json_output:
        console.print(result.model_dump_json(indent=2))
        return 0

    # Summary Panel
    m = result.metrics
    cal_status = (
        "[bold green]PASS (Calibrated)[/bold green]" if m.is_calibrated else "[bold red]FAIL (Uncalibrated)[/bold red]"
    )
    console.print(
        Panel.fit(
            f"[bold]Engine Version:[/bold] {result.engine_version} | [bold]Corpus Version:[/bold] {result.corpus_version}\n"
            f"[bold]Total Scraped Articles:[/bold] {result.total_articles}\n"
            f"[bold]Precision:[/bold] {m.precision:.2%} | [bold]Recall:[/bold] {m.recall:.2%}\n"
            f"[bold]False Positive Rate (FPR):[/bold] {m.false_positive_rate:.2%} | [bold]F1-Score:[/bold] {m.f1_score:.2%}\n"
            f"[bold]Recommended Confidence Cap:[/bold] {m.recommended_confidence_ceiling:.0%}\n"
            f"[bold]Active Hard Confidence Cap:[/bold] {m.active_confidence_ceiling:.0%}\n"
            f"[bold]Calibration Status:[/bold] {cal_status}",
            title="Statistical Calibration Report",
            border_style="cyan",
        )
    )

    # Archetype Breakdown Table
    table = Table(title="Newsroom Archetype Performance Matrix")
    table.add_column("Archetype", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("True Positives (TP)", justify="right", style="green")
    table.add_column("False Positives (FP)", justify="right", style="red")
    table.add_column("False Negatives (FN)", justify="right", style="yellow")
    table.add_column("True Negatives (TN)", justify="right", style="dim")

    for arch, stats in result.archetype_breakdown.items():
        table.add_row(
            arch,
            str(stats["total"]),
            str(stats["tp"]),
            str(stats["fp"]),
            str(stats["fn"]),
            str(stats["tn"]),
        )

    console.print(table)
    return 0 if m.is_calibrated else 1


async def run_heuristics_add_sample_command(
    url: str,
    json_output: bool = False,
) -> int:
    """Defensively fetch, validate against Red Team attacks, and append a live sample to calibration corpus."""
    console.print(f"[cyan]Defensively capturing and validating sample: {url}...[/cyan]")

    try:
        entry = await add_sample_to_corpus(url)
        if json_output:
            console.print(json.dumps(entry, indent=2))
        else:
            console.print("[bold green]✓ Sample Successfully Validated and Added to Anchor Corpus![/bold green]")
            console.print(f"  ID: {entry.get('id')}")
            console.print(f"  Title: {entry.get('title')}")
            console.print(f"  Domain: {entry.get('domain')}")
            console.print(f"  Word Count: {entry.get('word_count')}")
            console.print(f"  Detected Rules: {', '.join(entry.get('expected_violations', [])) or 'None (Clean)'}")
        return 0
    except Exception as e:
        console.print(f"[bold red]Security or Validation Error adding sample:[/bold red] {e}")
        return 1
