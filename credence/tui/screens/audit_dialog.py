"""Modal Dialog for URL Input in Credence TUI."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


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

    #url_input {
        margin: 1 0;
    }

    #button_row {
        align: right middle;
        height: auto;
    }

    Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Enter Webpage URL or Local HTML Path to Audit:", id="dialog_title")
            yield Input(placeholder="https://example.com/article or file:///path/to/doc.html", id="url_input")
            with Horizontal(id="button_row"):
                yield Button("Audit", variant="primary", id="btn_audit")
                yield Button("Cancel", variant="default", id="btn_cancel")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_audit":
            url_val = self.query_one(Input).value.strip()
            self.dismiss(url_val if url_val else None)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        url_val = event.value.strip()
        self.dismiss(url_val if url_val else None)
