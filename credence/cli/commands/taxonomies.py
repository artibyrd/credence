"""CLI Taxonomy & Catalog Export Command Handlers for Credence."""

from __future__ import annotations

from typing import Any, Optional

from rich import box
from rich.console import Console
from rich.table import Table

from credence.taxonomy_loader import TaxonomyRegistry

console = Console()


def run_taxonomy_list_command(domain: Optional[str] = None, *args: Any, **kwargs: Any) -> int:
    """List loaded epistemic rule catalogs and rule counts."""
    registry = TaxonomyRegistry()
    registry.load_all()

    table = Table(title="Epistemic Rule Taxonomies", box=box.ROUNDED)
    table.add_column("Catalog ID", style="bold cyan")
    table.add_column("Title", style="white")
    table.add_column("Rules", justify="right")
    table.add_column("SHA-256", style="dim")

    for cat in registry.catalogs.values():
        total_rules = sum(len(c.rules) for c in cat.clusters)
        hash_preview = (cat.catalog_hash[:16] + "...") if cat.catalog_hash else "None"
        table.add_row(cat.catalog_id, cat.description, str(total_rules), hash_preview)

    console.print(table)
    return 0
