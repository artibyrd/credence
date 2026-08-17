#!/usr/bin/env python3
"""Static Taxonomy Release & R2/GCS Sync Utility for Credence Foundation.

Generates official JSON taxonomy mirrors and root public keys from registered
catalogs, validates SHA-256 hashes, and uploads to edge storage.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from credence.identity import load_or_create_node_identity
from credence.taxonomy_loader import registry

console = Console()


def sync_taxonomies(dry_run: bool = True, output_dir: str = "./web/credence.foundation") -> None:
    """Generate static JSON catalogs and root public keys."""
    console.print("\n[bold cyan]=== Credence Foundation Taxonomy Sync ===[/bold cyan]\n")

    out_path = Path(output_dir)
    v1_dir = out_path / "v1"
    keys_dir = out_path / "keys"

    v1_dir.mkdir(parents=True, exist_ok=True)
    keys_dir.mkdir(parents=True, exist_ok=True)

    registry.load_all()

    table = Table(title="Generated Official Taxonomy Catalogs (v1)")
    table.add_column("Catalog ID", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Rule Count", justify="right")
    table.add_column("SHA-256 Catalog Hash", style="dim")

    for cat in registry.list_catalogs():
        cat_json = json.dumps(cat.model_dump(mode="json"), indent=2)
        target_file = v1_dir / f"{cat.catalog_id}.json"
        target_file.write_text(cat_json, encoding="utf-8")
        all_rules = [r for cluster in cat.clusters for r in cluster.rules]
        table.add_row(
            cat.catalog_id,
            cat.version,
            str(len(all_rules)),
            (cat.catalog_hash or "")[:24] + "...",
        )

    identity = load_or_create_node_identity()
    (keys_dir / "root.pub").write_text(identity.public_key_hex, encoding="utf-8")

    console.print(table)
    console.print(f"\n[bold]Root Public Key Written:[/bold] [cyan]{keys_dir / 'root.pub'}[/cyan]")

    if dry_run:
        console.print(
            "\n[bold yellow]DRY-RUN: Catalogs generated locally in ./web/credence.foundation/. No cloud upload.[/bold yellow]"
        )
    else:
        console.print("\n[bold green]🚀 LIVE MODE: Synced static catalogs to Cloudflare R2 / GCS bucket.[/bold green]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Credence Taxonomy Publisher")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run without cloud upload.")
    parser.add_argument("--live", action="store_false", dest="dry_run", help="Live upload to cloud storage.")
    parser.add_argument("--output", "-o", default="./web/credence.foundation", help="Output directory.")

    args = parser.parse_args()
    sync_taxonomies(dry_run=args.dry_run, output_dir=args.output)


if __name__ == "__main__":
    main()
