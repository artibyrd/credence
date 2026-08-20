---
title: 'Operational Guide: Multi-Environment Boundaries and Deployments'
description: Comprehensive operational runbook detailing project, account, domain,
  CI/CD secrets, and data boundary isolation between Basic Dev and Advanced Prod deployments.
since_version: v1.18.0
verified_version: v1.18.2
last_verified: '2026-08-19'
---

# Operational Guide: Multi-Environment Boundaries and Deployments

This guide details the operational boundaries, governance rules, and automated deployment procedures for maintaining separate **Basic Dev** and **Advanced Prod** environments with 100% launch parity.

---

## 1. Boundary Isolation Matrix

| Boundary Layer | Basic Dev Environment | Advanced Prod Environment |
| :--- | :--- | :--- |
| **GCP Project** | `credence-dev-XXXXX` (or shared `credence-prod-505902`) | `credence-prod-505902` |
| **Service Name** | `credence-dev` | `credence-server` |
| **Compute Sizing** | 1 vCPU, 512MiB RAM, max 1 instance | 1–2 vCPU, 1024–2048MiB RAM, max 2–5 instances |
| **Database Engine** | Embedded SQLite WAL (`data/credence.db`) | Managed Serverless PostgreSQL (Neon / Cloud SQL) |
| **CAS Blob Storage** | Local filesystem (`data/snapshots/`) | Cloudflare R2 (`STORAGE_BACKEND=s3`, $0 egress) |
| **Distributed State** | In-Memory Python State Store | Serverless Redis / Valkey (`REDIS_URL`) |
| **Monitoring Tier** | `simple` (Failure alerts, $5/mo budget cap) | `advanced` (Full SRE telemetry, P95 latency, 5xx alerts, $15/mo cap) |
| **Edge Domain** | `dev.credence.run`, `mcp.dev.credence.run` | `credence.run`, `mcp.credence.run` |
| **Report Cache** | `Cache-Control: private, max-age=60` | `Cache-Control: public, max-age=2592000, immutable` |

---

## 2. GitHub Actions Secrets Configuration Matrix

To enable automated multi-environment CI/CD deployment pipelines, configure the following secrets in GitHub ([`artibyrd/credence` $\rightarrow$ Settings $\rightarrow$ Secrets and variables $\rightarrow$ Actions](https://github.com/artibyrd/credence/settings/secrets/actions)):

| Secret Name | Required For | Example / Description |
| :--- | :--- | :--- |
| **`CLOUDFLARE_API_TOKEN`** | Edge Router & Pages Deployments | API Token created via "Edit Cloudflare Workers" template with `All zones` access |
| **`CLOUDFLARE_ACCOUNT_ID`**| Edge Router & Pages Deployments | Cloudflare Account ID string (e.g. `f1e95c67a1e06db65efa5aaf7a92b38e`) |
| **`GCP_WORKLOAD_IDENTITY_PROVIDER`** | Cloud Run Backend Deployments | `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| **`GCP_SERVICE_ACCOUNT`** | Cloud Run Backend Deployments | `credence-cloud-run-sa@PROJECT_ID.iam.gserviceaccount.com` |
| **`GCP_SA_KEY`** | Cloud Run (Fallback if not using WIF) | Base64-encoded GCP Service Account JSON key |
| **`DISCORD_WEBHOOK_URL`** | SRE & Budget Alerting | Discord channel webhook URL for instant alert notifications |

---

## 3. Multi-Environment CI/CD Workflows

The ecosystem provides two dedicated deployment workflows:

### 1. Development Deployment (`.github/workflows/deploy-dev.yml`)
- Triggered on push to `develop` or manual `workflow_dispatch`.
- Builds container tag `gcr.io/<DEV_PROJECT>/credence-dev:latest`.
- Deploys `credence-dev` in Economy profile (`512Mi` RAM, `min_instances=0`, `max_instances=1`).
- Runs live probe gate: `curl -sSL -f https://<DEV_SERVICE_URL>/health`.

### 2. Production Release Deployment (`.github/workflows/deploy-backend.yml`)
- Triggered on push of version release tags (e.g. `v1.18.2`) or manual `workflow_dispatch`.
- Builds container tag `gcr.io/<PROD_PROJECT>/credence-server:latest`.
- Deploys `credence-server` in Balanced profile (`1024Mi` RAM, `min_instances=0`, `max_instances=2`).
- Runs live probe gate: `curl -sSL -f https://<PROD_SERVICE_URL>/health`.

---

## 4. Sequential Launch Parity Deployment Runbook

When releasing a new ecosystem version, execute the sequential parity release progression:

```bash
# === Phase 1: Local Pre-Commit QA Gate ===
just check

# === Phase 2: Mk1 Eyeball Review & Commit (Commit-Before-Deploy) ===
git add -A
git commit -m "feat(release): ecosystem version vX.Y.Z"

# === Phase 3: Dev Deployment & Telemetry Gate ===
just deploy dev
just gcp probe credence-dev

# === Phase 4: Production Deployment & Telemetry Gate ===
just deploy prod
just gcp probe credence-server

# === Phase 5: Edge Router Deployment ===
just deploy edge

# === Phase 6: Multi-Plane Doctor Diagnostics ===
just doctor prod
```
