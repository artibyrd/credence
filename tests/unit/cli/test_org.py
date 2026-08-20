"""Unit tests for the Sovereign White-Label Mesh Organization Generator."""

from pathlib import Path

import pytest
import yaml

from credence.mesh.org import generate_mesh_org


@pytest.mark.unit
def test_generate_mesh_org_scaffolding(tmp_path: Path) -> None:
    """Verify generate_mesh_org creates keys, configs, terraform vars, web templates, and taxonomy mirrors."""
    out_dir = tmp_path / "test_org"
    config, identity = generate_mesh_org(
        org_name="Truth Alliance",
        base_domain="truthalliance.org",
        output_dir=out_dir,
        contact_email="admin@truthalliance.org",
        brand_title="Truth Alliance Epistemic Mesh",
    )

    assert config.org_name == "Truth Alliance"
    assert config.org_slug == "truth-alliance"
    assert config.brand_title == "Truth Alliance Epistemic Mesh"
    assert config.root_public_key == identity.public_key_hex

    # 1. Verify Keys Generated
    assert (out_dir / "keys" / "root.key").exists()
    assert (out_dir / "keys" / "root.pub").exists()
    pub_key_content = (out_dir / "keys" / "root.pub").read_text(encoding="utf-8").strip()
    assert pub_key_content == identity.public_key_hex

    # 2. Verify org-config.yaml
    config_file = out_dir / "org-config.yaml"
    assert config_file.exists()
    org_data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    assert org_data["org_name"] == "Truth Alliance"
    assert org_data["root_public_key"] == identity.public_key_hex
    assert org_data["domains"]["run"] == "app.truthalliance.org"

    # 3. Verify terraform.tfvars
    tfvars_file = out_dir / "terraform.tfvars"
    assert tfvars_file.exists()
    tfvars_content = tfvars_file.read_text(encoding="utf-8")
    assert 'domain_credence_run        = "app.truthalliance.org"' in tfvars_content
    assert 'alert_email_addresses  = ["admin@truthalliance.org"]' in tfvars_content

    # 4. Verify static taxonomy mirrors
    assert (out_dir / "static" / "taxonomies" / "v1" / "spj_ethics.json").exists()
    assert (out_dir / "static" / "taxonomies" / "v1" / "iep_fallacies.json").exists()
    assert (out_dir / "static" / "taxonomies" / "v1" / "deceptive_patterns.json").exists()

    # 5. Verify web artifacts and install script
    assert (out_dir / "web" / "index.html").exists()
    assert (out_dir / "web" / "install.sh").exists()
    index_html = (out_dir / "web" / "index.html").read_text(encoding="utf-8")
    assert "Truth Alliance Epistemic Mesh" in index_html
    assert identity.public_key_hex in index_html


@pytest.mark.unit
def test_generate_mesh_org_with_custom_domains(tmp_path: Path) -> None:
    """Verify generate_mesh_org handles custom domain mappings."""
    out_dir = tmp_path / "custom_org"
    custom_domains = {
        "run": "credence.run",
        "nexus": "credence.nexus",
        "foundation": "credence.foundation",
        "report": "credence.report",
    }
    config, _ = generate_mesh_org(
        org_name="Credence Nexus",
        base_domain="credence.nexus",
        output_dir=out_dir,
        custom_domains=custom_domains,
    )

    assert config.domain_run == "credence.run"
    assert config.domain_nexus == "credence.nexus"
    assert config.domain_foundation == "credence.foundation"
    assert config.domain_report == "credence.report"


@pytest.mark.unit
def test_cli_init_org(tmp_path: Path) -> None:
    """Verify CLI init-org execution cleanly creates workspace."""
    from credence.cli.main import cli_init_org

    target_dir = tmp_path / "cli_org"
    cli_init_org(
        name="Global Newsroom",
        domain="globalnews.nexus",
        output_dir=str(target_dir),
    )
    assert (target_dir / "org-config.yaml").exists()
    assert (target_dir / "keys" / "root.pub").exists()
