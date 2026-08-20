"""Rich Table Formatters for Credence CLI."""

from __future__ import annotations

from typing import List

from rich import box
from rich.table import Table

from credence.cli.formatting.badges import get_severity_badge
from credence.pipeline.schemas import SpecialistViolationFinding


def build_violations_table(violations: List[SpecialistViolationFinding]) -> Table:
    """Construct a Rich table presenting itemized grounded violations."""
    table = Table(
        title="[bold red]Itemized Epistemic Violations[/bold red]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Rule ID", style="bold white", width=12)
    table.add_column("Domain", style="magenta", width=20)
    table.add_column("Severity", justify="center", width=16)
    table.add_column("Grounded Excerpt", style="italic yellow", min_width=30)
    table.add_column("Reasoning", style="dim white", min_width=30)

    for v in violations:
        table.add_row(
            v.rule_id,
            v.domain,
            get_severity_badge(v.severity),
            v.quote_or_element[:120] + ("..." if len(v.quote_or_element) > 120 else ""),
            v.reasoning,
        )
    return table
