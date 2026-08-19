"""Automated vector SVG asset exporter for the Credence Textual TUI.

Boots CredenceApp in a headless Textual test pilot, seeds realistic in-memory
fixtures (clean, satire, deceptive clickbait, syndicated feeds, and token governor),
and exports high-resolution vector SVGs to credence-docs/assets/tui/.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import select

from credence.db import get_session
from credence.models import (
    AuditRecord,
    FeedItemRecord,
    FeedSubscriptionRecord,
    SnapshotRecord,
    TokenUsageRecord,
    ViolationRecord,
)
from credence.subjects.registry import get_subject_registry
from credence.taxonomy_loader import registry
from credence.tui.app import CredenceApp


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def seed_tui_fixtures() -> None:
    """Seed comprehensive fixture data for visual documentation capture."""
    registry.load_all()
    sub_reg = get_subject_registry()
    sub_reg.load_catalogs()

    async for session in get_session():
        # Clear any existing records in memory / dev db
        existing_snaps = (await session.exec(select(SnapshotRecord))).all()
        if existing_snaps:
            return  # Already seeded

        # 1. Seed Deceptive Health Clickbait Article
        snap_deceptive = SnapshotRecord(
            url="https://miracle-remedies.example.com/cancer-cure-breakthrough",
            captured_at=utc_now(),
            content_sha256="8f4e2b8c9d1a3e5f7b2c4d6e8a0b1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b",
            simhash_64="0xdeadbeefc001cafe",
            clean_text_length=4250,
            word_count=780,
            title="Miracle Green Tea Extract Cures 100% of Human Cancers in 48 Hours",
            byline="Dr. Health Secret",
            site_name="Miracle Remedies News",
            is_satire_cue=False,
        )
        session.add(snap_deceptive)
        await session.commit()
        await session.refresh(snap_deceptive)

        audit_deceptive = AuditRecord(
            snapshot_id=snap_deceptive.id,
            audited_at=utc_now(),
            content_sha256=snap_deceptive.content_sha256,
            suspicion_score=78.4,
            suspicion_density=3.85,
            confidence_score=0.96,
            classification="HIGHLY_DECEPTIVE",
            is_satire=False,
            content_type="ADVERTORIAL",
            node_pubkey="ed25519:7a4c9f1e8b2d3c4a5b6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c",
            node_signature="ed25519:sig:9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c",
            quota_preserved=False,
            evaluation_method="llm_multi_agent",
        )
        session.add(audit_deceptive)
        await session.commit()
        await session.refresh(audit_deceptive)

        v1 = ViolationRecord(
            audit_id=audit_deceptive.id,
            rule_id="MED-1.2",
            rule_uri="domain:medical/unsubstantiated_cure@1.0.0",
            domain="MEDICAL_HEALTH",
            cluster_id="EFFICACY_CLAIMS",
            severity=5,
            confidence=0.98,
            quote_or_element="Definitively cures 100% of stage 4 human malignancies within 48 hours without chemotherapy or radiation.",
            reasoning="Unsubstantiated medical claim guaranteeing absolute cancer cure rate without peer-reviewed human clinical trials.",
            line_or_selector="article > p:nth-child(3)",
        )
        v2 = ViolationRecord(
            audit_id=audit_deceptive.id,
            rule_id="ETH-2.1",
            rule_uri="domain:journalism/anonymous_conspiracy@1.0.0",
            domain="JOURNALISTIC_ETHICS",
            cluster_id="SOURCING",
            severity=4,
            confidence=0.92,
            quote_or_element="Leading pharmaceutical executives have conspired secretly to suppress this ancient natural herbal secret.",
            reasoning="Unattributed conspiratorial accusation violating standard SPJ verification and attribution guidelines.",
            line_or_selector="article > p:nth-child(5)",
        )
        v3 = ViolationRecord(
            audit_id=audit_deceptive.id,
            rule_id="FALLACY-4.3",
            rule_uri="domain:logic/false_dilemma@1.0.0",
            domain="LOGICAL_FALLACY",
            cluster_id="INFORMAL_FALLACIES",
            severity=3,
            confidence=0.90,
            quote_or_element="Either you drink this concentrated extract daily, or you are completely ignoring modern wellness science.",
            reasoning="False dilemma / false dichotomy forcing a binary choice where multiple nuanced medical options exist.",
            line_or_selector="article > p:nth-child(8)",
        )
        v4 = ViolationRecord(
            audit_id=audit_deceptive.id,
            rule_id="DP-1.1",
            rule_uri="domain:deceptive_patterns/urgency_countdown@1.0.0",
            domain="DECEPTIVE_PATTERN",
            cluster_id="FAUX_URGENCY",
            severity=4,
            confidence=0.95,
            quote_or_element="ONLY 3 BOTTLES REMAINING! Order within 04:59 before this video is permanently censored by authorities.",
            reasoning="Artificial scarcity countdown timer and manufactured platform censorship claim.",
            line_or_selector=".urgent-banner > span",
        )
        session.add_all([v1, v2, v3, v4])

        # 2. Seed Legitimate Satire Article
        snap_satire = SnapshotRecord(
            url="https://theonion.com/scientists-discover-new-form-of-procrastination",
            captured_at=utc_now(),
            content_sha256="4d7c2a1b9e8f0a3b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b",
            simhash_64="0x1234567890abcdef",
            clean_text_length=3100,
            word_count=520,
            title="Scientists Discover Novel Quantum Form of Procrastination",
            byline="Staff Reporter",
            site_name="The Onion",
            is_satire_cue=True,
        )
        session.add(snap_satire)
        await session.commit()
        await session.refresh(snap_satire)

        audit_satire = AuditRecord(
            snapshot_id=snap_satire.id,
            audited_at=utc_now(),
            content_sha256=snap_satire.content_sha256,
            suspicion_score=0.0,
            suspicion_density=0.0,
            confidence_score=0.99,
            classification="SATIRE_PARODY",
            is_satire=True,
            content_type="SATIRE_PARODY",
            satire_notes="Verified legitimate comedic satire via Schema.org/SatiricalArticle cues. Poe's Law neutrality active.",
            node_pubkey="ed25519:7a4c9f1e8b2d3c4a5b6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c",
            node_signature="ed25519:sig:satire123456789",
            quota_preserved=False,
            evaluation_method="llm_multi_agent",
        )
        session.add(audit_satire)

        # 3. Seed Clean Investigative Article
        snap_clean = SnapshotRecord(
            url="https://arstechnica.com/science/2026/08/fusion-breakthrough",
            captured_at=utc_now(),
            content_sha256="1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
            simhash_64="0xfedcba0987654321",
            clean_text_length=6200,
            word_count=1140,
            title="MIT Alcator C-Mod Team Demonstrates Sustained Net Energy Plasma",
            byline="John Timmer",
            site_name="Ars Technica",
            is_satire_cue=False,
        )
        session.add(snap_clean)
        await session.commit()
        await session.refresh(snap_clean)

        audit_clean = AuditRecord(
            snapshot_id=snap_clean.id,
            audited_at=utc_now(),
            content_sha256=snap_clean.content_sha256,
            suspicion_score=8.5,
            suspicion_density=0.0,
            confidence_score=0.98,
            classification="FACTUAL_REPORTING",
            is_satire=False,
            content_type="NEWS_ARTICLE",
            node_pubkey="ed25519:7a4c9f1e8b2d3c4a5b6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c",
            node_signature="ed25519:sig:clean123456789",
            quota_preserved=False,
            evaluation_method="llm_multi_agent",
        )
        session.add(audit_clean)

        # 4. Seed Syndicated Feed Subscriptions
        f1 = FeedSubscriptionRecord(
            feed_url="https://arstechnica.com/feed",
            title="Ars Technica Science & Tech",
            feed_format="rss",
            subject_tag="technology.computing",
            priority_tier=1,
            polling_interval_seconds=600,
            is_active=True,
        )
        f2 = FeedSubscriptionRecord(
            feed_url="https://apnews.com/feed",
            title="Associated Press Top News",
            feed_format="rss",
            subject_tag="journalism.investigative",
            priority_tier=1,
            polling_interval_seconds=300,
            is_active=True,
        )
        f3 = FeedSubscriptionRecord(
            feed_url="https://nature.com/nature/current_issue/rss",
            title="Nature Peer-Reviewed Articles",
            feed_format="rss",
            subject_tag="science.biology",
            priority_tier=1,
            polling_interval_seconds=900,
            is_active=True,
        )
        f4 = FeedSubscriptionRecord(
            feed_url="https://theonion.com/feed",
            title="The Onion Satirical Stream",
            feed_format="rss",
            subject_tag="humor.satire",
            priority_tier=4,
            polling_interval_seconds=1800,
            is_active=True,
            is_satire=True,
        )
        f5 = FeedSubscriptionRecord(
            feed_url="https://reuters.com/tools/rss",
            title="Reuters World Wire",
            feed_format="rss",
            subject_tag="journalism.news",
            priority_tier=2,
            polling_interval_seconds=600,
            is_active=True,
        )
        session.add_all([f1, f2, f3, f4, f5])
        await session.commit()

        # 5. Seed Discovered Feed Items (for Morning Digest & Token Savings)
        for i in range(1, 15):
            item = FeedItemRecord(
                item_url=f"https://apnews.com/article/world-news-{i}",
                feed_id=f2.id,
                title=f"Global Summit Reaches Landmark Epistemic Accord #{i}",
                subject_id="journalism.investigative",
                discovered_at=utc_now(),
                processing_status="mesh_adopted" if i % 2 == 0 else "evaluated",
                adopted_from_node="ed25519:node_peer_42" if i % 2 == 0 else None,
                tokens_saved=3200 if i % 2 == 0 else 0,
            )
            session.add(item)

        # 6. Seed Token Usage for Governor
        for _k in range(5):
            tok = TokenUsageRecord(
                timestamp=utc_now(),
                model_name="gemini-3.7-flash",
                prompt_tokens=1850,
                completion_tokens=420,
                thinking_tokens=1024,
                total_tokens=3294,
                estimated_cost_usd=0.00035,
                caller="specialist_evaluator",
                was_escalated=False,
            )
            session.add(tok)

        await session.commit()
        break


async def export_all_tui_screenshots() -> None:
    """Run Textual pilot and export all required SVG screenshots."""
    output_dir = Path(__file__).resolve().parent.parent.parent / "credence-docs" / "assets" / "tui"
    output_dir.mkdir(parents=True, exist_ok=True)

    await seed_tui_fixtures()

    app = CredenceApp()

    async with app.run_test(size=(120, 36)) as pilot:
        await pilot.pause()

        # 1. Main Inspector (Rich View) with Deceptive Clickbait Article
        app.action_switch_to_inspector()
        await app.load_recent_audits()
        # Select first audit (deceptive clickbait)
        if app.recent_audits:
            await app.display_audit_record(app.recent_audits[0])
        await pilot.pause()
        svg_rich = app.export_screenshot(title="Credence TUI Workstation - Inspector (Rich View)")
        (output_dir / "01-inspector-rich.svg").write_text(svg_rich, encoding="utf-8")
        print(f"✓ Exported: {output_dir / '01-inspector-rich.svg'}")

        # 2. Inspector in Compact View Mode
        app.action_cycle_view_mode()
        await pilot.pause()
        svg_compact = app.export_screenshot(title="Credence TUI Workstation - Compact Digest View")
        (output_dir / "02-inspector-compact.svg").write_text(svg_compact, encoding="utf-8")
        print(f"✓ Exported: {output_dir / '02-inspector-compact.svg'}")

        # 3. Inspector in Raw JSON RFC 8785 Mode
        app.action_cycle_view_mode()
        await pilot.pause()
        svg_raw = app.export_screenshot(title="Credence TUI Workstation - Raw RFC 8785 JSON Schema")
        (output_dir / "03-inspector-raw-json.svg").write_text(svg_raw, encoding="utf-8")
        print(f"✓ Exported: {output_dir / '03-inspector-raw-json.svg'}")

        # Cycle back to Rich View
        app.action_cycle_view_mode()
        await pilot.pause()

        # 4. Satire Article View (Poe's Law Neutralization)
        if len(app.recent_audits) >= 2:
            # Find satire record
            satire_rec = next((r for r in app.recent_audits if r.is_satire), app.recent_audits[1])
            await app.display_audit_record(satire_rec)
            await pilot.pause()
            svg_satire = app.export_screenshot(title="Credence TUI Workstation - Poe's Law Satire Neutralization")
            (output_dir / "04-inspector-satire.svg").write_text(svg_satire, encoding="utf-8")
            print(f"✓ Exported: {output_dir / '04-inspector-satire.svg'}")

        # 5. Taxonomies Hierarchy Tree
        app.action_switch_to_taxonomies()
        await pilot.pause()
        svg_tax = app.export_screenshot(title="Credence TUI Workstation - Registered Taxonomy Catalogs")
        (output_dir / "05-taxonomies-tree.svg").write_text(svg_tax, encoding="utf-8")
        print(f"✓ Exported: {output_dir / '05-taxonomies-tree.svg'}")

        # 6. Domain Subject Registry Hierarchy
        app.action_switch_to_subjects()
        await pilot.pause()
        svg_subj = app.export_screenshot(title="Credence TUI Workstation - Domain Subject Hierarchy")
        (output_dir / "06-domain-subjects.svg").write_text(svg_subj, encoding="utf-8")
        print(f"✓ Exported: {output_dir / '06-domain-subjects.svg'}")

        # 7. Syndicated Feeds Stream & Quality Scores (F_j)
        app.action_switch_to_feeds()
        await pilot.pause()
        svg_feeds = app.export_screenshot(title="Credence TUI Workstation - Syndicated Feeds & Dedup")
        (output_dir / "07-feeds-stream.svg").write_text(svg_feeds, encoding="utf-8")
        print(f"✓ Exported: {output_dir / '07-feeds-stream.svg'}")

        # 8. Morning Epistemic Digest & BitTorrent Mesh Savings
        tabs = app.query_one("#tabs")
        tabs.active = "tab_digest"
        await app._populate_digest_panel()
        await pilot.pause()
        svg_digest = app.export_screenshot(title="Credence TUI Workstation - Morning Epistemic Briefing")
        (output_dir / "08-morning-digest.svg").write_text(svg_digest, encoding="utf-8")
        print(f"✓ Exported: {output_dir / '08-morning-digest.svg'}")

        # 9. Token Safety Governor & Headroom Budget
        app.action_switch_to_quota()
        await app._populate_quota_panel()
        await pilot.pause()
        svg_quota = app.export_screenshot(title="Credence TUI Workstation - Token Quota & Circuit Breaker")
        (output_dir / "09-token-quota.svg").write_text(svg_quota, encoding="utf-8")
        print(f"✓ Exported: {output_dir / '09-token-quota.svg'}")

        # 10. Cryptographic Node Identity (Ed25519)
        app.action_switch_to_identity()
        app._populate_identity_panel()
        await pilot.pause()
        svg_identity = app.export_screenshot(title="Credence TUI Workstation - Cryptographic Node Identity")
        (output_dir / "10-node-identity.svg").write_text(svg_identity, encoding="utf-8")
        print(f"✓ Exported: {output_dir / '10-node-identity.svg'}")

        # 11. Live Audit Modal Dialog
        app.action_switch_to_inspector()
        app.action_open_audit_dialog()
        await pilot.pause()
        svg_modal = app.export_screenshot(title="Credence TUI Workstation - Audit Target URL Modal")
        (output_dir / "11-audit-modal.svg").write_text(svg_modal, encoding="utf-8")
        print(f"✓ Exported: {output_dir / '11-audit-modal.svg'}")


if __name__ == "__main__":
    asyncio.run(export_all_tui_screenshots())
