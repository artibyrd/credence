#!/usr/bin/env python3
"""Agent Command Approval Bootstrapping Engine for Credence.

Walks through standard, prefix-matchable command shapes used by the agent during
development. Executing each safe command once allows the human developer to grant
"Always Allow" in a fresh workspace, enabling autonomous agent workflows.

Supports two discrete scopes:
1. 'core': Open-source developer & fork tooling (local tests, quality gates, vcs, git, curl).
2. 'hosted': Artibyrd maintainer cloud telemetry, multi-cloud probes & live URLs.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import List, NamedTuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

REPO_ROOT = Path(__file__).resolve().parents[1]


class CommandShape(NamedTuple):
    name: str
    scope: str
    category: str
    command: List[str]
    description: str
    is_safe: bool
    timeout: int = 45


BOOTSTRAP_COMMAND_SHAPES: List[CommandShape] = [
    # --------------------------------------------------------------------------
    # 1. CORE SCOPE: Open-Source Developers, Contributors & Forks (Local Only)
    # --------------------------------------------------------------------------
    # Preflight & Authentication Checks
    CommandShape(
        name="Preflight Toolchain",
        scope="core",
        category="core: preflight",
        command=["just", "preflight", "all"],
        description="Verify developer CLI dependencies across all planes",
        is_safe=True,
    ),
    CommandShape(
        name="GitHub CLI Auth Verification",
        scope="core",
        category="core: preflight",
        command=["just", "auth-check", "gh"],
        description="Verify active GitHub authentication session",
        is_safe=True,
    ),
    CommandShape(
        name="Environment Secrets Verification",
        scope="core",
        category="core: preflight",
        command=["just", "auth-check", "env"],
        description="Inspect environment API keys and secrets",
        is_safe=True,
    ),
    # Quality & Testing Gates
    CommandShape(
        name="Pre-Commit QA Gauntlet",
        scope="core",
        category="core: quality",
        command=["just", "check"],
        description="Parallel multi-plane verification (<3s)",
        is_safe=True,
        timeout=120,
    ),
    CommandShape(
        name="Static Linting & Format Check",
        scope="core",
        category="core: quality",
        command=["just", "lint"],
        description="Ruff linter and Mypy type validation",
        is_safe=True,
    ),
    CommandShape(
        name="Hermetic Unit Tests",
        scope="core",
        category="core: test",
        command=["just", "test-unit"],
        description="Fast in-memory unit tests (<35s, $0.00 tokens)",
        is_safe=True,
        timeout=120,
    ),
    CommandShape(
        name="Documentation Integrity",
        scope="core",
        category="core: test",
        command=["just", "test-docs"],
        description="Frontmatter, 7-manifest parity & living canon tests",
        is_safe=True,
    ),
    CommandShape(
        name="Declarative Agent Health",
        scope="core",
        category="core: quality",
        command=["just", "agent-check"],
        description="AGENTS.md, skills schema and token budget check",
        is_safe=True,
    ),
    CommandShape(
        name="Skills Linter",
        scope="core",
        category="core: quality",
        command=["just", "audit-skills"],
        description="Validate .agents/skills schema and YAML frontmatter",
        is_safe=True,
    ),
    CommandShape(
        name="Demotions Audit",
        scope="core",
        category="core: quality",
        command=["just", "audit-demotions"],
        description="Audit invariant demotion candidates and token savings",
        is_safe=True,
    ),
    # Justfile VCS Inspection
    CommandShape(
        name="Ecosystem Git Status",
        scope="core",
        category="vcs: safe",
        command=["just", "status"],
        description="3-repo clean status check (credence, docs, agent)",
        is_safe=True,
    ),
    CommandShape(
        name="Ecosystem Git Diff",
        scope="core",
        category="vcs: safe",
        command=["just", "git-diff"],
        description="View uncommitted diffs across all ecosystem repos",
        is_safe=True,
    ),
    CommandShape(
        name="Ecosystem Git Log",
        scope="core",
        category="vcs: safe",
        command=["just", "git-log", "5"],
        description="Compact git log across ecosystem repos",
        is_safe=True,
    ),
    CommandShape(
        name="Pull Request Triad Status",
        scope="core",
        category="vcs: safe",
        command=["just", "pr-status"],
        description="Inspect active staged PRs across the ecosystem triad",
        is_safe=True,
    ),
    CommandShape(
        name="Pull Request Checks View",
        scope="core",
        category="vcs: safe",
        command=["just", "pr-checks"],
        description="Inspect CI/CD status on open pull requests",
        is_safe=True,
    ),
    CommandShape(
        name="Pull Request Markdown View",
        scope="core",
        category="vcs: safe",
        command=["just", "pr-view"],
        description="View details and diff of open pull requests",
        is_safe=True,
    ),
    # Direct Everyday Git Read Operations (Outside Just)
    CommandShape(
        name="Direct Git Status",
        scope="core",
        category="git: read",
        command=["git", "status", "-s"],
        description="Everyday git status inspection",
        is_safe=True,
    ),
    CommandShape(
        name="Direct Git Diff",
        scope="core",
        category="git: read",
        command=["git", "diff", "--stat"],
        description="Everyday git diff summary inspection",
        is_safe=True,
    ),
    CommandShape(
        name="Direct Git Log",
        scope="core",
        category="git: read",
        command=["git", "log", "-n", "3", "--oneline"],
        description="Everyday git commit history inspection",
        is_safe=True,
    ),
    CommandShape(
        name="Direct Git Branch List",
        scope="core",
        category="git: read",
        command=["git", "branch", "--list"],
        description="Everyday git local branch listing",
        is_safe=True,
    ),
    # Direct Everyday Python & Poetry Tooling (Outside Just)
    CommandShape(
        name="Direct Poetry Version Check",
        scope="core",
        category="python: read",
        command=["poetry", "version"],
        description="Inspect current project version",
        is_safe=True,
    ),
    CommandShape(
        name="Direct Ruff Linter Check",
        scope="core",
        category="python: read",
        command=["poetry", "run", "ruff", "check", "credence"],
        description="Direct linter invocation on credence package",
        is_safe=True,
    ),
    CommandShape(
        name="Direct Mypy Type Analysis",
        scope="core",
        category="python: read",
        command=["poetry", "run", "mypy", "credence"],
        description="Direct type checker invocation on codebase",
        is_safe=True,
    ),
    CommandShape(
        name="Direct Hermetic Unit Test Pass",
        scope="core",
        category="python: read",
        command=["poetry", "run", "pytest", "tests/governance/test_docs_integrity.py", "-k", "test_zero_npm_invariant"],
        description="Direct targeted pytest execution",
        is_safe=True,
    ),
    # Direct GitHub CLI Inspection (Outside Just)
    CommandShape(
        name="GitHub CLI Auth Status",
        scope="core",
        category="github: read",
        command=["gh", "auth", "status"],
        description="Inspect GitHub authentication state",
        is_safe=True,
    ),
    CommandShape(
        name="GitHub CLI PR Checks",
        scope="core",
        category="github: read",
        command=["gh", "pr", "checks"],
        description="Direct GitHub CLI check run inspection",
        is_safe=True,
    ),
    CommandShape(
        name="GitHub CLI PR View",
        scope="core",
        category="github: read",
        command=["gh", "pr", "view"],
        description="Direct GitHub CLI pull request viewer",
        is_safe=True,
    ),
    CommandShape(
        name="GitHub CLI Run List",
        scope="core",
        category="github: read",
        command=["gh", "run", "list", "--limit", "5"],
        description="Direct GitHub Actions workflow run listing",
        is_safe=True,
    ),
    # Public & Local HTTP Probes
    CommandShape(
        name="Live Public Docs Probe",
        scope="core",
        category="url: read",
        command=["curl", "-sI", "https://docs.credence.run"],
        description="Direct HTTP probe on live public docs portal",
        is_safe=True,
    ),
    CommandShape(
        name="Live GitHub Raw Endpoint Probe",
        scope="core",
        category="url: read",
        command=["curl", "-sI", "https://raw.githubusercontent.com/artibyrd/credence/main/README.md"],
        description="Direct HTTP probe on public GitHub repository assets",
        is_safe=True,
    ),
    # --------------------------------------------------------------------------
    # 2. HOSTED SCOPE: Artibyrd Maintainer Infrastructure, Cloud Run & Edge
    # --------------------------------------------------------------------------
    # Preflight Cloud Authentication Verification
    CommandShape(
        name="Google Cloud Auth Verification",
        scope="hosted",
        category="hosted: safe",
        command=["just", "auth-check", "gcloud"],
        description="Verify active GCP OAuth/WIF credentials",
        is_safe=True,
    ),
    CommandShape(
        name="Cloudflare Edge Auth Verification",
        scope="hosted",
        category="hosted: safe",
        command=["just", "auth-check", "wrangler"],
        description="Verify active Cloudflare API session",
        is_safe=True,
    ),
    CommandShape(
        name="All Ecosystem Auth Verification",
        scope="hosted",
        category="hosted: safe",
        command=["just", "auth-check", "all"],
        description="Verify complete ecosystem authentication freshness",
        is_safe=True,
    ),
    # Justfile Cloud Telemetry
    CommandShape(
        name="Cloud Run Compute Status",
        scope="hosted",
        category="hosted: safe",
        command=["just", "cloud-status"],
        description="Inspect Cloud Run revisions and traffic splits",
        is_safe=True,
    ),
    CommandShape(
        name="Cloud Run Dev Probe",
        scope="hosted",
        category="hosted: safe",
        command=["just", "cloud-probe", "credence-dev", "dev"],
        description="Probe live Dev HTTP and SSE endpoints with latency metrics",
        is_safe=True,
    ),
    CommandShape(
        name="Cloud Run Prod Probe",
        scope="hosted",
        category="hosted: safe",
        command=["just", "cloud-probe", "credence-server", "prod"],
        description="Probe live Prod HTTP and SSE endpoints with latency metrics",
        is_safe=True,
    ),
    CommandShape(
        name="Cloudflare Edge Status",
        scope="hosted",
        category="hosted: safe",
        command=["just", "edge-status"],
        description="Inspect Cloudflare worker routing and pages deployments",
        is_safe=True,
    ),
    CommandShape(
        name="GitHub Actions CI Status",
        scope="hosted",
        category="hosted: safe",
        command=["just", "ci-status"],
        description="List recent workflow runs across ecosystem repos",
        is_safe=True,
    ),
    CommandShape(
        name="Terraform Configuration Validation",
        scope="hosted",
        category="hosted: safe",
        command=["just", "tf-validate"],
        description="Terraform formatting and HCL syntax validation",
        is_safe=True,
    ),
    CommandShape(
        name="Multi-Plane Diagnostic Health",
        scope="hosted",
        category="hosted: safe",
        command=["just", "doctor"],
        description="Complete multi-plane diagnostic health check",
        is_safe=True,
    ),
    # Live Cloud & Edge URL Probes (Dev, Prod, Edge, Docs)
    CommandShape(
        name="Live Dev Health Endpoint Probe",
        scope="hosted",
        category="url: telemetry",
        command=["curl", "-sI", "https://credence-dev-865363499314.us-central1.run.app/health"],
        description="Direct HTTP probe on Cloud Run Dev container health",
        is_safe=True,
    ),
    CommandShape(
        name="Live Dev Health JSON Probe",
        scope="hosted",
        category="url: telemetry",
        command=["curl", "-s", "https://credence-dev-865363499314.us-central1.run.app/health"],
        description="Direct JSON payload probe on Cloud Run Dev container",
        is_safe=True,
    ),
    CommandShape(
        name="Live Prod Health Endpoint Probe",
        scope="hosted",
        category="url: telemetry",
        command=["curl", "-sI", "https://credence-server-663899237633.us-central1.run.app/health"],
        description="Direct HTTP probe on Cloud Run Production container health",
        is_safe=True,
    ),
    CommandShape(
        name="Live Prod Health JSON Probe",
        scope="hosted",
        category="url: telemetry",
        command=["curl", "-s", "https://credence-server-663899237633.us-central1.run.app/health"],
        description="Direct JSON payload probe on Cloud Run Production container",
        is_safe=True,
    ),
    CommandShape(
        name="Live Edge Domain Probe",
        scope="hosted",
        category="url: telemetry",
        command=["curl", "-sI", "https://credence.run/health"],
        description="Direct HTTP probe on Cloudflare Edge proxy and router",
        is_safe=True,
    ),
    CommandShape(
        name="Live Dev Edge Preview Domain Probe",
        scope="hosted",
        category="url: telemetry",
        command=["curl", "-sI", "https://dev.credence.run/health"],
        description="Direct HTTP probe on Cloudflare Dev preview router",
        is_safe=True,
    ),
    CommandShape(
        name="Live Docs Portal Probe",
        scope="hosted",
        category="url: telemetry",
        command=["curl", "-sI", "https://docs.credence.run"],
        description="Direct HTTP probe on zero-build documentation portal",
        is_safe=True,
    ),
    CommandShape(
        name="Live Reports Workstation Probe",
        scope="hosted",
        category="url: telemetry",
        command=["curl", "-sI", "https://credence.report"],
        description="Direct HTTP probe on investigative reports workstation",
        is_safe=True,
    ),
    CommandShape(
        name="Live Nexus Workstation Probe",
        scope="hosted",
        category="url: telemetry",
        command=["curl", "-sI", "https://credence.nexus"],
        description="Direct HTTP probe on node telemetry & admin deck",
        is_safe=True,
    ),
    CommandShape(
        name="Live Foundation Workstation Probe",
        scope="hosted",
        category="url: telemetry",
        command=["curl", "-sI", "https://credence.foundation"],
        description="Direct HTTP probe on public trust index & bylaws",
        is_safe=True,
    ),
]


def display_catalog(scope: str = "core") -> None:
    """Print the catalog of bootstrap command shapes for the selected scope."""
    selected_shapes = [s for s in BOOTSTRAP_COMMAND_SHAPES if scope == "all" or s.scope == scope]
    scope_title = (
        "Open-Source & Contributor Core"
        if scope == "core"
        else ("Maintainer Hosted Operations" if scope == "hosted" else "All Ecosystem")
    )

    table = Table(
        title=f"[bold cyan]Credence Autonomous Command Approval Catalog ({scope_title})[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", justify="right", style="cyan", width=4)
    table.add_column("Scope", justify="center", style="green" if scope == "core" else "yellow", width=8)
    table.add_column("Category", style="yellow", width=16)
    table.add_column("Command Shape", style="bold white", width=38)
    table.add_column("Safety Domain", justify="center", width=12)
    table.add_column("Purpose", style="dim")

    for i, shape in enumerate(selected_shapes, 1):
        safety_badge = "[green]SAFE (READ)[/green]" if shape.is_safe else "[red]GATED (WRITE)[/red]"
        cmd_str = " ".join(shape.command)
        table.add_row(f"#{i}", shape.scope.upper(), shape.category, cmd_str, safety_badge, shape.description)

    console.print(table)


def run_bootstrapping(scope: str = "core", dry_run: bool = False) -> None:
    """Execute all safe command shapes sequentially for the specified scope."""
    selected_shapes = [s for s in BOOTSTRAP_COMMAND_SHAPES if scope == "all" or s.scope == scope]
    scope_desc = (
        "Open-source core developer commands (fork-safe, local git/python/curl)"
        if scope == "core"
        else "Artibyrd maintainer cloud telemetry, deployment, and live URL probes"
    )

    console.print(
        Panel(
            f"[bold green]Credence Agent Approval Bootstrapping Runner[/bold green] [bold cyan]({scope.upper()} SCOPE)[/bold cyan]\n\n"
            f"{scope_desc}.\n"
            "When the Antigravity IDE approval dialog appears for each command,\n"
            "select [bold cyan]'Always Allow'[/bold cyan] to authorize autonomous workflows.",
            title="[bold]Workflow Safety Dance[/bold]",
            border_style="cyan",
        )
    )

    display_catalog(scope)

    if dry_run:
        console.print(
            f"\n[bold yellow]DRY-RUN MODE:[/bold yellow] Listed {len(selected_shapes)} command shapes. Run with [bold green]--execute[/bold green] to run through approvals."
        )
        return

    console.print(
        f"\n[bold cyan]=== Initiating Sequential Execution Pass ({len(selected_shapes)} Commands) ===[/bold cyan]\n"
    )

    for i, shape in enumerate(selected_shapes, 1):
        cmd_str = " ".join(shape.command)
        console.print(f"[bold cyan][{i}/{len(selected_shapes)}][/bold cyan] Running: [bold]{cmd_str}[/bold] ...")
        try:
            res = subprocess.run(  # noqa: S603
                shape.command,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=shape.timeout,
            )
            if res.returncode == 0:
                console.print(f"   [green]✅ Verified:[/green] {shape.name}")
            else:
                console.print(f"   [yellow]⚠️ Exited with code {res.returncode}:[/yellow] {shape.name}")
        except Exception as e:
            console.print(f"   [red]❌ Execution error:[/red] {e}")

    console.print(
        f"\n[bold green]🎉 Approval Bootstrapping Complete for Scope '{scope.upper()}'![/bold green]\n"
        "[dim]Primary safe command shapes have been executed and are ready for autonomous development.[/dim]\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Agent Command Approvals")
    parser.add_argument(
        "--scope",
        choices=["core", "hosted", "all"],
        default="core",
        help="Command scope to bootstrap: 'core' (open-source/fork-safe) or 'hosted' (maintainer infrastructure).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute all safe commands sequentially for IDE approval prompting.",
    )
    args = parser.parse_args()
    run_bootstrapping(scope=args.scope, dry_run=not args.execute)


if __name__ == "__main__":
    main()
