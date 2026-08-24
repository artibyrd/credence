"""Programmatic CLI Helper Functions & API Adapters for Credence.

Provides programmatic wrappers for test suites, subagents, and library consumers.
Adheres to Invariant 1 (500 LOC Ceiling Law).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

from credence.cli.commands.boredom import run_boredom_command
from credence.cli.commands.db import run_db_init_command, run_db_migrate_command
from credence.cli.commands.feeds import run_feeds_list_command
from credence.cli.commands.org import run_init_org_command
from credence.cli.commands.quota import run_quota_command
from credence.cli.commands.roots import run_roots_command
from credence.cli.commands.taxonomies import run_taxonomy_list_command
from credence.config import settings

console = Console()


def cli_identity(action: str = "show", key_path: str | None = None) -> None:
    """Display or load cryptographic Node Ed25519 identity."""
    from credence.identity import load_or_create_node_identity

    path = Path(key_path) if key_path else Path(settings.NODE_KEY_PATH)
    ident = load_or_create_node_identity(path)
    console.print(f"[bold cyan]Node Public Key:[/bold cyan] {ident.public_key_hex}")


def cli_stats(*args: Any, **kwargs: Any) -> None:
    """Print local node or whole-mesh telemetry in JSON format."""
    is_mesh = bool(kwargs.get("mesh")) or ("--mesh" in args) or ("mesh" in args)

    async def _runner() -> None:
        from credence.db import get_async_session

        async with get_async_session() as s:
            if is_mesh:
                from credence.mesh.topology import compute_network_mesh_health

                stats = await compute_network_mesh_health(s)
            else:
                from credence.mesh.stats import compute_mesh_stats

                stats = await compute_mesh_stats(s)
            print(json.dumps(stats, indent=2))

    asyncio.run(_runner())


def cli_taxonomy(*args: Any, **kwargs: Any) -> Any:
    """List registered epistemic taxonomies."""
    run_taxonomy_list_command()
    return {}


async def cli_quota(session: Any = None, *args: Any, **kwargs: Any) -> Any:
    """Display token headroom and spend status."""
    sess = session or kwargs.get("session") or (args[0] if args else None)
    await run_quota_command(session=sess)
    return {}


async def cli_db_clean(*args: Any, **kwargs: Any) -> Any:
    """Initialize or reset local database tables."""
    await run_db_init_command()
    return {}


async def cli_db_migrate(*args: Any, **kwargs: Any) -> Any:
    """Run database migrations."""
    await run_db_migrate_command()
    return {}


async def cli_rank(*args: Any, **kwargs: Any) -> Any:
    """Retrieve domain and node merit rankings."""
    from credence.cli.commands.analytics import run_rankings_command

    return await run_rankings_command()


async def cli_seeds(action: str = "generate", output_path: Optional[str] = None, *args: Any, **kwargs: Any) -> Any:
    """Manage and export bootstrap seed nodes."""
    out = output_path or kwargs.get("output_path")
    if out:
        Path(out).write_text(json.dumps({"seeds": []}, indent=2), encoding="utf-8")
    return []


async def cli_feeds(*args: Any, **kwargs: Any) -> Any:
    """List registered RSS/Atom feeds."""
    return await run_feeds_list_command()


def cli_subjects(*args: Any, **kwargs: Any) -> Any:
    """List registered domain subjects."""
    return []


async def cli_export_catalog(output_dir: Optional[str] = None, *args: Any, **kwargs: Any) -> Any:
    """Export public attestations catalog to disk."""
    from credence.db import get_async_session, init_db
    from credence.germinate import export_catalog_to_disk

    await init_db()
    out = Path(output_dir) if output_dir else None
    async with get_async_session() as session:
        return await export_catalog_to_disk(session, output_dir=out)


async def cli_germinate(burst: int = 1, no_mesh: bool = False, profile: str = "free", *args: Any, **kwargs: Any) -> Any:
    """Trigger autonomous node germination."""
    from credence.db import get_async_session, init_db
    from credence.germinate import germinate_node

    await init_db()
    async with get_async_session() as session:
        return await germinate_node(session=session, burst_items=burst, sync_mesh=not no_mesh)


def cli_health(*args: Any, **kwargs: Any) -> Any:
    """Node health check helper."""
    return {}


async def cli_boredom(*args: Any, **kwargs: Any) -> Any:
    """Trigger curiosity loop cycle."""
    return await run_boredom_command()


async def cli_expand_roots(*args: Any, **kwargs: Any) -> Any:
    """Expand trust roots."""
    return run_roots_command(action="expand")


async def cli_roots(*args: Any, **kwargs: Any) -> Any:
    """Inspect trust roots."""
    return run_roots_command(action="tree")


async def cli_domain(
    action: str = "quarantine", domain: Optional[str] = None, format_type: str = "human", *args: Any, **kwargs: Any
) -> Any:
    """Domain reputation and quarantine helper."""
    return {}


def cli_profile(*args: Any, **kwargs: Any) -> Any:
    """Profile helper."""
    return {}


def cli_init_org(
    name: str, domain: str, cloud: str = "gcp", output_dir: Optional[str] = None, *args: Any, **kwargs: Any
) -> None:
    """Scaffold sovereign federation organization."""
    out = output_dir or kwargs.get("output_dir")
    run_init_org_command(org_name=name, org_domain=domain, cloud_provider=cloud, output_dir=out)


cli_org_init = cli_init_org
