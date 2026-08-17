"""Bayesian Consensus Engine & Outlier Detection for Credence Mesh.

Aggregates multiple Ed25519-signed peer audit attestations for the same
content SHA-256, computes weighted Bayesian consensus suspicion scores,
and identifies / filters out adversarial or compromised rogue nodes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from credence.pipeline.schemas import AuditReport
from credence.pipeline.scoring import classify_verdict


class PeerAttestationWeight(BaseModel):
    """Calculated weight and credibility metric for an individual peer attestation."""

    node_pubkey: str
    suspicion_score: float
    confidence: float
    grounded_ratio: float
    effective_weight: float
    is_outlier: bool = False


class ConsensusVerdict(BaseModel):
    """Consolidated Bayesian Consensus Verdict across multiple decentralized nodes."""

    content_sha256: str
    consensus_score: float = Field(..., ge=0.0, le=100.0, description="Confidence-weighted consensus suspicion score")
    classification: str = Field(..., description="Consensus verdict classification band")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Aggregate network confidence")
    node_count: int = Field(..., description="Total number of peer attestations aggregated")
    agreement_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of nodes agreeing with verdict band")
    is_satire_consensus: bool = Field(default=False)
    is_byzantine_resilient: bool = Field(default=True, description="True if agreement meets or exceeds 66% threshold")
    outlier_nodes: List[str] = Field(default_factory=list, description="Public keys of detected divergent/rogue nodes")
    peer_weights: List[PeerAttestationWeight] = Field(default_factory=list)


class BayesianConsensusAggregator:
    """Consensus aggregator calculating weighted Bayesian agreement across peer nodes."""

    def __init__(self, consensus_threshold: float = 0.66, outlier_delta_threshold: float = 25.0) -> None:
        self.consensus_threshold = consensus_threshold
        self.outlier_delta_threshold = outlier_delta_threshold

    def calculate_consensus(
        self,
        attestations: List[AuditReport],
        node_reputations: Optional[Dict[str, float]] = None,
    ) -> Optional[ConsensusVerdict]:
        """Calculate weighted Bayesian consensus across a collection of signed attestations."""
        if not attestations:
            return None

        content_sha256 = attestations[0].content_sha256
        reputations = node_reputations or {}

        # Step 1: Calculate raw peer weights
        peer_meta: List[Dict[str, Any]] = []
        for att in attestations:
            pubkey = att.node_pubkey or "anonymous"
            rep = reputations.get(pubkey, 1.0)

            # Grounded citation ratio
            if att.violations:
                grounded_count = sum(1 for v in att.violations if v.is_grounded)
                grounded_ratio = grounded_count / len(att.violations)
            else:
                grounded_ratio = 1.0

            # Weight = confidence * reputation * grounded_ratio
            effective_weight = max(0.01, att.confidence_score * rep * (0.5 + 0.5 * grounded_ratio))

            peer_meta.append(
                {
                    "att": att,
                    "pubkey": pubkey,
                    "score": att.suspicion_score,
                    "confidence": att.confidence_score,
                    "grounded_ratio": grounded_ratio,
                    "weight": effective_weight,
                    "is_satire": att.is_satire,
                }
            )

        # Step 2: Reference Median Score (Robust to Byzantine Skew)
        sorted_scores = sorted(p["score"] for p in peer_meta)
        mid = len(sorted_scores) // 2
        median_score = (
            (sorted_scores[mid - 1] + sorted_scores[mid]) / 2.0
            if len(sorted_scores) % 2 == 0
            else float(sorted_scores[mid])
        )

        # Step 3: Outlier Detection (deviates > outlier_delta_threshold from robust median)
        outlier_pubkeys: List[str] = []
        valid_peers: List[Dict[str, Any]] = []

        for p in peer_meta:
            delta = abs(p["score"] - median_score)
            if delta > self.outlier_delta_threshold and len(peer_meta) >= 3:
                p["is_outlier"] = True
                outlier_pubkeys.append(p["pubkey"])
            else:
                p["is_outlier"] = False
                valid_peers.append(p)

        # Recalculate without rogue outliers if valid peers remain
        active_peers = valid_peers if valid_peers else peer_meta
        active_total_weight = sum(p["weight"] for p in active_peers)
        consensus_score = sum(p["score"] * p["weight"] for p in active_peers) / active_total_weight
        consensus_score = round(max(0.0, min(100.0, consensus_score)), 1)

        # Step 4: Satire consensus
        satire_votes = sum(1 for p in active_peers if p["is_satire"])
        is_satire_consensus = satire_votes > (len(active_peers) / 2)

        if is_satire_consensus:
            consensus_score = 0.0
            classification = "SATIRE_PARODY"
        else:
            classification = classify_verdict(consensus_score, is_satire=False)

        # Step 5: Calculate agreement percentage
        matching_band_count = sum(1 for p in active_peers if p["att"].classification == classification)
        agreement_pct = round((matching_band_count / len(active_peers)) * 100.0, 1)
        is_byzantine_resilient = (agreement_pct / 100.0) >= self.consensus_threshold

        # Step 6: Aggregate network confidence
        avg_confidence = sum(p["confidence"] * p["weight"] for p in active_peers) / active_total_weight

        # Format weights list
        peer_weights_list = [
            PeerAttestationWeight(
                node_pubkey=p["pubkey"],
                suspicion_score=p["score"],
                confidence=p["confidence"],
                grounded_ratio=p["grounded_ratio"],
                effective_weight=round(p["weight"], 3),
                is_outlier=p["is_outlier"],
            )
            for p in peer_meta
        ]

        return ConsensusVerdict(
            content_sha256=content_sha256,
            consensus_score=consensus_score,
            classification=classification,
            confidence=round(avg_confidence, 2),
            node_count=len(attestations),
            agreement_pct=agreement_pct,
            is_satire_consensus=is_satire_consensus,
            is_byzantine_resilient=is_byzantine_resilient,
            outlier_nodes=outlier_pubkeys,
            peer_weights=peer_weights_list,
        )
