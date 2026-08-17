"""Configuration settings for Credence using Pydantic Settings."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings for Credence."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    CREDENCE_ENV: Literal["development", "testing", "staging", "production"] = "development"
    CREDENCE_LOG_LEVEL: str = "INFO"

    # Storage & Paths
    DATABASE_URL: str = "sqlite+aiosqlite:///data/credence.db"
    SNAPSHOT_DIR: Path = Path("data/snapshots")
    TAXONOMY_DIR: Path = Path(__file__).resolve().parent / "taxonomies"
    NODE_KEY_PATH: Path = Path("data/node_identity.key")

    # LLM & Antigravity
    GEMINI_API_KEY: str | None = None

    # FastMCP & API Server
    MCP_HOST: str = "0.0.0.0"  # noqa: S104
    MCP_PORT: int = 8000

    # Ingestion & Playwright Concurrency
    MAX_CONCURRENT_SNAPSHOTS: int = 1
    PLAYWRIGHT_TIMEOUT_MS: int = 30000


settings = Settings()
