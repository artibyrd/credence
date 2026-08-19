"""Interactive Textual Terminal User Interface (TUI) for Credence.

Provides:
- Live audit dashboard and inspector.
- Recent audit history list with suspicion badges.
- Grounded citation and violation viewer.
- Interactive Taxonomy Catalog browser.
- Cryptographic Node Identity & Attestation manager.
- Real-time Token Headroom & Quota Circuit Breaker monitor.
"""

from __future__ import annotations

import webbrowser
from pathlib import Path
from typing import List, Optional

from rich.text import Text
from sqlmodel import select
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)

from credence.config import settings
from credence.db import get_session, init_db
from credence.identity import load_or_create_node_identity
from credence.models import AuditRecord, SnapshotRecord, ViolationRecord
from credence.pipeline.evaluator import audit_url
from credence.pipeline.governor import get_token_headroom_status
from credence.pipeline.schemas import AuditReport, SpecialistViolationFinding
from credence.taxonomy_loader import registry


class AuditInputDialog(ModalScreen[Optional[str]]):
    """Modal dialog to input a URL for live auditing."""

    DEFAULT_CSS = """
    AuditInputDialog {
        align: center middle;
    }

    #dialog {
        padding: 1 2;
        width: 70;
        height: 14;
        border: thick $primary;
        background: $surface;
    }

    #dialog Label {
        margin-bottom: 1;
        text-style: bold;
    }

    #dialog Input {
        margin-bottom: 1;
    }

    #dialog Horizontal {
        align: right middle;
    }

    #dialog Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("🌐 Enter Target URL to Audit:")
            yield Input(placeholder="https://... or file:///path/to/fixture.html", id="url_input")
            with Horizontal():
                yield Button("Cancel", variant="default", id="cancel_btn")
                yield Button("Audit", variant="primary", id="audit_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "audit_btn":
            inp = self.query_one("#url_input", Input)
            val = inp.value.strip()
            self.dismiss(val if val else None)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        self.dismiss(val if val else None)


class CredenceApp(App):
    """Main Credence TUI Application."""

    TITLE = "Credence Epistemic Workstation"
    SUB_TITLE = f"Decentralized Trust Network [{settings.CREDENCE_PROFILE.value.upper()}]"

    CSS = """
    Screen {
        background: $background;
    }

    #sidebar {
        width: 32;
        border-right: heavy $accent;
        padding: 0 1;
    }

    #history_title {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }

    #history_table {
        height: 1fr;
    }

    #main_container {
        padding: 0 1;
    }

    #score_banner {
        height: auto;
        border: round $primary;
        padding: 1;
        margin-bottom: 1;
        background: $surface;
    }

    #exec_summary_panel {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
        background: $surface;
    }

    #inspector_split {
        height: 1fr;
    }

    #inspector_left {
        width: 48%;
        height: 1fr;
        margin-right: 1;
    }

    #inspector_right {
        width: 52%;
        height: 1fr;
    }

    .metric_title {
        text-style: bold;
        margin-bottom: 1;
    }

    #filter_input {
        margin-bottom: 1;
    }

    #violations_table {
        height: 1fr;
        border: solid $secondary;
    }

    #detail_panel {
        height: auto;
        border: solid $accent;
        padding: 1;
        background: $surface;
    }

    #identity_panel {
        padding: 1;
        border: round $accent;
        margin: 1;
        background: $surface;
    }

    #quota_panel {
        padding: 1;
        border: round $accent;
        margin: 1;
        background: $surface;
    }

    #leaderboard_split {
        height: 1fr;
    }

    #leaderboard_left {
        width: 50%;
        height: 1fr;
        margin-right: 1;
    }

    #leaderboard_right {
        width: 50%;
        height: 1fr;
    }

    #leaderboard_table {
        height: 1fr;
        border: solid $secondary;
    }

    #merit_panel {
        padding: 1;
        border: round $accent;
        background: $surface;
    }

    #header_status_pill {
        dock: top;
        height: auto;
        padding: 0 1;
        background: $surface;
        border-bottom: solid $primary;
        text-align: center;
        text-style: bold;
    }

    #ops_panel {
        padding: 1;
        border: round $accent;
        margin: 1;
        background: $surface;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("slash", "open_audit_dialog", "Audit URL"),
        ("r", "random_audit", "Random Audit"),
        ("v", "cycle_view_mode", "View Mode (Rich/Compact/JSON)"),
        ("1", "switch_to_inspector", "Inspector"),
        ("2", "switch_to_taxonomies", "Taxonomies"),
        ("3", "switch_to_subjects", "Subjects"),
        ("4", "switch_to_feeds", "Feeds"),
        ("5", "switch_to_leaderboard", "Leaderboard"),
        ("6", "switch_to_quota", "Quota"),
        ("7", "switch_to_identity", "Identity"),
        ("8", "switch_to_ops", "Ops & Alerts"),
        ("o", "open_in_browser", "Open in Web"),
        ("e", "export_report_action", "Export Report"),
        ("f", "focus_filter", "Filter Findings"),
        ("s", "sync_feeds_action", "Sync Feeds"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.current_report: Optional[AuditReport] = None
        self.recent_audits: List[AuditRecord] = []
        self._filter_query: str = ""
        self._view_mode: str = "rich"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("🟢 Node Status: HEALTHY", id="header_status_pill")
        with Horizontal():
            # Left Sidebar: Audit History
            with Vertical(id="sidebar"):
                yield Label("📜 Recent Audits", id="history_title")
                yield DataTable(id="history_table")

            # Main View Tabs
            with Container(id="main_container"):
                with TabbedContent(id="tabs"):
                    with TabPane("🛡️ Inspector", id="tab_inspector"):
                        with Vertical():
                            yield Static("No audit selected. Press [bold]/[/bold] to audit a URL.", id="score_banner")
                            yield Static("Analyzing epistemic signals...", id="exec_summary_panel")
                            with Horizontal(id="inspector_split"):
                                with Vertical(id="inspector_left"):
                                    yield Label("🚨 Grounded Violations", classes="metric_title")
                                    yield Input(
                                        placeholder="🔍 Filter findings (e.g. SPJ, fallacy, critical)...",
                                        id="filter_input",
                                    )
                                    yield DataTable(id="violations_table")
                                with Vertical(id="inspector_right"):
                                    yield Label("🔎 In-Context Evidence & Citation Detail", classes="metric_title")
                                    with VerticalScroll():
                                        yield Static("Select a violation to view details.", id="detail_panel")

                    with TabPane("📚 Taxonomies", id="tab_taxonomies"):
                        yield Tree("Registered Taxonomy Catalogs", id="taxonomy_tree")

                    with TabPane("🧠 Domain Subjects", id="tab_subjects"):
                        yield Tree("Hierarchical Subject Registry", id="subjects_tree")

                    with TabPane("📡 Feeds & Dedup", id="tab_feeds"):
                        yield DataTable(id="feeds_table")

                    with TabPane("🏆 Leaderboard", id="tab_leaderboard"):
                        with Horizontal(id="leaderboard_split"):
                            with Vertical(id="leaderboard_left"):
                                yield Label("🏆 Epistemic Mesh Leaderboard ($Q_i$)", classes="metric_title")
                                yield DataTable(id="leaderboard_table")
                            with Vertical(id="leaderboard_right"):
                                yield Label("🛡️ Local Node Merit & Badges", classes="metric_title")
                                with VerticalScroll():
                                    yield Static("Loading Node Merit Card...", id="merit_panel")

                    with TabPane("🌅 Morning Digest", id="tab_digest"):
                        with VerticalScroll():
                            yield Static("Loading Morning Digest...", id="digest_panel")

                    with TabPane("⚡ Token Quota", id="tab_quota"):
                        yield Static("Loading Token Headroom & Safety Status...", id="quota_panel")

                    with TabPane("🔑 Node Identity", id="tab_identity"):
                        yield Static("Loading Node Identity...", id="identity_panel")

                    with TabPane("🚨 Ops & Alerts", id="tab_ops"):
                        with VerticalScroll():
                            yield Static("Loading Node Telemetry & Alert Status...", id="ops_panel")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize database, populate history table and taxonomy tree."""
        await init_db()
        registry.load_all()

        # Set up history table
        hist_table = self.query_one("#history_table", DataTable)
        hist_table.cursor_type = "row"
        hist_table.add_columns("Score", "Target")

        # Set up violations table
        v_table = self.query_one("#violations_table", DataTable)
        v_table.cursor_type = "row"
        v_table.add_columns("Rule ID", "Sev", "Domain", "Excerpt")

        # Set up feeds table
        feeds_table = self.query_one("#feeds_table", DataTable)
        feeds_table.cursor_type = "row"
        feeds_table.add_columns("Tier", "Title", "Quality (F_j)", "Feed URL", "Subject", "Status")

        # Set up leaderboard table
        lb_table = self.query_one("#leaderboard_table", DataTable)
        lb_table.cursor_type = "row"
        lb_table.add_columns("Rank", "Alias", "Tier", "Score", "Uptime", "Traffic")

        # Populate Views
        self._populate_taxonomy_tree()
        self._populate_subjects_tree()
        await self._populate_feeds_table()
        await self._populate_leaderboard_views()
        await self._populate_digest_panel()
        self._populate_identity_panel()
        await self._populate_quota_panel()
        await self._refresh_telemetry_loopback()

        # Set up periodic telemetry loopback updates (3s interval)
        self.set_interval(3.0, self._refresh_telemetry_loopback)

        # Load recent audits from DB
        await self.load_recent_audits()

    def _populate_taxonomy_tree(self) -> None:
        tree = self.query_one("#taxonomy_tree", Tree)
        tree.root.expand()

        for cat in registry.list_catalogs():
            cat_node = tree.root.add(f"[bold cyan]{cat.catalog_id}[/bold cyan] ({cat.domain}) - v{cat.version}")
            for clus in cat.clusters:
                clus_node = cat_node.add(f"[bold yellow]{clus.cluster_id}[/bold yellow]: {clus.name}")
                for rule in clus.rules:
                    clus_node.add_leaf(f"[bold]{rule.rule_id}[/bold] (Sev {rule.severity}): {rule.name}")

    def _populate_subjects_tree(self) -> None:
        from credence.subjects.registry import get_subject_registry

        tree = self.query_one("#subjects_tree", Tree)
        tree.root.expand()
        reg = get_subject_registry()
        for root in reg.get_hierarchy_tree():
            root_node = tree.root.add(f"[bold cyan]{root['title']}[/bold cyan] ([dim]{root['subject_id']}[/dim])")
            for child in root.get("children", []):
                root_node.add_leaf(f"[bold yellow]{child['title']}[/bold yellow] ([dim]{child['subject_id']}[/dim])")

    async def _populate_feeds_table(self) -> None:
        from sqlmodel import col

        from credence.feeds.health import calculate_feed_quality_score
        from credence.models import FeedSubscriptionRecord

        table = self.query_one("#feeds_table", DataTable)
        table.clear()
        async for session in get_session():
            stmt = select(FeedSubscriptionRecord).order_by(col(FeedSubscriptionRecord.priority_tier).asc())
            subs = (await session.exec(stmt)).all()
            for s in subs:
                metrics = calculate_feed_quality_score([], None)
                status = "[green]ACTIVE[/green]" if s.is_active else "[dim]PAUSED[/dim]"
                table.add_row(
                    f"T{s.priority_tier}",
                    s.title or "(feed)",
                    f"[cyan]{metrics.composite_score_fj:.2f}[/cyan]",
                    s.feed_url,
                    s.subject_tag,
                    status,
                )

    async def _populate_digest_panel(self) -> None:
        from credence.feeds.digest import generate_morning_digest

        panel = self.query_one("#digest_panel", Static)
        async for session in get_session():
            dig = await generate_morning_digest(session, timeframe_hours=24)
            lines = [
                "[bold cyan]🌅 Morning Epistemic Briefing (Past 24h)[/bold cyan]\n",
                f"- [bold]Total Articles Evaluated:[/bold] `{dig.total_articles_evaluated}`",
                f"- [bold]Clean & Verified Coverage:[/bold]  `{dig.clean_articles_count}`",
                f"- [bold]Flagged Deceptions/Fallacies:[/bold] `{dig.flagged_articles_count}`",
                f"- [bold]Verified Satire/Parody:[/bold]     `{dig.satire_articles_count}`",
                f"- [bold]Mesh Compute Savings:[/bold]       [green]{dig.estimated_tokens_saved:,} tokens (${dig.estimated_usd_saved:.2f})[/green] via `{dig.mesh_adoptions_count}` zero-token adoptions.\n",
            ]

            if dig.deceptive_items or dig.warning_items:
                lines.append("[bold yellow]⚠️ Recent Flagged Deceptions & Fallacies:[/bold yellow]")
                for item in (dig.deceptive_items + dig.warning_items)[:5]:
                    lines.append(
                        f"  • [bold red]{item.top_violation_rule or 'Flag'}[/bold red] ({item.suspicion_score:.1f}) - {item.title}"
                    )
                lines.append("")

            if dig.clean_items:
                lines.append("[bold green]🛡️ Top Clean Articles:[/bold green]")
                for item in dig.clean_items[:5]:
                    lines.append(f"  • [green]{item.suspicion_score:.1f}[/green] - {item.title}")

            panel.update("\n".join(lines))
            break

    def _populate_identity_panel(self) -> None:
        panel = self.query_one("#identity_panel", Static)
        identity = load_or_create_node_identity()
        content = (
            f"[bold cyan]Local Node Cryptographic Identity (Ed25519)[/bold cyan]\n\n"
            f"[bold]Public Key (Hex):[/bold] {identity.public_key_hex}\n"
            f"[bold]Keyfile Location:[/bold] {identity.key_path}\n\n"
            f"[green]✓ Node is ready to cryptographically sign and verify epistemic attestations on the Credence Mesh.[/green]"
        )
        panel.update(content)

    async def _populate_quota_panel(self) -> None:
        panel = self.query_one("#quota_panel", Static)
        async for s in get_session():
            status = await get_token_headroom_status(s)
            cb_style = (
                "bold red"
                if status.circuit_breaker_tripped
                else ("bold yellow" if status.throttle_active else "bold green")
            )
            cb_label = (
                "🚨 TRIPPED (QUOTA_PRESERVED)"
                if status.circuit_breaker_tripped
                else ("⚠️ THROTTLED (High Usage)" if status.throttle_active else "🟢 HEALTHY (Normal Concurrency)")
            )

            lines = [
                "[bold cyan]Token Safety Governor & Headroom Budget[/bold cyan]\n",
                f"[bold]Active API Key Source:[/bold] [cyan]{status.active_api_key_source}[/cyan]",
                f"[bold]Circuit Breaker Status:[/bold] [{cb_style}]{cb_label}[/{cb_style}]\n",
                f"[bold]Hourly Token Headroom:[/bold] [green]{status.hourly_headroom_pct:.1f}% remaining[/green] ({status.hourly_tokens_used:,} / {status.hourly_tokens_max:,} tokens)",
                f"[bold]Daily Token Headroom:[/bold]  [green]{status.daily_headroom_pct:.1f}% remaining[/green] ({status.daily_tokens_used:,} / {status.daily_tokens_max:,} tokens)",
                f"[bold]24h Estimated Spend:[/bold]    [yellow]${status.daily_spend_usd:.4f}[/yellow] / ${status.daily_budget_usd:.2f} USD ({status.daily_spend_pct:.1f}% budget used)\n",
                "[dim]The governor protects your Antigravity interactive pairing tokens by falling back to offline heuristics whenever limits are approached.[/dim]",
            ]
            panel.update("\n".join(lines))
            break

    async def load_recent_audits(self) -> None:
        """Query recent audits from SQLite and populate sidebar table."""
        hist_table = self.query_one("#history_table", DataTable)
        hist_table.clear()

        async for s in get_session():
            stmt = select(AuditRecord).order_by(AuditRecord.audited_at.desc()).limit(25)  # type: ignore[attr-defined]
            records = (await s.exec(stmt)).all()
            self.recent_audits = list(records)

            for rec in self.recent_audits:
                snap_stmt = select(SnapshotRecord).where(SnapshotRecord.id == rec.snapshot_id)
                snap = (await s.exec(snap_stmt)).first()
                label = snap.title[:18] if snap and snap.title else (snap.url[:18] if snap else rec.content_sha256[:12])

                score_style = (
                    "cyan"
                    if rec.is_satire
                    else ("green" if rec.suspicion_score <= 15 else ("yellow" if rec.suspicion_score <= 40 else "red"))
                )
                score_str = f"[{score_style}]{rec.suspicion_score:.0f}[/{score_style}]"
                if rec.is_satire:
                    score_str = "[cyan]SAT[/cyan]"

                hist_table.add_row(Text.from_markup(score_str), label, key=str(rec.id))

            if self.recent_audits:
                await self.display_audit_record(self.recent_audits[0])
            break

    async def display_audit_record(self, audit: AuditRecord) -> None:
        """Display an audit record in the main inspector."""
        async for s in get_session():
            snap_stmt = select(SnapshotRecord).where(SnapshotRecord.id == audit.snapshot_id)
            snap = (await s.exec(snap_stmt)).first()

            v_stmt = select(ViolationRecord).where(ViolationRecord.audit_id == audit.id)
            violations = (await s.exec(v_stmt)).all()

            violations_schemas = [
                SpecialistViolationFinding(
                    rule_id=v.rule_id,
                    rule_uri=v.rule_uri,
                    domain=v.domain,
                    cluster_id=v.cluster_id,
                    severity=v.severity,
                    confidence=v.confidence,
                    quote_or_element=v.quote_or_element,
                    reasoning=v.reasoning,
                    line_or_selector=v.line_or_selector,
                    is_grounded=True,
                )
                for v in violations
            ]

            report = AuditReport(
                url=snap.url if snap else "Unknown",
                content_sha256=audit.content_sha256,
                simhash_64=snap.simhash_64 if snap else "0x0000000000000000",
                audited_at=audit.audited_at,
                suspicion_score=audit.suspicion_score,
                suspicion_density=audit.suspicion_density,
                confidence_score=audit.confidence_score,
                classification=audit.classification,
                is_satire=audit.is_satire,
                content_type=audit.content_type,
                satire_notes=audit.satire_notes,
                violations=violations_schemas,
                node_pubkey=audit.node_pubkey,
                node_signature=audit.node_signature,
                quota_preserved=audit.quota_preserved,
            )

            self.current_report = report
            self._update_inspector_views(report)
            break

    def _generate_exec_summary(self, report: AuditReport) -> str:
        """Generate human-readable plain-English takeaway for TUI."""
        if report.is_satire:
            return (
                "[bold cyan]🧠 Human Takeaway:[/bold cyan] "
                "This publication was classified as [bold]Legitimate Satire / Parody[/bold]. "
                "Under Poe's Law neutrality rules, legitimate humor and exaggeration are neutralized to a 0.0 suspicion score."
            )
        if report.suspicion_score <= 15.0:
            return (
                "[bold green]🧠 Human Takeaway:[/bold green] "
                "This article exhibits [bold]high epistemic integrity[/bold] with verifiable factual citations, "
                "transparent author sourcing, and zero deceptive interface patterns."
            )

        fallacy_count = sum(1 for v in report.violations if v.domain == "LOGICAL_FALLACY")
        ethics_count = sum(1 for v in report.violations if v.domain == "JOURNALISTIC_ETHICS")
        deceptive_count = sum(1 for v in report.violations if v.domain == "DECEPTIVE_PATTERN")

        concerns = []
        if deceptive_count:
            concerns.append(f"[bold red]{deceptive_count} deceptive pattern(s)[/bold red]")
        if fallacy_count:
            concerns.append(f"[bold yellow]{fallacy_count} logical fallacy(ies)[/bold yellow]")
        if ethics_count:
            concerns.append(f"[bold yellow]{ethics_count} journalistic sourcing violation(s)[/bold yellow]")

        concern_str = ", ".join(concerns) if concerns else "minor structural anomalies"
        return (
            f"[bold dark_orange]🧠 Human Takeaway:[/bold dark_orange] "
            f"Multi-agent specialists flagged {concern_str}. "
            f"Readers are advised to verify primary sources before sharing."
        )

    def _update_inspector_views(self, report: AuditReport) -> None:
        # 1. Update Score Banner
        banner = self.query_one("#score_banner", Static)
        if report.is_satire:
            status_badge = "[bold cyan]🎭 SATIRE / PARODY (Poe's Law Neutralized)[/bold cyan]"
        elif report.suspicion_score <= 15:
            status_badge = "[bold green]🛡️ CLEAN CONTENT[/bold green]"
        elif report.suspicion_score <= 40:
            status_badge = "[bold yellow]⚠️ LOW SUSPICION[/bold yellow]"
        elif report.suspicion_score <= 70:
            status_badge = "[bold dark_orange]🚨 SUSPICIOUS[/bold dark_orange]"
        else:
            status_badge = "[bold red]🛑 HIGHLY DECEPTIVE[/bold red]"

        mode_badge = f"[magenta][{self._view_mode.upper()} VIEW][/magenta]"
        banner_text = (
            f"{status_badge}  |  Verdict: [bold]{report.classification}[/bold]  {mode_badge}\n"
            f"[bold]Target URL:[/bold] {report.url}\n"
            f"[bold]Suspicion Score:[/bold] {report.suspicion_score:.1f}/100.0  |  "
            f"[bold]Density:[/bold] {report.suspicion_density:.1f} / 1k words  |  "
            f"[bold]Confidence:[/bold] {report.confidence_score * 100:.0f}%\n"
            f"[bold]Content SHA-256:[/bold] {report.content_sha256[:28]}...  |  "
            f"[bold]Ed25519 Attestation:[/bold] {'[green]✓ Signed[/green]' if report.node_signature else '[yellow]Unsigned[/yellow]'}"
        )
        if report.quota_preserved:
            banner_text += "  |  [yellow]⚡ Quota Preserved (Offline)[/yellow]"

        banner.update(banner_text)

        # 2. Update Executive Summary Panel
        exec_panel = self.query_one("#exec_summary_panel", Static)
        if self._view_mode == "raw":
            exec_panel.update(
                "[bold cyan]Raw JSON Attestation Record (RFC 8785 Schema):[/bold cyan] (Press 'v' to switch mode)"
            )
        elif self._view_mode == "compact":
            exec_panel.update(
                f"[bold yellow]Compact Streamlined Summary:[/bold yellow] {report.classification} ({report.suspicion_score:.1f}/100.0) • Density: {report.suspicion_density:.1f}/1k • {len(report.violations)} finding(s)"
            )
        else:
            exec_panel.update(self._generate_exec_summary(report))

        # 3. Update Detail Panel if in Raw mode
        detail = self.query_one("#detail_panel", Static)
        if self._view_mode == "raw":
            detail.update(f"```json\n{report.model_dump_json(indent=2)}\n```")

        # 4. Update Violations Table with filtering
        self._populate_filtered_violations()

    def _populate_filtered_violations(self) -> None:
        if not self.current_report:
            return

        v_table = self.query_one("#violations_table", DataTable)
        v_table.clear()

        query = self._filter_query.lower().strip()
        filtered_violations = []

        for idx, v in enumerate(self.current_report.violations):
            if query:
                match = (
                    query in v.rule_id.lower()
                    or query in v.domain.lower()
                    or query in v.reasoning.lower()
                    or query in v.quote_or_element.lower()
                )
                if not match:
                    continue
            filtered_violations.append((idx, v))

        for idx, v in filtered_violations:
            sev_style = "red" if v.severity >= 4 else ("yellow" if v.severity == 3 else "green")
            excerpt = v.quote_or_element[:32] + "..." if len(v.quote_or_element) > 32 else v.quote_or_element
            v_table.add_row(
                v.rule_id,
                f"[{sev_style}]{v.severity}/5[/{sev_style}]",
                v.domain[:14],
                excerpt,
                key=str(idx),
            )

        # Reset detail panel
        detail = self.query_one("#detail_panel", Static)
        if filtered_violations:
            self._show_violation_detail(filtered_violations[0][1])
        elif self.current_report.violations:
            detail.update("[yellow]No violations match the active filter query.[/yellow]")
        else:
            detail.update("[green]✓ No violations discovered on this webpage snapshot.[/green]")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle live filter query changes."""
        if event.input.id == "filter_input":
            self._filter_query = event.value
            self._populate_filtered_violations()

    def _show_violation_detail(self, v: SpecialistViolationFinding) -> None:
        detail = self.query_one("#detail_panel", Static)
        sev_color = "red" if v.severity >= 4 else ("yellow" if v.severity == 3 else "green")
        detail_text = (
            f"[bold cyan]{v.rule_id}[/bold cyan] ([dim]{v.domain}[/dim])\n"
            f"[bold]Severity Rating:[/bold] [{sev_color}]{v.severity} / 5[/{sev_color}]  |  "
            f"[bold]Confidence:[/bold] {v.confidence * 100:.0f}%\n\n"
            f"[bold]Grounded Citation / DOM Excerpt:[/bold]\n"
            f'[italic cyan]"{v.quote_or_element}"[/italic cyan]\n\n'
            f"[bold]Specialist Reasoning & Evidence:[/bold]\n"
            f"{v.reasoning}\n\n"
            f"[dim]Canonical URI: {v.rule_uri}[/dim]"
        )
        detail.update(detail_text)

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle selection in history or violations table."""
        if event.data_table.id == "history_table":
            row_key = str(event.row_key.value)
            for audit in self.recent_audits:
                if str(audit.id) == row_key:
                    await self.display_audit_record(audit)
                    break
        elif event.data_table.id == "violations_table" and self.current_report:
            try:
                idx = int(str(event.row_key.value))
                if 0 <= idx < len(self.current_report.violations):
                    self._show_violation_detail(self.current_report.violations[idx])
            except ValueError:
                pass

    def action_focus_filter(self) -> None:
        """Focus the violation filter input bar."""
        inp = self.query_one("#filter_input", Input)
        inp.focus()

    def action_open_in_browser(self) -> None:
        """Open the active audit in the public web report viewer."""
        if not self.current_report:
            self.notify("No active report to open.", severity="warning")
            return

        target_url = f"https://credence.report/viewer.html?q={self.current_report.content_sha256}"
        try:
            webbrowser.open(target_url)
            self.notify(f"Opening report viewer: {target_url}")
        except Exception as e:
            self.notify(f"Failed to open browser: {e}", severity="error")

    def action_export_report_action(self) -> None:
        """Export the current audit report to Markdown on disk."""
        if not self.current_report:
            self.notify("No active report to export.", severity="warning")
            return

        from credence.cli.main import report_to_markdown

        md_content = report_to_markdown(self.current_report)
        out_path = Path("credence_audit_export.md")
        out_path.write_text(md_content, encoding="utf-8")
        self.notify(f"Report exported to {out_path.absolute()}", severity="information")

    def action_open_audit_dialog(self) -> None:
        """Open modal to audit a new URL."""

        def handle_url(url: Optional[str]) -> None:
            if url:
                self.run_worker(self._perform_audit(url), exclusive=True)

        self.push_screen(AuditInputDialog(), handle_url)

    async def _perform_audit(self, url: str) -> None:
        banner = self.query_one("#score_banner", Static)
        banner.update(
            f"[bold yellow]⏳ Evaluating {url}... Dual-capture & multi-agent auditing in progress...[/bold yellow]"
        )

        try:
            report = await audit_url(url, force_refresh=True)
            self.current_report = report
            await self.load_recent_audits()
            await self._populate_quota_panel()
            self._update_inspector_views(report)
            self.notify(f"Audit completed: {report.classification} ({report.suspicion_score:.1f})")
        except Exception as e:
            banner.update(f"[bold red]❌ Audit failed: {e}[/bold red]")
            self.notify(f"Audit failed: {e}", severity="error")

    async def action_random_audit(self) -> None:
        """Select and load a random audit from history."""
        if self.recent_audits:
            import secrets

            chosen = secrets.SystemRandom().choice(self.recent_audits)
            await self.display_audit_record(chosen)
            self.notify(f"Loaded random audit: {chosen.classification} ({chosen.suspicion_score:.1f})")
        else:
            await self.action_refresh_data()

    def action_cycle_view_mode(self) -> None:
        """Cycle through Rich, Compact, and Raw JSON view modes."""
        modes = ["rich", "compact", "raw"]
        current_idx = modes.index(self._view_mode)
        self._view_mode = modes[(current_idx + 1) % len(modes)]
        self.notify(f"Switched view mode to: {self._view_mode.upper()}")
        if self.current_report:
            self._update_inspector_views(self.current_report)

    async def action_refresh_data(self) -> None:
        """Refresh recent audits and quota status from DB."""
        await self.load_recent_audits()
        await self._populate_quota_panel()
        self.notify("Refreshed recent audits and quota metrics.")

    def action_switch_to_inspector(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab_inspector"

    def action_switch_to_taxonomies(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab_taxonomies"

    def action_switch_to_subjects(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab_subjects"

    def action_switch_to_feeds(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab_feeds"

    def action_switch_to_leaderboard(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab_leaderboard"

    def action_switch_to_quota(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab_quota"

    def action_switch_to_identity(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab_identity"

    def action_switch_to_ops(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab_ops"

    async def _refresh_telemetry_loopback(self) -> None:
        from credence.server.app import global_telemetry

        telem = global_telemetry.get_snapshot()
        status = telem.get("status", "healthy")
        counts = telem.get("request_counts", {})
        count_5xx = counts.get("5xx", 0)
        memory_mb = telem.get("memory_mb", 0.0)
        alerts = telem.get("active_alerts", [])

        # Update Header Status Pill
        try:
            pill = self.query_one("#header_status_pill", Static)
            if count_5xx >= 5 or any(a.get("severity") == "critical" for a in alerts):
                pill.update(f"[bold red]🔴 ⚠️ CRITICAL: 5xx Spike Detected ({count_5xx} errors in 5m)[/bold red]")
            elif memory_mb > 850.0:
                pill.update(f"[bold yellow]🟡 WARNING: High Memory Pressure ({memory_mb} MB)[/bold yellow]")
            elif count_5xx > 0:
                pill.update(f"[bold yellow]🟡 WARNING: {count_5xx} 5xx Error(s) in last 5m[/bold yellow]")
            else:
                pill.update(
                    "[bold green]🟢 Node Status: HEALTHY[/bold green] [dim]| Scale-to-Zero Active | No Active Alerts[/dim]"
                )
        except Exception:
            pass

        # Update Ops & Alerts Panel
        try:
            ops = self.query_one("#ops_panel", Static)
            from credence.mesh.stats import calculate_mesh_stats

            stats_data = {}
            try:
                async for session in get_session():
                    stats_data = await calculate_mesh_stats(session, telemetry_snapshot=telem)
            except Exception:
                pass

            my = stats_data.get("my_node", {})
            mesh = stats_data.get("mesh_dynamics", {})
            savings = mesh.get("compute_savings", {})
            v_break = my.get("verdicts_breakdown", {})

            lines = [
                "[bold cyan]🛡️ Credence Node & Mesh Health Dashboard[/bold cyan]\n",
                f"[bold]● Node Status:[/bold]        {'[bold green]HEALTHY[/bold green]' if status == 'healthy' else '[bold red]' + status.upper() + '[/bold red]'}  |  [dim]ID: {my.get('node_id', 'unknown')}[/dim]",
                f"[bold]Active Engine:[/bold]      [cyan]{str(my.get('active_profile', 'BALANCED')).upper()}[/cyan]  |  Merit: [green]{my.get('merit', {}).get('score', 100.0)}[/green] ({my.get('merit', {}).get('tier', 'Verified')})",
                f"[bold]Runtime Uptime:[/bold]     {my.get('uptime_human', str(telem.get('uptime_seconds', 0)) + 's')}",
                f"[bold]Memory RSS:[/bold]         {memory_mb} MB / 850 MB safe ceiling ({round(memory_mb / 850 * 100, 1)}%)",
                f"[bold]Latency Percentiles:[/bold] P50: {telem.get('latencies_ms', {}).get('p50', 0)}ms | P95: {telem.get('latencies_ms', {}).get('p95', 0)}ms\n",
                "[bold]1. MY AUDITING ACTIVITY:[/bold]",
                f"  • Total Audited:    [bold green]{my.get('total_audited_lifetime', 0):,}[/bold green] lifetime ([cyan]{my.get('total_audited_today', 0)} today[/cyan])",
                f"  • Avg Suspicion:    [bold]{my.get('avg_suspicion_score', 0.0)}[/bold] (Grounding: [green]G = {my.get('avg_grounding_quotient', 1.0):.2f}[/green])",
                f"  • Verdict Breakdown: [green]{v_break.get('clean', 0)} Clean[/green] | [yellow]{v_break.get('low_suspicion', 0)} Low Susp[/yellow] | [dark_orange]{v_break.get('suspicious', 0)} Susp[/dark_orange] | [red]{v_break.get('high_deception', 0)} Deceptive[/red] | [cyan]{v_break.get('satire', 0)} Satire[/cyan]\n",
                "[bold]2. P2P MESH & WORK-SHARING:[/bold]",
                f"  • Peer Connections: [bold cyan]{mesh.get('connected_peers_count', 4)} active nodes[/bold cyan] | Bootstrap: [green]CONNECTED[/green]",
                f"  • Compute Savings:  [bold green]{savings.get('tokens_saved_estimate', 0):,} tokens saved[/bold green] ([green]${savings.get('usd_saved_estimate', 0.0):.2f}[/green] avoided via {savings.get('adopted_from_mesh_count', 0)} adoptions)",
                f"  • Safety Margin:    [dim]{mesh.get('byzantine_safety_margin', '3f+1 Verified')}[/dim]\n",
                "[bold]3. SRE TELEMETRY & ALERTS (5m Window):[/bold]",
                f"  • Total Requests:   {counts.get('total', 0)}",
                f"  • 2xx Success:      [green]{counts.get('2xx', 0)}[/green]",
                f"  • 4xx Client Err:   [yellow]{counts.get('4xx', 0)}[/yellow]",
                f"  • 5xx Server Err:   [red]{counts.get('5xx', 0)}[/red]",
            ]
            if alerts:
                lines.append("\n[bold red]Active Incidents & Alerts:[/bold red]")
                for a in alerts:
                    lines.append(
                        f"  • [{a.get('severity', '').upper()}] [bold]{a.get('title', '')}:[/bold] {a.get('message', '')}"
                    )
            else:
                lines.append("  • Active Alerts:    [bold green]0 (Healthy)[/bold green]")

            recent_errs = telem.get("recent_errors", [])
            if recent_errs:
                lines.append("\n[bold yellow]Recent HTTP Error Events:[/bold yellow]")
                for e in recent_errs[:5]:
                    lines.append(
                        f"  • [{e.get('time')}] [red]{e.get('status')}[/red] {e.get('path')} ({e.get('error') or 'HTTP error'})"
                    )

            ops.update("\n".join(lines))
        except Exception:
            pass

    async def _populate_leaderboard_views(self) -> None:
        from credence.mesh.merit import get_leaderboard, get_local_node_merit

        table = self.query_one("#leaderboard_table", DataTable)
        table.clear()
        panel = self.query_one("#merit_panel", Static)

        async for session in get_session():
            entries = await get_leaderboard(session, category="quality", limit=25)
            for e in entries:
                rank_lbl = f"🥇 #{e.rank}" if e.rank == 1 else (f"🥈 #{e.rank}" if e.rank == 2 else f"#{e.rank}")
                traffic_str = (
                    f"[bold green]{e.traffic_class}[/bold green]"
                    if e.traffic_class == "FAST_LANE"
                    else f"[yellow]{e.traffic_class}[/yellow]"
                )
                table.add_row(
                    rank_lbl,
                    e.node_alias,
                    e.tier,
                    f"{e.score:.3f}",
                    f"{e.uptime_ratio * 100:.1f}%",
                    traffic_str,
                )

            card = await get_local_node_merit(session)
            tier_color = "cyan" if card.tier == "ROOT_ANCHOR" else ("magenta" if card.tier == "SPECIALIST" else "green")
            lines = [
                f"[bold]Node Alias:[/bold]       [cyan]{card.node_alias}[/cyan]",
                f"[bold]Epistemic Tier:[/bold]   [{tier_color}]{card.tier}[/{tier_color}] (Rank #{card.rank_overall} of {card.total_nodes})",
                f"[bold]Traffic Status:[/bold]   [bold green]{card.traffic_class}[/bold green]",
                f"[bold]5-Factor Quality:[/bold] [bold]{card.quality_score:.4f}[/bold]",
                f"[bold]Uptime / Grounding:[/bold] {card.uptime_ratio * 100:.1f}% / {card.grounding_ratio * 100:.1f}%",
                "",
                "[bold yellow]⚡ Compute Philanthropy:[/bold yellow]",
                f"  • Tokens Seeded: [bold]{card.tokens_seeded:,}[/bold]",
                f"  • Value Donated: [bold green]${card.usd_saved_estimate:.4f} USD[/bold green]",
                f"  • Galileo Finds: [bold]{card.galileo_discoveries}[/bold]",
                "",
                f"[bold]Earned Badges ({len(card.unlocked_badges)}):[/bold]",
            ]
            for b in card.unlocked_badges:
                lines.append(f"  • {b.icon} [bold]{b.name}[/bold]: {b.description}")

            panel.update("\n".join(lines))
            break

    def action_sync_feeds_action(self) -> None:
        """Trigger background syndicated feed synchronization."""
        self.run_worker(self._perform_feed_sync(), exclusive=True)

    async def _perform_feed_sync(self) -> None:
        from credence.feeds.worker import sync_all_feeds

        self.notify("Synchronizing syndicated feeds and checking mesh effort avoidance...")
        async for session in get_session():
            summary = await sync_all_feeds(session=session, dry_run=False)
            await self._populate_feeds_table()
            self.notify(
                f"Feeds synced: {summary.new_items_discovered} new, {summary.items_adopted_from_mesh} adopted from mesh!"
            )
            break


def run_tui() -> None:
    """Launch the Credence TUI."""
    app = CredenceApp()
    app.run()


if __name__ == "__main__":
    run_tui()
