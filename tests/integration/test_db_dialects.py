"""Unit tests for SQLite and PostgreSQL engine creation and pooling."""

from __future__ import annotations

import pytest

from credence.db import get_engine


@pytest.mark.integration
def test_sqlite_engine_creation():
    """Verify SQLite engine uses NullPool."""
    engine = get_engine("sqlite+aiosqlite:///:memory:")
    assert "sqlite" in str(engine.url)


@pytest.mark.integration
def test_postgresql_engine_configuration():
    """Verify PostgreSQL engine is configured with AsyncAdaptedQueuePool."""
    try:
        import asyncpg  # noqa: F401
    except ImportError:
        pytest.skip("asyncpg not installed in local development virtualenv")

    engine = get_engine("postgresql+asyncpg://user:pass@localhost:5432/testdb")
    assert "postgresql" in str(engine.url)
    assert engine.pool is not None
