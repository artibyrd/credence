"""Combined Lifespan Management for Background Daemons."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlmodel import col, func, select
from starlette.applications import Starlette

from credence.db import get_async_session, init_db
from credence.models import FeedSubscription

logger = logging.getLogger("credence.server.lifespan")


def combined_lifespan(app_instance: Starlette, enable_sifter: bool = True, enable_boredom: bool = True):
    """Generate combined async lifespan context manager."""
    should_sift = enable_sifter and os.environ.get("CREDENCE_SIFTER_ENABLED", "true").lower() not in ("0", "false")
    should_boredom = enable_boredom and os.environ.get("CREDENCE_BOREDOM_ENABLED", "true").lower() not in ("0", "false")
    original_lifespan = getattr(app_instance.router, "lifespan_context", None)

    @asynccontextmanager
    async def _lifespan(app: Starlette) -> AsyncGenerator[dict, None]:
        # Pre-boot restore hook: checks cloud backup / local archive before init_db
        try:
            from credence.storage.backup import create_database_backup, restore_latest_cloud_backup

            await restore_latest_cloud_backup()
        except Exception as re:
            logger.debug("Pre-boot cloud restore hook exception: %s", re)

        await init_db()

        # Check for zero-touch auto-germination on blank databases
        async def _run_background_germination() -> None:
            try:
                async with get_async_session() as session:
                    stmt_f = select(func.count(col(FeedSubscription.id)))
                    total_f = (await session.exec(stmt_f)).first() or 0

                    if total_f == 0:
                        logger.info("🌱 Cold node detected — auto-germinating identity and syndicated feeds...")
                        from credence.germinate import germinate_node

                        await germinate_node(session=session, burst_items=3, sync_mesh=True, verbose=True)
            except Exception as e:
                logger.warning("Auto-germination background task encountered error: %s", e)

        _germinate_task = asyncio.create_task(_run_background_germination())

        sifter_daemon = None
        sifter_task = None
        if should_sift:
            from credence.feeds.sifter import SifterDaemon

            sifter_daemon = SifterDaemon(poll_interval_seconds=300, auto_audit=True)
            sifter_task = asyncio.create_task(sifter_daemon.start())

        boredom_daemon = None
        boredom_task = None
        if should_boredom:
            from credence.feeds.boredom import BoredomDaemon

            boredom_daemon = BoredomDaemon(idle_interval_seconds=120, audit_burst=3, expand_roots_enabled=True)
            boredom_task = asyncio.create_task(boredom_daemon.start())

        try:
            if original_lifespan:
                async with original_lifespan(app) as state:
                    yield state
            else:
                yield {}
        finally:
            if _germinate_task and not _germinate_task.done():
                _germinate_task.cancel()
            if sifter_daemon and sifter_task:
                sifter_daemon.stop()
                try:
                    await asyncio.wait_for(sifter_task, timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
            if boredom_daemon and boredom_task:
                boredom_daemon.stop()
                try:
                    await asyncio.wait_for(boredom_task, timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass

            # Graceful shutdown: flush WAL and export backup snapshot
            try:
                from credence.storage.backup import create_database_backup

                create_database_backup(upload_cloud=True)
            except Exception as be:
                logger.debug("Shutdown backup hook non-blocking exception: %s", be)

    return _lifespan
