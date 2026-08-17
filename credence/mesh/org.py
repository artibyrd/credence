"""White-Label Mesh Organization & Federation Generator for Credence.

Allows sovereign newsrooms, academic consortia, DAOs, and enterprises to
scaffold, brand, and deploy their own independent Credence-compatible mesh
trust network with custom domains, root Ed25519 keys, and taxonomy mirrors.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from credence.identity import NodeIdentity
from credence.taxonomy_loader import registry


@dataclass
class MeshOrgConfig:
    """Configuration metadata for a sovereign mesh organization."""

    org_name: str
    org_slug: str
    brand_title: str
    contact_email: str
    domain_run: str
    domain_nexus: str
    domain_foundation: str
    domain_report: str
    root_public_key: str
    gcp_project_id: str = "your-gcp-project-id"
    cloudflare_account_id: str = "your-cloudflare-account-id"


def generate_mesh_org(
    org_name: str,
    base_domain: str,
    output_dir: Path | str,
    contact_email: Optional[str] = None,
    brand_title: Optional[str] = None,
    custom_domains: Optional[Dict[str, str]] = None,
) -> tuple[MeshOrgConfig, NodeIdentity]:
    """Scaffold a complete sovereign mesh organization workspace.

    Generates:
    - Independent root Ed25519 signing keypair (`root.key` & `root.pub`)
    - Organization configuration file (`org-config.yaml`)
    - Parameterized Terraform variables (`terraform.tfvars`)
    - Static web frontends with embedded branding and public keys
    - Static JSON mirrors of all registered taxonomies
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    org_slug = org_name.lower().replace(" ", "-").replace("_", "-")
    title = brand_title or org_name
    email = contact_email or f"security@{base_domain}"

    # 1. Generate Sovereign Root Ed25519 Keypair
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pubkey_bytes = public_key.public_bytes_raw()
    root_identity = NodeIdentity(
        private_key=private_key,
        public_key=public_key,
        public_key_hex=pubkey_bytes.hex(),
        key_path=out_path / "keys" / "root.key",
    )

    keys_dir = out_path / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    (keys_dir / "root.key").write_text(private_key.private_bytes_raw().hex(), encoding="utf-8")
    (keys_dir / "root.pub").write_text(root_identity.public_key_hex, encoding="utf-8")

    # 2. Determine 4 Domain Endpoints
    if custom_domains:
        domain_run = custom_domains.get("run", f"{org_slug}.run")
        domain_nexus = custom_domains.get("nexus", f"{org_slug}.nexus")
        domain_foundation = custom_domains.get("foundation", f"{org_slug}.foundation")
        domain_report = custom_domains.get("report", f"{org_slug}.report")
    else:
        # Default subdomains under base_domain if single TLD given, or 4-domain pattern
        if "." in base_domain and not any(
            base_domain.endswith(tld) for tld in [".run", ".nexus", ".foundation", ".report"]
        ):
            domain_run = f"app.{base_domain}"
            domain_nexus = f"mesh.{base_domain}"
            domain_foundation = f"taxonomies.{base_domain}"
            domain_report = f"report.{base_domain}"
        else:
            domain_run = f"{org_slug}.run"
            domain_nexus = f"{org_slug}.nexus"
            domain_foundation = f"{org_slug}.foundation"
            domain_report = f"{org_slug}.report"

    config = MeshOrgConfig(
        org_name=org_name,
        org_slug=org_slug,
        brand_title=title,
        contact_email=email,
        domain_run=domain_run,
        domain_nexus=domain_nexus,
        domain_foundation=domain_foundation,
        domain_report=domain_report,
        root_public_key=root_identity.public_key_hex,
    )

    # 3. Write org-config.yaml
    org_dict: Dict[str, Any] = {
        "org_name": config.org_name,
        "org_slug": config.org_slug,
        "brand_title": config.brand_title,
        "contact_email": config.contact_email,
        "root_public_key": config.root_public_key,
        "domains": {
            "run": config.domain_run,
            "mcp": f"mcp.{config.domain_run}",
            "seeds": f"seeds.{config.domain_nexus}",
            "relay": f"relay.{config.domain_nexus}",
            "taxonomies": f"taxonomies.{config.domain_foundation}",
            "report": config.domain_report,
        },
        "taxonomies": [
            {"id": "spj_ethics", "version": "v1.0.0"},
            {"id": "iep_fallacies", "version": "v1.0.0"},
            {"id": "deceptive_patterns", "version": "v1.0.0"},
        ],
    }
    (out_path / "org-config.yaml").write_text(yaml.safe_dump(org_dict, sort_keys=False), encoding="utf-8")

    # 4. Generate Pre-configured terraform.tfvars
    tfvars_content = f"""# Terraform Variables for {config.org_name}
project_id             = "{config.gcp_project_id}"
region                 = "us-central1"
service_name           = "{config.org_slug}-server"
credence_profile       = "balanced"
monthly_budget_limit_usd = 15.0
billing_account_id     = ""
alert_email_addresses  = ["{config.contact_email}"]

# Cloudflare Configuration
cloudflare_api_token   = "YOUR_CLOUDFLARE_API_TOKEN"
cloudflare_account_id  = "{config.cloudflare_account_id}"

# Domain Mappings
domain_credence_run        = "{config.domain_run}"
domain_credence_nexus      = "{config.domain_nexus}"
domain_credence_foundation = "{config.domain_foundation}"
domain_credence_report     = "{config.domain_report}"
"""
    (out_path / "terraform.tfvars").write_text(tfvars_content, encoding="utf-8")

    # 5. Generate Static Taxonomy JSON Files & Key Mirror
    tax_dir = out_path / "static" / "taxonomies" / "v1"
    tax_dir.mkdir(parents=True, exist_ok=True)

    registry.load_all()
    for cat in registry.list_catalogs():
        cat_json = cat.model_dump(mode="json")
        (tax_dir / f"{cat.catalog_id}.json").write_text(json.dumps(cat_json, indent=2), encoding="utf-8")

    # 6. Scaffold Branded Web Frontends
    web_dir = out_path / "web"
    web_dir.mkdir(parents=True, exist_ok=True)

    landing_html = _render_landing_template(config)
    (web_dir / "index.html").write_text(landing_html, encoding="utf-8")

    install_sh = _render_install_script(config)
    (web_dir / "install.sh").write_text(install_sh, encoding="utf-8")

    return config, root_identity


