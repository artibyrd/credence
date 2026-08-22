"""CLI Analytics & Rankings Command Handlers for Credence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from rich import box
from rich.console import Console
from rich.table import Table

from credence.db import get_async_session
from credence.mesh.badges import generate_svg_badge
from credence.subjects.analytics import get_domain_leaderboard

console = Console()


async def run_rankings_command(
    ranking_type: str = "domains",
    category: str = "best",
    limit: int = 50,
    format_type: str = "human",
    *args: Any,
    **kwargs: Any,
) -> int:
    """Display domain epistemic merit leaderboards."""
    async with get_async_session() as session:
        domains = await get_domain_leaderboard(session)

    if limit and limit > 0:
        domains = domains[:limit]

    table = Table(title=f"Epistemic Domain Rankings ({ranking_type})", box=box.ROUNDED)
    table.add_column("Domain", style="bold cyan")
    table.add_column("Score", justify="center")
    table.add_column("Band", style="magenta")
    table.add_column("Total Audits", justify="right")

    for d in domains:
        table.add_row(d.domain, f"{d.dci_score:.1f}", d.trust_band, str(d.total_audits))

    console.print(table)
    return 0


async def cli_leaderboard(*args: Any, **kwargs: Any) -> Any:
    return await run_rankings_command(*args, **kwargs)


async def cli_merit(export_svg: Optional[str] = None, *args: Any, **kwargs: Any) -> Any:
    if export_svg:
        svg_content = generate_svg_badge(
            badge_id="root_seed_candidate", node_alias="local-node", score_or_val="VERIFIED"
        )
        target = Path(export_svg)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(svg_content, encoding="utf-8")
        console.print(f"[green]Exported merit badge SVG to {export_svg}[/green]")
    return await run_rankings_command(*args, **kwargs)


async def cli_rankings(*args: Any, **kwargs: Any) -> Any:
    return await run_rankings_command(*args, **kwargs)


def cli_badge_export(
    badge_id: str = "root_seed_candidate",
    output_path: Optional[str] = None,
    node: str = "credence-node",
    score: str = "VERIFIED",
    style: str = "pill",
    theme: str = "dark",
    *args: Any,
    **kwargs: Any,
) -> None:
    svg_content = generate_svg_badge(
        badge_id=badge_id,
        node_alias=node,
        score_or_val=score,
        style=style,
        theme=theme,
    )
    if output_path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(svg_content, encoding="utf-8")
        console.print(f"[green]✓ Exported {style} badge SVG to {output_path}[/green]")
    else:
        print(svg_content)
