#!/usr/bin/env python3
"""Scheduled Sentinel Audit Daemon for Antigravity Workflows & Mesh Synchronization.

Orchestrates:
1. Ingestion of Sentinel RSS/Atom feeds and domain sitemaps.
2. Staleness inspection against the active taxonomy composite root hash.
3. Multi-pass cluster-level specialist swarm auditing under Antigravity / AI Studio drivers.
4. Sourcing forensics computation (R_byline, R_single, R_COI, ASI, DCI).
5. Canonical RFC 8785 JSON sealing and Ed25519 node identity attestation.
6. Local SQLite caching and optional mesh submission.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import List

from sqlmodel import select

from credence.db import get_async_session, init_db
from credence.models import Audit, Snapshot
from credence.pipeline.evaluator import audit_url
from credence.pipeline.schemas import AuditReport
from credence.pipeline.scoring import compute_domain_dci
from credence.taxonomy_loader import registry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sentinel_audit")


async def run_sentinel_audit(
    target_urls: List[str],
    force_reaudit: bool = False,
    driver: str = "auto",
) -> List[AuditReport]:
    """Execute scheduled Sentinel audit across target URLs."""
    await init_db()
    registry.load_all()
    current_root = registry.get_composite_catalog_hash()
    logger.info("Sentinel initialized with active Taxonomy Root Hash: %s", current_root)

    reports: List[AuditReport] = []

    async with get_async_session() as session:
        for idx, url in enumerate(target_urls, 1):
            logger.info("[%d/%d] Inspecting Sentinel target: %s", idx, len(target_urls), url)

            # Check existing audit staleness
            if not force_reaudit:
                snap_stmt = select(Snapshot).where(Snapshot.url == url)
                snap = (await session.exec(snap_stmt)).first()
                if snap:
                    aud_stmt = select(Audit).where(Audit.snapshot_id == snap.id).order_by(Audit.audited_at.desc())
                    audit_record = (await session.exec(aud_stmt)).first()
                    if audit_record:
                        try:
                            tax_map = json.loads(audit_record.taxonomies_used_json)
                        except Exception:
                            tax_map = {}
                        is_stale, delta_reasons = registry.is_audit_stale(
                            tax_map, getattr(audit_record, "taxonomy_root_hash", None)
                        )
                        if not is_stale:
                            logger.info(
                                "  ↳ Audit is fresh (hash: %s). Skipping re-audit.",
                                audit_record.taxonomy_root_hash or "legacy",
                            )
                            continue
                        logger.info("  ↳ Audit is STALE (%s). Triggering cluster swarm pass.", "; ".join(delta_reasons))

            # Execute fresh audit
            try:
                report = await audit_url(url, session=session, force_refresh=True)
                reports.append(report)
                logger.info(
                    "  ✓ Audited: Score=%.1f (%s) | Byline=%.0f%% | ASI=%.0f/100",
                    report.suspicion_score,
                    report.classification,
                    report.sourcing_ratios.get("r_byline", 0.0),
                    report.sourcing_ratios.get("asi", 100.0),
                )
            except Exception as e:
                logger.error("  ✗ Evaluation failed for %s: %s", url, e)

    if reports:
        mean_score = sum(r.suspicion_score for r in reports) / len(reports)
        mean_density = sum(r.suspicion_density for r in reports) / len(reports)
        byline_avg = sum(r.sourcing_ratios.get("r_byline", 0.0) for r in reports) / (len(reports) * 100.0)
        dci = compute_domain_dci(mean_score, mean_density, byline_avg)
        logger.info("Sentinel batch complete! Evaluated %d articles. Cohort DCI = %.1f/100.0", len(reports), dci)

    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description="Credence Scheduled Sentinel Audit Daemon")
    parser.add_argument("urls", nargs="*", help="Target URLs to audit")
    parser.add_argument("--force", action="store_true", help="Force re-audit even if taxonomy is fresh")
    parser.add_argument(
        "--driver", default="auto", choices=["auto", "agent", "ai-studio", "ollama"], help="Execution driver"
    )
    args = parser.parse_args()

    target_urls = args.urls or [
        "https://www.inmaricopa.com/copper-sky-land-sale-is-no-scandal/",
        "https://www.inmaricopa.com/a-charter-schools-adds-smartlab-stem-program-growth/",
        "https://www.inmaricopa.com/clean-skies-over-maricopa-as-monsoon-departs/",
    ]

    asyncio.run(run_sentinel_audit(target_urls, force_reaudit=args.force, driver=args.driver))


if __name__ == "__main__":
    main()
