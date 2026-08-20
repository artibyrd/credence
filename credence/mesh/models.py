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
        name="Sprout Node",
        tier=EpistemicTier.SPROUT,
        icon="🌱",
        description="Initialized and connected to the Credence P2P mesh network.",
    ),
    "sifter_pioneer": BadgeInfo(
        badge_id="sifter_pioneer",
        name="Sifter Pioneer",
        tier=EpistemicTier.SIFTER,
        icon="🔍",
        description="Completed 100+ local feed sifter evaluations.",
    ),
    "verified_auditor": BadgeInfo(
        badge_id="verified_auditor",
        name="Verified Auditor",
        tier=EpistemicTier.AUDITOR,
        icon="⚖️",
        description="Maintained >70% quality and >95% epistemic grounding over 100+ citations.",
    ),
    "domain_specialist": BadgeInfo(
        badge_id="domain_specialist",
        name="Domain Specialist",
        tier=EpistemicTier.SPECIALIST,
        icon="🎯",
        description="Demonstrated high domain-specific calibration across 5+ unique domains.",
    ),
    "philanthropic_relay": BadgeInfo(
        badge_id="philanthropic_relay",
        name="Philanthropic Relay",
        tier=EpistemicTier.AUDITOR,
        icon="🎁",
        description="Contributed over 1,000,000 LLM tokens to background mesh consensus.",
    ),
    "root_seed_candidate": BadgeInfo(
        badge_id="root_seed_candidate",
        name="Root Seed Candidate",
        tier=EpistemicTier.ROOT_ANCHOR,
        icon="🌳",
        description="Achieved >85% quality, 30+ days longevity, and valid genesis catalog hashes.",
    ),
    "galileo_pioneer": BadgeInfo(
        badge_id="galileo_pioneer",
        name="Galileo Pioneer",
        tier=EpistemicTier.SPECIALIST,
        icon="🔭",
        description="Discovered and validated non-consensus truthful outlier citations.",
    ),
    "sybil_shield": BadgeInfo(
        badge_id="sybil_shield",
        name="Sybil Shield",
        tier=EpistemicTier.ROOT_ANCHOR,
        icon="🛡️",
        description="Evaluated 5000+ attestations with zero slashing incidents.",
    ),
}
