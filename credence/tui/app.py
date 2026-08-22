"""Interactive Textual Terminal Epistemic Workstation for Credence.

Governed by Invariant: Universal 4-Way Feature Parity & Information Pyramid Invariant.
Architecture: Modular Textual Workstation (<320 LOC).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

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
from credence.db import init_db
from credence.tui.screens.audit_dialog import AuditInputDialog
from credence.tui.screens.info_modal import InfoModalScreen
from credence.tui.widgets.audit_views import format_exec_summary, format_score_banner
from credence.tui.widgets.dossier_views import PUBLISHER_PRESETS, format_publisher_dossier
from credence.tui.widgets.taxonomy_tree import populate_subjects_tree, populate_taxonomy_tree

SAMPLE_AUDIT_PRESETS: List[Dict[str, Any]] = [
    {
        "url": "https://reuters.com/world/energy/clean-grid-transition-2026",
        "title": "Global Clean Energy Investments Hit $2 Trillion Milestone, IEA Reports",
        "suspicion_score": 0.0,
        "classification": "CLEAN",
        "confidence_score": 0.98,
        "suspicion_density": 0.0,
        "is_satire": False,
        "content_sha256": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        "node_pubkey": "ed25519:e4d909c290d0fb1ca068ffaddf22cbd0",
        "simhash_hex": "4a8f9c1e2b3d4f50",
        "executive_summary": "Rigorous empirical wire reporting on international clean energy capacity additions. All statistical figures are explicitly attributed to the International Energy Agency.",
        "violations": [],
    },
    {
        "url": "https://theonion.com/science/astronomers-confirm-universe-expanding-into-neighboring-yard",
        "title": "Astronomers Confirm Universe Expanding Entirely Into Neighboring Yard",
        "suspicion_score": 0.0,
        "classification": "SATIRE_PROTECTED",
        "confidence_score": 1.0,
        "suspicion_density": 0.0,
        "is_satire": True,
        "content_sha256": "sha256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
        "node_pubkey": "ed25519:e4d909c290d0fb1ca068ffaddf22cbd0",
        "simhash_hex": "1020304050607080",
        "executive_summary": "Legitimate hyperbolic satire. Qualifies fully for Poe's Law Safe Harbor with zero defamatory claims.",
        "violations": [],
    },
    {
        "url": "https://dailycaller.com/2026/02/14/secret-subsidies-electric-vehicles-mandate",
        "title": "Secret Bureaucrats Funnel Subsidies to Preferred EV Firms",
        "suspicion_score": 68.4,
        "classification": "SUSPICIOUS",
        "confidence_score": 0.89,
        "suspicion_density": 3.42,
        "is_satire": False,
        "content_sha256": "sha256:3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c",
        "node_pubkey": "ed25519:e4d909c290d0fb1ca068ffaddf22cbd0",
        "simhash_hex": "feedfacecafebabe",
        "executive_summary": "Elevated astroturfing and selective omission. Anonymous assertions of secret subsidies without supporting documentary links.",
        "violations": [
            {
                "rule_id": "SPJ-1.3",
                "severity": 3,
                "reasoning": "Damaging assertions attributed to unnamed 'senior insiders' without independent corroboration.",
                "grounded_quote": "according to senior insiders who spoke on condition of anonymity",
            },
            {
                "rule_id": "IEP-2.4",
                "severity": 4,
                "reasoning": "Cherry-picked quarterly grant data while omitting broader competitive bidding figures.",
                "grounded_quote": "grants were awarded to select favored manufacturers during the spring cycle",
            },
        ],
    },
    {
        "url": "https://inmaricopa.com/breaking/miracle-supplement-cures-all-chronic-illness",
        "title": "Local Clinic Discovers 100% Miracle Cure for Chronic Illness",
        "suspicion_score": 96.2,
        "classification": "PROVEN_HOAX",
        "confidence_score": 0.99,
        "suspicion_density": 8.15,
        "is_satire": False,
        "content_sha256": "sha256:9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e",
        "node_pubkey": "ed25519:e4d909c290d0fb1ca068ffaddf22cbd0",
        "simhash_hex": "deadbeefdeadbeef",
        "executive_summary": "Critical deceptive fabrication. Fabricates medical trial data and masks commercial sales behind fake clinical breakthroughs.",
        "violations": [
            {
                "rule_id": "SPJ-1.6",
                "severity": 5,
                "reasoning": "Malicious health disinformation claiming an unapproved compound cures all illness.",
                "grounded_quote": "guaranteed 100% cure rate with zero clinical side effects in local patient trials",
            },
            {
                "rule_id": "DEC-3.1",
                "severity": 5,
                "reasoning": "Fake system warnings simulating medical authority endorsements.",
                "grounded_quote": "official health advisory: all citizens urged to claim allocation immediately",
            },
        ],
    },
]


class CredenceApp(App):
    """Main Credence Epistemic Workstation TUI Application."""

    TITLE = "Credence Epistemic Workstation"
    SUB_TITLE = f"Decentralized Trust Network [{settings.CREDENCE_PROFILE.value.upper() if hasattr(settings.CREDENCE_PROFILE, 'value') else settings.CREDENCE_PROFILE}]"

    CSS = """
    Screen { background: #0b1120; color: #f8fafc; }
    Header { background: #111b2f; color: #38bdf8; }
    Footer { background: #111b2f; color: #94a3b8; }
    TabbedContent { background: #0b1120; }
    TabPane { background: #0b1120; padding: 0; }
    #sidebar { width: 34; border-right: heavy #1e293b; padding: 0 1; background: #0b1120; }
    #history_title { text-style: bold; color: #38bdf8; margin: 1 0 0 0; }
    #history_table { height: 1fr; background: #111b2f; border: solid #1e293b; }
    #main_container { padding: 0 1; background: #0b1120; }
    #score_banner { height: auto; border: round #38bdf8; padding: 1; margin-bottom: 1; background: #111b2f; }
    #exec_summary_panel { height: auto; border: solid #1e293b; padding: 1; margin-bottom: 1; background: #111b2f; }
    #inspector_split { height: 1fr; }
    #inspector_left { width: 48%; height: 1fr; margin-right: 1; }
    #inspector_right { width: 52%; height: 1fr; }
    .metric_title { text-style: bold; color: #38bdf8; margin-bottom: 1; }
    #filter_input { margin-bottom: 1; background: #111b2f; border: solid #1e293b; color: #fff; }
    #violations_table { height: 1fr; border: solid #1e293b; background: #111b2f; }
    #detail_panel { height: auto; border: solid #1e293b; padding: 1; background: #111b2f; }
    #identity_panel { padding: 1; border: round #38bdf8; margin: 1; background: #111b2f; }
    #quota_panel { padding: 1; border: round #38bdf8; margin: 1; background: #111b2f; }
    #leaderboard_split { height: 1fr; }
    #leaderboard_left { width: 50%; height: 1fr; margin-right: 1; }
    #leaderboard_right { width: 50%; height: 1fr; }
    #leaderboard_table { height: 1fr; border: solid #1e293b; background: #111b2f; }
    #merit_panel { padding: 1; border: round #38bdf8; background: #111b2f; height: 1fr; }
    #header_status_pill { dock: top; height: auto; padding: 0 1; background: #111b2f; border-bottom: solid #38bdf8; text-align: center; text-style: bold; color: #4ade80; }
    #ops_panel { padding: 1; border: round #38bdf8; margin: 1; background: #111b2f; }
    #mesh_panel { padding: 1; border: round #38bdf8; margin: 1; background: #111b2f; }
    #feeds_table { height: 1fr; border: solid #1e293b; background: #111b2f; }
    Tree { background: #111b2f; border: solid #1e293b; padding: 1; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("slash", "open_audit_dialog", "Audit URL"),
        ("r", "random_audit", "Surprise Me"),
        ("v", "cycle_lens_mode", "Epistemic Lens"),
        ("question_mark", "open_info_modal", "Info / Bible"),
        ("i", "open_info_modal", "Info / Bible"),
        ("1", "switch_to_inspector", "Inspector"),
        ("2", "switch_to_taxonomies", "Taxonomies"),
        ("3", "switch_to_subjects", "Subjects"),
        ("4", "switch_to_feeds", "Feeds"),
        ("5", "switch_to_leaderboard", "Dossiers"),
        ("6", "switch_to_quota", "Quota"),
        ("7", "switch_to_identity", "Identity"),
        ("8", "switch_to_ops", "Ops"),
        ("9", "switch_to_mesh", "Mesh"),
        ("m", "switch_to_mesh", "Mesh"),
        ("o", "switch_to_ops", "Ops"),
        ("e", "switch_to_inspector", "Evaluator"),
        ("f", "switch_to_feeds", "Feeds"),
        ("s", "switch_to_subjects", "Subjects"),
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._lens_mode: int = 1  # 1: Surface, 2: Focus, 3: Deep Spectrum
        self._current_item: Any = SAMPLE_AUDIT_PRESETS[0]
        self._current_violations: List[Any] = SAMPLE_AUDIT_PRESETS[0]["violations"]
        self._sample_index: int = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("● READY | Profile: BALANCED | Headroom: 100.0% | G=1.00 Active", id="header_status_pill")

        with TabbedContent(id="tabs"):
            with TabPane("1. Inspector", id="tab_inspector"):
                with Horizontal():
                    with Vertical(id="sidebar"):
                        yield Label("Curated & Recent Audits", id="history_title")
                        yield DataTable(id="history_table")
                    with Vertical(id="main_container"):
                        yield Static("Select an audit from the left or press 'r' for Surprise Me.", id="score_banner")
                        yield Static("", id="exec_summary_panel")
                        with Horizontal(id="inspector_split"):
                            with Vertical(id="inspector_left"):
                                yield Label("Violations & Grounded Citations", classes="metric_title")
                                yield Input(placeholder="Filter by rule or keyword...", id="filter_input")
                                yield DataTable(id="violations_table")
                            with Vertical(id="inspector_right"):
                                yield Label("Citation & Evidence Inspector", classes="metric_title")
                                with VerticalScroll(id="detail_panel"):
                                    yield Static(
                                        "Select a violation to view verbatim grounding citation.", id="detail_text"
                                    )

            with TabPane("2. Taxonomies", id="tab_taxonomies"):
                yield Tree("Epistemic Taxonomies (36 Canonical Rules)", id="taxonomy_tree")

            with TabPane("3. Subjects", id="tab_subjects"):
                yield Tree("Subject Consensus Registries", id="subjects_tree")

            with TabPane("4. Feeds", id="tab_feeds"):
                yield DataTable(id="feeds_table")

            with TabPane("5. Dossiers", id="tab_leaderboard"):
                with Horizontal(id="leaderboard_split"):
                    with Vertical(id="leaderboard_left"):
                        yield DataTable(id="leaderboard_table")
                    with Vertical(id="leaderboard_right"):
                        yield Static("Select a publisher to view longitudinal dossier.", id="merit_panel")

            with TabPane("6. Quota", id="tab_quota"):
                yield Static("Token Safety Headroom: 100% | Circuit Breaker: OK (30% Headroom)", id="quota_panel")

            with TabPane("7. Identity", id="tab_identity"):
                yield Static("Cryptographic Identity: Ed25519 RFC 8785 Envelopes Active", id="identity_panel")

            with TabPane("8. Ops", id="tab_ops"):
                yield Static(
                    "SRE Telemetry: HEALTHY | Excitement: 🔥 HYPER (E:0.96) | Heartbeat: 10m Cron (5 Burst) | Scale-to-Zero ($0.00 Idle)",
                    id="ops_panel",
                )

            with TabPane("9. Mesh", id="tab_mesh"):
                yield Static("P2P Mesh Cluster: Standalone | HRW Rendezvous Hashing Ready", id="mesh_panel")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize widgets and load seed presets."""
        await init_db()
        hist_table = self.query_one("#history_table", DataTable)
        hist_table.add_columns("Score", "Target Domain", "Verdict")
        hist_table.cursor_type = "row"

        viol_table = self.query_one("#violations_table", DataTable)
        viol_table.add_columns("Rule", "Sev", "Finding")
        viol_table.cursor_type = "row"

        feeds_table = self.query_one("#feeds_table", DataTable)
        feeds_table.add_columns("Feed URL", "Status", "Last Polled")

        leaderboard_table = self.query_one("#leaderboard_table", DataTable)
        leaderboard_table.add_columns("Publisher", "DCI", "Trust Tier")
        leaderboard_table.cursor_type = "row"

        for pub in PUBLISHER_PRESETS:
            leaderboard_table.add_row(pub["domain"], pub["dci"], pub["tier"])

        populate_taxonomy_tree(self.query_one("#taxonomy_tree", Tree))
        populate_subjects_tree(self.query_one("#subjects_tree", Tree))

        await self.action_refresh_data()
        self._render_current_item()
        if PUBLISHER_PRESETS:
            self.query_one("#merit_panel", Static).update(format_publisher_dossier(PUBLISHER_PRESETS[0]["domain"]))

    async def action_refresh_data(self) -> None:
        """Refresh audit history from SQLite or sample presets."""
        hist_table = self.query_one("#history_table", DataTable)
        hist_table.clear()
        for p in SAMPLE_AUDIT_PRESETS:
            badge = "CLEAN" if p["suspicion_score"] < 20 else "SUSPICIOUS" if p["suspicion_score"] < 70 else "HOAX"
            if p.get("is_satire"):
                badge = "SATIRE"
            domain = p["url"].split("//")[-1].split("/")[0]
            hist_table.add_row(f"{p['suspicion_score']:.1f}", domain, badge)

    def _render_current_item(self) -> None:
        """Update Inspector views with current audit item and active lens."""
        if not self._current_item:
            return
        banner_widget = self.query_one("#score_banner", Static)
        exec_widget = self.query_one("#exec_summary_panel", Static)
        viol_table = self.query_one("#violations_table", DataTable)

        banner_widget.update(format_score_banner(self._current_item, lens_mode=self._lens_mode))
        exec_widget.update(format_exec_summary(self._current_item, self._current_violations, lens_mode=self._lens_mode))

        viol_table.clear()
        for v in self._current_violations:
            rule_id = v.get("rule_id", "UNKNOWN") if isinstance(v, dict) else getattr(v, "rule_id", "UNKNOWN")
            severity = v.get("severity", 1) if isinstance(v, dict) else getattr(v, "severity", 1)
            reasoning = v.get("reasoning", "") if isinstance(v, dict) else getattr(v, "reasoning", "")
            viol_table.add_row(rule_id, str(severity), reasoning[:30] + "...")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selections in history, violations, or leaderboard tables."""
        if event.data_table.id == "history_table":
            idx = event.cursor_row
            if 0 <= idx < len(SAMPLE_AUDIT_PRESETS):
                self._current_item = SAMPLE_AUDIT_PRESETS[idx]
                self._current_violations = SAMPLE_AUDIT_PRESETS[idx]["violations"]
                self._render_current_item()
        elif event.data_table.id == "leaderboard_table":
            idx = event.cursor_row
            if 0 <= idx < len(PUBLISHER_PRESETS):
                self.query_one("#merit_panel", Static).update(
                    format_publisher_dossier(PUBLISHER_PRESETS[idx]["domain"])
                )
        elif event.data_table.id == "violations_table":
            idx = event.cursor_row
            if 0 <= idx < len(self._current_violations):
                v = self._current_violations[idx]
                quote = v.get("grounded_quote", "") if isinstance(v, dict) else getattr(v, "grounded_quote", "")
                reasoning = v.get("reasoning", "") if isinstance(v, dict) else getattr(v, "reasoning", "")
                detail = f'[bold cyan]Reasoning:[/bold cyan] {reasoning}\n\n[bold green]Verbatim Citation (G=1.00):[/bold green]\n"{quote}"'
                self.query_one("#detail_text", Static).update(detail)

    def action_cycle_lens_mode(self) -> None:
        """Cycle through 3-tier epistemic lenses (1 -> 2 -> 3 -> 1)."""
        self._lens_mode = (self._lens_mode % 3) + 1
        self._render_current_item()
        lens_names = {1: "1. Surface (Glance)", 2: "2. Focus (Evidence & Diffs)", 3: "3. Deep Forensic (Crypto Proof)"}
        self.notify(f"Switched Epistemic Lens: {lens_names[self._lens_mode]}")

    def action_random_audit(self) -> None:
        """Pick next random sample from curated database."""
        self._sample_index = (self._sample_index + 1) % len(SAMPLE_AUDIT_PRESETS)
        self._current_item = SAMPLE_AUDIT_PRESETS[self._sample_index]
        self._current_violations = self._current_item["violations"]
        self._render_current_item()
        self.notify(f"Surprise Me: Loaded '{self._current_item['title'][:30]}...'")

    def action_open_info_modal(self) -> None:
        """Open in-terminal Topic & Invariant Bible modal dialog."""
        self.push_screen(InfoModalScreen())

    def action_open_audit_dialog(self) -> None:
        """Open audit URL prompt modal dialog."""

        def _handle_url(url: Optional[str]) -> None:
            if url:
                self.notify(f"Auditing {url}...")

        self.push_screen(AuditInputDialog(), _handle_url)

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


def run_tui() -> None:
    """Launch the interactive Textual TUI workstation."""
    CredenceApp().run()


if __name__ == "__main__":
    run_tui()
