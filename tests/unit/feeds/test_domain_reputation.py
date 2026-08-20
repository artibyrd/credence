"""Hermetic Unit Tests for Domain Reputation, Soft Quarantine Backoff, and the BuzzFeed News Doctrine.

Verifies:
- Asymmetric Bayesian reputation updates (rapid slashing, earned recovery).
- Automatic quarantine transition on severe deceptive streak.
- Exponential polling backoff interval calculation.
- The BuzzFeed News Doctrine redemption milestone (5 clean audits across >=2 subjects).
- Relapse circuit breaker on severity >= 3 violation during probation.
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.feeds.reputation import (
    compute_polling_backoff,
    get_domain_quarantine_list,
    get_or_create_domain_reputation,
    normalize_domain,
    update_domain_reputation,
)
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding


@pytest.mark.unit
def test_normalize_domain() -> None:
    """Verify domain normalization across various URL schemes and www prefixes."""
    assert normalize_domain("https://www.theonion.com/article/123") == "theonion.com"
    assert normalize_domain("http://buzzfeed.com/news") == "buzzfeed.com"
    assert normalize_domain("SUBDOMAIN.EXAMPLE.ORG:8080/path") == "subdomain.example.org"
    assert normalize_domain("") == ""


@pytest.mark.unit
def test_calculate_polling_backoff() -> None:
    """Verify exponential backoff multipliers capped at 64x."""
    assert compute_polling_backoff(0) == 1.0
    assert compute_polling_backoff(1) == 2.0
    assert compute_polling_backoff(2) == 4.0
    assert compute_polling_backoff(3) == 8.0
    assert compute_polling_backoff(4) == 16.0
    assert compute_polling_backoff(5) == 32.0
    assert compute_polling_backoff(6) == 64.0
    assert compute_polling_backoff(10) == 64.0  # Capped at 64x


@pytest.mark.unit
async def test_domain_reputation_slashing_and_quarantine(db_session: AsyncSession) -> None:
    """Verify that a deceptive audit slashes reputation and triggers quarantine backoff."""
    domain = "deceptive-tabloid.xyz"
    rep = await get_or_create_domain_reputation(db_session, domain)
    assert rep.reputation_score == 50.0
    assert rep.status == "NEUTRAL"

    deceptive_report = AuditReport(
        url=f"https://{domain}/fabricated-story",
        content_sha256="sha256:1111222233334444555566667777888899990000111122223333444455556666",
        simhash_64="0x1122334455667788",
        suspicion_score=85.0,
        suspicion_density=6.2,
        confidence_score=0.95,
        classification="DECEPTIVE",
        violations=[
            SpecialistViolationFinding(
                rule_id="SPJ-1.1",
                rule_uri="credence:rule:SPJ-1.1",
                domain="JOURNALISTIC_ETHICS",
                cluster_id="ACCURACY",
                severity=5,
                confidence=0.95,
                quote_or_element="Completely fabricated anonymous quote",
                reasoning="Source does not exist and was invented.",
                is_grounded=True,
            )
        ],
    )

    # 1. First deceptive audit
    rep1 = await update_domain_reputation(db_session, domain, deceptive_report)
    assert rep1.reputation_score < 50.0
    assert rep1.consecutive_deceptive_count == 1

    # 2. Second deceptive audit
    rep2 = await update_domain_reputation(db_session, domain, deceptive_report)
    assert rep2.consecutive_deceptive_count == 2

    # 3. Third deceptive audit triggers quarantine
    rep3 = await update_domain_reputation(db_session, domain, deceptive_report)
    assert rep3.consecutive_deceptive_count == 3
    assert rep3.status == "QUARANTINED_PROBATION"
    assert rep3.polling_backoff_factor >= 8.0
    assert rep3.quarantined_at is not None

    # Quarantine listing check
    quarantine_list = await get_domain_quarantine_list(db_session)
    assert any(q["domain"] == domain for q in quarantine_list)


@pytest.mark.unit
async def test_buzzfeed_news_doctrine_redemption(db_session: AsyncSession) -> None:
    """Verify that 5 consecutive clean audits across >=2 subjects graduate a quarantined domain."""
    domain = "buzzfeed-investigates.org"
    rep = await get_or_create_domain_reputation(db_session, domain)
    # Manually place in quarantine
    rep.status = "QUARANTINED_PROBATION"
    rep.reputation_score = 15.0
    rep.consecutive_deceptive_count = 3
    rep.polling_backoff_factor = 16.0
    db_session.add(rep)
    await db_session.commit()

    clean_report = AuditReport(
        url=f"https://{domain}/investigative-scoop",
        content_sha256="sha256:5555666677778888999900001111222233334444555566667777888899990000",
        simhash_64="0x9988776655443322",
        suspicion_score=4.0,
        suspicion_density=0.04,
        confidence_score=0.98,
        classification="CLEAN",
        violations=[],
    )

    # Clean audits 1 to 4 on subject "journalism.investigative"
    for i in range(1, 5):
        updated = await update_domain_reputation(
            db_session,
            domain,
            clean_report,
            subject_id="journalism.investigative",
        )
        assert updated.consecutive_clean_count == i
        assert updated.status == "QUARANTINED_PROBATION"  # Not yet graduated (needs 5 clean + 2 subjects)

    # Clean audit 5 on distinct subject "finance.corruption" -> triggers BuzzFeed News Doctrine graduation
    graduated = await update_domain_reputation(
        db_session,
        domain,
        clean_report,
        subject_id="finance.corruption",
    )
    assert graduated.consecutive_clean_count == 5
    assert graduated.status == "PROBATIONARY_RECOVERY"
    assert graduated.graduated_at is not None
    assert graduated.polling_backoff_factor < 16.0  # Reduced backoff


@pytest.mark.unit
async def test_relapse_circuit_breaker_during_probation(db_session: AsyncSession) -> None:
    """Verify that any severity >= 3 violation during probation immediately forces relapse to quarantine."""
    domain = "reformed-outlet.com"
    rep = await get_or_create_domain_reputation(db_session, domain)
    rep.status = "PROBATIONARY_RECOVERY"
    rep.reputation_score = 42.0
    rep.polling_backoff_factor = 2.0
    db_session.add(rep)
    await db_session.commit()

    relapse_report = AuditReport(
        url=f"https://{domain}/backslide-story",
        content_sha256="sha256:3333444455556666777788889999000011112222333344445555666677778888",
        simhash_64="0x3344556677889900",
        suspicion_score=65.0,
        suspicion_density=4.5,
        confidence_score=0.92,
        classification="DECEPTIVE",
        violations=[
            SpecialistViolationFinding(
                rule_id="SPJ-1.2",
                rule_uri="credence:rule:SPJ-1.2",
                domain="JOURNALISTIC_ETHICS",
                cluster_id="CORRECTIONS",
                severity=4,
                confidence=0.90,
                quote_or_element="Deceptive stealth edit without retraction notice",
                reasoning="Stealth alteration of material facts without disclosure.",
                is_grounded=True,
            )
        ],
    )

    relapsed = await update_domain_reputation(db_session, domain, relapse_report)
    assert relapsed.status == "QUARANTINED_PROBATION"
    assert relapsed.polling_backoff_factor == 64.0
    assert relapsed.consecutive_clean_count == 0
    assert relapsed.redemption_progress_pct == 0.0
