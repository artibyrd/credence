"""Hardware resource pre-flight safety governor.

Protects low-memory environments (Raspberry Pis, lightweight VMs, CI runners)
from kernel OOM panics when launching local multi-node P2P mesh clusters.
"""

from __future__ import annotations

import math
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


def recommend_cluster_size(requested: Optional[int] = None, force: bool = False, *args: Any, **kwargs: Any) -> int:
    return _orig_recommend_cluster_size(requested_nodes=requested, force=force)


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


def compute_max_mesh_peers(
    profile: Optional[Any] = None,
    available_memory_mb: Optional[int] = None,
    cluster_size: Optional[int] = None,
    nofile_soft_limit: Optional[int] = None,
) -> tuple[int, int, str]:
    """Dynamically compute optimal P2P mesh peer capacity, target degree, and hunger mode.

    Derives dynamic bounds from:
    1. Operational Cost Profile Hunger Preset (LEAN, ACTIVE, VORACIOUS)
    2. OS File Descriptor Soft Limits (RLIMIT_NOFILE, allocating <= 40% to P2P sockets)
    3. Available Host RAM Headroom (<1GB -> 12, 1-4GB -> 48, >4GB -> 256)
    4. Watts-Strogatz Small-World Topology Bound (k >= max(2, ceil(2 * ln(N))))

    Returns:
        Tuple of (max_peer_capacity, target_peer_degree, peer_hunger_mode)
    """
    from credence.config import COST_PROFILES, CostProfile, settings

    raw_prof = profile or getattr(settings, "CREDENCE_PROFILE", CostProfile.BALANCED)
    if isinstance(raw_prof, str):
        try:
            active_prof = CostProfile(raw_prof.lower())
        except ValueError:
            active_prof = CostProfile.BALANCED
    elif isinstance(raw_prof, CostProfile):
        active_prof = raw_prof
    else:
        active_prof = CostProfile.BALANCED

    prof_cfg = COST_PROFILES.get(active_prof, COST_PROFILES[CostProfile.BALANCED])

    # 1. Profile preset limits
    profile_cap = prof_cfg.max_peer_connections
    target_degree = prof_cfg.target_peer_degree
    hunger_mode = prof_cfg.peer_hunger

    # 2. File descriptor headroom
    if nofile_soft_limit is None:
        try:
            import resource

            soft_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
            nofile_soft_limit = soft_limit
        except (ImportError, Exception):
            nofile_soft_limit = 1024

    # Reserve 60% of FDs for SQLite WAL, HTTP REST APIs, and runtime logging
    fd_capacity = max(4, int(nofile_soft_limit * 0.40))

    # 3. Available system memory tier
    avail_mb = available_memory_mb if available_memory_mb is not None else get_available_system_memory_mb()
    if avail_mb < 1024:
        mem_capacity = 12
    elif avail_mb < 4096:
        mem_capacity = 48
    else:
        mem_capacity = 256

    # Dynamic maximum peers is the conservative intersection of all resource constraints
    dynamic_max = min(profile_cap, fd_capacity, mem_capacity)

    # 4. Watts-Strogatz graph topology lower bound
    if cluster_size and cluster_size > 1:
        topo_min = max(2, math.ceil(2 * math.log(cluster_size)))
        target_degree = max(target_degree, topo_min)
        dynamic_max = max(dynamic_max, target_degree)

    return dynamic_max, target_degree, hunger_mode
