"""FastMCP 2.0 Administrator Tools for Sovereign Backup, Recovery, and Curiosity Cycles."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from mcp.server.mcpserver import MCPServer

from credence.db import get_async_session, init_db
from credence.storage.backup import (
    create_database_backup,
    export_attestation_pack,
    get_backup_status,
    import_attestation_pack,
    restore_database_backup,
)

logger = logging.getLogger("credence.server.mcp.admin")


def _register_admin_tools(server: MCPServer) -> None:
    """Register sovereign administrative backup, recovery, and Curiosity Loop FastMCP tools."""

    @server.tool(
        name="credence_admin_backup_db",
        description="Create an atomic SQLite snapshot, compress with gzip, compute SHA-256 hash, and sign manifest.",
    )
    async def admin_backup_db_tool(
        output_path: Optional[str] = None,
        upload_cloud: bool = True,
    ) -> str:
        try:
            out = Path(output_path) if output_path else None
            meta = create_database_backup(output_path=out, upload_cloud=upload_cloud)
            return json.dumps(
                {
                    "status": "success",
                    "backup_id": meta.backup_id,
                    "file_name": meta.file_name,
                    "size_bytes": meta.size_bytes,
                    "sha256_hash": meta.sha256_hash,
                    "audit_count": meta.audit_count,
                    "snapshot_count": meta.snapshot_count,
                    "storage_backend": meta.storage_backend,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @server.tool(
        name="credence_admin_restore_db",
        description="Restore SQLite database from a verified .db.gz archive with SHA-256 integrity verification.",
    )
    async def admin_restore_db_tool(
        source_path: str,
        force: bool = False,
    ) -> str:
        try:
            src = Path(source_path)
            res = restore_database_backup(source_path=src, force=force)
            return json.dumps(res.model_dump(mode="json"), indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @server.tool(
        name="credence_admin_export_attestations",
        description="Export all local database audits and violations into an RFC 8785 signed attestation bundle.",
    )
    async def admin_export_attestations_tool(
        output_path: Optional[str] = None,
    ) -> str:
        await init_db()
        async with get_async_session() as session:
            try:
                out = Path(output_path) if output_path else None
                pack_path = await export_attestation_pack(session=session, output_path=out)
                return json.dumps(
                    {
                        "status": "success",
                        "pack_path": str(pack_path),
                        "message": "Attestation pack exported and signed successfully",
                    },
                    indent=2,
                )
            except Exception as e:
                return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @server.tool(
        name="credence_admin_import_attestations",
        description="Import and adopt signed attestations from a seed pack into local database at $0.00 token cost.",
    )
    async def admin_import_attestations_tool(
        source_path: str,
    ) -> str:
        await init_db()
        async with get_async_session() as session:
            try:
                res = await import_attestation_pack(session=session, pack_path_or_url=source_path)
                return json.dumps(res, indent=2)
            except Exception as e:
                return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @server.tool(
        name="credence_admin_trigger_boredom",
        description="Trigger an immediate opportunistic Curiosity Loop (Epistemic Boredom) evaluation cycle.",
    )
    async def admin_trigger_boredom_tool(
        burst: int = 3,
        ratio: float = 0.60,
    ) -> str:
        import dataclasses

        from credence.feeds.boredom import run_boredom_cycle

        await init_db()
        async with get_async_session() as session:
            try:
                summary = await run_boredom_cycle(
                    session=session,
                    audit_burst=burst,
                    expand_roots_enabled=True,
                    boredom_ratio=ratio,
                )
                data = dataclasses.asdict(summary)
                data["timestamp"] = summary.timestamp.isoformat()
                return json.dumps(data, indent=2)
            except Exception as e:
                return json.dumps({"status": "error", "message": str(e)}, indent=2)

    @server.tool(
        name="credence_admin_backup_status",
        description="Retrieve database storage, backup inventory, and latest snapshot telemetry.",
    )
    async def admin_backup_status_tool() -> str:
        status = get_backup_status()
        return json.dumps(status, indent=2)
