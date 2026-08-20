---
title: Cloud Run Deployment & Dual-Tier Monitoring Guide
description: Deploying to Google Cloud Run with Terraform, $15/mo budget cap, scale-to-zero
  compute, Workload Identity Federation, and automated CI/CD.
since_version: v1.8.0
verified_version: v1.18.2
last_verified: '2026-08-19'
---

# Cloud Run Deployment & Dual-Tier Monitoring Guide

This guide covers deploying the **Credence FastMCP Server** to **Google Cloud Platform (Cloud Run v2)** with strict cost controls ($15/month budget ceiling, scale-to-zero compute), automated **Cloud Build / GitHub Actions CI/CD**, **Workload Identity Federation (WIF)**, and **Dual-Tier SRE Observability** with **Discord & Email Alerting**.

---

## 1. Architecture Overview

```mermaid
graph LR
    subgraph Client ["Clients & Operators"]
        Antigravity[Antigravity IDE / Agent] -->|HTTPS / SSE| CloudRun
        TUI[Textual TUI / Terminal CLI] -->|Telemetry Loopback| CloudRun
    end

    subgraph GCP ["Google Cloud Platform (us-central1)"]
        CloudRun["Cloud Run v2 Service<br/>(Scale-to-Zero | 1024Mi | 1 CPU)"]
        SM["Secret Manager<br/>(credence-gemini-api-key)"]
        Budget["Cloud Billing Budget<br/>($15.00/mo Ceiling)"]
        Monitoring["Cloud Monitoring<br/>(Dual-Tier SRE & Uptime)"]
        CloudRun --> SM
        CloudRun --> Monitoring
    end

    subgraph Egress ["Alert Dispatch"]
        Discord["Discord / Powercord Webhook"]
        Email["Direct Admin Email"]
        Monitoring --> Discord
        Monitoring --> Email
        Budget --> Discord
        Budget --> Email
    end
```

---

## 2. Dual-Tier Monitoring Architecture

Credence provisions observability according to two operational modes controlled by `monitoring_tier`:

| Feature | "Guy in His Basement" Easy Mode (`monitoring_tier = "simple"`) | Advanced Production Tier (`monitoring_tier = "advanced"`) |
| :--- | :--- | :--- |
| **Default** | Yes (Default) | Optional |
| **Notification Channels**| Discord / Powercord Webhook (`discord_webhook_url`), Direct Email | Discord Webhook, Direct Email, Multi-Channel |
| **Budget Alerts** | 50%, 80%, 100% cap alerts sent to Discord & Email | 50%, 80%, 100% cap alerts sent to Discord & Email |
| **Core Failure Alerts** | 1. 🛑 Global Uptime Probe Failure (`/health`)<br/>2. 🔥 5xx Server Error Spike ($>5$ in 5m)<br/>3. ⚠️ Memory Near-OOM ($>85\%$) | 1. 🛑 Global Uptime Probe Failure<br/>2. 🔥 5xx Server Error Spike<br/>3. ⚠️ Memory Near-OOM |
| **Extended Alerts** | *Disabled (Zero false alarms)* | 4. ⏱️ P95 Latency Degradation ($>5000\text{ms}$)<br/>5. ⚙️ CPU Saturation ($>90\%$)<br/>6. 📅 Seed Publisher Cron Failure<br/>7. 📜 Log metric for `ERROR`/`CRITICAL` logs |
| **Dashboard** | 4-Quadrant SRE Visual Console | Multi-widget console with error log streams |

---

## 3. Step-by-Step Deployment Runbook

### Step 1: Initialize gcloud & Enable Required APIs
```bash
gcloud config set project YOUR_PROJECT_ID

gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    cloudbilling.googleapis.com
```

### Step 2: Configure Secret Manager Keys
```bash
# Add your Gemini API key to Secret Manager
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create credence-gemini-api-key \
    --data-file=- \
    --replication-policy="automatic"
```

### Step 3: Configure Terraform Variables
Create your git-ignored `terraform/terraform.prod.tfvars`:
```hcl
project_id                  = "YOUR_PROJECT_ID"
region                      = "us-central1"
service_name                = "credence-server"
environment                 = "prod"
credence_profile            = "balanced" # or 'economy', 'ultra'
monthly_budget_limit_usd    = 15.00
min_instance_count          = 0
max_instance_count          = 2

# Dual-Tier Monitoring & Discord Webhook
monitoring_tier             = "advanced" # or "simple"
discord_webhook_url         = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
enable_uptime_check         = true
```

