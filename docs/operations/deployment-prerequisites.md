---
title: Master Deployment Prerequisites & Setup Guide
description: Complete prerequisite checklists, credential matrices, CLI commands,
  and decision trees across all Credence deployment topologies.
since_version: v1.18.0
verified_version: v1.18.2
last_verified: '2026-08-19'
---

# Master Deployment Prerequisites & Setup Guide

Credence is architected as a **platform-agnostic sovereign stack**. Whether you are deploying on Google Cloud Platform with scale-to-zero serverless compute, running a decentralized homelab node on a Raspberry Pi, or deploying a multi-container planetary stack on Kubernetes, this guide details the exact prerequisites, credentials, IAM permissions, and setup steps required for each deployment topology.

---

## 1. Deployment Topology Decision Matrix

| Topology | Best For | Compute Cost | Complexity | Persistence | Minimum Hardware |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GCP Cloud Run (Dual-Project)** | Enterprise / Multi-Tenant Teams | ~$0.00–$15.00/mo (Scale-to-Zero) | Medium | Cloud Storage / R2 + SQLite/Postgres | Serverless Container |
| **GCP Cloud Run (Single-Project)** | Lean Startups / Solo Operators | ~$0.00–$15.00/mo (Scale-to-Zero) | Low | Local / Cloud Storage | Serverless Container |
| **Cloudflare Edge Router & Pages** | Web Frontend, FastMCP SSE, Docs | $0.00/mo (Free Tier Workers/Pages) | Low | Edge Cache / KV | Serverless Edge Workers |
| **Docker Compose (Basic Node)** | Solo Homelab / Air-Gapped Workstation | $0.00/mo (Local) | Very Low | Local SQLite / Volume | 1 vCPU, 512 MB RAM |
| **Docker Compose (Planetary Stack)** | Self-Hosted High-Throughput Cluster | $10–$40/mo (VPS / Bare-Metal) | Medium | PostgreSQL + MinIO + Valkey | 2 vCPU, 4 GB RAM |
| **Kubernetes / Helm** | Cloud-Native Enterprise Swarms | Varies by Cluster | High | PVC (RWX/RWO) / Managed DB | K8s 1.28+, 2 Nodes |
| **Bare-Metal Linux / VPS (Systemd)** | Sovereign Node Operators (Hetzner/OVH)| ~$4.00–$10.00/mo | Low | Local SQLite / WAL | 1 vCPU, 1 GB RAM |

---

## 2. Option A: Google Cloud Run (Compute Plane)

Google Cloud Run hosts the core `credence-server` (or `credence-dev`) FastMCP engine.

### 2.1 Project & Account Prerequisites
- **GCP Account**: An active Google Cloud billing account.
- **Project IDs**:
  - **Dual-Project Mode (Recommended)**: Two separate projects, e.g. `credence-dev-495173` (Dev) and `credence-prod-505902` (Prod).
  - **Single-Project Mode**: One unified project, e.g. `credence-prod-505902` (partitioned via service names).
- **Google Cloud SDK (`gcloud`)**: Installed and authenticated (`gcloud auth login`).

### 2.2 Required GCP APIs
Enable the following service APIs on your target project(s):
```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    cloudbilling.googleapis.com \
    --project="<YOUR_GCP_PROJECT_ID>"
```

### 2.3 Required IAM Roles
The deployment identity (Service Account or CI/CD runner) requires the following roles:
- `roles/run.admin` (Cloud Run Admin)
- `roles/artifactregistry.admin` (Container Registry Admin)
- `roles/cloudbuild.builds.editor` (Cloud Build Editor)
- `roles/secretmanager.secretAccessor` (Read API keys at runtime)
- `roles/storage.admin` (Optional, if using Google Cloud Storage for snapshot blobs)

### 2.4 Secret Manager Keys
Create the required Gemini API Key secret in Secret Manager:
```bash
# Production Secret
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create credence-gemini-api-key \
    --data-file=- \
    --replication-policy="automatic" \
    --project="<YOUR_GCP_PROJECT_ID>"

# Dev Secret (if using Single-Project partitioned namespacing)
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create credence-gemini-api-key-dev \
    --data-file=- \
    --replication-policy="automatic" \
    --project="<YOUR_GCP_PROJECT_ID>"
```

