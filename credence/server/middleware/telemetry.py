"""Interface Telemetry Loopback Protocol (ITLP-v1) Server Telemetry Tracker."""

from __future__ import annotations

import resource
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Optional


@dataclass
class TelemetryEvent:
    timestamp: float
    status_code: int
    path: str
    duration_ms: float
    error_message: Optional[str] = None


class ServerTelemetryTracker:
    """In-memory rolling telemetry tracker for Interface Telemetry Loopback (ITLP-v1)."""

    def __init__(self, window_seconds: float = 300.0) -> None:
        self.window_seconds = window_seconds
        self.start_time: float = time.time()
        self._events: Deque[TelemetryEvent] = deque()

    def record_request(
        self, status_code: int, path: str, duration_ms: float, error_message: Optional[str] = None
    ) -> None:
        now = time.time()
        event = TelemetryEvent(
            timestamp=now,
            status_code=status_code,
            path=path,
            duration_ms=duration_ms,
            error_message=error_message,
        )
        self._events.append(event)
        self._prune(now)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._events and self._events[0].timestamp < cutoff:
            self._events.popleft()

    def reset(self) -> None:
        """Reset events (useful for hermetic tests)."""
        self._events.clear()
        self.start_time = time.time()

    def get_snapshot(self) -> dict[str, Any]:
        now = time.time()
        self._prune(now)

        count_2xx = sum(1 for e in self._events if 200 <= e.status_code < 300)
        count_3xx = sum(1 for e in self._events if 300 <= e.status_code < 400)
        count_4xx = sum(1 for e in self._events if 400 <= e.status_code < 500)
        count_5xx = sum(1 for e in self._events if e.status_code >= 500)
        total = len(self._events)

        latencies = [e.duration_ms for e in self._events]
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.5)] if latencies else 0.0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

        try:
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            memory_mb = round(rusage.ru_maxrss / 1024.0, 2)
        except Exception:
            memory_mb = 0.0

        active_alerts: list[dict[str, Any]] = []
        status = "healthy"

        if count_5xx >= 5:
            active_alerts.append(
                {
                    "id": "alert_5xx_spike",
                    "severity": "CRITICAL",
                    "message": f"Elevated 5xx error rate detected: {count_5xx} server errors in 5min window.",
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                }
            )
            status = "degraded"

        recent_errors = [
            {
                "timestamp": time.strftime("%H:%M:%S", time.gmtime(e.timestamp)),
                "path": e.path,
                "status_code": e.status_code,
                "error_message": e.error_message or "Unknown server error",
            }
            for e in reversed(self._events)
            if e.status_code >= 400
        ][:10]

        return {
            "uptime_seconds": int(now - self.start_time),
            "status": status,
            "memory_mb": memory_mb,
            "request_counts": {
                "total": total,
                "2xx": count_2xx,
                "3xx": count_3xx,
                "4xx": count_4xx,
                "5xx": count_5xx,
            },
            "latencies_ms": {
                "p50": round(p50, 1),
                "p95": round(p95, 1),
            },
            "active_alerts": active_alerts,
            "recent_errors": recent_errors,
        }


global_telemetry = ServerTelemetryTracker()
