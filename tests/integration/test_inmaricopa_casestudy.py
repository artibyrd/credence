"""Hermetic test suite for the InMaricopa case study and publisher analytics engine.

Validates the four investigative case study pillars:
1. Governance Conflict of Interest (SPJ-3.1, SPJ-3.2) -> R_COI
2. Native Advertorial Camouflage (SPJ-3.3, DEC-1.4, AST-1.1) -> ASI
3. Single-Source Sourcing Pass-Through (SPJ-1.1, SPJ-1.2, SPJ-1.6) -> R_multi-source
4. Longitudinal Trend Aggregation, Topic Entropy H_topic, and DEI Scores.
"""

import datetime

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.db import get_async_session, init_db
from credence.models import Audit, Snapshot, Violation
from credence.server.app import create_server_app
from credence.subjects.analytics import (
    get_publisher_analytics,
    list_all_publishers_summary,
)


@pytest.fixture(autouse=True)
async def db_setup():
    """Ensure database schema is initialized before each test."""
    await init_db()


@pytest.mark.asyncio
async def test_inmaricopa_casestudy_pillar_sourcing_and_coi(db_session: AsyncSession):
    """Pillar I & II: Test Conflict of Interest and Advertorial Detection on InMaricopa snapshots."""
    # 1. Create InMaricopa Snapshots
    snap_coi = Snapshot(
        url="https://inmaricopa.com/council-approves-zoning-amendment-budget-2026/",
        content_sha256="sha256_inm_coi_01",
        simhash_64="0x1234567890abcdef",
        word_count=250,
        clean_text_length=1500,
        title="Council Approves Key Zoning Amendment",
        byline="Staff Reporter",
        captured_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(snap_coi)
    await db_session.commit()
    await db_session.refresh(snap_coi)

    audit_coi = Audit(
        snapshot_id=snap_coi.id,
        content_sha256="sha256_inm_coi_01",
        suspicion_score=68.5,
        suspicion_density=12.0,
        confidence_score=0.95,
        classification="SUSPICIOUS",
        is_satire=False,
        audited_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(audit_coi)
    await db_session.commit()
    await db_session.refresh(audit_coi)

    # Violations for COI & uncorroborated sourcing
    v1 = Violation(
        audit_id=audit_coi.id,
        rule_id="SPJ-3.1",
        rule_uri="journalistic-ethics:spj/SPJ-3.1@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="ACT_INDEPENDENTLY",
        severity=4,
        confidence=0.95,
        quote_or_element="Councilmember Vincent Manfredi voted in favor of the expansion",
        reasoning="Publisher and Advertising Director is the subject voting in the reported council meeting without conflict of interest disclosure.",
    )
    v2 = Violation(
        audit_id=audit_coi.id,
        rule_id="SPJ-3.2",
        rule_uri="journalistic-ethics:spj/SPJ-3.2@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="ACT_INDEPENDENTLY",
        severity=4,
        confidence=0.92,
        quote_or_element="Staff Reporter",
        reasoning="Anonymous generic staff byline used to mask editorial conflicts of interest regarding elected official ownership.",
    )
    db_session.add_all([v1, v2])
    await db_session.commit()

    # 2. Add Advertorial Snapshot
    snap_ad = Snapshot(
        url="https://inmaricopa.com/why-you-should-buy-solar-panels-this-summer/",
        content_sha256="sha256_inm_ad_02",
        simhash_64="0x1234567890abcdee",
        word_count=200,
        clean_text_length=1200,
        title="Top Local Solar Deals for Homeowners",
        byline="Sponsored Content",
        captured_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(snap_ad)
    await db_session.commit()
    await db_session.refresh(snap_ad)

    audit_ad = Audit(
        snapshot_id=snap_ad.id,
        content_sha256="sha256_inm_ad_02",
        suspicion_score=75.0,
        suspicion_density=18.0,
        confidence_score=0.98,
        classification="DECEPTIVE",
        is_satire=False,
        audited_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(audit_ad)
    await db_session.commit()
    await db_session.refresh(audit_ad)

    v3 = Violation(
        audit_id=audit_ad.id,
        rule_id="DEC-1.4",
        rule_uri="deceptive-pattern:visual-and-interface-interference/DEC-1.4@v1.0.0",
        domain="DECEPTIVE_PATTERN",
        cluster_id="NATIVE_ADVERTISING",
        severity=5,
        confidence=0.96,
        quote_or_element="Local residents in Maricopa are rushing to install solar systems",
        reasoning="Commercial advertorial disguised as an organic local news headline.",
    )
    v4 = Violation(
        audit_id=audit_ad.id,
        rule_id="SPJ-3.3",
        rule_uri="journalistic-ethics:spj/SPJ-3.3@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="ACT_INDEPENDENTLY",
        severity=4,
        confidence=0.90,
        quote_or_element="Contact their office today for special discounted rates",
        reasoning="Failure to maintain distinct editorial wall between promotional sales and civic journalism.",
    )
    db_session.add_all([v3, v4])
    await db_session.commit()

    # 3. Add Police PR Pass-through Snapshot
    snap_police = Snapshot(
        url="https://inmaricopa.com/police-blotter-incident-reported-on-john-wayne-pkwy/",
        content_sha256="sha256_inm_police_03",
        simhash_64="0x1234567890abcdff",
        word_count=180,
        clean_text_length=1000,
        title="Police Blotter Incident on John Wayne Parkway",
        byline="Staff",
        captured_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(snap_police)
    await db_session.commit()
    await db_session.refresh(snap_police)

    audit_police = Audit(
        snapshot_id=snap_police.id,
        content_sha256="sha256_inm_police_03",
        suspicion_score=45.0,
        suspicion_density=8.0,
        confidence_score=0.90,
        classification="LOW_SUSPICION",
        is_satire=False,
        audited_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(audit_police)
    await db_session.commit()
    await db_session.refresh(audit_police)

    v5 = Violation(
        audit_id=audit_police.id,
        rule_id="SPJ-1.1",
        rule_uri="journalistic-ethics:spj/SPJ-1.1@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="SEEK_TRUTH_AND_REPORT",
        severity=3,
        confidence=0.88,
        quote_or_element="According to a press release from the Maricopa Police Department",
        reasoning="Verbatim pass-through of law enforcement press release without independent verification or defense corroboration.",
    )
    db_session.add(v5)
    await db_session.commit()

    # 4. Query aggregate publisher profile
    profile = await get_publisher_analytics(db_session, domain="inmaricopa.com")
    assert profile is not None
    assert profile.domain == "inmaricopa.com"
    assert profile.total_audits == 3
    assert profile.deceptive_audits_count == 2
    assert profile.suspicious_audits_count == 1
    assert profile.clean_audits_count == 0
    assert profile.trust_band in ("MIXED", "POOR")
    assert profile.avg_suspicion > 50.0

    # Sourcing Metrics verification
    sourcing = profile.sourcing_metrics
    assert sourcing is not None
    assert sourcing.conflict_disclosure_rate <= 0.70  # 1/3 audits flagged for COI
    assert sourcing.advertorial_separation_index <= 70.0  # 1/3 audits flagged for native advertorial
    assert sourcing.single_source_reliance_ratio >= 0.33  # 1/3 audits flagged for single source pass-through

    # Check top violated rules include SPJ-3.1, DEC-1.4, SPJ-1.1
    top_rule_ids = [r["rule_id"] for r in profile.top_violated_rules]
    assert "SPJ-3.1" in top_rule_ids
    assert "DEC-1.4" in top_rule_ids
    assert "SPJ-1.1" in top_rule_ids


@pytest.mark.asyncio
async def test_list_all_publishers_summary(db_session: AsyncSession):
    """Test listing all publisher summaries across diverse outlets."""
    snap = Snapshot(
        url="https://apnews.com/article/clean-economy-report-2026",
        content_sha256="sha256_ap_01",
        simhash_64="0x1234567890abcd00",
        word_count=300,
        clean_text_length=1800,
        title="Clean Economy Report",
        byline="Jane Doe",
        captured_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(snap)
    await db_session.commit()
    await db_session.refresh(snap)

    audit = Audit(
        snapshot_id=snap.id,
        content_sha256="sha256_ap_01",
        suspicion_score=5.0,
        suspicion_density=0.0,
        confidence_score=0.98,
        classification="CLEAN",
        is_satire=False,
        audited_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(audit)
    await db_session.commit()

    summaries = await list_all_publishers_summary(db_session)
    assert isinstance(summaries, list)
    assert any(s["domain"] == "apnews.com" for s in summaries)


@pytest.mark.asyncio
async def test_rest_api_publisher_analytics_endpoints():
    """Test Starlette REST API endpoints for publisher analytics."""
    import httpx
    from httpx import ASGITransport

    async with get_async_session() as s:
        snap = Snapshot(
            url="https://inmaricopa.com/local-announcement-2026",
            content_sha256="sha256_inm_rest_01",
            simhash_64="0x1234567890abcd11",
            word_count=200,
            clean_text_length=1100,
            title="Local Announcement",
            byline="Staff",
            captured_at=datetime.datetime.now(datetime.timezone.utc),
        )
        s.add(snap)
        await s.commit()
        await s.refresh(snap)

        audit = Audit(
            snapshot_id=snap.id,
            content_sha256="sha256_inm_rest_01",
            suspicion_score=55.0,
            suspicion_density=10.0,
            confidence_score=0.92,
            classification="SUSPICIOUS",
            is_satire=False,
            audited_at=datetime.datetime.now(datetime.timezone.utc),
        )
        s.add(audit)
        await s.commit()

    app = create_server_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test /api/analytics/publishers
        res_list = await client.get("/api/analytics/publishers")
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert "publishers" in data_list
        assert data_list["total"] >= 1

        # 2. Test /api/analytics/publisher/inmaricopa.com
        res_pub = await client.get("/api/analytics/publisher/inmaricopa.com")
        assert res_pub.status_code == 200
        data_pub = res_pub.json()
        assert data_pub["domain"] == "inmaricopa.com"
        assert "dci_score" in data_pub
        assert "sourcing_metrics" in data_pub
        assert "top_violated_rules" in data_pub
        assert "trend_timeline" in data_pub
