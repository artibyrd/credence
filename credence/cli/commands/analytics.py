"""CLI Analytics & Rankings Command Handlers for Credence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from rich import box
from rich.console import Console
from rich.table import Table

from credence.db import get_async_session, init_db
from credence.mesh.badges import generate_attestation_badge_svg, generate_svg_badge
from credence.mesh.topology import compute_network_mesh_health
from credence.subjects.analytics import generate_publisher_svg_badge, get_domain_leaderboard

console = Console()


async def run_rankings_command(
    ranking_type: str = "domains",
    category: str = "best",
    limit: int = 50,
    format_type: str = "human",
    mesh: bool = False,
    *args: Any,
    **kwargs: Any,
) -> int:
    """Display domain epistemic merit leaderboards."""
    await init_db()
    async with get_async_session() as session:
        if mesh:
            mesh_health = await compute_network_mesh_health(session)
            n_nodes = mesh_health.get("active_nodes_count", 1)
            f_tol = mesh_health.get("byzantine_fault_tolerance_f", 0)
            status = "STANDALONE" if n_nodes <= 1 else "BYZANTINE QUORUM ACTIVE"
            console.print(
                f"[bold cyan]🕸️ P2P Mesh Network Reality:[/bold cyan] {n_nodes} Nodes | Byzantine Fault Tolerance f={f_tol} ({status})"
            )

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


async def cli_merit(
    category: str = "best",
    export_svg: Optional[str] = None,
    mesh: bool = False,
    **kwargs: Any,
) -> Any:
    if export_svg:
        svg_content = generate_svg_badge(
            badge_id="root_seed_candidate", node_alias="local-node", score_or_val="VERIFIED"
        )
        target = Path(export_svg)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(svg_content, encoding="utf-8")
        console.print(f"[green]Exported merit badge SVG to {export_svg}[/green]")
    return await run_rankings_command(category=category, mesh=mesh, **kwargs)


async def cli_rankings(*args: Any, **kwargs: Any) -> Any:
    return await run_rankings_command(*args, **kwargs)


def cli_badge_export(
    badge_id: str = "root_seed_candidate",
    output_path: Optional[str] = None,
    node: str = "credence-node",
    score: str = "VERIFIED",
    style: str = "shield",
    theme: str = "dark",
    modality: str = "node",
    format_type: str = "svg",
    *args: Any,
    **kwargs: Any,
) -> None:
    """Export SVG vector badges or Web Component markup across modalities."""
    mod = modality.lower().strip()
    fmt = format_type.lower().strip()

    if mod in ("publisher", "domain", "dci"):
        content = generate_publisher_svg_badge(
            domain=badge_id,
            dci_score=float(score) if score.replace(".", "", 1).isdigit() else 85.0,
            status="CLEAN" if score == "VERIFIED" else score,
            style=style,
            theme=theme,
        )
        component_tag = (
            f'<credence-badge type="publisher" domain="{badge_id}" style="{style}" theme="{theme}"></credence-badge>'
        )
    elif mod in ("attestation", "article"):
        content = generate_attestation_badge_svg(
            content_sha256=badge_id,
            suspicion_score=float(score) if score.replace(".", "", 1).isdigit() else 0.0,
            classification="VERIFIED",
            style=style,
            theme=theme,
            is_modified=False,
        )
        component_tag = (
            f'<credence-badge type="attestation" url="{badge_id}" style="{style}" theme="{theme}"></credence-badge>'
        )
    else:  # "node"
        content = generate_svg_badge(
            badge_id=badge_id,
            node_alias=node,
            score_or_val=score,
            style=style,
            theme=theme,
        )
        component_tag = f'<credence-badge type="node" badge="{badge_id}" node="{node}" style="{style}" theme="{theme}"></credence-badge>'

    output_str = component_tag if fmt in ("component", "html", "component_html") else content

    if output_path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output_str, encoding="utf-8")
        console.print(f"[green]✓ Exported {mod} {fmt} badge to {output_path}[/green]")
    else:
        print(output_str)
