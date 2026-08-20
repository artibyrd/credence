---
title: 'Operational Guide: Single-Project vs Dual-Project GCP Topologies'
description: Comprehensive architectural comparison, prerequisite runbooks, and
  CLI commands for running Credence in a single partitioned GCP project vs hard dual-project
  isolation.
since_version: v1.18.0
verified_version: v1.18.2
last_verified: '2026-08-19'
---

# Operational Guide: Single-Project vs Dual-Project GCP Topologies

Credence multi-cloud infrastructure natively supports both **Single-Project Service Partitioning** and **Dual-Project Hard Isolation** with zero architectural changes. This runbook details how to choose, provision, and operate both topologies with complete prerequisite setup instructions.

---

## 1. Architectural Comparison

```mermaid
graph TB
    subgraph DualProj ["Topology A: Dual-Project Hard Isolation (Enterprise Standard)"]
        subgraph DevProj ["GCP: credence-dev-XXXXXX"]
            DevCR["Cloud Run: credence-dev<br/>(512Mi | Economy Profile)"]
            DevSM["Secret Manager: credence-gemini-api-key"]
            DevBudget["Budget: $5.00/mo Cap"]
        end
        subgraph ProdProj ["GCP: credence-prod-XXXXXX"]
            ProdCR["Cloud Run: credence-server<br/>(1024Mi | Balanced Profile)"]
            ProdSM["Secret Manager: credence-gemini-api-key"]
            ProdBudget["Budget: $15.00/mo Cap"]
        end
    end

    subgraph SingleProj ["Topology B: Single-Project Service Partitioning (Lean Standard)"]
        subgraph SharedGCP ["GCP: credence-prod-XXXXXX"]
            S_DevCR["Cloud Run: credence-dev"]
            S_ProdCR["Cloud Run: credence-server"]
            S_DevSM["Secret: credence-gemini-api-key-dev"]
            S_ProdSM["Secret: credence-gemini-api-key"]
            SharedBudget["Budget: Combined $15.00/mo Cap"]
        end
    end
```

---

## 2. Comparison Matrix

| Feature | Dual-Project Hard Isolation | Single-Project Service Partitioning |
| :--- | :--- | :--- |
| **GCP Project Boundaries** | 2 Independent Projects (`credence-dev` & `credence-prod`) | 1 Unified Project (`credence-prod`) |
| **Billing Ceiling Isolation**| Hard independent caps ($5.00/mo dev vs $15.00/mo prod) | Shared combined billing cap ($15.00/mo) |
| **IAM Blast Radius** | Zero cross-project access; isolated Service Accounts | Scoped IAM roles within the same project |
| **Secret Manager Keys** | Identical secret names (`credence-gemini-api-key`) | Namespaced secret names (`...-dev` suffix) |
| **State File Isolation** | `terraform.dev.tfstate` & `terraform.prod.tfstate` | `terraform.dev.tfstate` & `terraform.prod.tfstate` |
| **Best For** | Multi-developer teams, compliance, enterprise SLA | Solo operators, homelabs, fast single-bill startups |

---

## 3. Provisioning Runbook: Topology A (Dual-Project Mode)

### Step 1: Create Projects & Link Billing
```bash
# 1. Generate unique project IDs (GCP project IDs must be globally unique)
DEV_PROJECT="credence-dev-$RANDOM"
PROD_PROJECT="credence-prod-$RANDOM"

# 2. Create the GCP projects
gcloud projects create "${DEV_PROJECT}" --name="Credence Dev"
gcloud projects create "${PROD_PROJECT}" --name="Credence Prod"

# 3. Retrieve your Billing Account ID
BILLING_ACCOUNT=$(gcloud billing accounts list --format="value(name)" | head -n 1)

# 4. Link billing account to both projects
gcloud billing projects link "${DEV_PROJECT}" --billing-account="${BILLING_ACCOUNT}"
gcloud billing projects link "${PROD_PROJECT}" --billing-account="${BILLING_ACCOUNT}"
```

