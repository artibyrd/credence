"""Hermetic unit tests for Epistemic Merit edge cases.

Covers:
- $N=1$ solitary genesis node with 0 heartbeats / 0 attestations
- $N=0$ empty state initialization
- $N=2$ duel with deterministic 4-level tie-breaking
- 24-hour half-life uptime decay grace period (operator maintenance)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.mesh.merit import (
    calculate_half_life_uptime,
    get_leaderboard,
    get_local_node_merit,
)
from credence.models import PeerMetricRecord


@pytest.mark.asyncio
async def test_solitary_genesis_node_defaults(db_session: AsyncSession) -> None:
    """Verify solitary $N=1$ genesis node gets healthy priors and STANDARD traffic class."""
    now = datetime.now(timezone.utc)
    metric = PeerMetricRecord(
        node_pubkey="a" * 64,
        node_alias="local-genesis-node",
        ws_url="ws://127.0.0.1:8765",
        first_seen=now - timedelta(hours=2),
        last_seen=now,
        total_heartbeats_sent=0,
        successful_heartbeats=0,
        average_latency_ms=0.0,
        total_attestations_evaluated=0,
        median_score_deviations_sum=0.0,
        grounded_citations_count=0,
        total_citations_count=0,
        has_valid_catalog_hashes=True,
        traffic_class="STANDARD",
        tokens_seeded_count=0,
        attestations_seeded_count=0,
        galileo_discoveries_count=0,
    )
    db_session.add(metric)
    await db_session.commit()

    card = await get_local_node_merit(db_session, local_pubkey="a" * 64)
    assert card.node_alias == "local-genesis-node"
    assert card.tier == "SPROUT"
    assert card.traffic_class == "STANDARD"
    # Mathematical priors must ensure non-zero quality and no division by zero
    assert card.quality_score > 0.0
    assert card.uptime_ratio == 1.0
    assert card.rank_overall == 1
    assert card.total_nodes == 1


@pytest.mark.asyncio
async def test_empty_database_merit_fallback(db_session: AsyncSession) -> None:
    """Verify empty database returns a default fallback card with rank 1."""
    card = await get_local_node_merit(db_session, local_pubkey="non_existent_key")
    assert card.node_alias.startswith("local-node")
    assert card.tier == "SPROUT"
    assert card.quality_score > 0.0
    assert card.traffic_class == "STANDARD"

    leaderboard = await get_leaderboard(db_session, category="quality")
    assert len(leaderboard) == 1
    assert leaderboard[0].rank == 1


@pytest.mark.asyncio
async def test_deterministic_tie_breaking(db_session: AsyncSession) -> None:
    """Verify 4-level deterministic tie-breaking: score -> tokens_seeded -> first_seen -> pubkey."""
    now = datetime.now(timezone.utc)
    # Node 1: quality 0.80, tokens 5000, first_seen 10 days ago
    n1 = PeerMetricRecord(
        node_pubkey="bb" * 32,
        node_alias="node-beta",
        ws_url="ws://127.0.0.1:8766",
        first_seen=now - timedelta(days=10),
        last_seen=now,
        total_heartbeats_sent=100,
        successful_heartbeats=80,
        total_attestations_evaluated=10,
        grounded_citations_count=8,
        total_citations_count=10,
        has_valid_catalog_hashes=True,
        traffic_class="STANDARD",
        tokens_seeded_count=5000,
    )
    # Node 2: identical quality 0.80, but seeded 15000 tokens (wins tie-breaker)
    n2 = PeerMetricRecord(
        node_pubkey="aa" * 32,
        node_alias="node-alpha",
        ws_url="ws://127.0.0.1:8767",
        first_seen=now - timedelta(days=5),
        last_seen=now,
        total_heartbeats_sent=100,
        successful_heartbeats=80,
        total_attestations_evaluated=10,
        grounded_citations_count=8,
        total_citations_count=10,
        has_valid_catalog_hashes=True,
        traffic_class="STANDARD",
        tokens_seeded_count=15000,
    )
    db_session.add_all([n1, n2])
    await db_session.commit()

    lb = await get_leaderboard(db_session, category="quality")
    assert len(lb) == 2
    # Node 2 must rank higher due to tokens_seeded tie-breaker
    assert lb[0].node_alias == "node-alpha"
    assert lb[0].rank == 1
    assert lb[1].node_alias == "node-beta"
    assert lb[1].rank == 2


def test_operator_half_life_uptime_decay() -> None:
    """Verify half-life uptime decay function ($\tau=24h$)."""
    now = datetime.now(timezone.utc)
    # 0 downtime: full raw uptime
    u0 = calculate_half_life_uptime(
        successful=99,
        total=100,
        last_seen=now,
        now=now,
        half_life_hours=24.0,
    )
    assert u0 == 0.99

    # 1h downtime (within 2h grace period): no decay
    u_grace = calculate_half_life_uptime(
        successful=99,
        total=100,
        last_seen=now - timedelta(hours=1),
        now=now,
        half_life_hours=24.0,
    )
    assert u_grace == 0.99

    # 26h downtime (2h grace + 24h half-life): decayed by ~50%
    u_halved = calculate_half_life_uptime(
        successful=90,
        total=100,
        last_seen=now - timedelta(hours=26),
        now=now,
        half_life_hours=24.0,
    )
    assert pytest.approx(u_halved, rel=1e-2) == 0.45
