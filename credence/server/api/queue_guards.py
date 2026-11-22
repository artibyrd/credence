"""Security Guardrails, Authoritative Enqueue Capture & Consensus Helpers for Mempool API.

Extracted from queue.py to uphold the 500 LOC Ceiling Law with strict DAG imports.
Enforces:
- Ed25519 proof-of-possession on /api/queue/claim (5-minute replay window)
- Strict worker_pubkey hex and worker_alias sanitization
- XSS and dangerous URI rejection in violation fields
- SSRF-safe, rate-limited, 10 MB-capped coordinator-side enqueue fetching
- Real BayesianConsensusAggregator with Galileo Rule override
"""

from __future__ import annotations

import re
import secrets
import time
from collections import deque
from datetime import timedelta
from typing import Any, Deque, Dict, List, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.requests import Request

from credence.config import settings
from credence.identity import canonical_json_bytes
from credence.ingestion.extractor import extract_clean_content
from credence.ingestion.hasher import compute_content_sha256
from credence.ingestion.security import MAX_INGESTION_PAYLOAD_BYTES, is_safe_url
from credence.ingestion.snapshot import capture_webpage_fastpath
from credence.mesh.consensus import BayesianConsensusAggregator
from credence.models import AuditJob, Snapshot, utc_now
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.server.middleware.security import get_auth_identity
from credence.storage.base import get_blob_storage
from credence.worker.leases import build_claim_proof_payload

MODEL_SLUG_REGEX = re.compile(r"^(?!.*\.\.)[a-zA-Z0-9_\-\.\/]{1,64}(?::[a-zA-Z0-9_\-\.]{1,32})?$")
PUBKEY_HEX_REGEX = re.compile(r"^[0-9a-f]{64}$")
AFFINITY_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.:]{1,64}$")
ALIAS_UNSAFE_RE = re.compile(r"[^a-zA-Z0-9 _.\-]")
HTML_TAG_RE = re.compile(r"<[^>]*>")
XSS_PAYLOAD_RE = re.compile(
    r"<[^>]*>|(?:on[a-z]{2,20}\s*=)|(?:javascript:|vbscript:|data\s*:\s*text/html)",
    re.IGNORECASE,
)

CLAIM_PROOF_WINDOW_SECONDS = 300
MAX_TOKENS_DONATED_PER_SUBMIT = 200_000
PUBLIC_ENQUEUE_LIMIT_PER_MIN = 30
_ENQUEUE_RATE_BUCKETS: Dict[str, Deque[float]] = {}


def is_authenticated_operator(request: Request) -> bool:
    """Return True only when request carries explicit operator credentials (never loopback bypass)."""
    api_key_hdr = request.headers.get("x-api-key", "").strip()
    if api_key_hdr:
        expected = settings.CREDENCE_ADMIN_API_KEY
        if expected and secrets.compare_digest(api_key_hdr, expected):
            return True
        if settings.ENV != "production" and api_key_hdr in ("dev_admin_key", "local_admin_token"):  # noqa: S105
            return True
    info = get_auth_identity(request)
    return bool(
        info.get("authenticated", False)
        and info.get("method") in ("API_KEY", "DEV_KEY", "OAUTH_JWT", "CLOUDFLARE_ACCESS")
    )


def validate_worker_pubkey(pubkey: Any) -> bool:
    """Validate that worker_pubkey is a canonical 64-character lowercase hex Ed25519 key."""
    return isinstance(pubkey, str) and bool(PUBKEY_HEX_REGEX.match(pubkey.strip().lower()))


def sanitize_worker_alias(alias: Optional[str], pubkey: str) -> str:
    """Strip HTML tags and unsafe characters from worker_alias, bounding to 40 chars."""
    fallback = f"worker-{pubkey[:8]}"
    if not alias or not isinstance(alias, str):
        return fallback
    stripped = HTML_TAG_RE.sub("", alias)
    cleaned = ALIAS_UNSAFE_RE.sub("", stripped)
    collapsed = re.sub(r"\s+", " ", cleaned).strip()[:40]
    return collapsed or fallback