### 2.5 GitHub Actions CI/CD Secrets (WIF or SA Key)
To enable automated deployments via GitHub Actions (`.github/workflows/deploy-backend.yml`), configure either:

**Method 1: Workload Identity Federation (WIF - Best Practice)**:
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider`
- `GCP_SERVICE_ACCOUNT`: `credence-cloud-run-sa@PROJECT_ID.iam.gserviceaccount.com`

**Method 2: Service Account Key (Fallback)**:
- `GCP_SA_KEY`: Base64-encoded JSON Service Account key.

---

## 3. Option B: Cloudflare Edge Router & Pages

The Cloudflare Edge Plane provides multi-domain zero-build edge routing, dynamic asset streaming, FastMCP SSE proxying, and documentation hosting across `credence.run`, `credence.nexus`, `credence.foundation`, and `credence.report`.

### 3.1 Account & Zone Prerequisites
- **Cloudflare Account**: Active Cloudflare account.
- **Account ID**: Found on the Cloudflare Dashboard overview sidebar (`CLOUDFLARE_ACCOUNT_ID`).
- **Domain Zones**: Active DNS zones added to Cloudflare:
  - `credence.run` (or your primary web domain)
  - `credence.nexus` (P2P directory)
  - `credence.foundation` (Governance mirror)
  - `credence.report` (Audit report viewer)

### 3.2 Cloudflare API Token Scopes
Create an API Token at **Cloudflare Dashboard $\rightarrow$ My Profile $\rightarrow$ [API Tokens](https://dash.cloudflare.com/profile/api-tokens)** using the pre-built template **"Edit Cloudflare Workers"**:

| Permission Scope | Resource | Access Level | Purpose |
| :--- | :--- | :--- | :--- |
| **Account** | `Workers Scripts` | **Edit** | Deploy worker script & assets bundle |
| **Account** | `Workers KV Storage` | **Edit** | Asset cache and metadata bindings |
| **Account** | `Account Settings` | **Read** | Verify account ID and limits |
| **Account** | `Cloudflare Pages` | **Edit** | Deploy zero-build documentation site |
| **Zone** | `Zone` | **Read** | Query and resolve zone domain IDs |
| **Zone** | `DNS` | **Read** | Verify active CNAME routing |

**Resource Scopes**:
- Account Resources: `Include` $\rightarrow$ `All accounts` (or your account)
- Zone Resources: `Include` $\rightarrow$ `All zones from an account` $\rightarrow$ select your account

### 3.3 GitHub Actions Secrets for Edge Deployment
Add the following secrets to your GitHub repository ([`artibyrd/credence` Settings $\rightarrow$ Secrets and variables $\rightarrow$ Actions](https://github.com/artibyrd/credence/settings/secrets/actions)):
- `CLOUDFLARE_API_TOKEN`: The API token generated above.
- `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare Account ID string (e.g. `f1e95c67a1e06db65efa5aaf7a92b38e`).

---

## 4. Option C: Self-Hosted Docker Compose

Docker Compose provides immediate local and VPS deployments without cloud lock-in.

### 4.1 System Prerequisites
- **Docker Engine**: Version 24.0 or higher.
- **Docker Compose**: Version 2.20 or higher (`docker compose version`).
- **Inbound Ports**:
  - `8000`: REST API, Health probe, FastMCP SSE endpoint.
  - `8765`: P2P WebSocket gossip relay.

### 4.2 Environment File (`.env`)
Create a `.env` file in the project root:

```bash
# Environment & Cost Profile
ENV=production
CREDENCE_PROFILE=balanced

# Epistemic LLM Inference Key
GEMINI_API_KEY=your_gemini_api_key_here

# Storage Backend Selection (local vs s3)
STORAGE_BACKEND=local
SNAPSHOT_DIR=/app/data/snapshots

# Admin API Key for authenticated endpoints
CREDENCE_ADMIN_API_KEY=your_secure_admin_key_here

# Optional: External S3 / MinIO Configuration (Planetary Stack)
# S3_ENDPOINT_URL=http://minio:9000
# S3_BUCKET_NAME=credence-snapshots
# S3_ACCESS_KEY_ID=minioadmin
# S3_SECRET_ACCESS_KEY=minioadmin123

# Optional: PostgreSQL Database (Planetary Stack)
# DATABASE_URL=postgresql+asyncpg://credence:credence_pass@postgres:5432/credence_db

# Optional: Valkey Distributed Cache (Planetary Stack)
# VALKEY_URL=redis://valkey:6379/0
```

