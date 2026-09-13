"""CLI Node Identity Command Handlers for Credence."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from credence.config import settings
from credence.identity import load_or_create_node_identity

console = Console()


def run_identity_show_command(key_file: str | None = None) -> int:
    """Display current node Ed25519 public key and cryptographic identity."""
    target_path = Path(key_file) if key_file else Path(getattr(settings, "NODE_KEY_PATH", "node_key.json"))
    ident = load_or_create_node_identity(target_path)
    console.print(
        Panel(
            f"[bold]Public Key:[/bold] {ident.public_key_hex}\n[bold]Key Source:[/bold] {ident.key_path}",
            title="[bold green]Credence Sovereign Node Identity[/bold green]",
            border_style="green",
        )
    )
    return 0


def run_key_show_command(key_file: str | None = None) -> int:
    """CLI handler for 'credence key show'."""
    return run_identity_show_command(key_file)


def run_key_export_command(out_file: str | None = None, key_file: str | None = None) -> int:
    """CLI handler for 'credence key export'."""
    from credence.identity import export_private_key_pem

    target_path = Path(key_file) if key_file else Path(getattr(settings, "NODE_KEY_PATH", "node_key.json"))
    ident = load_or_create_node_identity(target_path)
    pem_str = export_private_key_pem(ident)

    if out_file:
        out_path = Path(out_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(pem_str, encoding="utf-8")
        try:
            out_path.chmod(0o600)
        except OSError:
            pass
        console.print(f"[bold green]✓ Private key exported to:[/bold green] {out_path}")
    else:
        # Direct PEM output to stdout for piping / pasting
        sys_stdout = console.file
        sys_stdout.write(pem_str)
        sys_stdout.flush()

    return 0


def run_key_import_command(in_file: str | None = None, key_file: str | None = None) -> int:
    """CLI handler for 'credence key import'."""
    import sys
    from credence.identity import import_private_key_pem

    if in_file:
        in_path = Path(in_file)
        if not in_path.exists():
            console.print(f"[bold red]❌ Error: File not found:[/bold red] {in_file}")
            return 1
        pem_data = in_path.read_text(encoding="utf-8")
    else:
        console.print("[cyan]Reading PEM private key from stdin (press Ctrl+D when finished)...[/cyan]")
        pem_data = sys.stdin.read()

    target_path = Path(key_file) if key_file else Path(getattr(settings, "NODE_KEY_PATH", "node_key.json"))
    try:
        ident = import_private_key_pem(pem_data, target_path)
        console.print(
            Panel(
                f"[bold green]✓ Private key imported successfully![/bold green]\n"
                f"[bold]Public Key:[/bold] {ident.public_key_hex}\n"
                f"[bold]Saved to:[/bold] {ident.key_path}",
                title="[bold green]Credence Key Custody[/bold green]",
                border_style="green",
            )
        )
        return 0
    except Exception as e:
        console.print(f"[bold red]❌ Key Import Error:[/bold red] {e}")
        return 1


def run_key_generate_command(force: bool = False, key_file: str | None = None) -> int:
    """CLI handler for 'credence key generate'."""
    from credence.identity import generate_new_keypair_at_path

    target_path = Path(key_file) if key_file else Path(getattr(settings, "NODE_KEY_PATH", "node_key.json"))
    try:
        ident = generate_new_keypair_at_path(target_path, overwrite=force)
        console.print(
            Panel(
                f"[bold green]✓ New Ed25519 keypair generated![/bold green]\n"
                f"[bold]Public Key:[/bold] {ident.public_key_hex}\n"
                f"[bold]Saved to:[/bold] {ident.key_path}",
                title="[bold green]Credence Key Generation[/bold green]",
                border_style="green",
            )
        )
        return 0
    except FileExistsError:
        console.print(
            f"[bold yellow]⚠️ Key already exists at {target_path}.[/bold yellow]\n"
            "Use [bold]--force[/bold] to overwrite and replace your existing cryptographic identity."
        )
        return 1
    except Exception as e:
        console.print(f"[bold red]❌ Key Generation Error:[/bold red] {e}")
        return 1

