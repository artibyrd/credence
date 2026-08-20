"""CLI Organization Scaffolding Command Handlers for Credence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

console = Console()


def run_init_org_command(
    org_name: str, org_domain: str, cloud_provider: str = "gcp", output_dir: Optional[str] = None
) -> int:
    return run_org_init_command(org_name, org_domain, cloud_provider, output_dir)


def run_org_init_command(
    org_name: str, domain: str, cloud_provider: str = "gcp", output_dir: Optional[str] = None
) -> int:
    """Scaffold a new sovereign white-label organization workspace."""
    org_slug = org_name.lower().replace(" ", "-")
    target = Path(output_dir) if output_dir else Path.cwd() / "orgs" / org_slug
    target.mkdir(parents=True, exist_ok=True)

    config = {
        "organization_name": org_name,
        "apex_domain": domain,
        "catalogs": ["spj_ethics", "deceptive_patterns", "fallacy_detection"],
        "peer_seeds": ["ws://mesh.credence.nexus:8765"],
    }
    (target / "credence.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    yaml_config = f"""organization_name: "{org_name}"
apex_domain: "{domain}"
cloud_provider: "{cloud_provider}"
catalogs:
  - spj_ethics
  - deceptive_patterns
  - fallacy_detection
peer_seeds:
  - ws://mesh.credence.nexus:8765
"""
    (target / "org-config.yaml").write_text(yaml_config, encoding="utf-8")

    keys_dir = target / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    (keys_dir / "root.pub").write_text("credence-root-pubkey-placeholder\n", encoding="utf-8")

    console.print(
        Panel(
            f"[bold green]Organization Scaffolded Successfully![/bold green]\n"
            f"[cyan]Org:[/cyan] {org_name}\n"
            f"[cyan]Domain:[/cyan] {domain}\n"
            f"[cyan]Path:[/cyan] {target}",
            title="[bold blue]White-Label Organization Initialized[/bold blue]",
        )
    )
    return 0
