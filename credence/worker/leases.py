"""Local Lease Tracking and Model Family Resolution for Credence Volunteer Workers.

Governed by Theme 1: Botanical Network & Lifecycle & Theme 4: Sovereign Governance.
Ensures local lease validity before computation and handles exponential backoff.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from credence.identity import NodeIdentity, canonical_json_bytes

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def build_claim_proof_payload(worker_pubkey: str, model_slug: str, claim_timestamp: int) -> Dict[str, Any]:
    """Build canonical JSON payload signed by workers for Ed25519 claim proof-of-possession."""
    return {
        "action": "mempool_claim",
        "claim_timestamp": int(claim_timestamp),
        "model_slug": model_slug.strip(),
        "worker_pubkey": worker_pubkey.strip().lower(),
    }


def sign_claim_proof(
    identity: NodeIdentity,
    model_slug: str,
    claim_timestamp: Optional[int] = None,
) -> Tuple[int, str]:
    """Sign a mempool claim proof payload using the worker's Ed25519 private key."""
    ts = int(claim_timestamp if claim_timestamp is not None else utc_now().timestamp())
    payload = build_claim_proof_payload(identity.public_key_hex, model_slug, ts)
    sig_bytes = identity.private_key.sign(canonical_json_bytes(payload))
    return ts, sig_bytes.hex()


def resolve_model_family(model_slug: str) -> str:
    """Resolve canonical model family identifier from model slug or URI.

    Supports well-known families (Google Gemini, Anthropic Claude, OpenAI GPT,
    Meta Llama, DeepSeek, Mistral, Qwen, Microsoft Phi) as well as custom/local
    and open-weights models.
    """
    clean = model_slug.strip().lower()

    # 1. Standard Frontier / Known Open-Weight Roots
    if any(k in clean for k in ("gemini", "gemma")):
        return "google/gemini"
    if any(k in clean for k in ("claude", "anthropic")):
        return "anthropic/claude"
    if any(k in clean for k in ("gpt-", "gpt", "openai")) or re.search(r"(?:^|[/:_-])o[134](?:$|[/:_.-])", clean):
        return "openai/gpt"
    if "deepseek" in clean or re.search(r"(?:^|[/:_-])r1(?:$|[/:_.-])", clean):
        return "deepseek/deepseek"
    if any(k in clean for k in ("llama", "meta-llama")):
        return "meta/llama"
    if any(k in clean for k in ("qwen", "qwq")):
        return "qwen/qwen"
    if any(k in clean for k in ("mistral", "mixtral", "codestral")):
        return "mistral/mistral"
    if any(k in clean for k in ("phi", "microsoft/phi")):
        return "microsoft/phi"
    if any(k in clean for k in ("grok", "xai")):
        return "xai/grok"

    # 2. Dynamic Namespace Extraction for Novel/Custom Providers
    if "/" in clean:
        parts = clean.split("/", 1)
        vendor, model_part = parts[0], parts[1]
        base = re.split(r"[-_.]", model_part)[0]
        return f"{vendor}/{base}"

    # 3. Fallback for unnamespaced custom models
    base = re.split(r"[-_.]", clean)[0] if clean else "custom"
    return f"custom/{base}"


def compute_backoff_delay(
    consecutive_idle: int,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
) -> float:
    """Compute exponential backoff delay when queue is empty or after errors."""
    if consecutive_idle <= 0:
        return base_delay
    factor = 1.5 ** min(consecutive_idle, 8)
    delay = min(max_delay, base_delay * factor)
    return round(delay, 2)


@dataclass
class ActiveLease:
    """Represents a currently claimed job lease held by the local worker."""

    lease_id: str
    job_id: str
    url: str
    acquired_at: datetime
    expires_at: datetime
    lease_seconds: int


class LocalLeaseTracker:
    """Tracks active leases locally to prevent unfulfilled claims and premature submission."""

    def __init__(self, max_concurrency: int = 3) -> None:
        self.max_concurrency = max_concurrency
        self._leases: Dict[str, ActiveLease] = {}

    def track_lease(self, lease_id: str, job_id: str, url: str, lease_seconds: int) -> ActiveLease:
        """Register a newly acquired job lease."""
        now = utc_now()
        lease = ActiveLease(
            lease_id=lease_id,
            job_id=job_id,
            url=url,
            acquired_at=now,
            expires_at=now + timedelta(seconds=lease_seconds),
            lease_seconds=lease_seconds,
        )
        self._leases[lease_id] = lease
        return lease

    def is_lease_valid(self, lease_id: str) -> bool:
        """Check if lease exists and has not expired."""
        lease = self._leases.get(lease_id)
        if not lease:
            return False
        return utc_now() < lease.expires_at

    def release_lease(self, lease_id: str) -> Optional[ActiveLease]:
        """Remove a fulfilled or abandoned lease from tracking."""
        return self._leases.pop(lease_id, None)

    def active_lease_count(self) -> int:
        """Return number of unexpired leases currently active."""
        now = utc_now()
        active = [lease for lease in self._leases.values() if lease.expires_at > now]
        return len(active)

    def prune_expired(self) -> List[str]:
        """Prune any expired leases and return their IDs."""
        now = utc_now()
        expired = [lid for lid, lease in self._leases.items() if lease.expires_at <= now]
        for lid in expired:
            self._leases.pop(lid, None)
        return expired

    def can_claim_more(self) -> bool:
        """Verify worker has capacity to claim additional concurrent jobs."""
        return self.active_lease_count() < self.max_concurrency
