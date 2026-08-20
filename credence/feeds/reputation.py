"""Domain Reputation, Soft Blacklist Quarantine, and BuzzFeed Doctrine Redemption Engine for Credence.

Maintains domain-level trust metrics, calculates asymmetric Bayesian updates, manages
exponential polling backoff for quarantined feeds, and enforces the BuzzFeed News Doctrine
for verifiable redemption.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from rich.console import Console
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.models import DomainReputationRecord, FeedSubscriptionRecord, utc_now
from credence.pipeline.schemas import AuditReport

console = Console()


def normalize_domain(url_or_domain: str) -> str:
    """Normalize a URL or domain string to lowercased netloc without www prefix."""
    if not url_or_domain:
        return ""
    if not url_or_domain.startswith(("http://", "https://")):
        url_or_domain = f"https://{url_or_domain}"
    try:
        netloc = urlparse(url_or_domain).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        # Strip port if present
        if ":" in netloc:
            netloc = netloc.split(":")[0]
        return netloc
    except Exception:
        return ""


async def get_or_create_domain_reputation(
    session: AsyncSession,
    domain: str,
) -> DomainReputationRecord:
    """Fetch existing domain reputation record or initialize a new NEUTRAL entry."""
    clean_domain = normalize_domain(domain)
    stmt = select(DomainReputationRecord).where(DomainReputationRecord.domain == clean_domain)
    record = (await session.exec(stmt)).first()

    if not record:
        record = DomainReputationRecord(
            domain=clean_domain,
            reputation_score=50.0,
            status="NEUTRAL",
            polling_backoff_factor=1.0,
            distinct_clean_subjects_json="[]",
            first_seen_at=utc_now(),
            last_audited_at=utc_now(),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

    return record


def calculate_polling_backoff(consecutive_deceptions: int) -> float:
    """Calculate exponential backoff factor (1.0x to 64.0x) based on consecutive deceptions."""
    if consecutive_deceptions <= 0:
        return 1.0
    power = min(consecutive_deceptions, 6)
    return float(2**power)


async def update_domain_reputation(
    session: AsyncSession,
    url_or_domain: str,
    audit_report: AuditReport,
    subject_id: Optional[str] = None,
    word_count: int = 0,
) -> DomainReputationRecord:
    """Apply an asymmetric Bayesian reputation update following an audit.

    - Slashing: Immediate and severe for high-suspicion content.
    - Recovery: Earned gradually through verified clean audits across diverse subjects.
    - The BuzzFeed News Doctrine: 5 consecutive clean audits spanning >=2 subject namespaces
      graduates quarantined domains into probationary recovery.
    """
    domain = normalize_domain(url_or_domain or audit_report.url)
    if not domain:
        domain = "unknown.origin"

    record = await get_or_create_domain_reputation(session, domain)
    record.audits_count += 1
    record.last_audited_at = utc_now()

    suspicion = audit_report.suspicion_score
    max_severity = max([v.severity for v in audit_report.violations if v.is_grounded], default=1)
    is_clean = suspicion <= 20.0 and audit_report.classification in ("CLEAN", "SATIRE_PARODY")
    is_deceptive = suspicion >= 50.0 or max_severity >= 3

    # 1. Asymmetric Bayesian Score Adjustment
    if is_deceptive:
        record.consecutive_clean_count = 0
        record.consecutive_deceptive_count += 1
        record.deceptive_audits_count += 1

        # Relapse check during probation (immediate reset to max penalty)
        was_in_probation = record.status == "PROBATIONARY_RECOVERY"
        if was_in_probation:
            record.status = "QUARANTINED_PROBATION"
            record.quarantined_at = utc_now()
            record.consecutive_deceptive_count = 6
            record.polling_backoff_factor = 64.0
            record.redemption_progress_pct = 0.0
            record.distinct_clean_subjects_json = "[]"

        # Downward penalty formula: delta_R = -15.0 * severity * confidence
        conf = audit_report.confidence_score or 1.0
        penalty = 15.0 * (max_severity / 2.0) * conf
        record.reputation_score = max(0.0, round(record.reputation_score - penalty, 1))

        # Quarantine check (if not already handled by probation relapse)
        if not was_in_probation:
            if record.reputation_score <= 20.0 or record.consecutive_deceptive_count >= 3:
                record.status = "QUARANTINED_PROBATION"
                if not record.quarantined_at:
                    record.quarantined_at = utc_now()
                record.polling_backoff_factor = calculate_polling_backoff(record.consecutive_deceptive_count)
                record.redemption_progress_pct = 0.0
            elif record.reputation_score <= 40.0:
                record.status = "SUSPICIOUS"

    elif is_clean:
        record.consecutive_deceptive_count = 0
        record.consecutive_clean_count += 1
        record.clean_audits_count += 1

        # Upward recovery formula: delta_R = +5.0 * (1.0 - suspicion/100.0)
        gain = 5.0 * (1.0 - (suspicion / 100.0))
        record.reputation_score = min(100.0, round(record.reputation_score + gain, 1))

        # Subject diversity tracking for BuzzFeed News Doctrine
        subjects: Set[str] = set()
        try:
            subjects = set(json.loads(record.distinct_clean_subjects_json or "[]"))
        except Exception:
            subjects = set()

        if subject_id:
            subjects.add(subject_id)
        record.distinct_clean_subjects_json = json.dumps(sorted(list(subjects)))

        # Evaluate BuzzFeed News Doctrine Redemption
        if record.status in ("QUARANTINED_PROBATION", "PROBATIONARY_RECOVERY"):
            # Progress calculation (needs 5 clean audits + >=2 distinct subjects)
            clean_steps = min(5, record.consecutive_clean_count)
            subject_bonus = 20.0 if len(subjects) >= 2 else 0.0
            record.redemption_progress_pct = round(min(100.0, (clean_steps * 16.0) + subject_bonus), 1)

            # Graduation milestone
            if record.consecutive_clean_count >= 5 and len(subjects) >= 2:
                if record.status == "QUARANTINED_PROBATION":
                    record.status = "PROBATIONARY_RECOVERY"
                    record.graduated_at = utc_now()
                    record.polling_backoff_factor = max(1.0, record.polling_backoff_factor / 4.0)
                elif record.status == "PROBATIONARY_RECOVERY" and record.reputation_score >= 50.0:
                    record.status = "NEUTRAL"
                    record.polling_backoff_factor = 1.0
                    record.redemption_progress_pct = 100.0

        elif record.reputation_score >= 75.0 and record.consecutive_clean_count >= 3:
            record.status = "TRUSTED"
            record.polling_backoff_factor = 1.0
        elif record.reputation_score >= 45.0:
            record.status = "NEUTRAL"
            record.polling_backoff_factor = 1.0

    session.add(record)
    await session.commit()
    await session.refresh(record)

    # Sync backoff factor to active feed subscriptions for this domain
    stmt_subs = select(FeedSubscriptionRecord)
    subs = (await session.exec(stmt_subs)).all()
    for sub in subs:
        if normalize_domain(sub.feed_url) == domain:
            # Base interval is typically 900s (15m)
            sub.polling_interval_seconds = int(900 * record.polling_backoff_factor)
            session.add(sub)
    await session.commit()

    return record


async def get_domain_quarantine_list(
    session: AsyncSession,
) -> List[Dict[str, Any]]:
    """Return all currently quarantined or suspicious domains with backoff multipliers."""
    stmt = (
        select(DomainReputationRecord)
        .where(
            col(DomainReputationRecord.status).in_(
                ["QUARANTINED_PROBATION", "PROBATIONARY_RECOVERY", "SUSPICIOUS"]
            )
        )
        .order_by(col(DomainReputationRecord.reputation_score).asc())
    )
    records = (await session.exec(stmt)).all()

    return [
        {
            "domain": r.domain,
            "reputation_score": r.reputation_score,
            "status": r.status,
            "polling_backoff_factor": r.polling_backoff_factor,
            "audits_count": r.audits_count,
            "consecutive_deceptive_count": r.consecutive_deceptive_count,
            "consecutive_clean_count": r.consecutive_clean_count,
            "redemption_progress_pct": r.redemption_progress_pct,
            "quarantined_at": r.quarantined_at.isoformat() if r.quarantined_at else None,
            "last_audited_at": r.last_audited_at.isoformat() if r.last_audited_at else None,
        }
        for r in records
    ]