### Step 4: Provision Infrastructure with Terraform
```bash
cd terraform
terraform init
terraform plan -var-file="terraform.prod.tfvars"
terraform apply -var-file="terraform.prod.tfvars" -state="terraform.prod.tfstate"
```

### Step 5: Build & Deploy the Container (Commit-Before-Deploy)
Ensure your working tree is clean (`git status -s`), then deploy:
```bash
just deploy backend
```

---

## 4. Workload Identity Federation (WIF) for GitHub Actions CI/CD

To automate deployments without managing long-lived service account keys:

### 1. Create Workload Identity Pool and Provider
```bash
# 1. Create Pool
gcloud iam workload-identity-pools create "github-pool" \
    --project="YOUR_PROJECT_ID" \
    --location="global" \
    --display-name="GitHub Actions Pool"

# 2. Create Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
    --project="YOUR_PROJECT_ID" \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --display-name="GitHub Actions Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"
```

### 2. Bind IAM Service Account to Repository
```bash
gcloud iam service-accounts add-iam-policy-binding "credence-cloud-run-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --project="YOUR_PROJECT_ID" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_REPO"
```

---

## 5. Connecting Antigravity & Claude Desktop to Cloud Run

Once deployed, retrieve your Cloud Run SSE endpoint:
```bash
just gcp status
# Output: https://credence-server-xxxxx-uc.a.run.app
```

Add the remote endpoint to your `mcp_config.json`:
```json
{
  "mcpServers": {
    "credence_remote": {
      "url": "https://credence-server-xxxxx-uc.a.run.app/sse"
    }
  }
}
```

---

## 6. Parameterized Operator Workflows (`Justfile`)

The repository provides a single canonical parameterized operator command family (`just gcp [action] [arg]`) with automated preflight validation:

| Command | Action | Description |
| :--- | :--- | :--- |
| `just preflight gcloud` | Preflight Gate | Verifies `gcloud` binary installation and active authenticated account. |
| `just gcp status` | Inspection | Displays active Cloud Run revision, image tag, CPU/memory, and traffic split. |
| `just gcp logs [limit]` | Forensics | Queries structured Cloud Run logs via `gcloud logging read` (default: 30 lines). |
| `just gcp tail` | Live Stream | Streams real-time container logs via `gcloud beta run services logs tail`. |
| `just gcp revisions` | History | Lists all historical revisions with author, deploy timestamp, and traffic split. |
| `just gcp describe` | Deep Inspect | Dumps full JSON/YAML service specification. |
| `just gcp probe` | Multi-Probe | Probes `/health`, `/api/health`, `/sse`, `/api/reports`, and `/api/sifter/status`. |
| `just gcp germinate [burst]` | Remote Sifting | Invokes remote `/api/germinate` endpoint to trigger Miracle-Gro ignition. |
| `just gcp rollback <revision>` | Safe Revert | Rolls back 100% traffic allocation to a previous healthy revision. |
| `just deploy backend` | Safe Deploy | Submits container build via Cloud Build, deploys to Cloud Run, and executes health probe. |

---

## 7. Scale-to-Zero Cold Start Optimization & SRE Tuning

When operating under `min_instance_count = 0` ($0.00 idle compute ceiling), Credence implements a 5-pillar serverless cold start optimization framework:

1. **Startup CPU Boost (`startup_cpu_boost = true`)**: Dynamically allocates 2–4 vCPUs during container boot to accelerate CPU-bound Python AST parsing and import graph loading.
2. **Direct Virtualenv Binary Execution**: Bypasses Poetry's CLI wrapper by executing `/app/.venv/bin/credence serve` directly with `PATH="/app/.venv/bin:$PATH"`, saving ~950ms.
3. **Build-Time Bytecode Precompilation (`compileall`)**: Docker images precompile `.pyc` files during build, eliminating AST compilation on cold boots.
4. **Lazy Dependency Deferral**: Heavy modules (`trafilatura`, `dateparser`, `playwright`) are lazy-loaded inside tool handlers, dropping module import latency by >48%.
5. **Calibrated Startup Probe Sizing**: Configured with `failure_threshold = 30`, `period_seconds = 2`, `timeout_seconds = 2`, and `initial_delay_seconds = 0`, providing a 60s grace window for initial node germination while detecting HTTP readiness within ~1.5–2.0s once Uvicorn starts listening.

*For complete benchmarks and mathematical breakdown, see the [Cloud Run Cold Start Blueprint](blueprints/cloudrun-scale-to-zero-cold-start-optimization.md) and [Engineering Blog Essay](../blog/taming-the-10-second-cold-start-scale-to-zero.md).*
