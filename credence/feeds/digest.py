"""Morning Epistemic Digest Generator for Credence.

Compiles a daily executive intelligence briefing from audited feed items:
- Clean & Verified Investigative Journalism (Score <= 15.0)
- Rhetorical Fallacies & Clickbait Warnings (Score 15.0 .. 70.0)
- Deceptive Claims & Manipulative Dark Patterns (Score > 70.0)
- Verified Satire & Parody (Score 0.00)
- Swarm Compute Savings & Domain Entropy Metrics
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from credence.models import AuditRecord, SnapshotRecord, ViolationRecord

console = Console()


@dataclass
class DigestItem:
    url: str
    title: str
    suspicion_score: float
    verdict: str
    is_satire: bool
    grounded_violations_count: int
    top_violation_rule: Optional[str] = None
    sample_quote: Optional[str] = None
    feed_title: Optional[str] = None
    discovered_at: Optional[datetime] = None


@dataclass
class MorningEpistemicDigest:
    generated_at: datetime
    timeframe_hours: int
    total_articles_evaluated: int
    clean_articles_count: int
    flagged_articles_count: int
    satire_articles_count: int
    mesh_adoptions_count: int
    estimated_tokens_saved: int
    estimated_usd_saved: float
    clean_items: List[DigestItem] = field(default_factory=list)
    warning_items: List[DigestItem] = field(default_factory=list)
    deceptive_items: List[DigestItem] = field(default_factory=list)
    satire_items: List[DigestItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["generated_at"] = self.generated_at.isoformat()
        for key in ("clean_items", "warning_items", "deceptive_items", "satire_items"):
            for item in data.get(key, []):
                if item.get("discovered_at") and hasattr(item["discovered_at"], "isoformat"):
                    item["discovered_at"] = item["discovered_at"].isoformat()
                elif isinstance(item.get("discovered_at"), datetime):
                    item["discovered_at"] = item["discovered_at"].isoformat()
        return data

    def to_markdown(self) -> str:
        md = [
            "# 🌅 Credence Morning Epistemic Digest",
            f"*Generated on {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')} (Past {self.timeframe_hours} Hours)*\n",
            "---",
            "## 📊 Executive Swarm Summary",
            f"- **Total Articles Sifted**: `{self.total_articles_evaluated}`",
            f"- **Clean & Verified Coverage**: `{self.clean_articles_count}`",
            f"- **Questionable / Fallacious / Deceptive**: `{self.flagged_articles_count}`",
            f"- **Verified Satire / Parody**: `{self.satire_articles_count}`",
            f"- **BitTorrent Mesh Compute Savings**: **`{self.estimated_tokens_saved:,}` tokens (~${self.estimated_usd_saved:.2f})** across `{self.mesh_adoptions_count}` zero-token adoptions.\n",
            "---",
        ]

        if self.clean_items:
            md.append("## 🛡️ Clean & Verified Journalism (Top Scored)")
            for item in self.clean_items[:10]:
                md.append(
                    f"- **[{item.title}]({item.url})**  \n  *Score: `{item.suspicion_score:.1f}` | Zero violations detected*"
                )
            md.append("")

        if self.warning_items:
            md.append("## ⚠️ Rhetorical Fallacies & Clickbait Warnings")
            for item in self.warning_items[:10]:
                md.append(
                    f'- **[{item.title}]({item.url})**  \n  *Score: `{item.suspicion_score:.1f}` | Flag: `{item.top_violation_rule}`*  \n  > "{item.sample_quote or "Grounded excerpt"}"'
                )
            md.append("")

        if self.deceptive_items:
            md.append("## 🛑 High Deception & Manipulative Claims")
            for item in self.deceptive_items[:10]:
                md.append(
                    f'- **[{item.title}]({item.url})**  \n  *Score: `{item.suspicion_score:.1f}` | High Severity Flag: `{item.top_violation_rule}`*  \n  > "{item.sample_quote or "Grounded excerpt"}"'
                )
            md.append("")

        if self.satire_items:
            md.append("## 🎭 Verified Satire & Parody (Poe's Law Filtered)")
            for item in self.satire_items[:5]:
                md.append(f"- **[{item.title}]({item.url})**  \n  *Score: `{item.suspicion_score:.1f}` (Neutralized)*")
            md.append("")

        return "\n".join(md)


async def generate_morning_digest(
    session: AsyncSession,
    timeframe_hours: int = 24,
) -> MorningEpistemicDigest:
    """Generate the structured Morning Epistemic Digest from local audit history."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=timeframe_hours)

    # Fetch recent audit records with their snapshot
    stmt = (
        select(AuditRecord, SnapshotRecord)
        .join(SnapshotRecord, col(AuditRecord.snapshot_id) == col(SnapshotRecord.id))
        .where(AuditRecord.audited_at >= cutoff)
    )
    results = (await session.exec(stmt)).all()

    clean_items: List[DigestItem] = []
    warning_items: List[DigestItem] = []
    deceptive_items: List[DigestItem] = []
    satire_items: List[DigestItem] = []

    mesh_adoptions = 0
    tokens_saved = 0

    for rec, snap in results:
        # Fetch associated violations
        stmt_v = select(ViolationRecord).where(ViolationRecord.audit_id == rec.id)
        v_records = (await session.exec(stmt_v)).all()

        top_rule = v_records[0].rule_id if v_records else None
        sample_q = v_records[0].quote_or_element[:60] if v_records and v_records[0].quote_or_element else None

        item = DigestItem(
            url=snap.url,
            title=snap.url.split("/")[-1] or snap.url,
            suspicion_score=rec.suspicion_score,
            verdict=rec.classification,
            is_satire=rec.is_satire,
            grounded_violations_count=len(v_records),
            top_violation_rule=top_rule,
            sample_quote=sample_q,
            discovered_at=rec.audited_at,
        )

        if rec.is_satire:
            satire_items.append(item)
        elif rec.suspicion_score <= 15.0:
            clean_items.append(item)
        elif rec.suspicion_score <= 70.0:
            warning_items.append(item)
        else:
            deceptive_items.append(item)

        if rec.quota_preserved:
            mesh_adoptions += 1
            tokens_saved += 3200

    usd_saved = (tokens_saved / 1_000_000) * 0.30

    digest = MorningEpistemicDigest(
        generated_at=now,
        timeframe_hours=timeframe_hours,
        total_articles_evaluated=len(results),
        clean_articles_count=len(clean_items),
        flagged_articles_count=len(warning_items) + len(deceptive_items),
        satire_articles_count=len(satire_items),
        mesh_adoptions_count=mesh_adoptions,
        estimated_tokens_saved=tokens_saved,
        estimated_usd_saved=round(usd_saved, 3),
        clean_items=clean_items,
        warning_items=warning_items,
        deceptive_items=deceptive_items,
        satire_items=satire_items,
    )

    return digest


