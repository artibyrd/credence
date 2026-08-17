"""Unit tests for SQLModel schemas, relationships, and SQLite async storage."""

from pathlib import Path

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.db import get_engine, get_session, init_db
from credence.models import AuditRecord, SnapshotRecord, ViolationRecord


@pytest.mark.unit
async def test_create_and_query_snapshot(db_session: AsyncSession) -> None:
    """Verify SnapshotRecord can be inserted and queried asynchronously."""
    snapshot = SnapshotRecord(
        url="https://example.org/test-article",
        content_sha256="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        simhash_64="0x123456789abcdef0",
        title="Test Article Title",
        byline="Jane Doe",
        site_name="Example News",
        clean_text_length=1200,
        word_count=200,
    )
    db_session.add(snapshot)
    await db_session.commit()
    await db_session.refresh(snapshot)

    assert snapshot.id is not None
    assert snapshot.url == "https://example.org/test-article"

    # Query from database
    statement = select(SnapshotRecord).where(SnapshotRecord.url == "https://example.org/test-article")
    result = await db_session.exec(statement)
    found = result.first()

    assert found is not None
    assert found.title == "Test Article Title"
    assert found.clean_text_length == 1200


@pytest.mark.unit
async def test_create_audit_with_satire_flag(db_session: AsyncSession) -> None:
    """Verify AuditRecord properly stores satire flags and Poe's law attributes."""
    snapshot = SnapshotRecord(
        url="https://theonion.com/moon-cheese",
        content_sha256="sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        simhash_64="0xfedcba9876543210",
        is_satire_cue=True,
    )
    db_session.add(snapshot)
    await db_session.commit()
    await db_session.refresh(snapshot)

    audit = AuditRecord(
        snapshot_id=snapshot.id,
        content_sha256=snapshot.content_sha256,
        suspicion_score=0.0,
        suspicion_density=0.0,
        confidence_score=0.95,
        classification="SATIRE_PARODY",
        is_satire=True,
        content_type="SATIRE_PARODY",
        satire_notes="Humorous satire detected via masthead and absurd comedic premise.",
    )
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    assert audit.id is not None
    assert audit.is_satire is True
    assert audit.classification == "SATIRE_PARODY"
    assert audit.suspicion_score == 0.0


@pytest.mark.unit
async def test_violation_records_and_cascade_relationships(db_session: AsyncSession) -> None:
    """Verify child ViolationRecords are saved and linked to AuditRecord."""
    snapshot = SnapshotRecord(
        url="https://example.com/deceptive-ad",
        content_sha256="sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
        simhash_64="0x1122334455667788",
    )
    db_session.add(snapshot)
    await db_session.commit()
    await db_session.refresh(snapshot)

    audit = AuditRecord(
        snapshot_id=snapshot.id,
        content_sha256=snapshot.content_sha256,
        suspicion_score=35.0,
        suspicion_density=5.0,
        classification="SUSPICIOUS",
    )
    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    v1 = ViolationRecord(
        audit_id=audit.id,
        rule_id="SPJ-1.1",
        rule_uri="journalistic-ethics:seek-truth-and-report/SPJ-1.1@v1.0.0",
        domain="JOURNALISTIC_ETHICS",
        cluster_id="SEEK_TRUTH_AND_REPORT",
        severity=3,
        confidence=0.9,
        quote_or_element="Studies prove that 99% of people agree without question.",
        reasoning="Sweeping empirical claim made without study citation or methodology.",
    )
    v2 = ViolationRecord(
        audit_id=audit.id,
        rule_id="DP-2.2",
        rule_uri="deceptive-pattern:emotional-and-social-pressure/DP-2.2@v1.0.0",
        domain="DECEPTIVE_PATTERN",
        cluster_id="EMOTIONAL_AND_SOCIAL_PRESSURE",
        severity=4,
        confidence=1.0,
        quote_or_element="WARNING: Deal expires in 04:59!",
        reasoning="Artificial urgency countdown that resets on page reload.",
    )
    db_session.add(v1)
    db_session.add(v2)
    await db_session.commit()

    # Query violations for the audit
    stmt = select(ViolationRecord).where(ViolationRecord.audit_id == audit.id)
    result = await db_session.exec(stmt)
    violations = result.all()
    assert len(violations) == 2
    rule_ids = {v.rule_id for v in violations}
    assert "SPJ-1.1" in rule_ids
    assert "DP-2.2" in rule_ids


@pytest.mark.unit
async def test_db_init_and_session_generator(tmp_path: Path) -> None:
    """Verify get_engine, init_db, and get_session work with file-backed SQLite."""
    test_db_file = tmp_path / "test_credence.db"
    test_url = f"sqlite+aiosqlite:///{test_db_file}"

    engine = get_engine(test_url)
    await init_db(engine)

    assert test_db_file.exists()

    async for session in get_session():
        snap = SnapshotRecord(
            url="https://example.com/test",
            content_sha256="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            simhash_64="0x0000000000000000",
        )
        session.add(snap)
        await session.commit()
        break
