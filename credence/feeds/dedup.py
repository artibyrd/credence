"""Mesh-Aware Effort Avoidance and Zero-Token Attestation Adoption Protocol.

Allows Credence nodes to inspect existing signed attestations in the local
mesh gossip cache and adopt verified peer evaluations from trusted nodes
(Q_i >= 0.85) at $0.00 token cost — preventing the 'Tragedy of the Compute
Commons' and eliminating redundant LLM evaluations across the network.
"""

from typing import Optional

from sqlmodel import Field, SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.models import Audit, FeedItem, PeerMetric, Snapshot, utc_now


class MeshAttestationLookupResult(SQLModel):
    """Result of querying the mesh attestation cache prior to local LLM ingestion."""

    status: str = Field(..., description="local_cached | mesh_adopted | needs_evaluation")
    adopted_from_node: Optional[str] = None
    audit_record_id: Optional[int] = None
    tokens_saved: int = 0
    suspicion_score: Optional[float] = None
    classification: Optional[str] = None


async def check_mesh_effort_avoidance(
    session: AsyncSession,
    item_url: str,
    content_sha256: Optional[str] = None,
    min_peer_quality: float = 0.85,
) -> MeshAttestationLookupResult:
    """Check if content has already been audited locally or by trusted mesh peers.

    Returns:
        MeshAttestationLookupResult with status:
        - "local_cached": Already evaluated locally.
        - "mesh_adopted": Adopted from a trusted peer ($0.00 token spend).
        - "needs_evaluation": Novel content requiring local pipeline execution.
    """
    # 1. Check local snapshot / audit cache
    stmt_local = (
        select(Audit, Snapshot)
        .join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id))
        .where(Snapshot.url == item_url)
    )
    result_local = await session.exec(stmt_local)
    row = result_local.first()

    if row:
        audit, _ = row
        return MeshAttestationLookupResult(
            status="local_cached",
            adopted_from_node=audit.node_pubkey,
            audit_record_id=audit.id,
            tokens_saved=0,
            suspicion_score=audit.suspicion_score,
            classification=audit.classification,
        )

    # 2. Check if a high-quality mesh peer has signed an attestation for this URL / hash
    if content_sha256:
        stmt_peer = (
            select(Audit).where(Audit.content_sha256 == content_sha256).where(col(Audit.node_pubkey).isnot(None))
        )
        peer_audits = (await session.exec(stmt_peer)).all()

        for peer_audit in peer_audits:
            if not peer_audit.node_pubkey:
                continue

            # Lookup peer quality in PeerMetric
            stmt_quality = select(PeerMetric).where(PeerMetric.node_pubkey == peer_audit.node_pubkey)
            peer_metric = (await session.exec(stmt_quality)).first()

            peer_q = peer_metric.quality_score if peer_metric else 0.5
            if peer_q >= min_peer_quality and peer_audit.node_signature:
                # High-reputation peer verified: Adopt attestation at 0 token cost!
                estimated_tokens_saved = 1450  # Average multi-agent audit token footprint

                # Update FeedItem if present
                stmt_item = select(FeedItem).where(FeedItem.item_url == item_url)
                item_record = (await session.exec(stmt_item)).first()
                if item_record:
                    item_record.processing_status = "mesh_adopted"
                    item_record.adopted_from_node = peer_audit.node_pubkey
                    item_record.tokens_saved = estimated_tokens_saved
                    await session.commit()

                return MeshAttestationLookupResult(
                    status="mesh_adopted",
                    adopted_from_node=peer_audit.node_pubkey,
                    audit_record_id=peer_audit.id,
                    tokens_saved=estimated_tokens_saved,
                    suspicion_score=peer_audit.suspicion_score,
                    classification=peer_audit.classification,
                )

    return MeshAttestationLookupResult(status="needs_evaluation")


async def adopt_peer_attestation(
    session: AsyncSession,
    item_url: str,
    title: str,
    peer_pubkey: str,
    peer_signature: str,
    suspicion_score: float,
    classification: str,
    is_satire: bool,
    content_sha256: str,
    simhash_64: str,
) -> Audit:
    """Explicitly adopt a gossiped peer attestation into the local SQLite database."""
    # Create Snapshot
    snapshot = Snapshot(
        url=item_url,
        title=title,
        content_sha256=content_sha256,
        simhash_64=simhash_64,
        captured_at=utc_now(),
    )
    session.add(snapshot)
    await session.commit()
    await session.refresh(snapshot)

    # Create Audit
    audit = Audit(
        snapshot_id=snapshot.id,  # type: ignore
        content_sha256=content_sha256,
        suspicion_score=suspicion_score,
        confidence_score=0.95,
        classification=classification,
        is_satire=is_satire,
        node_pubkey=peer_pubkey,
        node_signature=peer_signature,
        audited_at=utc_now(),
    )
    session.add(audit)

    # Update or create FeedItem
    stmt_item = select(FeedItem).where(FeedItem.item_url == item_url)
    item_record = (await session.exec(stmt_item)).first()
    if item_record:
        item_record.processing_status = "mesh_adopted"
        item_record.adopted_from_node = peer_pubkey
        item_record.tokens_saved = 1450

    await session.commit()
    await session.refresh(audit)
    return audit