def render_digest_terminal(digest: MorningEpistemicDigest) -> None:
    """Render the Morning Epistemic Digest cleanly in the Rich terminal."""
    summary_text = (
        f"[bold cyan]Total Articles Sifted:[/] {digest.total_articles_evaluated}  |  "
        f"[bold green]Clean Verified:[/] {digest.clean_articles_count}  |  "
        f"[bold yellow]Flagged Deceptions:[/] {digest.flagged_articles_count}  |  "
        f"[bold magenta]Satire Cues:[/] {digest.satire_articles_count}\n"
        f"[bold cyan]Swarm Mesh Compute Savings:[/] [green]{digest.estimated_tokens_saved:,} tokens[/] "
        f"([green]${digest.estimated_usd_saved:.2f}[/]) across {digest.mesh_adoptions_count} zero-token adoptions."
    )
    console.print(Panel(summary_text, title="[bold]🌅 Credence Morning Epistemic Briefing[/bold]", border_style="cyan"))

    if digest.clean_items:
        t_clean = Table(title="🛡️ Clean & Verified Journalism", show_header=True, header_style="bold green")
        t_clean.add_column("Score", justify="right", width=7)
        t_clean.add_column("Article URL", style="cyan")
        for it in digest.clean_items[:5]:
            t_clean.add_row(f"{it.suspicion_score:.1f}", it.url)
        console.print(t_clean)

    if digest.warning_items or digest.deceptive_items:
        t_warn = Table(
            title="⚠️ Flagged Cognitive Fallacies & Deceptive Claims", show_header=True, header_style="bold yellow"
        )
        t_warn.add_column("Score", justify="right", width=7)
        t_warn.add_column("Primary Violation", style="bold red", width=16)
        t_warn.add_column("Cited Grounded Excerpt", style="italic")
        for it in (digest.deceptive_items + digest.warning_items)[:5]:
            t_warn.add_row(f"{it.suspicion_score:.1f}", it.top_violation_rule or "Deceptive", it.sample_quote or "")
        console.print(t_warn)
