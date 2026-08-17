"""Bayesian & Subject-Weighted Consensus Engine & Outlier Detection for Credence Mesh.

Aggregates multiple Ed25519-signed peer audit attestations for the same content SHA-256,
computes subject-weighted empirical consensus suspicion scores (e.g. Beekeeper vs Dog Walker),
and filters out adversarial or compromised rogue nodes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from credence.pipeline.schemas import AuditReport
from credence.pipeline.scoring import classify_verdict
from credence.subjects.expertise import calculate_effective_weight


class PeerAttestationWeight(BaseModel):
    """Calculated weight and credibility metric for an individual peer attestation."""

    node_pubkey: str
    suspicion_score: float
    confidence: float
    grounded_ratio: float
    effective_weight: float
    domain_expertise: float = 0.05
    is_outlier: bool = False


class ConsensusVerdict(BaseModel):
    """Consolidated Bayesian Consensus Verdict across multiple decentralized nodes."""

    content_sha256: str
    consensus_score: float = Field(..., ge=0.0, le=100.0, description="Confidence-weighted consensus suspicion score")
    classification: str = Field(..., description="Consensus verdict classification band")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Aggregate network confidence")
    node_count: int = Field(..., description="Total number of peer attestations aggregated")
    agreement_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of nodes agreeing with verdict band")
    subject_id: Optional[str] = Field(default=None, description="Subject namespace under evaluation")
    is_satire_consensus: bool = Field(default=False)
    is_byzantine_resilient: bool = Field(default=True, description="True if agreement meets or exceeds 66% threshold")
    outlier_nodes: List[str] = Field(default_factory=list, description="Public keys of detected divergent/rogue nodes")
    peer_weights: List[PeerAttestationWeight] = Field(default_factory=list)


class BayesianConsensusAggregator:
    """Consensus aggregator calculating weighted Bayesian agreement across peer nodes."""

    def __init__(self, consensus_threshold: float = 0.66, outlier_delta_threshold: float = 25.0) -> None:
        self.consensus_threshold = consensus_threshold
        self.outlier_delta_threshold = outlier_delta_threshold

    def _calculate_peer_meta(
        self,
        attestations: List[AuditReport],
        reputations: Dict[str, float],
        subject_id: Optional[str],
        exp_map: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        peer_meta: List[Dict[str, Any]] = []
        for att in attestations:
            pubkey = att.node_pubkey or "anonymous"
            rep = reputations.get(pubkey, 0.5)

            if att.violations:
                grounded_count = sum(1 for v in att.violations if v.is_grounded)
                grounded_ratio = grounded_count / len(att.violations)
            else:
                grounded_ratio = 1.0

            domain_exp = exp_map.get(pubkey, 0.05) if subject_id else 0.5
            if subject_id:
                base_weight = calculate_effective_weight(
                    node_pubkey=pubkey,
                    subject_id=subject_id,
                    base_quality=rep,
                    expertise_score=domain_exp,
                )
            else:
                base_weight = rep

            effective_weight = max(0.01, base_weight * att.confidence_score * (0.5 + 0.5 * grounded_ratio))
            peer_meta.append(
                {
                    "att": att,
                    "pubkey": pubkey,
                    "score": att.suspicion_score,
                    "confidence": att.confidence_score,
                    "grounded_ratio": grounded_ratio,
                    "domain_exp": domain_exp,
                    "weight": effective_weight,
                    "is_satire": att.is_satire,
                }
            )
        return peer_meta

    def _compute_median_score(
        self,
        peer_meta: List[Dict[str, Any]],
        subject_id: Optional[str],
    ) -> float:
        sorted_peers = sorted(peer_meta, key=lambda p: p["score"])
        total_weight = sum(p["weight"] for p in sorted_peers)
        cum_weight = 0.0
        median_score = float(sorted_peers[len(sorted_peers) // 2]["score"])

        if subject_id and total_weight > 0:
            for p in sorted_peers:
                cum_weight += p["weight"]
                if cum_weight >= (total_weight / 2.0):
                    return float(p["score"])
        return median_score

    def _filter_outliers(
        self,
        peer_meta: List[Dict[str, Any]],
        median_score: float,
    ) -> tuple[List[str], List[Dict[str, Any]]]:
        outlier_pubkeys: List[str] = []
        valid_peers: List[Dict[str, Any]] = []

        for p in peer_meta:
            delta = abs(p["score"] - median_score)
            has_grounded_violations = len(p["att"].violations) > 0 and p["grounded_ratio"] >= 0.80
            is_verified_authority = p.get("domain_exp", 0.0) >= 0.70 or p["weight"] >= 0.50

            # The Galileo Rule: Verified authorities providing 100% grounded citations
            # cannot be dismissed as outliers by low-expertise swarms reporting absence of evidence
            if is_verified_authority and has_grounded_violations:
                p["is_outlier"] = False
                valid_peers.append(p)
            elif delta > self.outlier_delta_threshold and len(peer_meta) >= 3:
                p["is_outlier"] = True
                outlier_pubkeys.append(p["pubkey"])
            else:
                p["is_outlier"] = False
                valid_peers.append(p)
        return outlier_pubkeys, valid_peers

    def calculate_consensus(
        self,
        attestations: List[AuditReport],
        node_reputations: Optional[Dict[str, float]] = None,
        subject_id: Optional[str] = None,
        subject_expertise_map: Optional[Dict[str, float]] = None,
    ) -> Optional[ConsensusVerdict]:
        """Calculate subject-weighted Bayesian consensus across signed attestations."""
        if not attestations:
            return None

        content_sha256 = attestations[0].content_sha256
        peer_meta = self._calculate_peer_meta(
            attestations=attestations,
            reputations=node_reputations or {},
            subject_id=subject_id,
            exp_map=subject_expertise_map or {},
        )
        median_score = self._compute_median_score(peer_meta, subject_id)
        outlier_pubkeys, valid_peers = self._filter_outliers(peer_meta, median_score)

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
                domain_expertise=round(p["domain_exp"], 3),
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
            subject_id=subject_id,
            is_satire_consensus=is_satire_consensus,
            is_byzantine_resilient=is_byzantine_resilient,
            outlier_nodes=outlier_pubkeys,
            peer_weights=peer_weights_list,
        )
