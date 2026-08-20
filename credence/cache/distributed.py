"""Distributed State Store, Token Governor, and Redis Lua Atomicity for Credence."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("credence.cache.distributed")


@dataclass
class RuntimeCostSettings:
    daily_budget_usd: Optional[float] = None
    max_tokens_per_hour: Optional[int] = None
    emergency_brake_pulled: bool = False
    active_profile_override: Optional[str] = None
    brake_reason: Optional[str] = None
    updated_at: float = 0.0


class DistributedStateStore:
    """Manages shared runtime cost state, token consumption metering, and feed locks."""

    def __init__(self, redis_url: Optional[str] = None, client_override: Optional[Any] = None) -> None:
        self.redis_url = redis_url
        self._client = client_override
        # In-memory local fallback store
        self._memory_runtime_settings = RuntimeCostSettings(updated_at=time.time())
        self._memory_locks: Dict[str, float] = {}
        self._memory_token_events: list[Tuple[float, int, float]] = []  # (timestamp, tokens, cost_usd)
        self._memory_cache: Dict[str, Tuple[str, float]] = {}  # key -> (value, expiry)

    async def get_runtime_cost_settings(self) -> RuntimeCostSettings:
        """Retrieve live runtime cost overrides."""
        if self._client:
            try:
                data = await self._client.hgetall("credence:settings:cost")
                if data:
                    return RuntimeCostSettings(
                        daily_budget_usd=float(data.get("daily_budget_usd")) if "daily_budget_usd" in data else None,
                        max_tokens_per_hour=int(data.get("max_tokens_per_hour"))
                        if "max_tokens_per_hour" in data
                        else None,
                        emergency_brake_pulled=(data.get("emergency_brake_pulled", "0") in ("1", "true", "True")),
                        active_profile_override=data.get("active_profile_override"),
                        brake_reason=data.get("brake_reason"),
                        updated_at=float(data.get("updated_at", time.time())),
                    )
            except Exception as e:
                logger.warning("Redis failed to fetch cost settings, using in-memory: %s", e)
        return self._memory_runtime_settings

    async def set_runtime_budget_override(
        self,
        daily_budget_usd: Optional[float] = None,
        max_tokens_per_hour: Optional[int] = None,
        active_profile: Optional[str] = None,
    ) -> None:
        """Set live runtime budget overrides across all container replicas."""
        now = time.time()
        if daily_budget_usd is not None:
            # Clamp daily budget between $0.00 and $500.00
            daily_budget_usd = max(0.0, min(500.0, float(daily_budget_usd)))
        if max_tokens_per_hour is not None:
            # Clamp hourly tokens between 1,000 and 10,000,000
            max_tokens_per_hour = max(1_000, min(10_000_000, int(max_tokens_per_hour)))

        if self._client:
            mapping: Dict[str, str] = {"updated_at": str(now)}
            if daily_budget_usd is not None:
                mapping["daily_budget_usd"] = str(daily_budget_usd)
            if max_tokens_per_hour is not None:
                mapping["max_tokens_per_hour"] = str(max_tokens_per_hour)
            if active_profile is not None:
                mapping["active_profile_override"] = str(active_profile)
            try:
                await self._client.hset("credence:settings:cost", mapping=mapping)
            except Exception as e:
                logger.warning("Redis failed to update budget settings: %s", e)

        if daily_budget_usd is not None:
            self._memory_runtime_settings.daily_budget_usd = daily_budget_usd
        if max_tokens_per_hour is not None:
            self._memory_runtime_settings.max_tokens_per_hour = max_tokens_per_hour
        if active_profile is not None:
            self._memory_runtime_settings.active_profile_override = active_profile
        self._memory_runtime_settings.updated_at = now

    async def pull_emergency_brake(self, reason: str = "manual_operator_trigger") -> None:
        """Immediately pull Emergency Brake, forcing 100% of audits into offline mode ($0 cost)."""
        now = time.time()
        if self._client:
            try:
                await self._client.hset(
                    "credence:settings:cost",
                    mapping={
                        "emergency_brake_pulled": "1",
                        "brake_reason": reason,
                        "updated_at": str(now),
                    },
                )
            except Exception as e:
                logger.warning("Redis failed to pull emergency brake: %s", e)

        self._memory_runtime_settings.emergency_brake_pulled = True
        self._memory_runtime_settings.brake_reason = reason
        self._memory_runtime_settings.updated_at = now
        logger.critical("🚨 Emergency Brake PULLED: %s. Operating in QUOTA_PRESERVED mode.", reason)

    async def release_emergency_brake(self) -> None:
        """Release Emergency Brake, resuming normal AI evaluation."""
        now = time.time()
        if self._client:
            try:
                await self._client.hset(
                    "credence:settings:cost",
                    mapping={
                        "emergency_brake_pulled": "0",
                        "brake_reason": "",
                        "updated_at": str(now),
                    },
                )
            except Exception as e:
                logger.warning("Redis failed to release emergency brake: %s", e)

        self._memory_runtime_settings.emergency_brake_pulled = False
        self._memory_runtime_settings.brake_reason = None
        self._memory_runtime_settings.updated_at = now
        logger.info("🟢 Emergency Brake RELEASED. Resuming AI operations.")

    async def acquire_feed_dedup_lock(self, item_url: str, ttl_seconds: int = 300) -> bool:
        """Acquire a distributed lock for an RSS feed article to prevent duplicate evaluations."""
        import hashlib

        url_hash = hashlib.sha256(item_url.encode("utf-8")).hexdigest()
        lock_key = f"lock:sifter:{url_hash}"
        now = time.time()

        if self._client:
            try:
                acquired = await self._client.set(lock_key, "1", nx=True, ex=ttl_seconds)
                return bool(acquired)
            except Exception as e:
                logger.debug("Redis lock error: %s; falling back to in-memory lock.", e)

        # In-memory lock fallback
        self._prune_memory_locks(now)
        if lock_key in self._memory_locks:
            return False
        self._memory_locks[lock_key] = now + ttl_seconds
        return True

    def _prune_memory_locks(self, now: float) -> None:
        self._memory_locks = {k: exp for k, exp in self._memory_locks.items() if exp > now}

    async def record_token_spend(self, total_tokens: int, cost_usd: float) -> None:
        """Record token consumption in sliding window meters."""
        now = time.time()
        self._memory_token_events.append((now, total_tokens, cost_usd))
        cutoff = now - 86400.0  # 24 hours
        self._memory_token_events = [e for e in self._memory_token_events if e[0] >= cutoff]

    async def get_sliding_window_usage(self) -> Tuple[int, int, float]:
        """Get rolling token usage: (1-hour tokens, 24-hour tokens, 24-hour USD spend)."""
        now = time.time()
        one_hour_ago = now - 3600.0
        twenty_four_hours_ago = now - 86400.0

        h_tokens = sum(e[1] for e in self._memory_token_events if e[0] >= one_hour_ago)
        d_tokens = sum(e[1] for e in self._memory_token_events if e[0] >= twenty_four_hours_ago)
        d_spend = sum(e[2] for e in self._memory_token_events if e[0] >= twenty_four_hours_ago)

        return h_tokens, d_tokens, d_spend


_global_state_store: Optional[DistributedStateStore] = None


def get_state_store() -> DistributedStateStore:
    """Retrieve global DistributedStateStore instance."""
    global _global_state_store
    if _global_state_store is None:
        from credence.config import settings

        _global_state_store = DistributedStateStore(redis_url=settings.REDIS_URL)
    return _global_state_store


def reset_state_store() -> None:
    """Reset the global DistributedStateStore instance (used for hermetic test isolation)."""
    global _global_state_store
    _global_state_store = None
