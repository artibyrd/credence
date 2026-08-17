# White-Label Mesh Federation Guide

Credence is designed from first principles to support **sovereign white-label federation**. Newsrooms, university journalism departments, enterprise compliance teams, and DAOs can spin up and host their own independent, brand-customized mesh networks that interoperate with the broader Credence ecosystem.

---

## 1. Quickstart: 1-Command Organization Scaffolding

To scaffold a complete sovereign mesh organization:

```bash
credence init-org \
  --name "Truth Consortium" \
  --domain "truthconsortium.org" \
  --output ./truth-consortium-mesh \
  --email "security@truthconsortium.org" \
  --brand-title "Truth Consortium Epistemic Mesh"
```

### What is Generated:
```
truth-consortium-mesh/
├── keys/
│   ├── root.key              # Independent Root Ed25519 Private Key
│   └── root.pub              # Independent Root Ed25519 Public Key
├── org-config.yaml           # Organization Metadata & Catalog List
├── terraform.tfvars          # Pre-configured Terraform Multi-Cloud Variables
├── static/
│   └── taxonomies/v1/        # Static JSON mirrors of SPJ, IEP, and Deceptive Patterns
└── web/
    ├── index.html            # Branded, high-contrast HTML5 landing page
    └── install.sh            # Parameterized one-line installer script
```

---

## 2. Deploying Your Sovereign Mesh

### Step 1: Link Custom Domains & Cloudflare
In your DNS provider or Cloudflare account, configure your four domain endpoints (e.g. `app.truthconsortium.org`, `mesh.truthconsortium.org`, `taxonomies.truthconsortium.org`, `report.truthconsortium.org`).

### Step 2: Deploy Multi-Cloud Infrastructure
```bash
# Copy terraform files into your org directory or run from repo root
cd /path/to/credence/terraform
terraform init
terraform plan -var-file=/path/to/truth-consortium-mesh/terraform.tfvars
terraform apply -var-file=/path/to/truth-consortium-mesh/terraform.tfvars
```

### Step 3: Publish Seeds & Taxonomies
```bash
# Generate and sign your organization's initial seed manifest
poetry run python scripts/publish_seeds.py \
  --output /path/to/truth-consortium-mesh/web/peers.json \
  --domain "https://mesh.truthconsortium.org/peers.json"
```

---

## 3. Joining or Bridging Between Federations

Because all Credence nodes evaluate standard namespaced rule URIs (`domain:cluster/rule_id@version`) and canonical RFC 8785 JSON bytes, nodes across different federations can gossiping attestations and establish mutual consensus bridges without vendor lock-in.
