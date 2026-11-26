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
from credence.subjects.expertise import (
    compute_divergence_acceleration_dampening,
    compute_effective_weight,
)


class PeerAttestationWeight(BaseModel):
    """Calculated weight and credibility metric for an individual peer attestation."""

    node_pubkey: str
    suspicion_score: float
    confidence: float
    grounded_ratio: float
    effective_weight: float
    domain_expertise: float = 0.05
    is_outlier: bool = False
    galileo_dampening: float = 1.0
    galileo_escalation: bool = False


class ConsensusVerdict(BaseModel):
    """Consolidated Bayesian Consensus Verdict across multiple decentralized nodes."""

    content_sha256: str
    consensus_score: float = Field(..., ge=0.0, le=100.0, description="Confidence-weighted consensus suspicion score")
    classification: str = Field(..., description="Consensus verdict classification band")
    consensus_verdict: str = Field(default="NEWS_ARTICLE", description="Alias for classification")
    byzantine_nodes_trimmed_count: int = Field(default=0, description="Count of trimmed byzantine nodes")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Aggregate network confidence")
    node_count: int = Field(..., description="Total number of peer attestations aggregated")
    agreement_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of nodes agreeing with verdict band")
    subject_id: Optional[str] = Field(default=None, description="Subject namespace under evaluation")
    is_satire_consensus: bool = Field(default=False)
    is_byzantine_resilient: bool = Field(default=True, description="True if agreement meets or exceeds 66% threshold")
    outlier_nodes: List[str] = Field(default_factory=list, description="Public keys of detected divergent/rogue nodes")
    galileo_override: bool = Field(default=False, description="True if Galileo Rule anchor elevated consensus")
    galileo_escalated_nodes: List[str] = Field(
        default_factory=list,
        description="Public keys of nodes flagged for Galileo divergence acceleration",
    )
    peer_weights: List[PeerAttestationWeight] = Field(default_factory=list)


