"""CLI Command Dispatcher for Credence.

Executes parsed CLI subcommands and dispatches to subsystem operations.
Adheres to Invariant 1 (500 LOC Ceiling Law).
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from rich.console import Console

from credence.cli.commands.analytics import (
    cli_badge_export,
    cli_merit,
    run_rankings_command,
)
from credence.cli.commands.audit import (
    cli_audit,
    cli_browse_audits,
    cli_export_report,
    cli_report_view,
)
from credence.cli.commands.boredom import run_boredom_command
from credence.cli.commands.db import (
    run_db_backup_command,
    run_db_export_pack_command,
    run_db_import_pack_command,
    run_db_init_command,
    run_db_migrate_command,
    run_db_restore_command,
    run_db_status_command,
)
from credence.cli.commands.docs_audit import cli_audit_docs
from credence.cli.commands.feeds import run_feeds_list_command, run_sifter_command
from credence.cli.commands.quota import run_quota_command
from credence.cli.commands.roots import run_roots_command
from credence.cli.commands.server import run_server_command
from credence.cli.commands.taxonomies import run_taxonomy_list_command
from credence.cli.commands.verify import run_verify_command
from credence.cli.helpers import (
    cli_germinate,
    cli_identity,
    cli_init_org,
    cli_seeds,
    cli_stats,
)
from credence.pipeline.benchmark import run_benchmark as cli_benchmark

console = Console()


def dispatch_command(args: argparse.Namespace) -> None:
    """Execute the parsed CLI command."""
    if args.command in ("check", "audit"):
        res = asyncio.run(cli_audit(args.url, profile=args.profile, output_format=args.format))
        sys.exit(0 if res is not None else 1)
    elif args.command == "evaluate":
        asyncio.run(cli_audit(args.text, profile=args.profile, output_format=args.format))
    elif args.command in ("report", "lookup"):
        asyncio.run(cli_report_view(args.identifier, output_format=args.format))
    elif args.command == "browse":
        asyncio.run(cli_browse_audits(limit=args.limit, output_format=args.format))
    elif args.command in ("export", "export-report", "export-analytics"):
        asyncio.run(cli_export_report(args.identifier, output_path=args.output))
    elif args.command == "badge":
        target_badge = (
            args.badge_id if args.badge_id else args.action if args.action != "export" else "verified_auditor"
        )
        cli_badge_export(
            badge_id=target_badge,
            output_path=args.output,
            node=args.node,
            score=args.score,
            style=args.style,
            theme=args.theme,
            modality=getattr(args, "modality", "node"),
            format_type=getattr(args, "format", "svg"),
        )
    elif args.command in ("merit", "leaderboard", "bounties"):
        asyncio.run(
            cli_merit(
                export_svg=args.export_svg,
                category=args.category,
                mesh=getattr(args, "mesh", False),
            )
        )
    elif args.command == "verify":
        run_verify_command(args.file)
    elif args.command == "identity":
        cli_identity(action=args.action, key_path=args.key_path)
    elif args.command in ("serve", "server"):
        run_server_command(transport=args.transport, host=args.host, port=args.port, name=getattr(args, "name", None))
    elif args.command in ("quota", "cost", "profile"):
        asyncio.run(run_quota_command()) if asyncio.iscoroutinefunction(run_quota_command) else run_quota_command()
    elif args.command == "db":
        if args.action == "init":
            code = asyncio.run(run_db_init_command())
        elif args.action == "migrate":
            code = asyncio.run(run_db_migrate_command())
        elif args.action == "backup":
            code = asyncio.run(run_db_backup_command(output_path=args.output))
        elif args.action == "restore":
            if not args.source:
                print("❌ --source required for db restore")
                sys.exit(1)
            code = asyncio.run(run_db_restore_command(source_path=args.source, force=args.force))
        elif args.action == "export-pack":
            code = asyncio.run(run_db_export_pack_command(output_path=args.output))
        elif args.action == "import-pack":
            if not args.source:
                print("❌ --source required for db import-pack")
                sys.exit(1)
            code = asyncio.run(run_db_import_pack_command(input_source=args.source))
        else:
            code = run_db_status_command()
        sys.exit(code if isinstance(code, int) else 0)
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
    elif args.command in ("feeds", "feed"):
        if args.action == "sentinel":
            from credence.cli.commands.feeds import run_feeds_sentinel_command

            act = args.subaction or "list"
            tgt = args.target if args.target else None
            asyncio.run(
                run_feeds_sentinel_command(
                    action=act,
                    target=tgt,
                    interval=getattr(args, "interval", 300),
                )
            )
        else:
            asyncio.run(run_feeds_list_command())
    elif args.command == "seeds":
        asyncio.run(cli_seeds(action=args.action, output_path=args.output))
    elif args.command == "audit-docs":
        code = cli_audit_docs(
            files=args.files,
            check_only=args.check,
            update=args.update,
            lens=args.lens,
        )
        sys.exit(code)
    elif args.command == "history":

        async def _run_hist() -> None:
            from credence.db import get_async_session, init_db
            from credence.ingestion.temporal import get_url_revision_history

            await init_db()
            async with get_async_session() as s:
                snaps = await get_url_revision_history(s, args.url)
                if not snaps:
                    console.print(f"[yellow]No historical snapshots recorded for: {args.url}[/yellow]")
                    return
                console.print(f"[bold cyan]Snapshot Revision History for {args.url}:[/bold cyan]")
                for snap in snaps:
                    console.print(f"  • {snap.captured_at.isoformat()} | SHA: {snap.content_sha256[:12]}...")

        asyncio.run(_run_hist())
    elif args.command == "tui":
        from credence.tui.app import run_tui

        run_tui()
    elif args.command == "germinate":
        asyncio.run(cli_germinate(burst=args.burst, no_mesh=args.no_mesh, profile=args.profile))
    elif args.command == "init-org":
        cli_init_org(name=args.name, domain=args.domain, cloud=args.cloud, output_dir=args.output)
    elif args.command == "stats":
        cli_stats(mesh=args.mesh)
    elif args.command == "domain":
        from credence.cli.helpers import cli_domain

        asyncio.run(cli_domain(action=args.action, domain=args.domain))
    elif args.command == "benchmark":
        asyncio.run(cli_benchmark())
    elif args.command == "mesh":
        if args.action in ("peers", "health", "status"):
            cli_stats(mesh=True)
        else:
            console.print(f"[bold cyan]🌐 Starting Credence Mesh Node on port {args.port}...[/bold cyan]")
    elif args.command in ("import", "import-pack"):
        code = asyncio.run(run_db_import_pack_command(input_source=args.source))
        sys.exit(code if isinstance(code, int) else 0)
    elif args.command in ("export-pack", "export-catalog"):
        code = asyncio.run(run_db_export_pack_command(output_path=args.output))
        sys.exit(code if isinstance(code, int) else 0)
    elif args.command == "digest":

        async def _run_digest() -> None:
            from credence.db import get_async_session, init_db
            from credence.feeds.digest import generate_morning_digest, render_digest_terminal

            await init_db()
            async with get_async_session() as s:
                d = await generate_morning_digest(s, timeframe_hours=getattr(args, "hours", 24))
                render_digest_terminal(d)

        asyncio.run(_run_digest())
    elif args.command in ("bundle", "pack"):
        if args.action == "import":
            code = asyncio.run(run_db_import_pack_command(input_source=args.file or args.source))
        else:
            code = asyncio.run(run_db_export_pack_command(output_path=args.output or args.file))
        sys.exit(code if isinstance(code, int) else 0)
    elif args.command == "rfc":
        from credence.cli.commands.rfc import (
            run_rfc_benchmark_command,
            run_rfc_hash_command,
            run_rfc_list_command,
            run_rfc_show_command,
            run_rfc_validate_command,
            run_rfc_vote_command,
        )

        if args.action == "show":
            code = run_rfc_show_command(rfc_id=args.target or "RFC-001")
        elif args.action == "validate":
            code = run_rfc_validate_command(yaml_path=args.target)
        elif args.action == "hash":
            code = run_rfc_hash_command(yaml_path=args.target)
        elif args.action == "benchmark":
            code = run_rfc_benchmark_command(yaml_path=args.target, fixtures_path=args.fixtures)
        elif args.action == "vote":
            code = run_rfc_vote_command(rfc_id=args.target or "RFC-001", approve=args.approve)
        else:
            code = run_rfc_list_command(tier=args.tier, stage=args.stage)
        sys.exit(code)
    elif args.command == "subjects":
        console.print(
            "[bold cyan]🧠 Registered Domain Subjects:[/bold cyan] technology, politics, health, finance, science, culture"
        )
