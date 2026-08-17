"""5-Factor Epistemic Node Quality Engine for Credence P2P Mesh Network.

Calculates composite node quality (Q_i) across:
1. Uptime & Latency (U_i, 25% weight)
2. Robust Consensus Concordance (C_i, 30% weight)
3. Quote Grounding Precision (G_i, 25% weight)
4. Taxonomy Version Currency (T_i, 10% weight)
5. Key Longevity & Sybil Damping (K_i, 10% weight)

Formula:
Q_i = 0.25 * U_i + 0.30 * C_i + 0.25 * G_i + 0.10 * T_i + 0.10 * K_i
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NodeMetrics(BaseModel):
    """Raw observed operational and epistemic metrics for a mesh node."""

    node_pubkey: str = Field(..., description="Ed25519 public key hex of the node")
    node_alias: str = Field(default="credence-node", description="Human-readable node label")
    ws_url: str = Field(..., description="P2P WebSocket URL")
    region: str = Field(default="us-central1", description="Node geographic region")
    first_seen: datetime = Field(default_factory=utc_now, description="First recorded appearance")
    last_seen: datetime = Field(default_factory=utc_now, description="Last successful communication")
    total_heartbeats_sent: int = Field(default=0, ge=0)
    successful_heartbeats: int = Field(default=0, ge=0)
    average_latency_ms: float = Field(default=100.0, ge=0.0)
    total_attestations_evaluated: int = Field(default=0, ge=0)
    median_score_deviations_sum: float = Field(default=0.0, ge=0.0)
    grounded_citations_count: int = Field(default=0, ge=0)
    total_citations_count: int = Field(default=0, ge=0)
    has_valid_catalog_hashes: bool = Field(default=True)
    supported_catalogs: Dict[str, str] = Field(default_factory=dict)


class NodeQualityScore(BaseModel):
    """Detailed breakdown of calculated 5-factor quality scores for a node."""

    node_pubkey: str
    node_alias: str
    ws_url: str
    region: str
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Composite Q_i score")
    uptime_factor: float = Field(..., ge=0.0, le=1.0, description="U_i score")
    concordance_factor: float = Field(..., ge=0.0, le=1.0, description="C_i score")
    grounding_factor: float = Field(..., ge=0.0, le=1.0, description="G_i score")
    taxonomy_factor: float = Field(..., ge=0.0, le=1.0, description="T_i score")
    longevity_factor: float = Field(..., ge=0.0, le=1.0, description="K_i score")
    is_seed_candidate: bool = Field(default=False, description="True if Q_i >= 0.85")


def calculate_node_quality(
    metrics: NodeMetrics,
    now: Optional[datetime] = None,
) -> NodeQualityScore:
    """Calculate the 5-factor composite epistemic quality score (Q_i)."""
    current_time = now or datetime.now(timezone.utc)

    # 1. Uptime & Latency Factor (U_i) - 25%
    if metrics.total_heartbeats_sent > 0:
        heartbeat_ratio = metrics.successful_heartbeats / max(1, metrics.total_heartbeats_sent)
    else:
        heartbeat_ratio = 1.0  # Default initial prior for new healthy connections

    latency_factor = max(0.0, 1.0 - min(metrics.average_latency_ms, 1000.0) / 1000.0)
    u_i = min(1.0, max(0.0, heartbeat_ratio * (0.7 + 0.3 * latency_factor)))

    # 2. Consensus Concordance Factor (C_i) - 30%
    if metrics.total_attestations_evaluated > 0:
        avg_deviation = metrics.median_score_deviations_sum / metrics.total_attestations_evaluated
        c_i = max(0.0, 1.0 - (avg_deviation / 50.0))
    else:
        c_i = 0.85  # Neutral default prior before evaluations

    # 3. Quote Grounding Precision Factor (G_i) - 25%
    if metrics.total_citations_count > 0:
        g_i = min(1.0, max(0.0, metrics.grounded_citations_count / metrics.total_citations_count))
    else:
        g_i = 0.90  # Neutral default prior

    # 4. Taxonomy Catalog Currency (T_i) - 10%
    t_i = 1.0 if metrics.has_valid_catalog_hashes else 0.0

    # 5. Key Longevity & Sybil Damping (K_i) - 10%
    days_active = max(0.0, (current_time - metrics.first_seen).total_seconds() / 86400.0)
    k_i = min(1.0, max(0.0, math.log(1.0 + days_active) / math.log(1.0 + 90.0)))

    # Composite Score Calculation (Weights: 0.25, 0.30, 0.25, 0.10, 0.10)
    q_i = (0.25 * u_i) + (0.30 * c_i) + (0.25 * g_i) + (0.10 * t_i) + (0.10 * k_i)
    q_i = round(min(1.0, max(0.0, q_i)), 4)

    is_candidate = q_i >= 0.85 and u_i >= 0.80 and g_i >= 0.80 and metrics.has_valid_catalog_hashes

    return NodeQualityScore(
        node_pubkey=metrics.node_pubkey,
        node_alias=metrics.node_alias,
        ws_url=metrics.ws_url,
        region=metrics.region,
        quality_score=q_i,
        uptime_factor=round(u_i, 4),
        concordance_factor=round(c_i, 4),
        grounding_factor=round(g_i, 4),
        taxonomy_factor=round(t_i, 4),
        longevity_factor=round(k_i, 4),
        is_seed_candidate=is_candidate,
    )


def rank_nodes(
    metrics_list: List[NodeMetrics],
    min_score: float = 0.85,
    top_k: int = 20,
    now: Optional[datetime] = None,
) -> List[NodeQualityScore]:
    """Calculate quality scores for a list of node metrics and return ranked seed candidates."""
    scores = [calculate_node_quality(m, now=now) for m in metrics_list]
    # Sort descending by composite score, then by uptime
    scores.sort(key=lambda s: (s.quality_score, s.uptime_factor), reverse=True)
    return scores[:top_k]
