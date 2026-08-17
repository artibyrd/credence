"""Interactive Textual Terminal User Interface (TUI) for Credence.

Provides:
- Live audit dashboard and inspector.
- Recent audit history list with suspicion badges.
- Grounded citation and violation viewer.
- Interactive Taxonomy Catalog browser.
- Cryptographic Node Identity & Attestation manager.
"""

from __future__ import annotations

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

from credence.db import get_session, init_db
from credence.identity import load_or_create_node_identity
from credence.models import AuditRecord, SnapshotRecord, ViolationRecord
from credence.pipeline.evaluator import audit_url
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

    TITLE = "Credence | Epistemic Trust Engine"
    SUB_TITLE = "Autonomous Multi-Agent Evaluation & Trust Network"

    CSS = """
    Screen {
        background: $background;
    }

    #sidebar {
        width: 34;
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

    .metric_title {
        text-style: bold;
    }

    #violations_table {
        height: 12;
        border: solid $secondary;
        margin-bottom: 1;
    }

    #detail_panel {
        height: 1fr;
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
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("slash", "open_audit_dialog", "Audit URL"),
        ("r", "refresh_data", "Refresh"),
        ("t", "switch_to_taxonomies", "Taxonomies"),
        ("i", "switch_to_identity", "Node Identity"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.current_report: Optional[AuditReport] = None
        self.recent_audits: List[AuditRecord] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            # Left Sidebar: Audit History
            with Vertical(id="sidebar"):
                yield Label("📜 Recent Audits", id="history_title")
                yield DataTable(id="history_table")

            # Main View Tabs
            with Container(id="main_container"):
                with TabbedContent(id="tabs"):
                    with TabPane("🛡️ Inspector", id="tab_inspector"):
                        with VerticalScroll():
                            yield Static("No audit selected. Press [bold]/[/bold] to audit a URL.", id="score_banner")
                            yield Label("🚨 Grounded Violations", classes="metric_title")
                            yield DataTable(id="violations_table")
                            yield Label("🔎 Grounded Citation & Evidence Detail", classes="metric_title")
                            yield Static("Select a violation to view details.", id="detail_panel")

                    with TabPane("📚 Taxonomies", id="tab_taxonomies"):
                        yield Tree("Registered Taxonomy Catalogs", id="taxonomy_tree")

                    with TabPane("🔑 Node Identity", id="tab_identity"):
                        yield Static("Loading Node Identity...", id="identity_panel")

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

        # Populate Taxonomy Tree
        self._populate_taxonomy_tree()

        # Populate Node Identity Tab
        self._populate_identity_panel()

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
            )

            self.current_report = report
            self._update_inspector_views(report)
            break

    def _update_inspector_views(self, report: AuditReport) -> None:
        # Update Banner
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

        banner_text = (
            f"{status_badge}  |  Verdict: [bold]{report.classification}[/bold]\n"
            f"[bold]Target URL:[/bold] {report.url}\n"
            f"[bold]Suspicion Score:[/bold] {report.suspicion_score:.1f}/100.0  |  "
            f"[bold]Density:[/bold] {report.suspicion_density:.1f} / 1k words  |  "
            f"[bold]Confidence:[/bold] {report.confidence_score * 100:.0f}%\n"
            f"[bold]Content SHA-256:[/bold] {report.content_sha256[:28]}...  |  "
            f"[bold]Ed25519 Attestation:[/bold] {'[green]✓ Signed[/green]' if report.node_signature else '[yellow]Unsigned[/yellow]'}"
        )
        banner.update(banner_text)

        # Update Violations Table
        v_table = self.query_one("#violations_table", DataTable)
        v_table.clear()
        for idx, v in enumerate(report.violations):
            sev_style = "red" if v.severity >= 4 else ("yellow" if v.severity == 3 else "green")
            excerpt = v.quote_or_element[:32] + "..." if len(v.quote_or_element) > 32 else v.quote_or_element
            v_table.add_row(
                v.rule_id,
                f"[{sev_style}]{v.severity}[/{sev_style}]",
                v.domain[:14],
                excerpt,
                key=str(idx),
            )

        # Reset detail panel
        detail = self.query_one("#detail_panel", Static)
        if report.violations:
            first_v = report.violations[0]
            self._show_violation_detail(first_v)
        else:
            detail.update("[green]✓ No violations discovered on this webpage snapshot.[/green]")

    def _show_violation_detail(self, v: SpecialistViolationFinding) -> None:
        detail = self.query_one("#detail_panel", Static)
        detail_text = (
            f"[bold cyan]{v.rule_id}[/bold cyan] ({v.domain}) - Severity [bold red]{v.severity}/5[/bold red]\n\n"
            f'[bold]Grounded Quote / Element:[/bold]\n[italic]"{v.quote_or_element}"[/italic]\n\n'
            f"[bold]Auditor Reasoning:[/bold]\n{v.reasoning}\n\n"
            f"[dim]Namespaced URI: {v.rule_uri}[/dim]"
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
            self._update_inspector_views(report)
            self.notify(f"Audit completed: {report.classification} ({report.suspicion_score:.1f})")
        except Exception as e:
            banner.update(f"[bold red]❌ Audit failed: {e}[/bold red]")
            self.notify(f"Audit failed: {e}", severity="error")

    async def action_refresh_data(self) -> None:
        """Refresh recent audits from DB."""
        await self.load_recent_audits()
        self.notify("Refreshed recent audits.")

    def action_switch_to_taxonomies(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab_taxonomies"

    def action_switch_to_identity(self) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = "tab_identity"


def run_tui() -> None:
    """Launch the Credence TUI."""
    app = CredenceApp()
    app.run()


if __name__ == "__main__":
    run_tui()
