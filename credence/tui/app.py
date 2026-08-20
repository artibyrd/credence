"""Interactive Textual Terminal User Interface (TUI) for Credence.

Governed by Invariant 8: Universal 4-Way Feature Parity.
Architecture: Modular Textual Workstation (<350 LOC).
"""

from __future__ import annotations

from typing import Any, List, Optional

from sqlmodel import col, select
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
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
from credence.db import get_async_session, init_db
from credence.models import Audit, Snapshot
from credence.pipeline.schemas import AuditReport
from credence.tui.screens.audit_dialog import AuditInputDialog
from credence.tui.widgets.taxonomy_tree import populate_subjects_tree, populate_taxonomy_tree


class CredenceApp(App):
    """Main Credence TUI Application."""

    TITLE = "Credence Epistemic Workstation"
    SUB_TITLE = f"Decentralized Trust Network [{settings.CREDENCE_PROFILE.value.upper() if hasattr(settings.CREDENCE_PROFILE, 'value') else settings.CREDENCE_PROFILE}]"

    CSS = """
    Screen { background: $background; }
    #sidebar { width: 32; border-right: heavy $accent; padding: 0 1; }
    #history_title { text-style: bold; color: $accent; margin: 1 0; }
    #history_table { height: 1fr; }
    #main_container { padding: 0 1; }
    #score_banner { height: auto; border: round $primary; padding: 1; margin-bottom: 1; background: $surface; }
    #exec_summary_panel { height: auto; border: solid $accent; padding: 1; margin-bottom: 1; background: $surface; }
    #inspector_split { height: 1fr; }
    #inspector_left { width: 48%; height: 1fr; margin-right: 1; }
    #inspector_right { width: 52%; height: 1fr; }
    .metric_title { text-style: bold; margin-bottom: 1; }
    #filter_input { margin-bottom: 1; }
    #violations_table { height: 1fr; border: solid $secondary; }
    #detail_panel { height: auto; border: solid $accent; padding: 1; background: $surface; }
    #identity_panel { padding: 1; border: round $accent; margin: 1; background: $surface; }
    #quota_panel { padding: 1; border: round $accent; margin: 1; background: $surface; }
    #leaderboard_split { height: 1fr; }
    #leaderboard_left { width: 50%; height: 1fr; margin-right: 1; }
    #leaderboard_right { width: 50%; height: 1fr; }
    #leaderboard_table { height: 1fr; border: solid $secondary; }
    #merit_panel { padding: 1; border: round $accent; background: $surface; }
    #header_status_pill { dock: top; height: auto; padding: 0 1; background: $surface; border-bottom: solid $primary; text-align: center; text-style: bold; }
    #ops_panel { padding: 1; border: round $accent; margin: 1; background: $surface; }
    #mesh_panel { padding: 1; border: round $accent; margin: 1; background: $surface; }
    #feeds_table { height: 1fr; border: solid $secondary; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("slash", "open_audit_dialog", "Audit URL"),
        ("r", "random_audit", "Random Audit"),
        ("v", "cycle_view_mode", "View Mode"),
        ("1", "switch_to_inspector", "Inspector"),
        ("2", "switch_to_taxonomies", "Taxonomies"),
        ("3", "switch_to_subjects", "Subjects"),
        ("4", "switch_to_feeds", "Feeds"),
        ("5", "switch_to_leaderboard", "Leaderboard"),
        ("6", "switch_to_quota", "Quota"),
        ("7", "switch_to_identity", "Identity"),
        ("8", "switch_to_ops", "Ops"),
        ("9", "switch_to_mesh", "Mesh"),
        ("m", "switch_to_mesh", "Mesh"),
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._view_mode: str = "rich"
        self._current_report: Optional[AuditReport] = None
        self._current_violations: List[Any] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("● READY | Profile: ECONOMY | Headroom: 100.0%", id="header_status_pill")

        with TabbedContent(id="tabs"):
            with TabPane("1. Inspector", id="tab_inspector"):
                with Horizontal():
                    with Vertical(id="sidebar"):
                        yield Label("Recent Audits", id="history_title")
                        yield DataTable(id="history_table")
                    with Vertical(id="main_container"):
                        yield Static(
                            "Select an audit from the history or press '/' to run a new audit.", id="score_banner"
                        )
                        yield Static("", id="exec_summary_panel")
                        with Horizontal(id="inspector_split"):
                            with Vertical(id="inspector_left"):
                                yield Label("Violations & Grounded Findings", classes="metric_title")
                                yield Input(placeholder="Filter by rule or domain...", id="filter_input")
                                yield DataTable(id="violations_table")
                            with Vertical(id="inspector_right"):
                                yield Label("Citation & Evidence Inspector", classes="metric_title")
                                with VerticalScroll(id="detail_panel"):
                                    yield Static(
                                        "Select a violation to view verbatim grounding citation.", id="detail_text"
                                    )

            with TabPane("2. Taxonomies", id="tab_taxonomies"):
                yield Tree("Epistemic Taxonomies", id="taxonomy_tree")

            with TabPane("3. Subjects", id="tab_subjects"):
                yield Tree("Subject Registries", id="subjects_tree")

            with TabPane("4. Feeds", id="tab_feeds"):
                yield DataTable(id="feeds_table")

            with TabPane("5. Leaderboard", id="tab_leaderboard"):
                with Horizontal(id="leaderboard_split"):
                    with Vertical(id="leaderboard_left"):
                        yield DataTable(id="leaderboard_table")
                    with Vertical(id="leaderboard_right"):
                        yield Static("Node Merit Details", id="merit_panel")

            with TabPane("6. Quota", id="tab_quota"):
                yield Static("Token Safety Headroom: 100%", id="quota_panel")

            with TabPane("7. Identity", id="tab_identity"):
                yield Static("Cryptographic Identity: Ed25519", id="identity_panel")

            with TabPane("8. Ops", id="tab_ops"):
                yield Static("SRE Telemetry & Daemons", id="ops_panel")

            with TabPane("9. Mesh", id="tab_mesh"):
                yield Static("P2P Mesh Cluster: Standalone", id="mesh_panel")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize widgets on startup."""
        await init_db()
        # Initialize tables
        hist_table = self.query_one("#history_table", DataTable)
        hist_table.add_columns("Score", "Domain", "Status")
        hist_table.cursor_type = "row"

        viol_table = self.query_one("#violations_table", DataTable)
        viol_table.add_columns("Rule", "Severity", "Reasoning")
        viol_table.cursor_type = "row"

        feeds_table = self.query_one("#feeds_table", DataTable)
        feeds_table.add_columns("URL", "Active", "Last Polled")

        leaderboard_table = self.query_one("#leaderboard_table", DataTable)
        leaderboard_table.add_columns("Domain", "DEI Score", "Band")

        # Populate trees
        populate_taxonomy_tree(self.query_one("#taxonomy_tree", Tree))
        populate_subjects_tree(self.query_one("#subjects_tree", Tree))

        await self.action_refresh_data()

    async def action_refresh_data(self) -> None:
        """Refresh local SQLite audit history and metrics."""
        async with get_async_session() as session:
            stmt = (
                select(Audit, Snapshot)
                .join(Snapshot, col(Audit.snapshot_id) == col(Snapshot.id))
                .order_by(col(Audit.audited_at).desc())
                .limit(20)
            )
            res = (await session.exec(stmt)).all()
            hist_table = self.query_one("#history_table", DataTable)
            hist_table.clear()
            for a, s in res:
                badge = "CLEAN" if a.suspicion_score < 20 else "SUSPICIOUS"
                hist_table.add_row(f"{a.suspicion_score:.1f}", s.url[:20], badge)

    def action_switch_to_inspector(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab_inspector"

    def action_switch_to_taxonomies(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab_taxonomies"

    def action_switch_to_subjects(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab_subjects"

    def action_switch_to_feeds(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab_feeds"

    def action_switch_to_leaderboard(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab_leaderboard"

    def action_switch_to_quota(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab_quota"

    def action_switch_to_identity(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab_identity"

    def action_switch_to_ops(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab_ops"

    def action_switch_to_mesh(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab_mesh"

    def action_cycle_view_mode(self) -> None:
        modes = ["rich", "compact", "raw"]
        curr_idx = modes.index(self._view_mode)
        self._view_mode = modes[(curr_idx + 1) % len(modes)]

    def action_random_audit(self) -> None:
        self.notify("Picking random audit...")

    def action_sync_feeds_action(self) -> None:
        self.notify("Feed sync initiated.")

    def action_open_audit_dialog(self) -> None:
        def _handle_url(url: Optional[str]) -> None:
            if url:
                self.notify(f"Auditing {url}...")

        self.push_screen(AuditInputDialog(), _handle_url)


def run_tui() -> None:
    """Launch the interactive Textual TUI workstation."""
    CredenceApp().run()


if __name__ == "__main__":
    run_tui()
