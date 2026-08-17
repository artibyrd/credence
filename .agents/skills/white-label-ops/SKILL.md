---
name: white-label-ops
description: Scaffold independent sovereign federation organizations (credence init-org), validate multi-cloud Terraform templates (GCP and Cloudflare), and review zero-build web deployments.
---

# White-Label Federation & Multi-Cloud Infrastructure Skill

Use this skill when deploying, provisioning, or scaffolding sovereign federated Credence networks.

## Core Commands
- `credence init-org acme-corp --domain acme.org --region us-central1`: Scaffold turnkey organization.
- `just tf-validate`: Validate Terraform configurations across Cloudflare and GCP modules.
- `just serve-web`: Launch local preview server for visual Mk1 Eyeball review of web artifacts.

## Architecture Invariants
- **Multi-Cloud Topology**:
  - GCP: Cloud Run v2 (scale-to-zero, $15.00/mo budget cap, Secret Manager API keys).
  - Cloudflare: Zero-build static web hosting and DNS edge routing.
- **Dry-Run Mode**: All deployment utilities must provide non-destructive `--dry-run` inspection flags.
