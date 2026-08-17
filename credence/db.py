"""Asynchronous Database Management for Credence.

Provides async SQLite engine with WAL mode optimization, session management,
and schema initialization using SQLModel and aiosqlite.
"""

from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import settings

# Global async engine instance
_engine: AsyncEngine | None = None


def get_engine(db_url: str | None = None) -> AsyncEngine:
    """Get or create the global SQLAlchemy async engine."""
    global _engine
    if _engine is None or db_url is not None:
        target_url = db_url or settings.DATABASE_URL

        # Ensure parent directory exists for SQLite database files
        if target_url.startswith("sqlite+aiosqlite:///"):
            raw_path = target_url.replace("sqlite+aiosqlite:///", "")
            if raw_path != ":memory:" and not raw_path.startswith(":memory:"):
                db_path = Path(raw_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)

        _engine = create_async_engine(
            target_url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False} if "sqlite" in target_url else {},
        )
    return _engine


async def init_db(engine: AsyncEngine | None = None) -> None:
    """Initialize database schemas and apply SQLite performance pragmas."""
    target_engine = engine or get_engine()

    # Enable WAL mode and foreign keys for SQLite
    if "sqlite" in str(target_engine.url):
        async with target_engine.connect() as conn:
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
            await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")

    async with target_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for dependency injection or transactions."""
    engine = get_engine()
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session


async def close_db() -> None:
    """Dispose the global async engine connection pool."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
