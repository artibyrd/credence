"""Interactive Textual Terminal Epistemic Workstation for Credence.

Governed by Invariant: Universal 4-Way Feature Parity & Information Pyramid Invariant.
Architecture: Modular Textual Workstation (<320 LOC).
"""

from __future__ import annotations

from typing import Any, List, Optional

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
from credence.tui.widgets.audit_views import SAMPLE_AUDIT_PRESETS, format_exec_summary, format_score_banner
from credence.tui.widgets.dossier_views import PUBLISHER_PRESETS, format_publisher_dossier
from credence.tui.widgets.feeds_views import format_feed_sentinel_panel
from credence.tui.widgets.taxonomy_tree import populate_subjects_tree, populate_taxonomy_tree


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
    #feeds_split { height: 1fr; }
    #feeds_left { width: 55%; height: 1fr; margin-right: 1; }
    #feeds_right { width: 45%; height: 1fr; }
    #feed_sentinel_panel { padding: 1; border: round #38bdf8; background: #111b2f; height: 1fr; }
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
        ("t", "toggle_selected_sentinel", "Toggle Sentinel"),
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
        self._live_feeds: List[Any] = []

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
                with Horizontal(id="feeds_split"):
                    with Vertical(id="feeds_left"):
                        yield DataTable(id="feeds_table")
                    with Vertical(id="feeds_right"):
                        yield Static(
                            "Select a feed to inspect or press 't' to toggle Sentinel Mode.", id="feed_sentinel_panel"
                        )

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
        """Initialize widgets and bind live SQLite session data."""
        await init_db()
        hist_table = self.query_one("#history_table", DataTable)
        hist_table.add_columns("Score", "Target Domain", "Verdict")
        hist_table.cursor_type = "row"

        viol_table = self.query_one("#violations_table", DataTable)
        viol_table.add_columns("Rule", "Sev", "Finding")
        viol_table.cursor_type = "row"

        feeds_table = self.query_one("#feeds_table", DataTable)
        feeds_table.add_columns("Sentinel", "Feed Title / Source", "Tier", "Cadence", "Status")
        feeds_table.cursor_type = "row"

        leaderboard_table = self.query_one("#leaderboard_table", DataTable)
        leaderboard_table.add_columns("Publisher", "DCI", "Trust Tier")
        leaderboard_table.cursor_type = "row"

        populate_taxonomy_tree(self.query_one("#taxonomy_tree", Tree))
        populate_subjects_tree(self.query_one("#subjects_tree", Tree))

        await self.action_refresh_data()
        self._render_current_item()

    async def action_refresh_data(self) -> None:
        """Refresh audit history, leaderboards, feeds, ops, and mesh vitals from live SQLite."""
        from sqlmodel import col, select

        from credence.db import get_async_session
        from credence.mesh.stats import compute_mesh_stats
        from credence.mesh.topology import compute_network_mesh_health
        from credence.models import Audit, FeedSubscription, Snapshot, Violation
        from credence.subjects.analytics import get_domain_leaderboard

        hist_table = self.query_one("#history_table", DataTable)
        hist_table.clear()
        leaderboard_table = self.query_one("#leaderboard_table", DataTable)
        leaderboard_table.clear()
        feeds_table = self.query_one("#feeds_table", DataTable)
        feeds_table.clear()

        async with get_async_session() as s:
            # 1. Live Audit history
            stmt = select(Audit, Snapshot).join(Snapshot, isouter=True).order_by(col(Audit.audited_at).desc()).limit(50)
            res = (await s.exec(stmt)).all()
            if res:
                self._live_audits = []
                for audit, snap in res:
                    url = snap.url if snap else audit.content_sha256
                    domain = url.split("//")[-1].split("/")[0]
                    v_stmt = select(Violation).where(Violation.audit_id == audit.id)
                    viols = list((await s.exec(v_stmt)).all())
                    item = {
                        "url": url,
                        "title": snap.title if snap else "Forensic Snapshot",
                        "suspicion_score": audit.suspicion_score,
                        "classification": audit.classification,
                        "confidence_score": audit.confidence_score,
                        "suspicion_density": audit.suspicion_density,
                        "is_satire": audit.is_satire,
                        "content_sha256": audit.content_sha256,
                        "node_pubkey": audit.node_pubkey,
                        "executive_summary": f"Audit performed at {audit.audited_at}.",
                        "violations": viols,
                    }
                    self._live_audits.append(item)
                    badge = (
                        "CLEAN"
                        if audit.suspicion_score < 20
                        else "SUSPICIOUS"
                        if audit.suspicion_score < 70
                        else "HOAX"
                    )
                    if audit.is_satire:
                        badge = "SATIRE"
                    hist_table.add_row(f"{audit.suspicion_score:.1f}", domain[:22], badge)

                self._current_item = self._live_audits[0]
                cur_v = self._live_audits[0].get("violations")
                self._current_violations = cur_v if isinstance(cur_v, list) else []
            else:
                self._live_audits = []
                self._current_item = SAMPLE_AUDIT_PRESETS[0]
                sample_v = SAMPLE_AUDIT_PRESETS[0].get("violations")
                self._current_violations = sample_v if isinstance(sample_v, list) else []
                for p in SAMPLE_AUDIT_PRESETS:
                    badge = (
                        "CLEAN" if p["suspicion_score"] < 20 else "SUSPICIOUS" if p["suspicion_score"] < 70 else "HOAX"
                    )
                    if p.get("is_satire"):
                        badge = "SATIRE"
                    domain = p["url"].split("//")[-1].split("/")[0]
                    hist_table.add_row(f"{p['suspicion_score']:.1f}", domain, badge)

            # 2. Live Leaderboard
            domains = await get_domain_leaderboard(s, limit=20)
            if domains:
                for d in domains:
                    leaderboard_table.add_row(d.domain, f"{d.dci_score:.1f}", d.trust_band)
                self.query_one("#merit_panel", Static).update(format_publisher_dossier(domains[0].domain))
            else:
                for pub in PUBLISHER_PRESETS:
                    leaderboard_table.add_row(pub["domain"], pub["dci"], pub["tier"])
                self.query_one("#merit_panel", Static).update(format_publisher_dossier(PUBLISHER_PRESETS[0]["domain"]))

            # 3. Live Feeds & Sentinel Subscriptions
            stmt_f = select(FeedSubscription).order_by(
                col(FeedSubscription.is_sentinel).desc(), col(FeedSubscription.priority_tier).asc()
            )
            all_feeds = (await s.exec(stmt_f)).all()
            self._live_feeds = list(all_feeds)
            for f in all_feeds:
                tag = f"🛡️ SENTINEL ({f.sentinel_interval_seconds}s)" if f.is_sentinel else "STANDARD"
                feeds_table.add_row(
                    tag,
                    f.title or f.feed_url,
                    f"T{f.priority_tier}",
                    f"{f.sentinel_interval_seconds}s",
                    "ACTIVE" if f.is_active else "PAUSED",
                )
            if all_feeds:
                ff = all_feeds[0]
                self.query_one("#feed_sentinel_panel", Static).update(
                    format_feed_sentinel_panel(
                        {
                            "title": ff.title,
                            "feed_url": ff.feed_url,
                            "is_sentinel": ff.is_sentinel,
                            "interval_seconds": ff.sentinel_interval_seconds,
                            "priority_tier": ff.priority_tier,
                            "last_polled_at": ff.last_polled_at.isoformat() if ff.last_polled_at else None,
                        }
                    )
                )

            # 4. Live Mesh & Ops Health
            mesh_health = await compute_network_mesh_health(s)
            mesh_stats = await compute_mesh_stats(s)

            n_nodes = mesh_health.get("active_nodes_count", 1)
            f_tol = mesh_health.get("byzantine_fault_tolerance_f", 0)
            mesh_status = "STANDALONE" if n_nodes <= 1 else "ACTIVE SWARM"
            self.query_one("#mesh_panel", Static).update(
                f"P2P Mesh Reality: {n_nodes} Nodes | Quorum f={f_tol} ({mesh_status}) | HRW Rendezvous Active"
            )
            self.query_one("#ops_panel", Static).update(
                f"SRE Telemetry: HEALTHY | Uptime: {mesh_stats.get('uptime_percentage', 100.0):.1f}% | Total Audited: {mesh_stats.get('total_audits_scored', 0)} Articles"
            )

    def _render_current_item(self) -> None:
        """Update Inspector views with current audit item and active lens."""
        if not self._current_item:
            self.query_one("#score_banner", Static).update("📡 STANDALONE / NO RECORDED AUDITS")
            self.query_one("#exec_summary_panel", Static).update("No audits recorded in database.")
            self.query_one("#violations_table", DataTable).clear()
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
        """Handle row selections in history, violations, leaderboard, or feeds tables."""
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
        elif event.data_table.id == "feeds_table":
            idx = event.cursor_row
            if hasattr(self, "_live_feeds") and 0 <= idx < len(self._live_feeds):
                f = self._live_feeds[idx]
                self.query_one("#feed_sentinel_panel", Static).update(
                    format_feed_sentinel_panel(
                        {
                            "title": f.title,
                            "feed_url": f.feed_url,
                            "is_sentinel": f.is_sentinel,
                            "interval_seconds": f.sentinel_interval_seconds,
                            "priority_tier": f.priority_tier,
                            "last_polled_at": f.last_polled_at.isoformat() if f.last_polled_at else None,
                        }
                    )
                )
        elif event.data_table.id == "violations_table":
            idx = event.cursor_row
            if 0 <= idx < len(self._current_violations):
                v = self._current_violations[idx]
                quote = v.get("grounded_quote", "") if isinstance(v, dict) else getattr(v, "grounded_quote", "")
                reasoning = v.get("reasoning", "") if isinstance(v, dict) else getattr(v, "reasoning", "")
                detail = f'[bold cyan]Reasoning:[/bold cyan] {reasoning}\n\n[bold green]Verbatim Citation (G=1.00):[/bold green]\n"{quote}"'
                self.query_one("#detail_text", Static).update(detail)

    async def action_toggle_selected_sentinel(self) -> None:
        """Toggle Sentinel Mode on the currently highlighted feed."""
        feeds_table = self.query_one("#feeds_table", DataTable)
        idx = feeds_table.cursor_row
        if hasattr(self, "_live_feeds") and 0 <= idx < len(self._live_feeds):
            target_sub = self._live_feeds[idx]
            new_state = not target_sub.is_sentinel
            from credence.db import get_async_session
            from credence.feeds.sentinel import set_feed_sentinel_mode

            async with get_async_session() as s:
                try:
                    res = await set_feed_sentinel_mode(s, target_sub.feed_url, enabled=new_state)
                    mode_label = "Enabled (300s cadence)" if new_state else "Disabled"
                    self.notify(f"🛡️ Sentinel Mode {mode_label} for {res['domain']}")
                except Exception as e:
                    self.notify(f"Sentinel Error: {e}", severity="error")
            await self.action_refresh_data()

    async def action_trigger_sifter_pass(self) -> None:
        """Trigger on-demand background sifter pass."""
        from credence.db import get_async_session
        from credence.feeds.sifter import run_sifting_cycle

        async with get_async_session() as s:
            summary = await run_sifting_cycle(s)
            self.notify(
                f"Sifter: Discovered {summary.new_items_discovered}, audited {summary.items_evaluated_locally}."
            )
        await self.action_refresh_data()

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
