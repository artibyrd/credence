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
            from credence.storage.backup import restore_latest_cloud_backup

            restored = await restore_latest_cloud_backup()
            if restored:
                logger.info("🚀 Pre-boot cloud restore completed successfully prior to init_db")
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
                    else:
                        from credence.feeds.worker import bootstrap_preset_feeds

                        await bootstrap_preset_feeds(session)

                    # Synchronize node-configured sentinels from CREDENCE_SENTINEL_FEEDS environment variable
                    from credence.feeds.sentinel import sync_env_sentinel_sources

                    await sync_env_sentinel_sources(session)

                    # Trigger boot sifting burst on all active sentinel subscriptions
                    stmt_s = select(FeedSubscription).where(
                        FeedSubscription.is_sentinel == True,  # noqa: E712
                        FeedSubscription.is_active == True,  # noqa: E712
                    )
                    sent_subs = (await session.exec(stmt_s)).all()
                    if sent_subs:
                        logger.info(
                            "🛡️ Triggering initial sentinel sifting burst on boot for %d active sentinel sources...",
                            len(sent_subs),
                        )
                        from credence.feeds.worker import sync_single_feed

                        for s_sub in sent_subs:
                            try:
                                await sync_single_feed(
                                    session, s_sub, dry_run=False, evaluate_novel=True, force_refresh=True
                                )
                            except Exception as se:
                                logger.warning("Boot sentinel sync failed for %s: %s", s_sub.feed_url, se)

                        # Create database backup after initial boot sifting
                        try:
                            from credence.storage.backup import create_database_backup_async

                            await create_database_backup_async(upload_cloud=True)
                        except Exception as cbe:
                            logger.debug("Initial boot backup upload exception: %s", cbe)
            except Exception as e:
                logger.warning("Auto-germination background task encountered error: %s", e)

        _germinate_task = asyncio.create_task(_run_background_germination())

        # Periodic background database backup task (every 30 minutes)
        async def _run_periodic_backups() -> None:
            while True:
                try:
                    await asyncio.sleep(1800)
                    from credence.storage.backup import create_database_backup_async

                    await create_database_backup_async(upload_cloud=True)
                except asyncio.CancelledError:
                    break
                except Exception as pe:
                    logger.debug("Periodic backup task exception: %s", pe)

        _backup_task = asyncio.create_task(_run_periodic_backups())

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
            if _backup_task and not _backup_task.done():
                _backup_task.cancel()
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

            # Graceful shutdown: flush WAL and export backup snapshot to cloud
            try:
                from credence.storage.backup import create_database_backup_async

                await create_database_backup_async(upload_cloud=True)
            except Exception as be:
                logger.debug("Shutdown backup hook exception: %s", be)

    return _lifespan
