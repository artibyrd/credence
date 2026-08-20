"""CLI Database Operations Command Handlers for Credence.

Governed by Theme 1: Botanical Network & Lifecycle & Theme 4: Sovereign Governance.
"""

from __future__ import annotations

from rich.console import Console

from credence.db import get_engine, init_db, migrate_db_v1_to_v2

console = Console()


async def run_db_init_command() -> int:
    """Initialize or migrate the SQLite database schema."""
    engine = get_engine()
    await init_db(engine)
    console.print("[bold green]✅ Database schema initialized cleanly with WAL pragmas enabled.[/bold green]")
    return 0


async def run_db_migrate_command() -> int:
    """Execute automated v1 -> v2 schema migrations and verify SQLite integrity."""
    engine = get_engine()
    await migrate_db_v1_to_v2(engine)
    console.print("[bold green]✅ Database schema verified and migrated to v2.0.0 cleanly.[/bold green]")
    return 0
