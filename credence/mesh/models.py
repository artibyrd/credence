"""P2P Mesh Badge & Topology Data Models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from pydantic import BaseModel

from credence.models import EpistemicTier


@dataclass
class BadgeInfo:
    """Metadata definition for an achievable node badge."""

    badge_id: str
    name: str
    tier: EpistemicTier
    icon: str
    description: str


class BadgeAward(BaseModel):
    """Specific badge unlocked by a node."""

    badge_id: str
    name: str
    tier: str
    icon: str
    description: str
    unlocked_at: str


BADGE_REGISTRY: Dict[str, BadgeInfo] = {
    "sprout_node": BadgeInfo(
        badge_id="sprout_node",
        name="Sprout Genesis",
        tier=EpistemicTier.SPROUT,
        icon="🌱",
        description="Initialized and connected to the Credence P2P mesh network.",
    ),
    "first_attestation": BadgeInfo(
        badge_id="first_attestation",
        name="First Attestation",
        tier=EpistemicTier.SPROUT,
        icon="🌾",
        description="Completed first 5 grounded audits with zero schema violations.",
    ),
    "sifter_pioneer": BadgeInfo(
        badge_id="sifter_pioneer",
        name="Sifter Century",
        tier=EpistemicTier.SIFTER,
        icon="🔍",
        description="Evaluated 100+ local feed articles with grounded rule extraction.",
    ),
    "cadence_keeper": BadgeInfo(
        badge_id="cadence_keeper",
        name="Cadence Keeper",
        tier=EpistemicTier.SIFTER,
        icon="⏱️",
        description="Sustained 7+ days of active node longevity with >=98% operational uptime.",
    ),
    "verified_auditor": BadgeInfo(
        badge_id="verified_auditor",
        name="Verified Auditor",
        tier=EpistemicTier.AUDITOR,
        icon="⚖️",
        description="Maintained quality Qi >= 0.85 and verbatim grounding G >= 0.95 across 500+ audits.",
    ),
    "philanthropic_relay": BadgeInfo(
        badge_id="philanthropic_relay",
        name="Philanthropic Relay",
        tier=EpistemicTier.AUDITOR,
        icon="🎁",
        description="Contributed over 1,000,000 LLM tokens to background mesh consensus.",
    ),
    "domain_specialist": BadgeInfo(
        badge_id="domain_specialist",
        name="Domain Specialist",
        tier=EpistemicTier.SPECIALIST,
        icon="🎯",
        description="Demonstrated high domain-specific calibration (>=0.85) across 10+ unique domains.",
    ),
    "galileo_pioneer": BadgeInfo(
        badge_id="galileo_pioneer",
        name="Galileo Pioneer",
        tier=EpistemicTier.SPECIALIST,
        icon="🔭",
        description="Discovered and validated non-consensus truthful outlier citations.",
    ),
    "root_seed_candidate": BadgeInfo(
        badge_id="root_seed_candidate",
        name="Root Seed Candidate",
        tier=EpistemicTier.ROOT_ANCHOR,
        icon="🌳",
        description="Achieved >85% quality, 30+ days longevity, and valid genesis catalog hashes.",
    ),
    "sybil_shield": BadgeInfo(
        badge_id="sybil_shield",
        name="Sybil Sentinel",
        tier=EpistemicTier.ROOT_ANCHOR,
        icon="🛡️",
        description="Evaluated 5,000+ attestations with zero slashing incidents.",
    ),
    "century_anchor": BadgeInfo(
        badge_id="century_anchor",
        name="Century Anchor",
        tier=EpistemicTier.ROOT_ANCHOR,
        icon="🏛️",
        description="Achieved 100+ days uninterrupted sovereign operation with Qi >= 0.90 and G >= 0.98.",
    ),
    "quorum_sentinel": BadgeInfo(
        badge_id="quorum_sentinel",
        name="Quorum Sentinel",
        tier=EpistemicTier.ROOT_ANCHOR,
        icon="🛡️",
        description="Maintained Byzantine consensus participation during 3f+1 peer quorum rounds.",
    ),
}

# Add alias mappings for seamless backward & forward naming compatibility
BADGE_REGISTRY["sprout_genesis"] = BADGE_REGISTRY["sprout_node"]
BADGE_REGISTRY["sifter_century"] = BADGE_REGISTRY["sifter_pioneer"]
BADGE_REGISTRY["sybil_sentinel"] = BADGE_REGISTRY["sybil_shield"]
