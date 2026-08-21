"""Configuration, cost profile presets, and environment settings for Credence."""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CostProfile(str, Enum):
    """Operational cost profiles mapped to Gemini subscription tiers."""

    OFFLINE = "offline"
    FREE = "free"
    ECONOMY = "economy"
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
    CostProfile.OFFLINE: CostProfileConfig(
        profile=CostProfile.OFFLINE,
        name="Offline / Sovereign Air-Gapped",
        description="Strict zero-cloud operation using deterministic structural heuristics and pattern matching at $0.00 cost.",
        target_tier="Local Structural Heuristics Only (Zero Cloud)",
        primary_model="offline-heuristic",
        escalation_model="offline-heuristic",
        triage_model="offline-heuristic",
        default_thinking_budget=0,
        escalation_thinking_budget=0,
        max_tokens_per_hour=1,
        max_tokens_per_day=1,
        max_daily_budget_usd=0.00,
        max_article_words=5000,
        concurrency_limit=1,
        enable_deep_verification=False,
    ),
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
    CostProfile.ECONOMY: CostProfileConfig(
        profile=CostProfile.ECONOMY,
        name="Economy / Conservative Developer (Default)",
        description="Most conservative fully functional profile pairing Gemini 3.7 Flash thinking with strict 15 cent/day ceiling.",
        target_tier="Gemini Pay-As-You-Go ($0.15/day Max Budget)",
        primary_model="gemini-3.7-flash",
        escalation_model="gemini-3.7-flash",
        triage_model="gemini-2.5-flash-lite",
        default_thinking_budget=512,
        escalation_thinking_budget=1024,
        max_tokens_per_hour=50_000,
        max_tokens_per_day=300_000,
        max_daily_budget_usd=0.15,
        max_article_words=2500,
        concurrency_limit=2,
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
        description="Maximum epistemic depth utilizing Gemini 3.7 Flash high-reasoning budgets (4k-16k tokens) and Gemini 1.5 Pro for full long-form articles.",
        target_tier="Gemini Advanced / Ultra / Newsroom Desk",
        primary_model="gemini-3.7-flash",
        escalation_model="gemini-1.5-pro",
        triage_model="gemini-3.7-flash",
        default_thinking_budget=4096,
        escalation_thinking_budget=16384,
        max_tokens_per_hour=2_000_000,
        max_tokens_per_day=10_000_000,
        max_daily_budget_usd=5.00,
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

    # Cloud & Blob Storage Configuration (Local Filesystem or S3 / Cloudflare R2 / GCS)
    STORAGE_BACKEND: str = "local"
    S3_BUCKET_NAME: Optional[str] = None
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_REGION_NAME: str = "auto"
    CREDENCE_BACKUP_BUCKET: Optional[str] = None
    CREDENCE_BACKUP_DIR: Path = Path("data/backups")
    CREDENCE_BACKUP_ENABLED: bool = True
    CREDENCE_BOREDOM_ENABLED: bool = True
    CREDENCE_SIFTER_ENABLED: bool = False

    # Distributed Cache & State Store (Redis / Valkey)
    REDIS_URL: Optional[str] = None

    # Administrative Security & Alert Webhooks
    CREDENCE_ADMIN_API_KEY: Optional[str] = None
    CREDENCE_ADMIN_EMAILS: str = ""
    CREDENCE_OAUTH_GOOGLE_CLIENT_ID: Optional[str] = None
    CREDENCE_OAUTH_GITHUB_CLIENT_ID: Optional[str] = None
    DISCORD_ALERT_WEBHOOK_URL: Optional[str] = None
    SLACK_ALERT_WEBHOOK_URL: Optional[str] = None

    # Playwright Snapshotting Configuration
    HEADLESS_BROWSER: bool = True
    PLAYWRIGHT_TIMEOUT_MS: int = 15000
    BROWSER_TIMEOUT_MS: int = 15000
    MAX_CONCURRENT_SNAPSHOTS: int = 1  # Memory-safe concurrency gate

    # Active Cost & Operational Profile (Defaults to ECONOMY)
    CREDENCE_PROFILE: CostProfile = CostProfile.ECONOMY

    # Multi-Agent & LLM Models (Gemini 3.7 Flash with Thinking)
    CREDENCE_GEMINI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEFAULT_SPECIALIST_MODEL: str = "gemini-3.7-flash"
    DEFAULT_TRIAGE_MODEL: str = "gemini-2.5-flash-lite"
    DEFAULT_THINKING_BUDGET: int = 512
    ESCALATION_THINKING_BUDGET: int = 1024

    # Token Safety Governor & Circuit Breaker
    MAX_TOKENS_PER_HOUR: int = 50_000
    MAX_TOKENS_PER_DAY: int = 300_000
    MAX_DAILY_BUDGET_USD: float = 0.15
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
        cfg = COST_PROFILES.get(self.CREDENCE_PROFILE, COST_PROFILES[CostProfile.ECONOMY]).model_copy()
        if self.MAX_TOKENS_PER_HOUR != 50_000:
            cfg.max_tokens_per_hour = self.MAX_TOKENS_PER_HOUR
        if self.MAX_TOKENS_PER_DAY != 300_000:
            cfg.max_tokens_per_day = self.MAX_TOKENS_PER_DAY
        if self.MAX_DAILY_BUDGET_USD != 0.15:
            cfg.max_daily_budget_usd = self.MAX_DAILY_BUDGET_USD
        return cfg


settings = Settings()
