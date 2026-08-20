"""Pytest Configuration and Fixtures for Credence Test Suite."""

from pathlib import Path
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.cache.distributed import reset_state_store
from credence.db import init_db
from credence.taxonomy_loader import TaxonomyRegistry


@pytest.fixture(autouse=True)
def reset_governor_state() -> None:
    """Reset distributed state store and runtime cost settings before each test."""
    reset_state_store()


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).resolve().parent / "fixtures" / "html"


@pytest.fixture
def clean_html(fixtures_dir: Path) -> str:
    """Return contents of clean news article fixture."""
    return (fixtures_dir / "clean_article.html").read_text(encoding="utf-8")


@pytest.fixture
def satire_html(fixtures_dir: Path) -> str:
    """Return contents of satire news article fixture."""
    return (fixtures_dir / "satire_article.html").read_text(encoding="utf-8")


@pytest.fixture
def deceptive_html(fixtures_dir: Path) -> str:
    """Return contents of deceptive UI page fixture."""
    return (fixtures_dir / "deceptive_page.html").read_text(encoding="utf-8")


@pytest.fixture
def fallacious_html(fixtures_dir: Path) -> str:
    """Return contents of fallacious op-ed fixture."""
    return (fixtures_dir / "fallacious_op_ed.html").read_text(encoding="utf-8")


@pytest.fixture
def test_registry() -> TaxonomyRegistry:
    """Return a fresh TaxonomyRegistry loaded with standard catalogs."""
    reg = TaxonomyRegistry()
    reg.load_all()
    return reg


@pytest.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Provide an isolated in-memory SQLite async engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    await init_db(engine)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated async database session for unit tests."""
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
async def auto_isolated_db(async_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Ensure credence.db._engine points to the isolated in-memory test engine for all tests."""
    import credence.db

    old_engine = credence.db._engine
    credence.db._engine = async_engine
    yield
    credence.db._engine = old_engine
