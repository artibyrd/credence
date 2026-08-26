"""Root CLI Entrypoint & Argument Dispatcher for Credence.

Governed by Invariant 8: Universal 4-Way Feature Parity.
Architecture: Lean Argument Parser & Dispatcher (<250 LOC).
"""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

from credence.cli.commands.analytics import (
    cli_badge_export,
    cli_leaderboard,
    cli_merit,
    cli_rankings,
)
from credence.cli.commands.audit import (
    cli_audit,
    cli_browse_audits,
    cli_export_report,
    cli_lookup,
    cli_report_view,
    cli_verify_file,
)
from credence.cli.commands.docs_audit import cli_audit_docs
from credence.cli.formatting.summaries import render_audit_report, report_to_markdown
from credence.cli.helpers import (
    cli_boredom,
    cli_db_clean,
    cli_domain,
    cli_expand_roots,
    cli_export_catalog,
    cli_feeds,
    cli_germinate,
    cli_health,
    cli_identity,
    cli_init_org,
    cli_org_init,
    cli_profile,
    cli_quota,
    cli_rank,
    cli_roots,
    cli_seeds,
    cli_stats,
    cli_subjects,
    cli_taxonomy,
)
from credence.pipeline.benchmark import run_benchmark as cli_benchmark

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="credence",
        description="Credence: Autonomous Epistemic Trust & Deception Detection Protocol",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # check (alias: audit)
    p_check = subparsers.add_parser("check", aliases=["audit"], help="Run comprehensive epistemic audit on target URL")
    p_check.add_argument("url", help="Target webpage URL")
    p_check.add_argument("--profile", default="free", choices=["free", "balanced", "ultra"])
    p_check.add_argument("--format", default="human", choices=["human", "json", "compact", "ndjson", "tsv"])

    # evaluate
    p_eval = subparsers.add_parser("evaluate", help="Audit standalone text from argument or stdin")
    p_eval.add_argument("text", nargs="?", help="Text to audit")
    p_eval.add_argument("--profile", default="free", choices=["free", "balanced", "ultra"])
    p_eval.add_argument("--format", default="human", choices=["human", "json"])

    # report (alias: lookup)
    p_rep = subparsers.add_parser("report", aliases=["lookup"], help="Retrieve cached audit report by SHA-256 or URL")
    p_rep.add_argument("identifier", help="SHA-256 hash or exact URL")
    p_rep.add_argument("--format", default="human", choices=["human", "json", "compact", "ndjson", "tsv"])

    # browse
    p_browse = subparsers.add_parser("browse", help="Browse historical audit reports")
    p_browse.add_argument("--limit", type=int, default=20, help="Maximum records to display")
    p_browse.add_argument("--format", default="human", choices=["human", "json", "compact", "ndjson", "tsv"])

    # export (aliases: export-report, export-analytics)
    p_exp = subparsers.add_parser(
        "export", aliases=["export-report", "export-analytics"], help="Export audit report or analytics"
    )
    p_exp.add_argument("identifier", help="SHA-256 hash, URL, or domain")
    p_exp.add_argument("--format", default="human", choices=["human", "json", "csv", "compact"])
    p_exp.add_argument("--output", "-o", help="Output file path (default stdout)")

    # verify
    p_ver = subparsers.add_parser("verify", help="Verify cryptographic Ed25519 signature of an audit report")
    p_ver.add_argument("file", help="Path to signed audit JSON file")

    # identity
    p_ident = subparsers.add_parser("identity", help="Manage cryptographic Node Ed25519 identity")
    p_ident.add_argument("action", default="show", nargs="?", choices=["show", "generate"])
    p_ident.add_argument("--key-path", help="Custom path to node private key")

    # serve (alias: server)
    p_serve = subparsers.add_parser("serve", aliases=["server"], help="Launch FastAPI + FastMCP 2.0 server")
    p_serve.add_argument("--transport", default="sse", choices=["sse", "stdio", "web"], help="Transport mode")
    p_serve.add_argument("--port", type=int, default=8000, help="Server bind port")
    p_serve.add_argument("--host", default="0.0.0.0", help="Server bind host")  # noqa: S104
    p_serve.add_argument("--name", "--alias", dest="name", default=None, help="Authoritative node alias / server name")

    # quota (aliases: cost, profile, governor)
    p_quota = subparsers.add_parser(
        "quota", aliases=["cost", "profile", "governor"], help="Token headroom, cost governance, spend status"
    )
    p_quota.add_argument(
        "action", default="status", nargs="?", choices=["status", "stop", "resume", "optimize", "list"]
    )
    p_quota.add_argument("--reason", help="Reason for cost stop")
    p_quota.add_argument("--apply", action="store_true", help="Apply cost optimization")

    # db
    p_db = subparsers.add_parser("db", aliases=["backup"], help="Database backup, recovery, and migration operations")
    p_db.add_argument(
        "action",
        default="status",
        nargs="?",
        choices=["status", "backup", "restore", "export-pack", "import-pack", "init", "migrate"],
    )
    p_db.add_argument("--source", "-s", help="Source file for restore or import-pack")
    p_db.add_argument("--output", "-o", help="Target output file for backup or export-pack")
    p_db.add_argument("--force", "-f", action="store_true", help="Force overwrite on restore")

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

    # feeds (alias: feed)
    p_feed = subparsers.add_parser("feeds", aliases=["feed"], help="Manage RSS/Atom feed subscriptions")
    p_feed.add_argument(
        "action", default="list", nargs="?", choices=["list", "discover", "inspect", "status", "sentinel"]
    )
    p_feed.add_argument(
        "subaction",
        nargs="?",
        default="list",
        help="Sentinel action (list, enable, disable, set-interval) or target parameter",
    )
    p_feed.add_argument("target", nargs="?", default="", help="Target feed URL, domain, or candidate URL")
    p_feed.add_argument("--interval", type=int, default=300, help="Sentinel polling interval in seconds")

    # seeds
    p_seeds = subparsers.add_parser("seeds", help="Manage and export bootstrap seed nodes")
    p_seeds.add_argument("action", default="list", nargs="?", choices=["list", "generate", "sync"])
    p_seeds.add_argument("--output", "-o", help="Target output file for seeds export")

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

    # badge
    p_badge = subparsers.add_parser("badge", help="Generate or export SVG and Web Component badges")
    p_badge.add_argument("action", default="export", nargs="?", help="Action ('export') or target badge ID")
    p_badge.add_argument("badge_id", default="", nargs="?", help="Badge ID, domain, or article URL")
    p_badge.add_argument("--output", "-o", help="Target output file path (default stdout)")
    p_badge.add_argument(
        "--modality", "-m", default="node", choices=["node", "publisher", "attestation"], help="Attestation modality"
    )
    p_badge.add_argument(
        "--format", "-f", dest="format", default="svg", choices=["svg", "component", "html"], help="Output format"
    )
    p_badge.add_argument("--node", default="credence-node", help="Node alias or label")
    p_badge.add_argument("--score", default="VERIFIED", help="Metric score or value")
    p_badge.add_argument(
        "--style", default="shield", choices=["glass", "pill", "shield", "meta", "compact"], help="Visual style variant"
    )
    p_badge.add_argument("--theme", default="dark", choices=["dark", "midnight", "light"], help="Theme palette")

    # merit (aliases: leaderboard, bounties)
    p_merit = subparsers.add_parser(
        "merit", aliases=["leaderboard", "bounties"], help="Display node epistemic merit and leaderboards"
    )
    p_merit.add_argument("--category", default="best", choices=["best", "worst", "quality", "uptime"])
    p_merit.add_argument("--export-svg", help="Export merit badge SVG to file path")
    p_merit.add_argument("--mesh", action="store_true", help="Display live Byzantine quorum capacity")

    # tui
    subparsers.add_parser("tui", help="Launch interactive Textual Terminal Dashboard")

    # germinate
    p_germ = subparsers.add_parser("germinate", help="Trigger autonomous node germination")
    p_germ.add_argument("--burst", type=int, default=1, help="Number of items to evaluate")
    p_germ.add_argument("--no-mesh", action="store_true", help="Skip peer mesh synchronization")
    p_germ.add_argument("--profile", default="free", choices=["free", "balanced", "ultra"])

    # init-org
    p_org = subparsers.add_parser("init-org", help="Scaffold new sovereign federation organization")
    p_org.add_argument("name", help="Organization name")
    p_org.add_argument("domain", help="Apex domain name")
    p_org.add_argument("--cloud", default="gcp", choices=["gcp", "cloudflare", "multi-cloud"])
    p_org.add_argument("--output", "-o", help="Target output directory")

    # stats
    p_stats = subparsers.add_parser("stats", help="Display local node and P2P mesh telemetry")
    p_stats.add_argument("--mesh", action="store_true", help="Display whole-mesh topology")

    # domain
    p_dom = subparsers.add_parser("domain", help="Inspect domain intelligence, reputation, and quarantine status")
    p_dom.add_argument(
        "action",
        default="status",
        nargs="?",
        choices=["intel", "status", "history", "entropy", "quarantine", "probe", "appeal", "blacklist"],
        help="Domain action",
    )
    p_dom.add_argument("domain", nargs="?", help="Domain FQDN")
    p_dom.add_argument("--window", help="Historical window")
    p_dom.add_argument("--probation", action="store_true", help="Include probation status")

    # benchmark
    subparsers.add_parser("benchmark", help="Run epistemic benchmark evaluation")

    # mesh
    p_mesh = subparsers.add_parser("mesh", help="Manage P2P mesh peering and gossip daemon")
    p_mesh.add_argument(
        "action", default="start", nargs="?", choices=["start", "peers", "health", "discover", "status"]
    )
    p_mesh.add_argument("--port", type=int, default=8765, help="Mesh listen port")
    p_mesh.add_argument("--host", default="0.0.0.0", help="Mesh listen host")  # noqa: S104
    p_mesh.add_argument("--peer", nargs="*", help="Initial peer websocket URL")
    p_mesh.add_argument("--node-id", "--node-name", dest="node_id", default=None, help="Node alias")
    p_mesh.add_argument("--tier", default="dns-srv", help="Discovery tier")
    p_mesh.add_argument("--org-manifest", help="Path to organization manifest")

    # import
    p_imp = subparsers.add_parser("import", aliases=["import-pack"], help="Import truth attestation pack")
    p_imp.add_argument("source", help="Source JSON pack file path")

    # export-pack
    p_exp_pack = subparsers.add_parser("export-pack", aliases=["export-catalog"], help="Export truth attestation pack")
    p_exp_pack.add_argument("--output", "-o", help="Target output pack file path")

    # digest
    p_dig = subparsers.add_parser("digest", help="Generate or display Morning Epistemic Digest")
    p_dig.add_argument("--hours", type=int, default=24, help="Historical window in hours")

    # rfc
    p_rfc = subparsers.add_parser("rfc", help="Manage standards RFC proposals, synthetic benchmarks, and votes")
    p_rfc.add_argument(
        "action",
        default="list",
        nargs="?",
        choices=["list", "show", "validate", "benchmark", "shadow", "hash", "vote"],
        help="RFC action",
    )
    p_rfc.add_argument("target", nargs="?", default="", help="RFC ID or YAML file path")
    p_rfc.add_argument("--tier", choices=["general", "specialist", "niche"], help="Standard tier filter")
    p_rfc.add_argument("--stage", help="RFC lifecycle stage filter")
    p_rfc.add_argument("--fixtures", help="Path to synthetic benchmark fixtures JSON")
    p_rfc.add_argument("--approve", action="store_true", default=True, help="Vote approval")
    p_rfc.add_argument("--reject", action="store_false", dest="approve", help="Vote rejection")

    # subjects
    p_sub = subparsers.add_parser("subjects", help="List registered domain subjects")
    p_sub.add_argument("action", default="list", nargs="?", choices=["list", "tree", "inspect"])

    # bundle (alias: pack)
    p_bun = subparsers.add_parser("bundle", aliases=["pack"], help="Manage air-gapped truth bundles and packs")
    p_bun.add_argument("action", default="export", nargs="?", choices=["export", "import", "verify", "status"])
    p_bun.add_argument("file", nargs="?", help="Target pack file path")
    p_bun.add_argument("--output", "-o", help="Target output bundle path")
    p_bun.add_argument("--since", help="Export attestations since date")
    p_bun.add_argument("--source", "-s", help="Source bundle path")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    from credence.cli.dispatch import dispatch_command

    dispatch_command(args)


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
