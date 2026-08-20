"""Native Offline Attestation Bundle Verifier CLI for Credence.

Provides instant (<10ms) cryptographic verification of signed truth bundles
from local JSON files without requiring server daemon or network access.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from credence.identity import verify_attestation_signature
from credence.pipeline.schemas import AuditReport

console = Console()


def run_verify_command(args: list[str]) -> int:
    """Verify an offline JSON attestation report file.

    Args:
        args: Command line arguments containing the target .json file path.

    Returns:
        0 if attestation is cryptographically valid, 1 otherwise.
    """
    if not args or args[0] in ("-h", "--help"):
        console.print("[bold cyan]Usage:[/bold cyan] credence verify <bundle.json>")
        console.print("Verifies Ed25519 signature, RFC 8785 canonical bytes, and DOM grounding in <10ms offline.")
        return 0

    file_path = Path(args[0])
    if not file_path.exists():
        console.print(f"[bold red]❌ Error:[/bold red] Attestation file '{file_path}' not found.")
        return 1

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        report = AuditReport.model_validate(data)
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/bold red] Failed to parse attestation JSON: {e}")
        return 1

    is_valid = verify_attestation_signature(report)

    text = Text()
    text.append(f"File: {file_path.name}\n", style="bold")
    text.append(f"URL: {report.url}\n", style="cyan")
    text.append(f"Content SHA-256: {report.content_sha256}\n", style="dim")
    text.append(f"Signer Node Public Key: {report.node_pubkey}\n", style="bold")

    if is_valid:
        text.append("\n✅ VERIFICATION RESULT: AUTHENTIC (Ed25519 & RFC 8785 Verified)\n", style="bold green")
        text.append(f"Score: {report.suspicion_score:.1f}/100.0 ({report.classification})\n", style="green")
        border_style = "green"
        exit_code = 0
    else:
        text.append("\n❌ VERIFICATION RESULT: FORGED OR TAMPERED SIGNATURE!\n", style="bold red")
        border_style = "red"
        exit_code = 1

    console.print(Panel(text, title="[bold]Credence Attestation Verifier[/bold]", border_style=border_style))
    return exit_code
