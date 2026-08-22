"""Database Storage Gravity & Backup Recovery REST API Handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from starlette.responses import JSONResponse

from credence.config import settings
from credence.db import get_async_session, init_db
from credence.server.middleware.security import _check_admin_auth
from credence.storage.backup import (
    create_database_backup,
    export_attestation_pack,
    get_backup_status,
    import_attestation_pack,
    restore_database_backup,
)


async def api_db_backup(request: Any) -> Any:
    """REST API: Trigger on-demand compressed SQLite database snapshot (Admin Gated)."""
    if not bool(_check_admin_auth(request)):
        return JSONResponse(
            {"error": "Unauthorized: Administrator authentication required to create backups"},
            status_code=401,
        )

    await init_db()
    try:
        body = {}
        if request.method == "POST":
            try:
                body = await request.json()
            except Exception:
                body = {}
        upload_cloud = bool(body.get("upload_cloud", True))
        descriptor = create_database_backup(upload_cloud=upload_cloud)
        return JSONResponse({"status": "success", "backup": descriptor.model_dump(mode="json")})
    except Exception as e:
        return JSONResponse({"error": f"Backup generation failed: {e}"}, status_code=500)


async def api_db_restore(request: Any) -> Any:
    """REST API: Restore database from cloud or local compressed snapshot (Admin Gated)."""
    if not bool(_check_admin_auth(request)):
        return JSONResponse(
            {"error": "Unauthorized: Administrator authentication required to restore database"},
            status_code=401,
        )

    try:
        body = {}
        if request.method == "POST":
            try:
                body = await request.json()
            except Exception:
                body = {}
        archive_str = body.get("archive_path")
        source_path = Path(archive_str) if archive_str else (settings.CREDENCE_BACKUP_DIR / "credence_latest.db.gz")
        force = bool(body.get("force", False))
        res = restore_database_backup(source_path=source_path, force=force)
        return JSONResponse({"status": "success", "restored": res.model_dump(mode="json")})
    except Exception as e:
        return JSONResponse({"error": f"Database restoration failed: {e}"}, status_code=500)


async def api_db_status(request: Any) -> Any:
    """REST API: Retrieve database storage gravity, manifest, and snapshot health."""
    try:
        status = get_backup_status()
        return JSONResponse(status)
    except Exception as e:
        return JSONResponse({"error": f"Failed retrieving backup status: {e}"}, status_code=500)


async def api_db_export_pack(request: Any) -> Any:
    """REST API: Export cryptographic attestation pack for P2P sharing and portability."""
    await init_db()
    try:
        async with get_async_session() as s:
            target_path = await export_attestation_pack(session=s)
            pack_data = json.loads(target_path.read_text(encoding="utf-8"))
            return JSONResponse(pack_data)
    except Exception as e:
        return JSONResponse({"error": f"Export attestation pack failed: {e}"}, status_code=500)


async def api_db_import_pack(request: Any) -> Any:
    """REST API: Import signed attestation pack and verify signatures (Admin Gated)."""
    if not bool(_check_admin_auth(request)):
        return JSONResponse(
            {"error": "Unauthorized: Administrator authentication required to import attestation packs"},
            status_code=401,
        )

    await init_db()
    try:
        data = await request.json()
        temp_pack = settings.CREDENCE_BACKUP_DIR / "imported_pack.json"
        temp_pack.parent.mkdir(parents=True, exist_ok=True)
        temp_pack.write_text(json.dumps(data), encoding="utf-8")

        async with get_async_session() as s:
            imported_res = await import_attestation_pack(session=s, pack_path_or_url=temp_pack)
            return JSONResponse({"status": "success", "imported_attestations": imported_res.get("adopted_count", 0)})
    except Exception as e:
        return JSONResponse({"error": f"Import attestation pack failed: {e}"}, status_code=500)