### 4.3 Launch Commands
```bash
# Basic Mode (Single Container + Local SQLite)
docker compose up -d

# Advanced Planetary Mode (Credence + PostgreSQL + MinIO + Valkey)
docker compose -f docker-compose.prod.yml up -d
```

---

## 5. Option D: Kubernetes & Helm

For high-availability container orchestrators and enterprise clusters.

### 5.1 Cluster Prerequisites
- **Kubernetes**: Version 1.28+ (`kubectl version`).
- **Helm**: Version 3.12+ (if deploying via Helm chart).
- **Persistent Volume Provisioner**: Standard CSI driver supporting `ReadWriteOnce` (for SQLite WAL) or `ReadWriteMany` (for shared storage).
- **Ingress Controller**: Ingress-NGINX, Traefik, or Istio.

### 5.2 Kubernetes Secrets Creation
```bash
kubectl create namespace credence

kubectl create secret generic credence-secrets \
    --namespace=credence \
    --from-literal=GEMINI_API_KEY="your_api_key" \
    --from-literal=CREDENCE_ADMIN_API_KEY="your_admin_key"
```

### 5.3 Deploying Manifests
```bash
kubectl apply -f k8s/deployment.yaml -n credence
```

---

## 6. Option E: Bare-Metal Linux VPS & Systemd

For dedicated servers on Hetzner, OVH, AWS EC2, or Linode.

### 6.1 System Prerequisites
- **OS**: Ubuntu 22.04 LTS, Debian 12, or AlmaLinux 9.
- **Python**: Python 3.12+ (`python3 --version`).
- **Poetry**: Poetry 2.0+ (`poetry --version`).
- **Reverse Proxy**: Caddy (automated TLS) or Nginx with Certbot.

### 6.2 Service Unit Setup
Create `/etc/systemd/system/credence.service`:
```ini
[Unit]
Description=Credence Sovereign Epistemic Trust Node
After=network.target

[Service]
Type=simple
User=credence
WorkingDirectory=/opt/credence
EnvironmentFile=/opt/credence/.env
ExecStart=/opt/credence/.venv/bin/uvicorn credence.server:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5s
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

### 6.3 Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable credence
sudo systemctl start credence
sudo systemctl status credence
```

---

## 7. Option F: Local Developer Workstation & Homelab

### 7.1 Workstation Prerequisites
The Credence Justfile provides automated preflight verification:
```bash
# Run complete preflight validation across all tooling
just preflight all
```

Expected output:
```text
✅ Google Cloud SDK (gcloud): Account & Project verified
✅ Cloudflare Wrangler (npx): Installed
✅ GitHub CLI (gh): Logged in
✅ HashiCorp Terraform: Terraform v1.15.8
✅ Python 3.12 & Poetry: Poetry 2.4.1
✅ Docker & Docker Compose: Engine 24+
=== Preflight Validation Complete ===
```

---

## 8. Summary Checklist Before Production Release

Before executing any production release:
1. [ ] **GCP APIs Enabled**: Cloud Run, Cloud Build, Secret Manager, Cloud Monitoring.
2. [ ] **Secrets Stored**: Gemini API Key in Secret Manager (`credence-gemini-api-key`).
3. [ ] **Cloudflare Token Scoped**: "Edit Cloudflare Workers" with `All zones` resource access.
4. [ ] **GitHub Secrets Configured**: `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` in repo secrets.
5. [ ] **Working Tree Clean**: Confirmed `git status --porcelain` is clean per the **Commit-Before-Deploy** invariant.
6. [ ] **QA Gauntlet Passed**: 100% pass on `just check` (176 unit tests, static types, formatting, docs integrity).
