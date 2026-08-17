"""Configuration, cost profile presets, and environment settings for Credence."""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CostProfile(str, Enum):
    """Operational cost profiles mapped to Gemini subscription tiers."""

    FREE = "free"
    BALANCED = "balanced"
    ULTRA = "ultra"


class CostProfileConfig(BaseModel):
    """Configuration definition for an operational cost profile."""

    profile: CostProfile
    name: str
    description: str
    target_tier: str
    primary_model: str
    escalation_model: str
    triage_model: str
    default_thinking_budget: int = Field(ge=0, description="Thinking tokens allocated per subagent")
    escalation_thinking_budget: int = Field(ge=0, description="Thinking tokens on ambiguous scores")
    max_tokens_per_hour: int = Field(gt=0)
    max_tokens_per_day: int = Field(gt=0)
    max_daily_budget_usd: float = Field(ge=0.0)
    max_article_words: int = Field(gt=0)
    concurrency_limit: int = Field(gt=0)
    enable_deep_verification: bool = False


COST_PROFILES: Dict[CostProfile, CostProfileConfig] = {
    CostProfile.FREE: CostProfileConfig(
        profile=CostProfile.FREE,
        name="Free / Zero-Marginal-Cost",
        description="Strict zero-spend budget enforcing Gemini API Free Tier limits (15 RPM / 1M TPM) with zero thinking tokens.",
        target_tier="Gemini API Free Tier (Zero-Cost)",
        primary_model="gemini-2.0-flash-lite",
        escalation_model="gemini-2.0-flash-lite",
        triage_model="gemini-2.0-flash-lite",
        default_thinking_budget=0,
        escalation_thinking_budget=0,
        max_tokens_per_hour=50_000,
        max_tokens_per_day=250_000,
        max_daily_budget_usd=0.00,
        max_article_words=1500,
        concurrency_limit=1,
        enable_deep_verification=False,
    ),
    CostProfile.BALANCED: CostProfileConfig(
        profile=CostProfile.BALANCED,
        name="Balanced / Developer Standard",
        description="Standard pay-as-you-go developer profile balancing low token costs with calibrated Gemini 3.7 Flash thinking on ambiguity.",
        target_tier="Gemini Pay-As-You-Go ($0.10/$0.40 per 1M)",
        primary_model="gemini-3.7-flash",
        escalation_model="gemini-3.7-flash",
        triage_model="gemini-2.5-flash-lite",
        default_thinking_budget=1024,
        escalation_thinking_budget=4096,
        max_tokens_per_hour=100_000,
        max_tokens_per_day=1_000_000,
        max_daily_budget_usd=0.50,
        max_article_words=3000,
        concurrency_limit=3,
        enable_deep_verification=False,
    ),
    CostProfile.ULTRA: CostProfileConfig(
        profile=CostProfile.ULTRA,
        name="Ultra / Newsroom Fidelity",
        description="Maximum epistemic depth utilizing Gemini 3.7 Flash high-reasoning budgets (8k-16k tokens) and Gemini 1.5 Pro for full long-form articles.",
        target_tier="Gemini Advanced / Ultra / Newsroom Desk",
        primary_model="gemini-3.7-flash",
        escalation_model="gemini-1.5-pro",
        triage_model="gemini-3.7-flash",
        default_thinking_budget=4096,
        escalation_thinking_budget=16384,
        max_tokens_per_hour=2_000_000,
        max_tokens_per_day=20_000_000,
        max_daily_budget_usd=15.00,
        max_article_words=10000,
        concurrency_limit=8,
        enable_deep_verification=True,
    ),
}


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

    # Active Cost & Operational Profile
    CREDENCE_PROFILE: CostProfile = CostProfile.BALANCED

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
    MESH_ENABLED: bool = True
    MESH_HOST: str = "0.0.0.0"  # noqa: S104
    MESH_PORT: int = 8765
    PEER_SEEDS: str = ""  # Comma-separated list of peer ws://host:port endpoints
    CONSENSUS_THRESHOLD: float = 0.66
    RATE_LIMIT_MSGS_PER_SEC: int = 50
    MCP_HOST: str = "0.0.0.0"  # noqa: S104
    MCP_PORT: int = 8000

    # Canonical Domain Endpoints & P2P Bootstrapping
    DEFAULT_SEED_URL: str = "https://seeds.credence.nexus/peers.json"
    CANONICAL_MCP_URL: str = "https://mcp.credence.run/sse"
    CANONICAL_TAXONOMY_URL: str = "https://taxonomies.credence.foundation"
    CANONICAL_REPORT_URL: str = "https://credence.report"
    TRUSTED_ROOT_PUBKEY: Optional[str] = None
    ENABLE_LOCAL_DISCOVERY: bool = True
    DISCOVERY_BEACON_PORT: int = 8766
    DISCOVERY_TIMEOUT_SEC: float = 2.0

    def get_profile_config(self) -> CostProfileConfig:
        """Retrieve the CostProfileConfig for the active CREDENCE_PROFILE."""
        cfg = COST_PROFILES.get(self.CREDENCE_PROFILE, COST_PROFILES[CostProfile.BALANCED]).model_copy()
        if self.MAX_TOKENS_PER_HOUR != 100_000:
            cfg.max_tokens_per_hour = self.MAX_TOKENS_PER_HOUR
        if self.MAX_TOKENS_PER_DAY != 1_000_000:
            cfg.max_tokens_per_day = self.MAX_TOKENS_PER_DAY
        if self.MAX_DAILY_BUDGET_USD != 0.50:
            cfg.max_daily_budget_usd = self.MAX_DAILY_BUDGET_USD
        return cfg


settings = Settings()
