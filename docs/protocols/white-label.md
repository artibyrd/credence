---
title: White-Label Federation
description: Scaffold sovereign, independent mesh organizations with custom root keys
  and multi-cloud Terraform templates.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
sidebar:
  order: 6
---

# White-Label Federation Specification

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
```text
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

### Step 1: Configure Custom DNS Endpoints
Configure your four domain endpoints (e.g. `app.truthconsortium.org`, `mesh.truthconsortium.org`, `taxonomies.truthconsortium.org`, `report.truthconsortium.org`).

### Step 2: Deploy Multi-Cloud Infrastructure
```bash
cd terraform
terraform init
terraform plan -var-file=/path/to/truth-consortium-mesh/terraform.tfvars
terraform apply -var-file=/path/to/truth-consortium-mesh/terraform.tfvars
```

### Step 3: Publish Signed Seeds
Generate and sign your organization's initial seed manifest using your independent root keypair.
