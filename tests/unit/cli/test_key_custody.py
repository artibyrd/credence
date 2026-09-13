"""Unit tests for 'credence key' CLI commands."""

from pathlib import Path
import pytest

from credence.cli.commands.identity import (
    run_key_export_command,
    run_key_generate_command,
    run_key_import_command,
    run_key_show_command,
)
from credence.identity import load_or_create_node_identity


@pytest.mark.unit
def test_cli_key_show_and_generate(tmp_path: Path) -> None:
    """Verify 'key show' and 'key generate' CLI commands."""
    key_file = str(tmp_path / "node.key")

    # Generate key
    code = run_key_generate_command(force=False, key_file=key_file)
    assert code == 0
    assert Path(key_file).exists()

    # Generating again without force fails
    code_fail = run_key_generate_command(force=False, key_file=key_file)
    assert code_fail == 1

    # Generating with force succeeds
    code_force = run_key_generate_command(force=True, key_file=key_file)
    assert code_force == 0

    # Show key
    code_show = run_key_show_command(key_file=key_file)
    assert code_show == 0


@pytest.mark.unit
def test_cli_key_export_and_import(tmp_path: Path) -> None:
    """Verify 'key export' and 'key import' CLI commands."""
    orig_key_file = str(tmp_path / "orig.key")
    export_pem_file = str(tmp_path / "exported.pem")
    imported_key_file = str(tmp_path / "imported.key")

    # Initialize key
    ident1 = load_or_create_node_identity(Path(orig_key_file))

    # Export to file
    code_exp = run_key_export_command(out_file=export_pem_file, key_file=orig_key_file)
    assert code_exp == 0
    assert Path(export_pem_file).exists()

    # Import from file
    code_imp = run_key_import_command(in_file=export_pem_file, key_file=imported_key_file)
    assert code_imp == 0
    assert Path(imported_key_file).exists()

    ident2 = load_or_create_node_identity(Path(imported_key_file))
    assert ident1.public_key_hex == ident2.public_key_hex
