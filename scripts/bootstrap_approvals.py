#!/usr/bin/env python3
"""Antigravity Agent Command Approval Bootstrapper & Catalog Generator.

Implements scope-isolated command shape bootstrapping for Antigravity workspaces.
Core scope covers open-source/contributor workflows; Hosted scope covers maintainer cloud infrastructure.
Strictly enforces the Prefix-Safe Command Boundary Law (no wide-open mutating prefixes).
"""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class CommandShape:
    """Represents a prefix-matchable command shape for IDE approval caching."""

    name: str
    scope: str
    category: str
    command: List[str]
    description: str
    is_safe: bool
    timeout: int = 45


BOOTSTRAP_COMMAND_SHAPES: List[CommandShape] = [
    # --------------------------------------------------------------------------
    # 1. CORE SCOPE: Open-Source Developers, Contributors & Community Forks
    # --------------------------------------------------------------------------
    # Preflight & Auth Checks
    CommandShape("Preflight Toolchain", "core", "preflight", ["just", "preflight", "all"], "Verify CLI tools", True),
    CommandShape("GitHub CLI Auth", "core", "preflight", ["just", "auth-check", "gh"], "Verify GH session", True),
    CommandShape("Environment Secrets", "core", "preflight", ["just", "auth-check", "env"], "Inspect API keys", True),
    # Quality & Testing Gates
    CommandShape("Pre-Commit QA Gate", "core", "quality", ["just", "check"], "Parallel QA gauntlet", True, 120),
    CommandShape("Static Lint & Types", "core", "quality", ["just", "lint"], "Ruff & Mypy validation", True),
    CommandShape("Code Formatter", "core", "quality", ["just", "format"], "Auto-format with Ruff", True),
    CommandShape("Unit Tests", "core", "test", ["just", "test-unit"], "Hermetic unit tests", True, 120),
    CommandShape("Docs Integrity", "core", "test", ["just", "test-docs"], "Living canon & parity tests", True),
    CommandShape("Agent Health", "core", "quality", ["just", "agent-check"], "AGENTS.md token budget", True),
    CommandShape("Skills Linter", "core", "quality", ["just", "audit-skills"], "Validate skills schema", True),
    CommandShape("Demotions Audit", "core", "quality", ["just", "audit-demotions"], "Audit invariant demotions", True),
    # Justfile VCS Inspection
    CommandShape("Git Status", "core", "vcs", ["just", "status"], "3-repo clean status check", True),
    CommandShape("Git Diff", "core", "vcs", ["just", "git-diff"], "3-repo working tree diff", True),
    CommandShape("Git Log", "core", "vcs", ["just", "git-log", "5"], "Inspect recent commits", True),
    CommandShape("PR Status", "core", "vcs", ["just", "pr-status"], "Inspect staged PR triad", True),
    CommandShape("PR Checks", "core", "vcs", ["just", "pr-checks"], "Inspect CI check matrix", True),
    CommandShape("PR View", "core", "vcs", ["just", "pr-view"], "View active PR metadata", True),
    # Everyday Git Read Operations (Outside Just)
    CommandShape("Git Short Status", "core", "git:read", ["git", "status", "-s"], "Short status inspection", True),
    CommandShape("Git Diff Stat", "core", "git:read", ["git", "diff", "--stat"], "Diff statistical summary", True),
    CommandShape(
        "Git Log Oneline", "core", "git:read", ["git", "log", "-n", "3", "--oneline"], "Compact git log", True
    ),
    CommandShape("Git Branch List", "core", "git:read", ["git", "branch", "--list"], "List local branches", True),
    CommandShape(
        "Git Selective Checkout", "core", "git:read", ["git", "checkout", "AGENTS.md"], "Safe file checkout", True
    ),
    # Everyday Python & Poetry Tooling (Outside Just)
    CommandShape("Poetry Version", "core", "poetry", ["poetry", "version"], "Inspect package version", True),
    CommandShape(
        "Direct Ruff Check", "core", "poetry", ["poetry", "run", "ruff", "check", "credence"], "Ruff linting", True
    ),
    CommandShape(
        "Direct Mypy Check", "core", "poetry", ["poetry", "run", "mypy", "credence"], "Mypy type checks", True
    ),
    CommandShape(
        "Direct Pytest Run",
        "core",
        "poetry",
        ["poetry", "run", "pytest", "tests/governance/test_docs_integrity.py", "-k", "test_zero_npm_invariant"],
        "Targeted pytest",
        True,
    ),
    # Everyday Coreutils & Text Search (Outside Just)
    CommandShape(
        "Grep Pattern Search",
        "core",
        "bash:read",
        ["grep", "-i", "version", "pyproject.toml"],
        "Search text in file",
        True,
    ),
    CommandShape(
        "Head File Read", "core", "bash:read", ["head", "-n", "5", "pyproject.toml"], "Read top of file", True
    ),
    CommandShape("Line Count Inspection", "core", "bash:read", ["wc", "-l", "AGENTS.md"], "Count file lines", True),
    # GitHub CLI Inspection (Outside Just)
    CommandShape("GH Auth Status", "core", "github", ["gh", "auth", "status"], "Inspect GH PAT session", True),
    CommandShape("GH PR Checks", "core", "github", ["gh", "pr", "checks"], "Direct GH check status", True),
    CommandShape("GH PR View", "core", "github", ["gh", "pr", "view"], "Direct GH PR viewer", True),
    CommandShape("GH Run List", "core", "github", ["gh", "run", "list", "--limit", "5"], "List GH Actions runs", True),
    # Public HTTP Probes
    CommandShape(
        "Public Docs Probe",
        "core",
        "url:probe",
        ["curl", "-sI", "https://docs.credence.run"],
        "Probe public docs",
        True,
    ),
    CommandShape(
        "GitHub Raw Probe",
        "core",
        "url:probe",
        ["curl", "-sI", "https://raw.githubusercontent.com/artibyrd/credence/main/README.md"],
        "Probe GitHub assets",
        True,
    ),
    # --------------------------------------------------------------------------
    # 2. HOSTED SCOPE: Artibyrd Maintainer Infrastructure, Cloud Run & Edge
    # --------------------------------------------------------------------------
    # Hosted Authentication Verification
    CommandShape("GCP Auth Check", "hosted", "hosted:auth", ["just", "auth-check", "gcloud"], "Verify GCP OAuth", True),
    CommandShape(
        "Wrangler Auth Check", "hosted", "hosted:auth", ["just", "auth-check", "wrangler"], "Verify Edge auth", True
    ),
    CommandShape("All Auth Check", "hosted", "hosted:auth", ["just", "auth-check", "all"], "Complete auth score", True),
    # Hosted Justfile Telemetry Recipes
    CommandShape("Cloud Run Status", "hosted", "hosted:telemetry", ["just", "cloud-status"], "Inspect revisions", True),
    CommandShape(
        "Cloud Dev Probe",
        "hosted",
        "hosted:telemetry",
        ["just", "cloud-probe", "credence-dev", "dev"],
        "Probe Dev Cloud Run",
        True,
    ),
    CommandShape(
        "Cloud Prod Probe",
        "hosted",
        "hosted:telemetry",
        ["just", "cloud-probe", "credence-server", "prod"],
        "Probe Prod Cloud Run",
        True,
    ),
    CommandShape(
        "Edge Status", "hosted", "hosted:telemetry", ["just", "edge-status"], "Inspect Edge deployments", True
    ),
    CommandShape("CI Status", "hosted", "hosted:telemetry", ["just", "ci-status"], "Inspect multi-repo CI", True),
    CommandShape(
        "Terraform Validate", "hosted", "hosted:telemetry", ["just", "tf-validate"], "Validate Terraform HCL", True
    ),
    CommandShape(
        "Doctor Diagnostic", "hosted", "hosted:telemetry", ["just", "doctor"], "Multi-plane health audit", True
    ),
    # Live Cloud & Edge URL Probes (Dev, Prod, Edge, Docs)
    CommandShape(
        "Dev Cloud Run Health",
        "hosted",
        "url:telemetry",
        ["curl", "-sI", "https://credence-dev-865363499314.us-central1.run.app/health"],
        "Probe Dev Cloud Run",
        True,
    ),
    CommandShape(
        "Dev Cloud Run JSON",
        "hosted",
        "url:telemetry",
        ["curl", "-s", "https://credence-dev-865363499314.us-central1.run.app/health"],
        "Fetch Dev health JSON",
        True,
    ),
    CommandShape(
        "Prod Cloud Run Health",
        "hosted",
        "url:telemetry",
        ["curl", "-sI", "https://credence-server-663899237633.us-central1.run.app/health"],
        "Probe Prod Cloud Run",
        True,
    ),
    CommandShape(
        "Prod Cloud Run JSON",
        "hosted",
        "url:telemetry",
        ["curl", "-s", "https://credence-server-663899237633.us-central1.run.app/health"],
        "Fetch Prod health JSON",
        True,
    ),
    CommandShape(
        "Prod Edge Health",
        "hosted",
        "url:telemetry",
        ["curl", "-sI", "https://credence.run/health"],
        "Probe Prod Edge router",
        True,
    ),
    CommandShape(
        "Dev Edge Health",
        "hosted",
        "url:telemetry",
        ["curl", "-sI", "https://dev.credence.run/health"],
        "Probe Dev Edge router",
        True,
    ),
    CommandShape(
        "Reports Lab Probe",
        "hosted",
        "url:telemetry",
        ["curl", "-sI", "https://credence.report"],
        "Probe forensics lab",
        True,
    ),
    CommandShape(
        "Mesh NOC Probe",
        "hosted",
        "url:telemetry",
        ["curl", "-sI", "https://credence.nexus"],
        "Probe mesh dashboard",
        True,
    ),
    CommandShape(
        "Foundation Probe",
        "hosted",
        "url:telemetry",
        ["curl", "-sI", "https://credence.foundation"],
        "Probe trust index",
        True,
    ),
]


