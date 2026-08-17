"""Configuration and environment settings for Credence."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with .env file support and environment variable overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core environment & paths
    ENV: str = "development"
    DATA_DIR: Path = Path("data")
    DB_PATH: Path = Path("data/credence.db")
    DATABASE_URL: str = f"sqlite+aiosqlite:///{Path('data/credence.db')}"
    SNAPSHOT_DIR: Path = Path("data/snapshots")
    NODE_KEY_PATH: Path = Path("data/node_identity.key")
    TAXONOMY_DIR: Path = Path("credence/taxonomies")

    # Playwright Snapshotting Configuration
    HEADLESS_BROWSER: bool = True
    PLAYWRIGHT_TIMEOUT_MS: int = 15000
    BROWSER_TIMEOUT_MS: int = 15000
    MAX_CONCURRENT_SNAPSHOTS: int = 1  # Memory-safe concurrency gate

    # Multi-Agent & LLM Models (Gemini 3.7 Flash with Thinking)
    CREDENCE_GEMINI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEFAULT_SPECIALIST_MODEL: str = "gemini-3.7-flash"
    DEFAULT_TRIAGE_MODEL: str = "gemini-2.5-flash-lite"
    DEFAULT_THINKING_BUDGET: int = 1024
    ESCALATION_THINKING_BUDGET: int = 4096

    # Token Safety Governor & Circuit Breaker
    MAX_TOKENS_PER_HOUR: int = 100_000
    MAX_TOKENS_PER_DAY: int = 1_000_000
    MAX_DAILY_BUDGET_USD: float = 0.50
    ENABLE_CIRCUIT_BREAKER: bool = True

    # P2P Mesh & MCP Networking
    MESH_ENABLED: bool = False
    MESH_PORT: int = 8765
    MCP_HOST: str = "0.0.0.0"  # noqa: S104
    MCP_PORT: int = 8000


settings = Settings()
