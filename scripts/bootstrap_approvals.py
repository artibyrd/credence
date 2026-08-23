#!/usr/bin/env python3
"""Agent Command Approval Bootstrapping Engine for Credence.

Walks through standard, prefix-matchable command shapes used by the agent during
development. Executing each safe command once allows the human developer to grant
"Always Allow" in a fresh workspace, enabling autonomous agent workflows.
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
    category: str
    command: List[str]
    description: str
    is_safe: bool


BOOTSTRAP_COMMAND_SHAPES: List[CommandShape] = [
    # 1. Preflight & Quality Gates
    CommandShape(
        name="Preflight Toolchain",
        category="core: preflight",
        command=["just", "preflight", "all"],
        description="Verify developer CLI dependencies across all planes",
        is_safe=True,
    ),
    CommandShape(
        name="Pre-Commit QA Gauntlet",
        category="core: quality",
        command=["just", "check"],
        description="Parallel multi-plane verification (<3s)",
        is_safe=True,
    ),
    CommandShape(
        name="Static Linting & Format Check",
        category="core: quality",
        command=["just", "lint"],
        description="Ruff linter and Mypy type validation",
        is_safe=True,
    ),
    CommandShape(
        name="Hermetic Unit Tests",
        category="core: test",
        command=["just", "test-unit"],
        description="Fast in-memory unit tests (<35s, $0.00 tokens)",
        is_safe=True,
    ),
    CommandShape(
        name="Documentation Integrity",
        category="core: test",
        command=["just", "test-docs"],
        description="Frontmatter, 7-manifest parity & living canon tests",
        is_safe=True,
    ),
    CommandShape(
        name="Declarative Agent Health",
        category="core: quality",
        command=["just", "agent-check"],
        description="AGENTS.md, skills schema and token budget check",
        is_safe=True,
    ),
    CommandShape(
        name="Skills Linter",
        category="core: quality",
        command=["just", "audit-skills"],
        description="Validate .agents/skills schema and YAML frontmatter",
        is_safe=True,
    ),
    CommandShape(
        name="Demotions Audit",
        category="core: quality",
        command=["just", "audit-demotions"],
        description="Audit invariant demotion candidates and token savings",
        is_safe=True,
    ),
    # 2. Version Control & PR Inspection
    CommandShape(
        name="Ecosystem Git Status",
        category="vcs: safe",
        command=["just", "status"],
        description="3-repo clean status check (credence, docs, agent)",
        is_safe=True,
    ),
    CommandShape(
        name="Ecosystem Git Diff",
        category="vcs: safe",
        command=["just", "git-diff"],
        description="View uncommitted diffs across all ecosystem repos",
        is_safe=True,
    ),
    CommandShape(
        name="Ecosystem Git Log",
        category="vcs: safe",
        command=["just", "git-log", "5"],
        description="Compact git log across ecosystem repos",
        is_safe=True,
    ),
    CommandShape(
        name="Pull Request Triad Status",
        category="vcs: safe",
        command=["just", "pr-status"],
        description="Inspect active staged PRs across the ecosystem triad",
        is_safe=True,
    ),
    CommandShape(
        name="Pull Request Checks View",
        category="vcs: safe",
        command=["just", "pr-checks"],
        description="Inspect CI/CD status on open pull requests",
        is_safe=True,
    ),
    CommandShape(
        name="Pull Request Markdown View",
        category="vcs: safe",
        command=["just", "pr-view"],
        description="View details and diff of open pull requests",
        is_safe=True,
    ),
    CommandShape(
        name="GitHub CLI PR Checks",
        category="vcs: safe",
        command=["gh", "pr", "checks"],
        description="Direct GitHub CLI check run inspection",
        is_safe=True,
    ),
    CommandShape(
        name="GitHub CLI PR View",
        category="vcs: safe",
        command=["gh", "pr", "view"],
        description="Direct GitHub CLI pull request viewer",
        is_safe=True,
    ),
    # 3. Cloud & Infrastructure Telemetry (Read-Only)
    CommandShape(
        name="Cloud Run Compute Status",
        category="hosted: safe",
        command=["just", "cloud-status"],
        description="Inspect Cloud Run revisions and traffic splits",
        is_safe=True,
    ),
    CommandShape(
        name="Cloud Run Dev Probe",
        category="hosted: safe",
        command=["just", "cloud-probe", "credence-dev", "dev"],
        description="Probe live Dev HTTP and SSE endpoints with latency metrics",
        is_safe=True,
    ),
    CommandShape(
        name="Cloud Run Prod Probe",
        category="hosted: safe",
        command=["just", "cloud-probe", "credence-server", "prod"],
        description="Probe live Prod HTTP and SSE endpoints with latency metrics",
        is_safe=True,
    ),
    CommandShape(
        name="Cloudflare Edge Status",
        category="hosted: safe",
        command=["just", "edge-status"],
        description="Inspect Cloudflare worker routing and pages deployments",
        is_safe=True,
    ),
    CommandShape(
        name="GitHub Actions CI Status",
        category="hosted: safe",
        command=["just", "ci-status"],
        description="List recent workflow runs across ecosystem repos",
        is_safe=True,
    ),
    CommandShape(
        name="GitHub CLI Run List",
        category="hosted: safe",
        command=["gh", "run", "list", "--limit", "5"],
        description="Direct GitHub Actions workflow run listing",
        is_safe=True,
    ),
    CommandShape(
        name="Terraform Configuration Validation",
        category="hosted: safe",
        command=["just", "tf-validate"],
        description="Terraform formatting and HCL syntax validation",
        is_safe=True,
    ),
    CommandShape(
        name="Multi-Plane Diagnostic Health",
        category="hosted: safe",
        command=["just", "doctor"],
        description="Complete multi-plane diagnostic health check",
        is_safe=True,
    ),
    # 4. Live URL & Web Endpoint Telemetry (HTTP / curl)
    CommandShape(
        name="Live Dev Health Endpoint Probe",
        category="url: telemetry",
        command=["curl", "-sI", "https://credence-dev-663899237633.us-central1.run.app/health"],
        description="Direct HTTP probe on Cloud Run Dev container health",
        is_safe=True,
    ),
    CommandShape(
        name="Live Prod Health Endpoint Probe",
        category="url: telemetry",
        command=["curl", "-sI", "https://credence-server-663899237633.us-central1.run.app/health"],
        description="Direct HTTP probe on Cloud Run Production container health",
        is_safe=True,
    ),
    CommandShape(
        name="Live Edge Domain Probe",
        category="url: telemetry",
        command=["curl", "-sI", "https://credence.run/health"],
        description="Direct HTTP probe on Cloudflare Edge proxy and router",
        is_safe=True,
    ),
    CommandShape(
        name="Live Docs Portal Probe",
        category="url: telemetry",
        command=["curl", "-sI", "https://docs.credence.run"],
        description="Direct HTTP probe on zero-build documentation portal",
        is_safe=True,
    ),
]


def display_catalog() -> None:
    """Print the complete catalog of bootstrap command shapes."""
    table = Table(
        title="[bold cyan]Credence Autonomous Command Approval Catalog[/bold cyan]",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", justify="right", style="cyan", width=4)
    table.add_column("Category", style="yellow", width=16)
    table.add_column("Command Shape", style="bold white", width=36)
    table.add_column("Safety Domain", justify="center", width=12)
    table.add_column("Purpose", style="dim")

    for i, shape in enumerate(BOOTSTRAP_COMMAND_SHAPES, 1):
        safety_badge = "[green]SAFE (READ)[/green]" if shape.is_safe else "[red]GATED (WRITE)[/red]"
        cmd_str = " ".join(shape.command)
        table.add_row(f"#{i}", shape.category, cmd_str, safety_badge, shape.description)

    console.print(table)


def run_bootstrapping(dry_run: bool = False) -> None:
    """Execute all safe command shapes sequentially."""
    console.print(
        Panel(
            "[bold green]Credence Agent Approval Bootstrapping Runner[/bold green]\n\n"
            "This utility executes each safe, read-only command pattern once.\n"
            "When the Antigravity IDE approval dialog appears for each command,\n"
            "select [bold cyan]'Always Allow'[/bold cyan] to authorize autonomous workflows.",
            title="[bold]Workflow Safety Dance[/bold]",
            border_style="cyan",
        )
    )

    display_catalog()

    if dry_run:
        console.print(
            "\n[bold yellow]DRY-RUN MODE:[/bold yellow] Listed all command shapes. Run with [bold green]--execute[/bold green] to run through approvals."
        )
        return

    console.print("\n[bold cyan]=== Initiating Sequential Execution Pass ===[/bold cyan]\n")

    for i, shape in enumerate(BOOTSTRAP_COMMAND_SHAPES, 1):
        cmd_str = " ".join(shape.command)
        console.print(
            f"[bold cyan][{i}/{len(BOOTSTRAP_COMMAND_SHAPES)}][/bold cyan] Running: [bold]{cmd_str}[/bold] ..."
        )
        try:
            res = subprocess.run(  # noqa: S603
                shape.command,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=45,
            )
            if res.returncode == 0:
                console.print(f"   [green]✅ Verified:[/green] {shape.name}")
            else:
                console.print(f"   [yellow]⚠️ Exited with code {res.returncode}:[/yellow] {shape.name}")
        except Exception as e:
            console.print(f"   [red]❌ Execution error:[/red] {e}")

    console.print(
        "\n[bold green]🎉 Approval Bootstrapping Complete![/bold green]\n"
        "[dim]All primary safe command shapes have been executed and are ready for autonomous development.[/dim]\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Agent Command Approvals")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute all safe commands sequentially for IDE approval prompting.",
    )
    args = parser.parse_args()
    run_bootstrapping(dry_run=not args.execute)


if __name__ == "__main__":
    main()