### Step 2: Enable Required APIs on Both Projects
```bash
APIS="run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com monitoring.googleapis.com logging.googleapis.com cloudbilling.googleapis.com"

gcloud services enable ${APIS} --project="${DEV_PROJECT}"
gcloud services enable ${APIS} --project="${PROD_PROJECT}"
```

### Step 3: Populate Secrets in Both Projects
```bash
# Store Gemini API Key in Dev Project
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create credence-gemini-api-key \
    --data-file=- \
    --replication-policy="automatic" \
    --project="${DEV_PROJECT}"

# Store Gemini API Key in Prod Project
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create credence-gemini-api-key \
    --data-file=- \
    --replication-policy="automatic" \
    --project="${PROD_PROJECT}"
```

### Step 4: Configure Terraform Variable Files
Create your git-ignored `terraform.dev.tfvars` and `terraform.prod.tfvars` in `credence/terraform/`:

```hcl
# terraform/terraform.dev.tfvars
project_id               = "credence-dev-XXXXXX"
region                   = "us-central1"
service_name             = "credence-dev"
environment              = "dev"
credence_profile         = "economy"
monthly_budget_limit_usd = 5.00
min_instance_count       = 0
max_instance_count       = 1
monitoring_tier          = "simple"
enable_uptime_check      = true
```

```hcl
# terraform/terraform.prod.tfvars
project_id               = "credence-prod-XXXXXX"
region                   = "us-central1"
service_name             = "credence-server"
environment              = "prod"
credence_profile         = "balanced"
monthly_budget_limit_usd = 15.00
min_instance_count       = 0
max_instance_count       = 2
monitoring_tier          = "advanced"
enable_uptime_check      = true
```

### Step 5: Execute Independent State Deployments
```bash
cd terraform

# 1. Deploy Dev Infrastructure
terraform init
terraform apply -var-file="terraform.dev.tfvars" -state="terraform.dev.tfstate" -auto-approve

# 2. Deploy Prod Infrastructure
terraform apply -var-file="terraform.prod.tfvars" -state="terraform.prod.tfstate" -auto-approve
```

---

## 4. Provisioning Runbook: Topology B (Single-Project Mode)

If deploying both Dev and Prod inside one single GCP project:

### Step 1: Create Single Project & Enable APIs
```bash
PROJECT_ID="credence-prod-$RANDOM"
gcloud projects create "${PROJECT_ID}" --name="Credence Unified"
gcloud billing projects link "${PROJECT_ID}" --billing-account="${BILLING_ACCOUNT}"

gcloud services enable \
    run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
    secretmanager.googleapis.com monitoring.googleapis.com logging.googleapis.com cloudbilling.googleapis.com \
    --project="${PROJECT_ID}"
```

### Step 2: Create Partitioned Secrets
```bash
# Production Secret
echo -n "YOUR_PROD_API_KEY" | gcloud secrets create credence-gemini-api-key \
    --data-file=- \
    --replication-policy="automatic" \
    --project="${PROJECT_ID}"

# Development Secret (namespaced)
echo -n "YOUR_DEV_API_KEY" | gcloud secrets create credence-gemini-api-key-dev \
    --data-file=- \
    --replication-policy="automatic" \
    --project="${PROJECT_ID}"
```

### Step 3: Configure Single-Project Variable Files
Both `terraform.dev.tfvars` and `terraform.prod.tfvars` point to the **same** `project_id`, but retain separate `service_name` and state files:

```hcl
# terraform.dev.tfvars
project_id   = "credence-prod-XXXXXX"
service_name = "credence-dev"
environment  = "dev"

# terraform.prod.tfvars
project_id   = "credence-prod-XXXXXX"
service_name = "credence-server"
environment  = "prod"
```

---

## 5. Live Verification & Health Probing

Verify both environments independently using `just doctor`:

```bash
# Probe Dev Environment
just doctor dev

# Probe Production Environment
just doctor prod
```