def validate_violation_safety(violations: List[Any]) -> Optional[str]:
    """Reject empty quotes, HTML tags, event handlers, or dangerous URI schemes in violations."""
    for v in violations:
        quote = (getattr(v, "quote_or_element", "") or "").strip()
        reasoning = getattr(v, "reasoning", "") or ""
        selector = getattr(v, "line_or_selector", "") or ""
        if not quote:
            return "Empty quote_or_element is forbidden under G=1.00 grounding"
        if XSS_PAYLOAD_RE.search(quote):
            return "XSS or unsafe markup payload detected in violation quote"
        if XSS_PAYLOAD_RE.search(reasoning):
            return "XSS or unsafe markup payload detected in violation reasoning"
        if selector and XSS_PAYLOAD_RE.search(selector):
            return "XSS or unsafe markup payload detected in line_or_selector"
    return None


def verify_claim_proof(
    worker_pubkey: str,
    model_slug: str,
    claim_timestamp: Any,
    claim_signature: Any,
) -> Optional[str]:
    """Verify Ed25519 proof-of-possession signature over canonical claim request within 5-minute window."""
    if claim_timestamp is None or not claim_signature or not isinstance(claim_signature, str):
        return "Missing Ed25519 claim_timestamp or claim_signature proof-of-possession"
    try:
        ts = int(claim_timestamp)
    except (TypeError, ValueError):
        return "Invalid claim_timestamp format"

    now_ts = int(utc_now().timestamp())
    if abs(now_ts - ts) > CLAIM_PROOF_WINDOW_SECONDS:
        return "Claim proof timestamp outside permitted 300-second window"

    try:
        pubkey_bytes = bytes.fromhex(worker_pubkey.lower())
        sig_bytes = bytes.fromhex(claim_signature.strip())
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pubkey_bytes)
        payload = build_claim_proof_payload(worker_pubkey.lower(), model_slug, ts)
        public_key.verify(sig_bytes, canonical_json_bytes(payload))
        return None
    except (ValueError, InvalidSignature):
        return "Invalid Ed25519 claim proof-of-possession signature"


def check_public_enqueue_rate_limit(request: Request) -> bool:
    """Enforce per-IP sliding-window rate limit for unauthenticated public enqueue requests."""
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    client_ip = forwarded or (request.client.host if request.client else "unknown")
    now = time.monotonic()

    if len(_ENQUEUE_RATE_BUCKETS) > 1024:
        stale_ips = [ip for ip, dq in _ENQUEUE_RATE_BUCKETS.items() if not dq or now - dq[-1] > 60.0]
        for ip in stale_ips:
            _ENQUEUE_RATE_BUCKETS.pop(ip, None)

    bucket = _ENQUEUE_RATE_BUCKETS.setdefault(client_ip, deque())
    while bucket and now - bucket[0] > 60.0:
        bucket.popleft()
    if len(bucket) >= PUBLIC_ENQUEUE_LIMIT_PER_MIN:
        return False
    bucket.append(now)
    return True