def _render_landing_template(config: MeshOrgConfig) -> str:
    """Generate high-contrast, accessible HTML5 landing page for sovereign mesh."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{config.brand_title} — Sovereign Epistemic Trust Network</title>
  <meta name="description" content="Autonomous Epistemic Evaluation Engine and P2P Mesh Network for {config.org_name}.">
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #131b2e;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --border: #1e293b;
      --code-bg: #020617;
      --green: #4ade80;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 2rem 1rem;
    }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    header {{ text-align: center; margin-bottom: 3rem; }}
    h1 {{ font-size: 2.5rem; color: #fff; margin-bottom: 0.5rem; }}
    .badge {{ display: inline-block; padding: 0.25rem 0.75rem; background: var(--card-bg); border: 1px solid var(--border); border-radius: 9999px; font-size: 0.85rem; color: var(--accent); margin-bottom: 1rem; }}
    p.lead {{ font-size: 1.15rem; color: var(--muted); max-width: 650px; margin: 0 auto; }}
    .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }}
    h2 {{ font-size: 1.3rem; margin-bottom: 1rem; color: var(--accent); }}
    pre {{ background: var(--code-bg); padding: 1rem; border-radius: 6px; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.9rem; border: 1px solid var(--border); }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    @media (max-width: 600px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    .key {{ word-break: break-all; color: var(--green); font-size: 0.85rem; }}
    footer {{ text-align: center; margin-top: 3rem; color: var(--muted); font-size: 0.85rem; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <span class="badge">Sovereign Mesh Federation</span>
      <h1>{config.brand_title}</h1>
      <p class="lead">Autonomous, cryptographically verifiable epistemic trust network evaluating media against rigorous journalistic ethics and logical fallacy standards.</p>
    </header>

    <div class="card">
      <h2>Quickstart Installation</h2>
      <pre><code># Install {config.org_name} CLI
curl -fsSL https://{config.domain_run}/install.sh | sh

# Audit any web article against sovereign taxonomy rules
credence audit https://example.com/article</code></pre>
    </div>

    <div class="grid">
      <div class="card">
        <h2>Network Root Authority</h2>
        <p style="color: var(--muted); margin-bottom: 0.5rem;">Sovereign Ed25519 Root Public Key:</p>
        <pre class="key"><code>{config.root_public_key}</code></pre>
      </div>

      <div class="card">
        <h2>Endpoints</h2>
        <ul style="list-style: none; color: var(--muted);">
          <li>🌐 <b>Website:</b> https://{config.domain_run}</li>
          <li>⚡ <b>FastMCP SSE:</b> https://mcp.{config.domain_run}/sse</li>
          <li>🌱 <b>P2P Seeds:</b> https://seeds.{config.domain_nexus}/peers.json</li>
          <li>📚 <b>Taxonomies:</b> https://taxonomies.{config.domain_foundation}</li>
          <li>🔍 <b>Public Reports:</b> https://{config.domain_report}</li>
        </ul>
      </div>
    </div>

    <footer>
      <p>Powered by <a href="https://github.com/arthur-davis/credence" style="color: var(--accent);">Credence Epistemic Engine</a> &bull; {config.contact_email}</p>
    </footer>
  </div>
</body>
</html>
"""


def _render_install_script(config: MeshOrgConfig) -> str:
    """Generate POSIX-compliant one-line installer script for sovereign mesh."""
    return f"""#!/usr/bin/env sh
# {config.brand_title} One-Line Installer
set -e

echo "=== Installing {config.brand_title} CLI ==="

# Check Python 3.12+
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required. Please install Python 3.12+." >&2
  exit 1
fi

# Prefer pipx or pip
if command -v pipx >/dev/null 2>&1; then
  pipx install credence
else
  python3 -m pip install --user credence
fi

# Configure sovereign mesh endpoints
export CREDENCE_DEFAULT_SEED_URL="https://seeds.{config.domain_nexus}/peers.json"
export CREDENCE_CANONICAL_MCP_URL="https://mcp.{config.domain_run}/sse"
export CREDENCE_TRUSTED_ROOT_PUBKEY="{config.root_public_key}"

echo "=== {config.brand_title} successfully installed! ==="
echo "Run 'credence identity show' to inspect your local node public key."
"""
