"""In-Terminal Topic Definitions and Invariant Bible Modal for Credence TUI.

Architecture: Modal Screen Component (<180 LOC).
"""

from __future__ import annotations

from typing import Dict, List

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Label, Static

INFO_TOPICS: List[Dict[str, str]] = [
    {
        "id": "dci",
        "title": "Domain Credibility Index (DCI)",
        "badge": "Bayesian Scoring",
        "glance": "A 0-100 credibility rating for publishers computed via Bayesian longitudinal smoothing over verified audits.",
        "mechanics": "credence rankings --domain <domain>\nFormula: DCI = (Sum(w_i * S_i) / Sum(w_i)) * (1.0 - Exp(-N / tau))",
        "invariant": "Invariant: Domain Longevity & Longitudinal Reputation Scoring",
    },
    {
        "id": "g_rate",
        "title": "Verbatim Grounding (G=1.00)",
        "badge": "Anti-Hallucination",
        "glance": "Zero-tolerance citation accuracy where quotes must match source text character-for-character.",
        "mechanics": "credence audit <url> --full\nSlashing: Any hallucinated citation triggers an autonomous 50% node merit slash.",
        "invariant": "Invariant: Epistemic Verbatim Grounding (G=1.00) & Slashing",
    },
    {
        "id": "rfc8785",
        "title": "RFC 8785 Canonical Envelopes",
        "badge": "Ed25519 Custody",
        "glance": "Cryptographic tamper-proofing ensuring audit results cannot be altered post-evaluation.",
        "mechanics": "credence verify <envelope.json>\nUses deterministic JCS byte ordering with Ed25519 asymmetric signatures.",
        "invariant": "Invariant: RFC 8785 Canonical JSON & Ed25519 Custody",
    },
    {
        "id": "poe",
        "title": "Poe's Law & Satire Defense",
        "badge": "Satire Protection",
        "glance": "Protects legitimate satire while preventing bad-faith disinformation from hiding behind satire claims.",
        "mechanics": "SPJ-1.6 Override automatically strips satire safe harbor if defamatory allegations are made.",
        "invariant": "Invariant: Topic Entropy Astroturfing Defense & Poe's Law",
    },
    {
        "id": "boredom",
        "title": "Headroom-Aware Ingestion (Boredom)",
        "badge": "Token Safety",
        "glance": "Autonomous background evaluation that pauses automatically when LLM token headroom drops below 30%.",
        "mechanics": "credence boredom\nEvaluates pending queue opportunistically during off-peak hours.",
        "invariant": "Invariant: Multi-Model Sovereignty & Token Budget Circuit Breakers",
    },
    {
        "id": "mesh",
        "title": "13-Node Watts-Strogatz P2P Mesh",
        "badge": "Sybil Cartel Defense",
        "glance": "Decentralized consensus clustering resistant to Byzantine cartels up to 3f+1 fault tolerance.",
        "mechanics": "credence mesh --status\nUses Highest Random Weight (HRW) rendezvous hashing for feed syndication.",
        "invariant": "Invariant: Byzantine Sybil Cartel Resistance & Mesh Clustering",
    },
]


class InfoModalScreen(ModalScreen[None]):
    """Modal screen displaying Topic definitions and Invariant references."""

    CSS = """
    InfoModalScreen {
        align: center middle;
    }
    #modal_dialog {
        width: 85%;
        height: 80%;
        background: #111b2f;
        border: heavy #38bdf8;
        padding: 1 2;
    }
    #topic_split {
        height: 1fr;
    }
    #topic_list {
        width: 35%;
        height: 1fr;
        border: solid #1e293b;
        margin-right: 1;
    }
    #topic_detail_scroll {
        width: 65%;
        height: 1fr;
        background: #0b1120;
        border: solid #1e293b;
        padding: 1;
    }
    #close_btn {
        dock: bottom;
        width: 100%;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="modal_dialog"):
            yield Label("📘 Credence Invariant Bible & Epistemic Lexicon", id="modal_title")
            with Horizontal(id="topic_split"):
                yield DataTable(id="topic_list")
                with VerticalScroll(id="topic_detail_scroll"):
                    yield Static("Select a topic on the left to inspect.", id="topic_detail_text")
            yield Button("Close (Esc)", variant="primary", id="close_btn")

    def on_mount(self) -> None:
        table = self.query_one("#topic_list", DataTable)
        table.add_columns("Topic", "Badge")
        table.cursor_type = "row"
        for t in INFO_TOPICS:
            table.add_row(t["title"], t["badge"])
        if INFO_TOPICS:
            self._render_topic(INFO_TOPICS[0])

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_idx = event.cursor_row
        if 0 <= row_idx < len(INFO_TOPICS):
            self._render_topic(INFO_TOPICS[row_idx])

    def _render_topic(self, topic: Dict[str, str]) -> None:
        text = Text()
        text.append(f"📘 {topic['title']}\n", style="bold white")
        text.append(f"Pillar: [{topic['badge']}]\n\n", style="bold #38bdf8")

        text.append("Overview & Glance:\n", style="bold #4ade80")
        text.append(f"{topic['glance']}\n\n", style="white")

        text.append("Technical Mechanics & CLI Recipe:\n", style="bold #f59e0b")
        text.append(f"{topic['mechanics']}\n\n", style="cyan")

        text.append("Living Invariant Canon Reference:\n", style="bold #c084fc")
        text.append(f"{topic['invariant']}\n", style="dim italic")

        self.query_one("#topic_detail_text", Static).update(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_btn":
            self.dismiss()
