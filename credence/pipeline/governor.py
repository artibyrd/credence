"""Token Safety Governor, Response Quality Gates & Model Tiering for Credence.

Guarantees:
1. Autonomous audits never exhaust shared API tokens or starve Antigravity dev sessions.
2. In-database token consumption, thinking tokens, and USD cost tracking in SQLite.
3. Automated circuit breaker tripping into offline heuristic mode (QUOTA_PRESERVED).
4. Response quality evaluation with Grounded Citation Ratio and Dynamic Escalation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import settings
from credence.models import TokenUsageRecord
from credence.pipeline.schemas import SpecialistViolationFinding

# Model Pricing Matrix (Price per 1,000,000 tokens in USD)
MODEL_PRICING_PER_MILLION: Dict[str, Dict[str, float]] = {
    "gemini-3.7-flash": {"prompt": 0.15, "completion": 0.60, "thinking": 0.60},
    "gemini-2.5-flash-lite": {"prompt": 0.075, "completion": 0.30, "thinking": 0.30},
    "gemini-2.0-flash": {"prompt": 0.10, "completion": 0.40, "thinking": 0.40},
    "gemini-1.5-pro": {"prompt": 1.25, "completion": 5.00, "thinking": 5.00},
}


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class TokenHeadroomStatus(BaseModel):
    """Real-time token headroom, spend tracking, and circuit breaker status."""

    hourly_tokens_used: int = Field(default=0, description="Tokens consumed in the rolling 1-hour window")
    hourly_tokens_max: int = Field(default=100_000, description="Hourly token limit")
    hourly_headroom_pct: float = Field(default=100.0, description="Remaining hourly headroom percentage (0-100%)")

    daily_tokens_used: int = Field(default=0, description="Tokens consumed in the rolling 24-hour window")
    daily_tokens_max: int = Field(default=1_000_000, description="Daily token limit")
    daily_headroom_pct: float = Field(default=100.0, description="Remaining daily headroom percentage (0-100%)")

    daily_spend_usd: float = Field(default=0.0, description="Total USD cost incurred in last 24 hours")
    daily_budget_usd: float = Field(default=0.50, description="Daily cost budget limit in USD")
    daily_spend_pct: float = Field(default=0.0, description="Percentage of daily spend budget utilized")

    circuit_breaker_tripped: bool = Field(default=False, description="True if quota limits have been reached")
    throttle_active: bool = Field(default=False, description="True if concurrency is throttled (>80% usage)")
    active_api_key_source: str = Field(
        default="NONE_OFFLINE",
        description="Source of active API key (CREDENCE_GEMINI_API_KEY, GEMINI_API_KEY, or NONE_OFFLINE)",
    )


def calculate_call_cost(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    thinking_tokens: int = 0,
) -> float:
    """Calculate estimated USD cost for a Gemini API call based on token counts."""
    pricing = MODEL_PRICING_PER_MILLION.get(
        model_name,
        {"prompt": 0.15, "completion": 0.60, "thinking": 0.60},
    )

    prompt_cost = (prompt_tokens / 1_000_000.0) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000.0) * pricing["completion"]
    thinking_cost = (thinking_tokens / 1_000_000.0) * pricing.get("thinking", pricing["completion"])

    return round(prompt_cost + completion_cost + thinking_cost, 6)


def get_active_api_key() -> Tuple[Optional[str], str]:
    """Retrieve active API key, strictly prioritizing CREDENCE_GEMINI_API_KEY for isolation."""
    if settings.CREDENCE_GEMINI_API_KEY:
        return settings.CREDENCE_GEMINI_API_KEY, "CREDENCE_GEMINI_API_KEY"
    if settings.GEMINI_API_KEY:
        return settings.GEMINI_API_KEY, "GEMINI_API_KEY"
    return None, "NONE_OFFLINE"


async def record_token_usage(
    session: AsyncSession,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    thinking_tokens: int = 0,
    caller: str = "specialist",
    was_escalated: bool = False,
) -> TokenUsageRecord:
    """Persist a token usage record to SQLite and update the rolling budget."""
    total_tokens = prompt_tokens + completion_tokens + thinking_tokens
    cost_usd = calculate_call_cost(model_name, prompt_tokens, completion_tokens, thinking_tokens)

    record = TokenUsageRecord(
        timestamp=utc_now(),
        model_name=model_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        thinking_tokens=thinking_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=cost_usd,
        caller=caller,
        was_escalated=was_escalated,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def get_token_headroom_status(session: AsyncSession) -> TokenHeadroomStatus:
    """Calculate rolling 1-hour and 24-hour token headroom from SQLite records."""
    now = utc_now()
    one_hour_ago = now - timedelta(hours=1)
    twenty_four_hours_ago = now - timedelta(hours=24)

    # 1-Hour window query
    h_stmt = select(TokenUsageRecord).where(TokenUsageRecord.timestamp >= one_hour_ago)
    h_records = (await session.exec(h_stmt)).all()
    hourly_tokens = sum(r.total_tokens for r in h_records)

    # 24-Hour window query
    d_stmt = select(TokenUsageRecord).where(TokenUsageRecord.timestamp >= twenty_four_hours_ago)
    d_records = (await session.exec(d_stmt)).all()
    daily_tokens = sum(r.total_tokens for r in d_records)
    daily_spend = sum(r.estimated_cost_usd for r in d_records)

    # Calculate Headroom Percentages
    hourly_max = settings.MAX_TOKENS_PER_HOUR
    daily_max = settings.MAX_TOKENS_PER_DAY
    daily_budget = settings.MAX_DAILY_BUDGET_USD

    hourly_headroom = max(0.0, min(100.0, 100.0 * (1.0 - (hourly_tokens / max(1, hourly_max)))))
    daily_headroom = max(0.0, min(100.0, 100.0 * (1.0 - (daily_tokens / max(1, daily_max)))))
    daily_spend_pct = min(100.0, 100.0 * (daily_spend / max(0.001, daily_budget)))

    # Determine Circuit Breaker & Throttle States
    circuit_breaker_tripped = False
    throttle_active = False

    if settings.ENABLE_CIRCUIT_BREAKER:
        if hourly_tokens >= hourly_max or daily_tokens >= daily_max or daily_spend >= daily_budget:
            circuit_breaker_tripped = True
        elif hourly_headroom < 20.0 or daily_headroom < 20.0 or daily_spend_pct > 80.0:
            throttle_active = True

    _, key_source = get_active_api_key()

    return TokenHeadroomStatus(
        hourly_tokens_used=hourly_tokens,
        hourly_tokens_max=hourly_max,
        hourly_headroom_pct=round(hourly_headroom, 1),
        daily_tokens_used=daily_tokens,
        daily_tokens_max=daily_max,
        daily_headroom_pct=round(daily_headroom, 1),
        daily_spend_usd=round(daily_spend, 4),
        daily_budget_usd=daily_budget,
        daily_spend_pct=round(daily_spend_pct, 1),
        circuit_breaker_tripped=circuit_breaker_tripped,
        throttle_active=throttle_active,
        active_api_key_source=key_source,
    )


async def check_budget_before_call(
    session: AsyncSession,
    estimated_tokens: int = 2000,
) -> Tuple[bool, str]:
    """Check whether token budget permits an LLM call or if circuit breaker should trip."""
    headroom = await get_token_headroom_status(session)

    if headroom.circuit_breaker_tripped:
        return False, "Circuit breaker TRIPPED: Token or USD spend budget exceeded. Operating in QUOTA_PRESERVED mode."

    if headroom.hourly_tokens_used + estimated_tokens > headroom.hourly_tokens_max:
        return (
            False,
            "Hourly token safety ceiling reached. Falling back to offline heuristics to protect developer pairing.",
        )

    if headroom.daily_tokens_used + estimated_tokens > headroom.daily_tokens_max:
        return False, "Daily token limit reached. Falling back to offline heuristics to protect developer pairing."

    return True, "BUDGET_AVAILABLE"


def evaluate_quality_and_should_escalate(
    violations: List[SpecialistViolationFinding],
    confidence: float,
    suspicion_score: float,
) -> Tuple[bool, str]:
    """Evaluate response quality against Grounded Citation Ratio and ambiguity margin.

    Returns: (should_escalate: bool, reason: str)
    """
    total_findings = len(violations)
    if total_findings > 0:
        grounded_count = sum(1 for v in violations if v.is_grounded)
        grounded_ratio = grounded_count / total_findings

        # Quality Gate 1: Grounded citation ratio below 75%
        if grounded_ratio < 0.75:
            return True, f"Low grounded citation ratio ({grounded_ratio * 100:.0f}% < 75%). Potential hallucination."

    # Quality Gate 2: Low evaluator confidence
    if confidence < 0.80:
        return True, f"Subagent confidence low ({confidence:.2f} < 0.80). Escalating for secondary verification."

    # Quality Gate 3: High-uncertainty decision boundary (between clean and suspicious)
    if 12.0 <= suspicion_score <= 18.0:
        return True, f"Suspicion score on ambiguous decision boundary ({suspicion_score:.1f}). Escalating for tiebreak."

    return False, "QUALITY_VERIFIED"
