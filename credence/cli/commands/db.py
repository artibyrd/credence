from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from credence.db import get_async_session, get_engine, init_db, migrate_db_v1_to_v2
from credence.storage.backup import (
    create_database_backup,
    export_attestation_pack,
    get_backup_status,
    import_attestation_pack,
    restore_database_backup,
)

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


async def run_db_backup_command(output_path: Optional[str] = None) -> int:
    """Create an atomic, compressed SQLite snapshot and sign manifest."""
    out = Path(output_path) if output_path else None
    try:
        meta = create_database_backup(output_path=out, upload_cloud=True)
        console.print(f"[bold green]✅ Atomic database backup created:[/bold green] {meta.file_name}")
        console.print(f"   • Archive Size : {meta.size_bytes:,} bytes (raw: {meta.uncompressed_bytes:,} bytes)")
        console.print(f"   • SHA-256 Hash : {meta.sha256_hash}")
        console.print(f"   • Audits Count : {meta.audit_count} captured")
        sig = meta.manifest_signature[:32] if meta.manifest_signature else "none"
        console.print(f"   • Ed25519 Sig  : {sig}...")
        return 0
    except Exception as e:
        console.print(f"[bold red]❌ Database backup failed: {e}[/bold red]")
        return 1


async def run_db_restore_command(source_path: str, force: bool = False) -> int:
    """Restore SQLite database from a compressed .db.gz archive with integrity verification."""
    src = Path(source_path)
    if not src.exists():
        console.print(f"[bold red]❌ Backup archive not found: {source_path}[/bold red]")
        return 1
    try:
        res = restore_database_backup(source_path=src, force=force)
        console.print(f"[bold green]🔄 Database restored successfully in {res.duration_ms:.1f}ms[/bold green]")
        console.print(f"   • Active Audits    : {res.audit_count}")
        console.print(f"   • Active Snapshots : {res.snapshot_count}")
        console.print("   • SHA-256 Checksum : Verified Authentic")
        return 0
    except Exception as e:
        console.print(f"[bold red]❌ Database restore failed: {e}[/bold red]")
        return 1


async def run_db_export_pack_command(output_path: Optional[str] = None) -> int:
    """Export local database audits into an RFC 8785 signed attestation pack."""
    out = Path(output_path) if output_path else None
    async with get_async_session() as session:
        try:
            pack_path = await export_attestation_pack(session=session, output_path=out)
            console.print(f"[bold green]📦 Exported signed attestation pack:[/bold green] {pack_path}")
            return 0
        except Exception as e:
            console.print(f"[bold red]❌ Failed to export attestation pack: {e}[/bold red]")
            return 1


async def run_db_import_pack_command(input_source: str) -> int:
    """Import and adopt signed attestations from a seed pack at $0.00 token cost."""
    async with get_async_session() as session:
        try:
            res = await import_attestation_pack(session=session, pack_path_or_url=input_source)
            console.print("[bold green]📥 Attestation pack inoculated successfully:[/bold green]")
            console.print(f"   • Adopted Novel Attestations : {res['adopted_count']} ($0.00 spend)")
            console.print(f"   • Skipped Existing Audits   : {res['skipped_existing']}")
            console.print(f"   • Total Items in Bundle     : {res['total_in_pack']}")
            return 0
        except Exception as e:
            console.print(f"[bold red]❌ Failed to import attestation pack: {e}[/bold red]")
            return 1


def run_db_status_command() -> int:
    """Display database storage, backup inventory, and latest snapshot telemetry."""
    status = get_backup_status()
    table = Table(title="Credence Sovereign Database & Backup Telemetry")
    table.add_column("Property", style="cyan bold")
    table.add_column("Value", style="green")

    table.add_row("Backup Enabled", str(status["backup_enabled"]))
    table.add_row("Storage Backend", status["storage_backend"])
    table.add_row("Cloud Bucket", str(status["cloud_bucket"] or "None (Local Only)"))
    table.add_row("Backup Directory", status["local_backup_dir"])
    table.add_row("Total Retained Backups", str(status["total_backups"]))
    table.add_row("Latest Backup Available", "🟢 Yes" if status["latest_backup_available"] else "🔴 None")
    if status["latest_backup_available"]:
        table.add_row("Latest Backup Size", f"{status['latest_backup_size_bytes']:,} bytes")
        table.add_row("Latest Backup Timestamp", str(status["latest_backup_mtime"]))

    console.print(table)
    return 0
