---
title: 'Tutorial 04: Sovereign Org Scaffolding'
description: Scaffold an independent, custom-branded trust federation using the credence
  init-org command.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
sidebar:
  order: 4
---

# Tutorial 04: Sovereign Org Scaffolding

Learn how newsrooms, universities, and sovereign consortiums can instantiate an independent Credence federation with custom root keys, custom taxonomies, and multi-cloud Terraform templates.

---

## 1. Scaffolding Your Organization

Run the interactive white-label scaffolding wizard:

```bash
credence init-org --name "Veritas Journalism Collective" --domain "veritas.media"
```

### Generated Directory Structure:
```text
veritas-federation/
├── credence.org.yaml             # Sovereign federation manifest & root public keys
├── taxonomies/                   # Custom investigative journalism rule catalogs
│   └── investigative-v1.json
├── terraform/                    # Parameterized GCP + Cloudflare infrastructure
│   ├── main.tf
│   ├── cloud_run.tf
│   └── variables.tf
└── web/                          # Sovereign-branded zero-build web viewer
    └── viewer.html
```

---

## 2. Deploying Your Sovereign Mesh

1. Generate your air-gapped root Ed25519 signing keypair:
```bash
   cd veritas-federation
   credence identity generate --out keys/veritas-root.pem
```
2. Apply Terraform to provision Cloud Run and Cloudflare:
```bash
   cd terraform
   terraform init
   terraform apply -var="org_domain=veritas.media"
```
3. Boot your initial seed node:
```bash
   credence mesh start --port 8765 --org-manifest ../credence.org.yaml
```
