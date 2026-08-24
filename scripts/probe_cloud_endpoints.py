#!/usr/bin/env python3
"""Cloud Run Endpoint Health & Latency Probing Utility."""

from __future__ import annotations

import os
import sys
import time
from typing import List, Tuple

import httpx

ENDPOINTS: List[Tuple[str, str]] = [
    ("/health", "GET"),
    ("/api/health", "GET"),
    ("/sse", "STREAM"),
    ("/api/cost/telemetry", "GET"),
    ("/api/reports?limit=3", "GET"),
    ("/api/sifter/status", "GET"),
    ("/api/feeds/stream?limit=3", "GET"),
]


def probe_endpoints(base_url: str) -> None:
    base = base_url.rstrip("/")
    with httpx.Client() as client:
        for path, method in ENDPOINTS:
            t0 = time.perf_counter()
            try:
                if method == "STREAM":
                    with client.stream("GET", base + path, timeout=15.0) as r:
                        dt = (time.perf_counter() - t0) * 1000
                        icon = "🟢" if r.status_code == 200 else "🔴"
                        print(f"{icon} {r.status_code} [{method}] {path.ljust(28)} ({round(dt, 1)}ms)")
                else:
                    r = client.request(method, base + path, timeout=15.0)
                    dt = (time.perf_counter() - t0) * 1000
                    icon = "🟢" if r.status_code == 200 else ("🟡" if r.status_code < 500 else "🔴")
                    print(f"{icon} {r.status_code} [{method}] {path.ljust(28)} ({round(dt, 1)}ms)")
            except Exception as e:
                print(f"🔴 ERR [{method}] {path.ljust(28)} ({e})")


def main() -> None:
    target_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.environ.get("TARGET_URL", "https://credence-server-663899237633.us-central1.run.app")
    )
    probe_endpoints(target_url)


if __name__ == "__main__":
    main()