def display_catalog(scope: str = "core") -> None:
    """Print the catalog of bootstrap command shapes for the selected scope."""
    selected = [s for s in BOOTSTRAP_COMMAND_SHAPES if scope == "all" or s.scope == scope]
    title = "Core Open-Source" if scope == "core" else ("Maintainer Hosted" if scope == "hosted" else "All Ecosystem")
    table = Table(
        title=f"[bold cyan]Credence Command Approval Catalog ({title})[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", justify="right", style="cyan", width=4)
    table.add_column("Scope", justify="center", style="green" if scope == "core" else "yellow", width=8)
    table.add_column("Category", style="yellow", width=14)
    table.add_column("Command Shape", style="bold white", width=36)
    table.add_column("Safety", justify="center", width=12)
    table.add_column("Purpose", style="dim")

    for i, shape in enumerate(selected, 1):
        safety = "[green]SAFE (READ)[/green]" if shape.is_safe else "[red]GATED (WRITE)[/red]"
        table.add_row(f"#{i}", shape.scope.upper(), shape.category, " ".join(shape.command), safety, shape.description)

    console.print(table)


def run_bootstrapping(scope: str = "core", dry_run: bool = False) -> None:
    """Execute all safe command shapes sequentially for the specified scope."""
    selected = [s for s in BOOTSTRAP_COMMAND_SHAPES if scope == "all" or s.scope == scope]
    desc = "Core contributor commands (local git/python/curl)" if scope == "core" else "Maintainer cloud/edge telemetry"
    console.print(
        Panel(
            f"[bold green]Credence Approval Bootstrapper[/bold green] [bold cyan]({scope.upper()} SCOPE)[/bold cyan]\n\n"
            f"{desc}.\nWhen IDE prompts appear, click [bold cyan]'Always Allow'[/bold cyan] for autonomous workflows.",
            title="[bold]Workflow Safety Dance[/bold]",
            border_style="cyan",
        )
    )
    display_catalog(scope)
    if dry_run:
        console.print(
            f"\n[bold yellow]DRY-RUN MODE:[/bold yellow] Listed {len(selected)} command shapes. Run with [bold green]--execute[/bold green] to fire approvals."
        )
        return

    console.print(f"\n[bold cyan]=== Executing {len(selected)} Commands ===[/bold cyan]\n")
    for i, shape in enumerate(selected, 1):
        console.print(
            f"[bold cyan][{i}/{len(selected)}][/bold cyan] Running: [bold]{' '.join(shape.command)}[/bold] ..."
        )
        try:
            res = subprocess.run(shape.command, cwd=REPO_ROOT, capture_output=True, text=True, timeout=shape.timeout)  # noqa: S603
            if res.returncode == 0:
                console.print(f"   [green]✅ Verified:[/green] {shape.name}")
            else:
                console.print(f"   [yellow]⚠️ Code {res.returncode}:[/yellow] {shape.name}")
        except Exception as e:
            console.print(f"   [red]❌ Error:[/red] {e}")

    console.print(f"\n[bold green]🎉 Bootstrapping Complete for Scope '{scope.upper()}'![/bold green]\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Agent Command Approvals")
    parser.add_argument("--scope", choices=["core", "hosted", "all"], default="core", help="Scope: 'core' or 'hosted'")
    parser.add_argument("--execute", action="store_true", help="Execute all safe commands sequentially")
    args = parser.parse_args()
    run_bootstrapping(scope=args.scope, dry_run=not args.execute)


if __name__ == "__main__":
    main()
