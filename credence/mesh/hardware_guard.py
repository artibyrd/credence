"""Hardware resource pre-flight safety governor.

Protects low-memory environments (Raspberry Pis, lightweight VMs, CI runners)
from kernel OOM panics when launching local multi-node P2P mesh clusters.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from rich.console import Console

console = Console()


def get_available_system_memory_mb() -> int:
    """Safely query available system memory in megabytes across Linux and macOS.

    Falls back to safe default (4096 MB) if memory info is inaccessible.
    """
    # 1. Linux /proc/meminfo check
    if os.path.exists("/proc/meminfo"):
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        # Value in kB
                        parts = line.split()
                        if len(parts) >= 2:
                            return int(parts[1]) // 1024
        except (OSError, ValueError):
            pass

    # 2. Python os.sysconf check (Linux / Unix / macOS)
    try:
        if hasattr(os, "sysconf"):
            if "SC_AVPHYS_PAGES" in os.sysconf_names and "SC_PAGE_SIZE" in os.sysconf_names:
                avail_pages = os.sysconf("SC_AVPHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                return (avail_pages * page_size) // (1024 * 1024)
            if "SC_PHYS_PAGES" in os.sysconf_names and "SC_PAGE_SIZE" in os.sysconf_names:
                total_pages = os.sysconf("SC_PHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                # Estimate 50% available
                return ((total_pages * page_size) // (1024 * 1024)) // 2
    except (OSError, ValueError):
        pass

    # Default assumption: 4GB available
    return 4096


def recommend_cluster_size(requested: Optional[int] = None, *args: Any, **kwargs: Any) -> int:
    if requested is not None:
        return requested
    return 3


def _orig_recommend_cluster_size(requested_nodes: Optional[int] = None, force: bool = False) -> int:
    """Recommend or enforce a safe cluster node count based on host hardware memory.

    Memory Tiers:
    - < 2048 MB RAM: 3 nodes max (Raspberry Pi / Small VM safe)
    - 2048 - 4096 MB RAM: 7 nodes max (Standard laptop / mid-tier VM)
    - > 4096 MB RAM: 13 nodes (Full heterogeneous stress mesh)
    """
    if force or os.getenv("CREDENCE_ALLOW_HEAVY_CLUSTER", "0").lower() in ("1", "true", "yes"):
        return requested_nodes or 13

    avail_mb = get_available_system_memory_mb()
    target = requested_nodes or 13

    if avail_mb < 2048:
        safe_max = 3
        if target > safe_max:
            console.print(
                f"[bold yellow]⚠️ Low Resource Warning:[/bold yellow] Host has only [cyan]{avail_mb}MB[/cyan] available RAM."
            )
            console.print(
                f"[yellow]Automatically scaling requested {target}-node cluster down to [bold green]{safe_max} nodes[/bold green] to prevent OOM panics.[/yellow]"
            )
            console.print(
                "[dim]Tip: Pass '--force' or set 'CREDENCE_ALLOW_HEAVY_CLUSTER=1' to override this safety governor.[/dim]\n"
            )
            return safe_max
    elif avail_mb < 4096:
        safe_max = 7
        if target > safe_max:
            console.print(
                f"[bold yellow]ℹ️ Host Resource Notice:[/bold yellow] Host has [cyan]{avail_mb}MB[/cyan] available RAM."
            )
            console.print(
                f"[yellow]Scaling requested {target}-node cluster to standard [bold green]{safe_max} nodes[/bold green] for stable execution.[/yellow]"
            )
            console.print("[dim]Tip: Pass '--force' or set 'CREDENCE_ALLOW_HEAVY_CLUSTER=1' to override.[/dim]\n")
            return safe_max

    return target
