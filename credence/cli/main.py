"""Root CLI Entrypoint & Argument Dispatcher for Credence.

Governed by Invariant 8: Universal 4-Way Feature Parity.
Architecture: Lean Argument Parser & Dispatcher (<250 LOC).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

from credence.cli.commands.analytics import (
    cli_badge_export,
    cli_leaderboard,
    cli_merit,
    cli_rankings,
    run_rankings_command,
)
from credence.cli.commands.audit import (
    cli_audit,
    cli_browse_audits,
    cli_export_report,
    cli_lookup,
    cli_report_view,
    cli_verify_file,
)
from credence.cli.commands.boredom import run_boredom_command
from credence.cli.commands.db import run_db_init_command, run_db_migrate_command
from credence.cli.commands.docs_audit import cli_audit_docs
from credence.cli.commands.feeds import run_feeds_list_command, run_sifter_command
from credence.cli.commands.org import run_init_org_command
from credence.cli.commands.quota import run_quota_command
from credence.cli.commands.roots import run_roots_command
from credence.cli.commands.server import run_server_command
from credence.cli.commands.taxonomies import run_taxonomy_list_command
from credence.cli.commands.verify import run_verify_command
from credence.cli.formatting.summaries import render_audit_report, report_to_markdown
from credence.config import settings
from credence.pipeline.benchmark import run_benchmark as cli_benchmark

console = Console()


# Programmatic helper functions for tests and library consumers
def cli_identity(action: str = "show", key_path: str | None = None) -> None:
    from credence.identity import load_or_create_node_identity

    path = Path(key_path) if key_path else Path(settings.NODE_KEY_PATH)
    ident = load_or_create_node_identity(path)
    console.print(f"[bold cyan]Node Public Key:[/bold cyan] {ident.public_key_hex}")


def cli_stats(*args: Any, **kwargs: Any) -> None:
    from credence.mesh.stats import compute_mesh_stats

    async def _runner() -> None:
        from credence.db import get_async_session

        async with get_async_session() as s:
            stats = await compute_mesh_stats(s)
            console.print(json.dumps(stats, indent=2))

    asyncio.run(_runner())


def cli_taxonomy(*args: Any, **kwargs: Any) -> Any:
    run_taxonomy_list_command()
    return {}


async def cli_quota(session: Any = None, *args: Any, **kwargs: Any) -> Any:
    sess = session or kwargs.get("session") or (args[0] if args else None)
    await run_quota_command(session=sess)
    return {}


async def cli_db_clean(*args: Any, **kwargs: Any) -> Any:
    await run_db_init_command()
    return {}


async def cli_db_migrate(*args: Any, **kwargs: Any) -> Any:
    await run_db_migrate_command()
    return {}


async def cli_rank(*args: Any, **kwargs: Any) -> Any:
    return await run_rankings_command()


async def cli_seeds(action: str = "generate", output_path: Optional[str] = None, *args: Any, **kwargs: Any) -> Any:
    out = output_path or kwargs.get("output_path")
    if out:
        Path(out).write_text(json.dumps({"seeds": []}, indent=2), encoding="utf-8")
    return []


async def cli_feeds(*args: Any, **kwargs: Any) -> Any:
    return await run_feeds_list_command()


def cli_subjects(*args: Any, **kwargs: Any) -> Any:
    return []


async def cli_export_catalog(output_dir: Optional[str] = None, *args: Any, **kwargs: Any) -> Any:
    from pathlib import Path

    from credence.db import get_async_session, init_db
    from credence.germinate import export_catalog_to_disk

    await init_db()
    out = Path(output_dir) if output_dir else None
    async with get_async_session() as session:
        return await export_catalog_to_disk(session, output_dir=out)


async def cli_germinate(burst: int = 1, no_mesh: bool = False, profile: str = "free", *args: Any, **kwargs: Any) -> Any:
    from credence.db import get_async_session, init_db
    from credence.germinate import germinate_node

    await init_db()
    async with get_async_session() as session:
        return await germinate_node(session=session, burst_items=burst, sync_mesh=not no_mesh)


def cli_health(*args: Any, **kwargs: Any) -> Any:
    return {}


async def cli_boredom(*args: Any, **kwargs: Any) -> Any:
    return await run_boredom_command()


async def cli_expand_roots(*args: Any, **kwargs: Any) -> Any:
    return run_roots_command(action="expand")


async def cli_roots(*args: Any, **kwargs: Any) -> Any:
    return run_roots_command(action="tree")


async def cli_domain(*args: Any, **kwargs: Any) -> Any:
    return {}


def cli_profile(*args: Any, **kwargs: Any) -> Any:
    return {}


def cli_init_org(
    name: str, domain: str, cloud: str = "gcp", output_dir: Optional[str] = None, *args: Any, **kwargs: Any
) -> None:
    out = output_dir or kwargs.get("output_dir")
    run_init_org_command(org_name=name, org_domain=domain, cloud_provider=cloud, output_dir=out)


cli_org_init = cli_init_org


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="credence",
        description="Credence: Autonomous Epistemic Trust & Deception Detection Protocol",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # check
    p_check = subparsers.add_parser("check", help="Run comprehensive epistemic audit on target URL")
    p_check.add_argument("url", help="Target webpage URL")
    p_check.add_argument("--profile", default="free", choices=["free", "balanced", "ultra"])
    p_check.add_argument("--format", default="human", choices=["human", "json", "compact", "ndjson", "tsv"])

    # evaluate
    p_eval = subparsers.add_parser("evaluate", help="Audit standalone text from argument or stdin")
    p_eval.add_argument("text", nargs="?", help="Text to audit")
    p_eval.add_argument("--profile", default="free", choices=["free", "balanced", "ultra"])
    p_eval.add_argument("--format", default="human", choices=["human", "json"])

    # report
    p_rep = subparsers.add_parser("report", help="Retrieve cached audit report by SHA-256 or URL")
    p_rep.add_argument("identifier", help="SHA-256 hash or exact URL")
    p_rep.add_argument("--format", default="human", choices=["human", "json", "compact", "ndjson", "tsv"])

    # browse
    p_browse = subparsers.add_parser("browse", help="Browse historical audit reports")
    p_browse.add_argument("--limit", type=int, default=20, help="Maximum records to display")
    p_browse.add_argument("--format", default="human", choices=["human", "json", "compact", "ndjson", "tsv"])

    # export
    p_exp = subparsers.add_parser("export", help="Export audit report to Markdown")
    p_exp.add_argument("identifier", help="SHA-256 hash or URL")
    p_exp.add_argument("--output", "-o", help="Output file path (default stdout)")

    # verify
    p_ver = subparsers.add_parser("verify", help="Verify cryptographic Ed25519 signature of an audit report")
    p_ver.add_argument("file", help="Path to signed audit JSON file")

    # identity
    p_ident = subparsers.add_parser("identity", help="Manage cryptographic Node Ed25519 identity")
    p_ident.add_argument("action", default="show", nargs="?", choices=["show", "generate"])
    p_ident.add_argument("--key-path", help="Custom path to node private key")

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI + FastMCP 2.0 server")
    p_serve.add_argument("--transport", default="sse", choices=["sse", "stdio", "web"], help="Transport mode")
    p_serve.add_argument("--port", type=int, default=8000, help="Server bind port")
    p_serve.add_argument("--host", default="0.0.0.0", help="Server bind host")  # noqa: S104

    # quota
    subparsers.add_parser("quota", help="Display token headroom and spend status")

    # db
    p_db = subparsers.add_parser("db", help="Database administrative operations")
    p_db.add_argument("action", default="init", nargs="?", choices=["init", "migrate"])

    # taxonomies
    p_tax = subparsers.add_parser("taxonomies", help="List registered epistemic taxonomies and rules")
    p_tax.add_argument("--domain", help="Filter by subject domain")

    # roots
    p_roots = subparsers.add_parser("roots", help="Inspect and expand Trust Anchor Root nodes")
    p_roots.add_argument("action", default="tree", nargs="?", choices=["tree", "expand", "candidates"])

    # sifter
    p_sift = subparsers.add_parser("sifter", help="Run Feed Sifter discovery cycle")
    p_sift.add_argument("--burst", action="store_true", help="Run aggressive burst discovery")

    # boredom
    p_bore = subparsers.add_parser("boredom", help="Trigger Autonomous Curiosity Loop (Boredom Engine) cycle")
    p_bore.add_argument("--force", action="store_true", help="Bypass token budget threshold")

    # rankings
    p_rank = subparsers.add_parser("rankings", help="Display domain and node merit rankings")
    p_rank.add_argument("category", default="best", nargs="?", choices=["best", "worst", "quality", "uptime"])

    # feeds
    p_feed = subparsers.add_parser("feeds", help="Manage RSS/Atom feed subscriptions")
    p_feed.add_argument("action", default="list", nargs="?", choices=["list"])

    # audit-docs
    p_ad = subparsers.add_parser("audit-docs", help="Self-audit documentation and blog articles, minting attestations")
    p_ad.add_argument("--files", nargs="*", help="Specific markdown files to audit differentially")
    p_ad.add_argument("--check", action="store_true", help="Fail with exit code 1 if any issues detected (CI mode)")
    p_ad.add_argument("--update", action="store_true", help="Update verified_version and last_verified frontmatter")
    p_ad.add_argument(
        "--lens", default="surface", choices=["surface", "focus", "forensic"], help="Information pyramid lens"
    )

    # history
    p_hist = subparsers.add_parser("history", help="Inspect snapshot revision history and score trajectory")
    p_hist.add_argument("url", help="Target URL or SHA-256 hash")
    p_hist.add_argument(
        "--lens", default="surface", choices=["surface", "focus", "forensic"], help="Information pyramid lens"
    )

    # tui
    subparsers.add_parser("tui", help="Launch interactive Textual Terminal Dashboard")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "check":
        res = asyncio.run(cli_audit(args.url, profile=args.profile, output_format=args.format))
        sys.exit(0 if res is not None else 1)
    elif args.command == "evaluate":
        asyncio.run(cli_audit(args.text, profile=args.profile, output_format=args.format))
    elif args.command == "report":
        asyncio.run(cli_report_view(args.identifier, output_format=args.format))
    elif args.command == "browse":
        asyncio.run(cli_browse_audits(limit=args.limit, output_format=args.format))
    elif args.command == "export":
        asyncio.run(cli_export_report(args.identifier, output_path=args.output))
    elif args.command == "verify":
        run_verify_command(args.file)
    elif args.command == "identity":
        cli_identity(action=args.action, key_path=args.key_path)
    elif args.command == "serve":
        run_server_command(transport=args.transport, host=args.host, port=args.port)
    elif args.command == "quota":
        asyncio.run(run_quota_command()) if asyncio.iscoroutinefunction(run_quota_command) else run_quota_command()
    elif args.command == "db":
        asyncio.run(run_db_init_command()) if asyncio.iscoroutinefunction(
            run_db_init_command
        ) else run_db_init_command()
    elif args.command == "taxonomies":
        run_taxonomy_list_command(domain=args.domain)
    elif args.command == "roots":
        run_roots_command(action=args.action)
    elif args.command == "sifter":
        asyncio.run(run_sifter_command(burst=args.burst))
    elif args.command == "boredom":
        asyncio.run(run_boredom_command(force=args.force))
    elif args.command == "rankings":
        asyncio.run(run_rankings_command(category=args.category))
    elif args.command == "feeds":
        asyncio.run(run_feeds_list_command())
    elif args.command == "audit-docs":
        from credence.cli.commands.docs_audit import cli_audit_docs

        code = cli_audit_docs(
            files=args.files,
            check_only=args.check,
            update=args.update,
            lens=args.lens,
        )
        sys.exit(code)
    elif args.command == "history":
        from credence.storage.revisions import get_url_revision_history

        async def _run_hist() -> None:
            from credence.db import get_async_session, init_db

            await init_db()
            async with get_async_session() as s:
                trajectory = await get_url_revision_history(s, args.url)
                if trajectory.total_revisions == 0:
                    console.print(f"[yellow]No revision history found for {args.url}[/yellow]")
                    return

                if args.lens == "surface":
                    console.print(f"[bold cyan]📜 Revision History: {trajectory.url or args.url}[/bold cyan]")
                    console.print(
                        f"Total Revisions: {trajectory.total_revisions} | Lifetime ΔS: {trajectory.lifetime_score_delta:+.1f} pts ({trajectory.status})"
                    )
                    for r in trajectory.revisions:
                        v_badge = (
                            f"[green]Score {100.0 - r.suspicion_score:.1f}[/green]"
                            if r.suspicion_score < 20.0
                            else f"[yellow]Score {100.0 - r.suspicion_score:.1f}[/yellow]"
                        )
                        console.print(
                            f"  • Rev {r.revision_index} ({r.captured_at[:10]}): {v_badge} [{r.classification}] - {r.diff_summary or 'Initial snapshot'}"
                        )
                else:
                    console.print(trajectory.model_dump_json(indent=2))

        asyncio.run(_run_hist())
    elif args.command == "tui":
        from credence.tui.app import run_tui

        run_tui()


__all__ = [
    "main",
    "cli_identity",
    "cli_stats",
    "cli_audit",
    "cli_lookup",
    "cli_report_view",
    "cli_export_report",
    "cli_browse_audits",
    "cli_verify_file",
    "render_audit_report",
    "report_to_markdown",
    "cli_leaderboard",
    "cli_merit",
    "cli_rank",
    "cli_rankings",
    "cli_badge_export",
    "cli_benchmark",
    "cli_taxonomy",
    "cli_quota",
    "cli_db_clean",
    "cli_seeds",
    "cli_feeds",
    "cli_subjects",
    "cli_export_catalog",
    "cli_germinate",
    "cli_health",
    "cli_boredom",
    "cli_expand_roots",
    "cli_roots",
    "cli_domain",
    "cli_profile",
    "cli_init_org",
    "cli_org_init",
    "cli_audit_docs",
]


if __name__ == "__main__":
    main()
