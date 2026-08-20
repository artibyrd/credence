"""Rate limiting and request governance for Credence Server."""

from __future__ import annotations

import time
from typing import Any, List


class ServerRateLimiter:
    """In-memory rate limiter per tool to defend against token starvation and burst DoS."""

    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0, max_chars: int = 100_000) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_chars = max_chars
        self._calls: List[float] = []

    def check(self, payload_length: int = 0) -> None:
        if payload_length > self.max_chars:
            raise ValueError(
                f"Payload size ({payload_length} chars) exceeds maximum safety limit ({self.max_chars} chars)."
            )
        now = time.monotonic()
        self._calls = [t for t in self._calls if now - t < self.window_seconds]
        if len(self._calls) >= self.max_requests:
            raise RuntimeError(f"Rate limit exceeded ({self.max_requests} requests per {self.window_seconds}s).")
        self._calls.append(now)

    def check_and_record(
        self, client_id: str = "", cost: int = 1, payload_length: int = 0, *args: Any, **kwargs: Any
    ) -> tuple[bool, str]:
        """Check if client is within rate limits and record call."""
        try:
            self.check(payload_length=payload_length)
            return True, "OK"
        except Exception as e:
            return False, str(e)


# Global tool limiters
eval_limiter = ServerRateLimiter(max_requests=30, window_seconds=60.0, max_chars=150_000)
query_limiter = ServerRateLimiter(max_requests=120, window_seconds=60.0, max_chars=20_000)
consensus_limiter = ServerRateLimiter(max_requests=60, window_seconds=60.0, max_chars=500_000)
feed_sync_limiter = ServerRateLimiter(max_requests=20, window_seconds=60.0, max_chars=50_000)
feed_mgmt_limiter = ServerRateLimiter(max_requests=60, window_seconds=60.0, max_chars=10_000)
cost_limiter = ServerRateLimiter(max_requests=120, window_seconds=60.0, max_chars=10_000)