class BayesianConsensusAggregator:
    """Consensus aggregator calculating weighted Bayesian agreement across peer nodes."""

    def __init__(
        self,
        consensus_threshold: float = 0.66,
        outlier_delta_threshold: float = 25.0,
        f: Optional[int] = None,
        prior_mean: float = 20.0,
        prior_variance: float = 100.0,
        enable_byzantine_trimming: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.f = f
        self.prior_mean = prior_mean
        self.prior_variance = prior_variance
        self.enable_byzantine_trimming = enable_byzantine_trimming
        self.consensus_threshold = consensus_threshold
        self.outlier_delta_threshold = outlier_delta_threshold

    def _calculate_peer_meta(
        self,
        attestations: List[AuditReport],
        reputations: Dict[str, float],
        subject_id: Optional[str],
        exp_map: Dict[str, float],
        peer_recent_deviations: Optional[Dict[str, List[float]]] = None,
        peer_baseline_deviations: Optional[Dict[str, Optional[float]]] = None,
    ) -> List[Dict[str, Any]]:
        peer_meta: List[Dict[str, Any]] = []
        recent_map = peer_recent_deviations or {}
        baseline_map = peer_baseline_deviations or {}
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
                base_weight = compute_effective_weight(
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
                    "base_weight": base_weight,
                    "subject_id": subject_id,
                    "weight": effective_weight,
                    "is_satire": att.is_satire,
                    "recent_deviations": recent_map.get(pubkey, []),
                    "baseline_deviation": baseline_map.get(pubkey),
                    "galileo_dampening": 1.0,
                    "galileo_escalation": False,
                }
            )
        return peer_meta

    @staticmethod
    def _is_verified_authority(p: Dict[str, Any]) -> bool:
        if p.get("domain_exp", 0.0) >= 0.70:
            return True
        if p.get("subject_id") is not None:
            return bool(p["weight"] >= 0.50)
        return bool(p.get("base_weight", 0.0) >= 0.70 and p["weight"] >= 0.50)

    def _apply_galileo_dampening(self, peer_meta: List[Dict[str, Any]]) -> None:
        """Compute Galileo acceleration dampening and scale peer weights before median calculation."""
        for p in peer_meta:
            has_grounded_violations = len(p["att"].violations) > 0 and p["grounded_ratio"] >= 0.80
            is_verified_authority = self._is_verified_authority(p)
            p["is_verified_authority"] = is_verified_authority

            if is_verified_authority and has_grounded_violations:
                dampening = compute_divergence_acceleration_dampening(
                    p.get("recent_deviations", []),
                    baseline_deviation=p.get("baseline_deviation"),
                )
                p["galileo_dampening"] = dampening
                if dampening > 0.5:
                    p["weight"] = max(0.01, p["weight"] * dampening)
                    if dampening < 1.0:
                        p["galileo_escalation"] = True
                else:
                    p["weight"] = max(0.01, p["weight"] * (dampening**2))
                    p["galileo_escalation"] = True

    def _compute_median_score(
        self,
        peer_meta: List[Dict[str, Any]],
        subject_id: Optional[str] = None,
    ) -> float:
        if not peer_meta:
            return 0.0
        sorted_peers = sorted(peer_meta, key=lambda p: p["score"])
        total_weight = sum(p["weight"] for p in sorted_peers)
        if total_weight <= 0:
            return float(sorted_peers[len(sorted_peers) // 2]["score"])

        cum_weight = 0.0
        for p in sorted_peers:
            cum_weight += p["weight"]
            if cum_weight >= (total_weight / 2.0):
                return float(p["score"])
        return float(sorted_peers[-1]["score"])

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
            is_verified_authority = p.get("is_verified_authority", self._is_verified_authority(p))
            dampening = p.get("galileo_dampening", 1.0)

            # The Galileo Rule: Verified authorities providing grounded citations
            # retain outlier immunity unless divergence acceleration indicates a pivot.
            if is_verified_authority and has_grounded_violations and dampening > 0.5:
                p["is_outlier"] = False
                valid_peers.append(p)
            elif delta > self.outlier_delta_threshold and len(peer_meta) >= 3:
                p["is_outlier"] = True
                outlier_pubkeys.append(p["pubkey"])
            else:
                p["is_outlier"] = False
                valid_peers.append(p)
        return outlier_pubkeys, valid_peers

    def compute_consensus(
        self,
        attestations: List[AuditReport],
        node_reputations: Optional[Dict[str, float]] = None,
        subject_id: Optional[str] = None,
        subject_expertise_map: Optional[Dict[str, float]] = None,
        peer_recent_deviations: Optional[Dict[str, List[float]]] = None,
        peer_baseline_deviations: Optional[Dict[str, Optional[float]]] = None,
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
            peer_recent_deviations=peer_recent_deviations,
            peer_baseline_deviations=peer_baseline_deviations,
        )
        self._apply_galileo_dampening(peer_meta)
        median_score = self._compute_median_score(peer_meta, subject_id)
        outlier_pubkeys, valid_peers = self._filter_outliers(peer_meta, median_score)

        # Calculate true Domain Authority Weighted Median over active non-outlier peers
        active_peers = valid_peers if valid_peers else peer_meta
        active_total_weight = sum(p["weight"] for p in active_peers)
        consensus_score = self._compute_median_score(active_peers, subject_id)
        consensus_score = round(max(0.0, min(100.0, consensus_score)), 1)

        # Galileo Rule Anchor: If non-pivoting verified authorities with grounded citations exist,
        # their discoveries cannot be silenced by low-expertise swarms scoring in the CLEAN band (<= 15.0)
        authoritative_evidentiary_peers = [
            p
            for p in active_peers
            if p.get("is_verified_authority", self._is_verified_authority(p))
            and p["grounded_ratio"] >= 0.80
            and len(p["att"].violations) > 0
            and p.get("galileo_dampening", 1.0) > 0.5
        ]
        galileo_override = False
        if authoritative_evidentiary_peers and consensus_score <= 15.0:
            anchored_score = round(
                max(0.0, min(100.0, self._compute_median_score(authoritative_evidentiary_peers, subject_id))),
                1,
            )
            if anchored_score > 15.0:
                consensus_score = anchored_score
                galileo_override = True

        # Step 4: Satire consensus
        satire_votes = sum(1 for p in active_peers if p["is_satire"])
        is_satire_consensus = satire_votes > (len(active_peers) / 2)

        if is_satire_consensus:
            consensus_score = 0.0
            classification = "SATIRE_PARODY"
            galileo_override = False
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
                galileo_dampening=round(p.get("galileo_dampening", 1.0), 4),
                galileo_escalation=bool(p.get("galileo_escalation", False)),
            )
            for p in peer_meta
        ]
        galileo_escalated_nodes = [p["pubkey"] for p in peer_meta if p.get("galileo_escalation", False)]

        return ConsensusVerdict(
            content_sha256=content_sha256,
            consensus_score=consensus_score,
            classification=classification,
            consensus_verdict=classification,
            byzantine_nodes_trimmed_count=len(outlier_pubkeys),
            confidence=round(avg_confidence, 2),
            node_count=len(attestations),
            agreement_pct=agreement_pct,
            subject_id=subject_id,
            is_satire_consensus=is_satire_consensus,
            is_byzantine_resilient=is_byzantine_resilient,
            outlier_nodes=outlier_pubkeys,
            galileo_override=galileo_override,
            galileo_escalated_nodes=galileo_escalated_nodes,
            peer_weights=peer_weights_list,
        )


def should_adopt_attestation(
    report: AuditReport,
    peer_quality: float = 0.5,
    min_quality: float = 0.70,
    min_grounding: float = 0.85,
) -> bool:
    """Evaluate whether a peer's signed attestation qualifies for zero-cost cache adoption.

    Requires:
    1. Valid node public key and signature
    2. Peer quality score >= min_quality (default 0.70)
    3. Verbatim quote grounding precision >= min_grounding (default 0.85)
    """
    if not report.node_pubkey or not report.node_signature:
        return False

    if peer_quality < min_quality:
        return False

    if report.violations:
        grounded_count = sum(1 for v in report.violations if v.is_grounded)
        ratio = grounded_count / len(report.violations)
        if ratio < min_grounding:
            return False

    return True
