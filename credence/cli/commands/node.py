"""CLI Node Role & Evaluator Sweep Command Handlers."""

from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel

from credence.config import ExhaustionStrategy, NodeRole, settings
from credence.db import get_async_session, init_db
from credence.pipeline.rescore import rescore_heuristic_audits

console = Console()


async def run_node_role_command(
    role: str | None = None,
    strategy: str | None = None,
    auto_rescore: bool | None = None,
    json_output: bool = False,
) -> int:
    """View or configure node operational role (evaluator, serving, hybrid) and exhaustion strategy."""
    if role:
        try:
            settings.CREDENCE_NODE_ROLE = NodeRole(role.lower())
        except ValueError:
            console.print(f"[bold red]Invalid role '{role}'. Choose from: {[r.value for r in NodeRole]}[/bold red]")
            return 1

    if strategy:
        try:
            settings.CREDENCE_EXHAUSTION_STRATEGY = ExhaustionStrategy(strategy.lower())
        except ValueError:
            console.print(
                f"[bold red]Invalid strategy '{strategy}'. Choose from: {[e.value for e in ExhaustionStrategy]}[/bold red]"
            )
            return 1

    if auto_rescore is not None:
        settings.CREDENCE_AUTO_RESCORE_HEURISTICS = auto_rescore

    data = {
        "node_role": settings.CREDENCE_NODE_ROLE.value,
        "exhaustion_strategy": settings.CREDENCE_EXHAUSTION_STRATEGY.value,
        "auto_rescore_heuristics": settings.CREDENCE_AUTO_RESCORE_HEURISTICS,
        "heuristic_engine_version": settings.HEURISTIC_ENGINE_VERSION,
        "heuristic_max_confidence_ceiling": settings.HEURISTIC_MAX_CONFIDENCE_CEILING,
    }

    if json_output:
        console.print(json.dumps(data, indent=2))
        return 0

    console.print(
        Panel.fit(
            f"[bold]Node Role:[/bold] [cyan]{settings.CREDENCE_NODE_ROLE.value.upper()}[/cyan]\n"
            f"[bold]Exhaustion Strategy:[/bold] [magenta]{settings.CREDENCE_EXHAUSTION_STRATEGY.value.upper()}[/magenta]\n"
            f"[bold]Auto Re-Score Heuristics:[/bold] {'[green]Enabled[/green]' if settings.CREDENCE_AUTO_RESCORE_HEURISTICS else '[dim]Disabled[/dim]'}\n"
            f"[bold]Heuristic Engine Version:[/bold] {settings.HEURISTIC_ENGINE_VERSION}\n"
            f"[bold]Confidence Ceiling:[/bold] {settings.HEURISTIC_MAX_CONFIDENCE_CEILING:.0%}",
            title="Node Operational Configuration",
            border_style="cyan",
        )
    )
    return 0


async def run_node_rescore_command(
    limit: int = 20,
    force: bool = False,
    json_output: bool = False,
) -> int:
    """Manually trigger an immediate re-scoring sweep of heuristic fallback audits."""
    console.print(f"[cyan]Initiating evaluator re-scoring sweep (Limit: {limit})...[/cyan]")
    await init_db()

    async with get_async_session() as session:
        rescored = await rescore_heuristic_audits(session, limit=limit, force=force)

    if json_output:
        console.print(json.dumps([r.model_dump(mode="json") for r in rescored], indent=2))
        return 0

    if not rescored:
        console.print(
            "[yellow]No heuristic fallback audits required re-scoring or governor headroom throttled.[/yellow]"
        )
        return 0

    console.print(
        f"[bold green]✓ Successfully re-scored {len(rescored)} audit(s) with LLM specialist pipeline:[/bold green]"
    )
    for r in rescored:
        console.print(
            f"  - [bold]{r.url}[/bold]: {r.suspicion_score:.1f} pts ({r.classification}) via {r.evaluation_method} ({len(r.violations)} violations)"
        )
    return 0