def validate_enqueue_payload(body: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Validate enqueue payload URL safety (SSRF), byte cap, priority, quorum, and affinity."""
    raw_url = body.get("url")
    if not raw_url or not isinstance(raw_url, str):
        return None, "Missing required 'url' field"
    url = raw_url.strip()
    if not is_safe_url(url, allow_local=False):
        return None, "Target URL rejected by SSRF and private-network security policy"

    normalized_text = body.get("normalized_text") or ""
    if not isinstance(normalized_text, str):
        return None, "normalized_text must be a string"
    if len(normalized_text.encode("utf-8")) > MAX_INGESTION_PAYLOAD_BYTES:
        return None, f"normalized_text exceeds maximum allowed payload size ({MAX_INGESTION_PAYLOAD_BYTES} bytes)"

    try:
        priority = max(1, min(3, int(body.get("priority", 2))))
        target_quorum = max(1, min(7, int(body.get("target_quorum", 1))))
    except (TypeError, ValueError):
        return None, "Invalid priority or target_quorum integer"

    affinity = body.get("client_affinity")
    if affinity is not None:
        if not isinstance(affinity, str) or not AFFINITY_REGEX.match(affinity.strip()):
            return None, "Invalid client_affinity format"
        affinity = affinity.strip()

    content_sha256 = str(body.get("content_sha256") or "").strip()
    return {
        "url": url,
        "normalized_text": normalized_text,
        "content_sha256": content_sha256,
        "priority": priority,
        "target_quorum": target_quorum,
        "client_affinity": affinity,
        "force": bool(body.get("force", False)),
    }, None


async def resolve_authoritative_enqueue_content(
    session: AsyncSession,
    url: str,
    caller_text: str,
    caller_sha256: str,
    is_operator: bool,
) -> Tuple[str, str, Optional[str]]:
    """Resolve authoritative normalized_text and content_sha256 for an enqueued job.

    - text:// inline jobs: require non-empty caller_text and compute canonical SHA-256.
    - Authenticated operators: may supply pre-extracted normalized_text for http(s):// URLs.
    - Public unauthenticated http(s):// callers: ignore untrusted caller_text and reuse a fresh
      server Snapshot or perform an SSRF-safe, 10 MB-capped Trafilatura fastpath HTTP fetch.
    """
    if url.startswith("text://"):
        if not caller_text.strip():
            return "", "", "Inline text:// jobs require non-empty normalized_text"
        return caller_text, compute_content_sha256(caller_text), None

    if is_operator and caller_text.strip():
        resolved_sha = caller_sha256 or compute_content_sha256(caller_text)
        return caller_text, resolved_sha, None

    # Public http(s):// enqueue: reuse fresh coordinator Snapshot blob if available
    cutoff = utc_now() - timedelta(hours=24)
    snap_stmt = select(Snapshot).where(Snapshot.url == url).order_by(desc(Snapshot.captured_at)).limit(1)
    existing_snap = (await session.exec(snap_stmt)).first()
    if existing_snap and existing_snap.dom_file_path:
        snap_time = existing_snap.captured_at
        if snap_time.tzinfo is None:
            snap_time = snap_time.replace(tzinfo=utc_now().tzinfo)
        if snap_time >= cutoff:
            try:
                blob = await get_blob_storage().get_blob(existing_snap.dom_file_path)
                if blob:
                    extracted = extract_clean_content(blob.decode("utf-8", errors="replace"), url=url)
                    if extracted.clean_text.strip():
                        return extracted.clean_text, existing_snap.content_sha256, None
            except Exception:
                pass

    # Reuse recent coordinator-captured AuditJob text for the same URL if present
    job_stmt = select(AuditJob).where(AuditJob.url == url).order_by(desc(AuditJob.created_at)).limit(1)
    prev_job = (await session.exec(job_stmt)).first()
    if prev_job and prev_job.normalized_text.strip() and prev_job.content_sha256:
        job_time = prev_job.created_at
        if job_time.tzinfo is None:
            job_time = job_time.replace(tzinfo=utc_now().tzinfo)
        if job_time >= cutoff:
            return prev_job.normalized_text, prev_job.content_sha256, None

    # Perform SSRF-safe, 10 MB-capped fastpath HTTP fetch (no Playwright on enqueue)
    try:
        capture = await capture_webpage_fastpath(url, save_artifacts=True, allow_playwright_fallback=False)
    except Exception as exc:
        return "", "", f"Coordinator authoritative fetch failed for target URL: {exc}"

    snap_exists = (
        await session.exec(select(Snapshot).where(Snapshot.content_sha256 == capture.content_sha256))
    ).first()
    if not snap_exists:
        session.add(
            Snapshot(
                url=capture.url,
                content_sha256=capture.content_sha256,
                simhash_64=capture.simhash_64,
                dom_file_path=capture.dom_file_path,
                clean_text_length=len(capture.extracted.clean_text),
                word_count=capture.extracted.word_count,
                title=capture.extracted.title,
                byline=capture.extracted.byline,
                site_name=capture.extracted.site_name,
                is_satire_cue=capture.extracted.is_satire_cue,
            )
        )
    return capture.extracted.clean_text, capture.content_sha256, None


def compute_consensus_verdict(
    audits: List[Dict[str, Any]],
    worker_qualities: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Compute quality-weighted Bayesian consensus verdict with Galileo Rule override."""
    if not audits:
        return {
            "consensus_score": 0.0,
            "median_score": 0.0,
            "classification": "CLEAN",
            "evaluations_count": 0,
            "galileo_override": False,
            "violations_count": 0,
        }

    reports: List[AuditReport] = []
    grounded_violations: List[Dict[str, Any]] = []
    scores: List[float] = []

    for idx, audit in enumerate(audits):
        score = float(audit.get("suspicion_score", 0.0))
        scores.append(score)
        pubkey = str(audit.get("node_pubkey") or f"worker-{idx}")
        findings: List[SpecialistViolationFinding] = []
        for raw_v in audit.get("violations", []):
            quote = str(raw_v.get("quote_or_element") or raw_v.get("quote") or "").strip()
            if not quote:
                continue
            is_grounded = bool(raw_v.get("is_grounded", True))
            if is_grounded:
                grounded_violations.append(raw_v)
            findings.append(
                SpecialistViolationFinding(
                    rule_id=str(raw_v.get("rule_id") or "SPJ-1.1"),
                    rule_uri=str(raw_v.get("rule_uri") or "journalistic-ethics:general/SPJ-1.1@v1.0.0"),
                    domain=str(raw_v.get("domain") or "JOURNALISTIC_ETHICS"),
                    cluster_id=str(raw_v.get("cluster_id") or "GENERAL"),
                    severity=max(1, min(5, int(raw_v.get("severity", 3)))),
                    confidence=float(raw_v.get("confidence", 0.9)),
                    quote_or_element=quote,
                    reasoning=str(raw_v.get("reasoning") or "Verified verbatim finding."),
                    is_grounded=is_grounded,
                )
            )
        band = "CLEAN" if score < 25.0 else ("SUSPICIOUS" if score < 60.0 else "DECEPTIVE")
        reports.append(
            AuditReport(
                url=str(audit.get("url") or "https://consensus.local/item"),
                content_sha256=str(audit.get("content_sha256") or "sha256:consensus"),
                simhash_64=str(audit.get("simhash_64") or "0x0"),
                suspicion_score=max(0.0, min(100.0, score)),
                suspicion_density=float(audit.get("suspicion_density", len(findings))),
                confidence_score=float(audit.get("confidence_score", 0.9)),
                classification=str(audit.get("classification") or band),
                is_satire=bool(audit.get("is_satire", False)),
                violations=findings,
                node_pubkey=pubkey,
            )
        )

    aggregator = BayesianConsensusAggregator()
    verdict = aggregator.compute_consensus(reports, node_reputations=worker_qualities or {})
    sorted_scores = sorted(scores)
    mid = len(sorted_scores) // 2
    raw_median = (
        sorted_scores[mid] if len(sorted_scores) % 2 != 0 else (sorted_scores[mid - 1] + sorted_scores[mid]) / 2.0
    )

    final_score = verdict.consensus_score if verdict else raw_median
    galileo_override = False
    if grounded_violations and final_score < 25.0:
        galileo_override = True
        final_score = max(max(scores), 45.0)

    classification = "CLEAN" if final_score < 25.0 else ("SUSPICIOUS" if final_score < 60.0 else "DECEPTIVE")
    return {
        "consensus_score": round(final_score, 1),
        "median_score": round(raw_median, 1),
        "classification": classification,
        "evaluations_count": len(audits),
        "galileo_override": galileo_override,
        "violations_count": len(grounded_violations),
        "agreement_pct": verdict.agreement_pct if verdict else 100.0,
        "outlier_nodes": verdict.outlier_nodes if verdict else [],
    }
