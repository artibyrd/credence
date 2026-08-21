"""RFC 8785 Canonical Attestation Pack Export & Inoculation Engine."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.config import settings
from credence.identity import canonical_json_bytes, load_or_create_node_identity
from credence.models import Audit, Snapshot, Violation

logger = logging.getLogger("credence.storage.backup.packs")


async def export_attestation_pack(
    session: AsyncSession,
    output_path: Optional[Path] = None,
) -> Path:
    """Export all local audits into an RFC 8785 canonical, signed attestation bundle."""
    identity = load_or_create_node_identity()
    target_file = output_path or (settings.DATA_DIR / "seeds" / "genesis_attestations.json")
    target_file.parent.mkdir(parents=True, exist_ok=True)

    stmt = (
        select(Audit, Snapshot)
        .join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id), isouter=True)
        .order_by(col(Audit.audited_at).desc())
    )
    results = list((await session.exec(stmt)).all())

    attestation_items = []
    for audit, snap in results:
        stmt_v = select(Violation).where(Violation.audit_id == audit.id)
        violations = list((await session.exec(stmt_v)).all())

        item = {
            "content_sha256": audit.content_sha256,
            "url": snap.url if snap else "",
            "title": snap.title if snap else "",
            "byline": snap.byline if snap else "",
            "site_name": snap.site_name if snap else "",
            "simhash_64": snap.simhash_64 if snap else "",
            "suspicion_score": audit.suspicion_score,
            "suspicion_density": audit.suspicion_density,
            "confidence_score": audit.confidence_score,
            "classification": audit.classification,
            "is_satire": audit.is_satire,
            "audited_at": audit.audited_at.isoformat() if audit.audited_at else None,
            "node_pubkey": audit.node_pubkey or identity.public_key_hex,
            "node_signature": audit.node_signature,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "rule_uri": v.rule_uri,
                    "domain": v.domain,
                    "cluster_id": v.cluster_id,
                    "severity": v.severity,
                    "confidence": v.confidence,
                    "quote_or_element": v.quote_or_element,
                    "reasoning": v.reasoning,
                    "line_or_selector": v.line_or_selector,
                }
                for v in violations
            ],
        }
        attestation_items.append(item)

    payload = {
        "protocol": "credence-attestation-pack/1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exporter_node_pubkey": identity.public_key_hex,
        "total_attestations": len(attestation_items),
        "attestations": attestation_items,
    }

    canon_bytes = canonical_json_bytes(payload)
    sig = identity.private_key.sign(canon_bytes)
    payload["bundle_signature"] = sig.hex()

    target_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("📦 Exported %d signed attestations to %s", len(attestation_items), target_file)
    return target_file


async def import_attestation_pack(
    session: AsyncSession,
    pack_path_or_url: str | Path,
) -> Dict[str, Any]:
    """Import and inoculate signed attestations from an attestation bundle with $0.00 token cost."""
    path_obj = Path(pack_path_or_url)
    if not path_obj.exists():
        raise FileNotFoundError(f"Attestation pack not found at {pack_path_or_url}")

    data = json.loads(path_obj.read_text(encoding="utf-8"))
    attestations = data.get("attestations", [])

    adopted_count = 0
    skipped_count = 0

    for item in attestations:
        content_sha = item.get("content_sha256", "")
        url = item.get("url", "")
        if not content_sha:
            continue

        stmt_snap = select(Snapshot).where(Snapshot.content_sha256 == content_sha)
        existing_snap = (await session.exec(stmt_snap)).first()

        if existing_snap:
            skipped_count += 1
            continue

        snap = Snapshot(
            url=url,
            content_sha256=content_sha,
            simhash_64=item.get("simhash_64", ""),
            title=item.get("title", ""),
            byline=item.get("byline", ""),
            site_name=item.get("site_name", ""),
            is_satire_cue=item.get("is_satire", False),
        )
        session.add(snap)
        await session.commit()
        await session.refresh(snap)

        audit = Audit(
            snapshot_id=snap.id,
            content_sha256=content_sha,
            suspicion_score=item.get("suspicion_score", 0.0),
            suspicion_density=item.get("suspicion_density", 0.0),
            confidence_score=item.get("confidence_score", 1.0),
            classification=item.get("classification", "CLEAN"),
            is_satire=item.get("is_satire", False),
            node_pubkey=item.get("node_pubkey"),
            node_signature=item.get("node_signature"),
            quota_preserved=True,
        )
        session.add(audit)
        await session.commit()
        await session.refresh(audit)

        for v in item.get("violations", []):
            viol = Violation(
                audit_id=audit.id,
                rule_id=v.get("rule_id", "GEN-0.0"),
                rule_uri=v.get("rule_uri", ""),
                domain=v.get("domain", "GENERAL"),
                cluster_id=v.get("cluster_id", 0),
                severity=v.get("severity", "LOW"),
                confidence=v.get("confidence", 1.0),
                quote_or_element=v.get("quote_or_element", ""),
                reasoning=v.get("reasoning", ""),
                line_or_selector=v.get("line_or_selector"),
            )
            session.add(viol)

        await session.commit()
        adopted_count += 1

    return {
        "status": "imported",
        "adopted_count": adopted_count,
        "skipped_existing": skipped_count,
        "total_in_pack": len(attestations),
    }
