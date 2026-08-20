---
title: 'Multi-Cloud Deployment: AWS, Azure, Hetzner & K8s'
description: Deploying the Credence FastMCP server and mesh relays to AWS ECS Fargate,
  Azure Container Apps, Hetzner, and Kubernetes.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Multi-Cloud Deployment: AWS, Azure, Hetzner & K8s

While our reference Terraform infrastructure targets **Google Cloud Platform (Cloud Run v2)**, Credence is packaged as a lightweight, standard OCI container that can run seamlessly on any cloud provider or bare-metal VPS.

```mermaid
graph TD
    subgraph MultiCloud["Decentralized Multi-Cloud Mesh Federation"]
        GCP["GCP Cloud Run v2<br>(FastMCP SSE Reference)"]
        AWS["AWS ECS Fargate<br>(Scale-to-Zero Container)"]
        Azure["Azure Container Apps<br>(Managed Ingress)"]
        Hetzner["Hetzner Cloud / VPS<br>(Sovereign $5/mo CAX11)"]
        K8s["Bare-Metal k3s / K8s<br>(Air-Gapped Newsroom)"]
    end

    CF["Cloudflare Multi-Domain Edge CDN"] --> GCP & AWS & Azure & Hetzner & K8s
    GCP <-->|P2P Gossip 8765| AWS
    AWS <-->|P2P Gossip 8765| Azure
    Azure <-->|P2P Gossip 8765| Hetzner
    Hetzner <-->|P2P Gossip 8765| K8s
```

### Multi-Cloud Provider Matrix

| Platform | Recommended Target | Monthly Cost | Scale-to-Zero | Sovereignty Level |
| :--- | :--- | :--- | :--- | :--- |
| **GCP Cloud Run v2** | Reference FastMCP SSE deployment | $0.00 – $5.00 | ✅ Yes | Commercial Cloud |
| **AWS ECS Fargate** | Enterprise AWS environments | $8.00 – $15.00 | ⚠️ Minimum 1 task | Commercial Cloud |
| **Azure Container Apps** | Microsoft Azure stacks | $0.00 – $5.00 | ✅ Yes | Commercial Cloud |
| **Hetzner Cloud (CAX11)** | Dedicated sovereign nodes | **$4.00 fixed** | ❌ Always-on | **100% Sovereign EU** |
| **Bare-Metal / k3s** | Air-gapped newsrooms | **$0.00 (Self-hosted)** | ❌ Always-on | **100% Air-Gapped** |

---

## 1. AWS Deployment (ECS Fargate & Secrets Manager)

Deploy scale-to-zero or low-cost serverless containers on Amazon Web Services:

```hcl
# terraform/aws/main.tf
resource "aws_ecs_cluster" "credence" {
  name = "credence-cluster"
}

resource "aws_ecs_task_definition" "credence" {
  family                   = "credence-server"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"

  container_definitions = jsonencode([{
    name      = "credence"
    image     = "ghcr.io/artibyrd/credence:latest"
    essential = true
    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
    }]
    environment = [
      { name = "CREDENCE_PROFILE", value = "BALANCED" }
    ]
    secrets = [
      { name = "CREDENCE_GEMINI_API_KEY", valueFrom = aws_secretsmanager_secret.gemini_key.arn }
    ]
  }])
}
```

---

## 2. Microsoft Azure (Azure Container Apps)

Scale-to-zero serverless deployment on Microsoft Azure:

```bash
# Create Azure Container App with scale-to-zero
az containerapp create \
  --name credence-server \
  --resource-group rg-credence \
  --environment env-credence \
  --image ghcr.io/artibyrd/credence:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --secrets gemini-key=YOUR_API_KEY \
  --env-vars CREDENCE_GEMINI_API_KEY=secretref:gemini-key CREDENCE_PROFILE=BALANCED
```

---

## 3. Hetzner / Sovereign Bare-Metal VPS ($5/Month)

For maximum cost efficiency with zero cloud vendor lock-in, deploy on a $5/month Hetzner Cloud VPS (CAX11 ARM64 or CX22 x86):

```yaml
# docker-compose.yml
version: '3.8'

services:
  credence:
    image: ghcr.io/artibyrd/credence:latest
    restart: always
    ports:
      - "8000:8000"
      - "8765:8765"
    environment:
      - CREDENCE_GEMINI_API_KEY=${CREDENCE_GEMINI_API_KEY}
      - CREDENCE_PROFILE=BALANCED
    volumes:
      - ./data:/app/data
```

```bash
docker compose up -d
```

---

## 4. Kubernetes / k3s Sovereign Newsroom Helm Deployment

Deploy on sovereign Kubernetes clusters (`k3s` / `RKE2`):

```bash
helm repo add credence https://charts.credence.nexus
helm install credence-node credence/credence-node \
  --set profile=BALANCED \
  --set persistence.size=10Gi \
  --set apiKeySecret=credence-secrets
```

---

## 5. Local Self-Hosted Execution & Autonomous Feed Sifting (Zero-GCP)

Credence is completely self-contained and does not require Google Cloud Platform or any commercial cloud infrastructure to operate at full fidelity.

### Running 100% Locally

1. **Bootstrap Feed Subscriptions & Run Single Pass**:
```bash
   just seed-reports
   # Equivalent to:
   # poetry run credence feeds bootstrap-presets
   # poetry run credence sifter --once
   # poetry run credence export-catalog
```

2. **Launch Unified Server (FastMCP SSE + REST Gateway + Feed Sifter)**:
```bash
   just serve-sifter
   # Launches Starlette server on http://localhost:8000
   # Exposes /sse (FastMCP 2.0), /api/reports, /api/audit, and background sifter
```

3. **Explore Locally in Web UI**:
```bash
   just serve-web
   # Open http://localhost:8080/viewer.html
   # Web UI automatically detects local REST API on port 8000 and displays live audits
```

> [!TIP]
> All audit snapshots, attestation records, and token consumption ledgers are stored in local SQLite WAL (`credence.db`) with zero network dependencies. Signed Ed25519 attestations are produced with your node's local keypair (`node_identity.json`).

---

## 6. The 3 Delivery Planes & Unified Deployment Architecture

Credence strictly isolates deployment concerns into three independent operational planes:

```mermaid
flowchart TD
    Plane1["1. Edge Plane (Zero-Build CDN)<br>Cloudflare Pages (credence-docs)<br>Cloudflare Workers (credence/web/)"]
    Plane2["2. Compute Plane (FastMCP & REST API)<br>Google Cloud Run (credence-server)<br>Self-Hosted Docker/K3s"]
    Plane3["3. Infra Plane (Static Shells)<br>Terraform (GCP IAM, DNS, GCS Buckets)"]

    Plane1 -->|Automated via deploy-edge.yml / just deploy-edge| LiveEdge["Public Edge CDN"]
    Plane2 -->|Automated via release.yml / just deploy-backend| LiveCompute["Cloud Run Service"]
    Plane3 -->|Manual via tf-apply| LiveInfra["Cloud Resources"]
```

| Operational Plane | Managed Artifacts | Deployment Mechanism |
| :--- | :--- | :--- |
| **Edge Plane** | `web/_worker.js`, static HTML5/CSS, `reports.json` | `just deploy-edge` or `.github/workflows/deploy-edge.yml` on push to `main` |
| **Compute Plane** | `credence-server` container (FastMCP SSE + REST API + Sifter) | `just deploy-backend` or `.github/workflows/release.yml` on version tag |
| **Infra Plane** | DNS Zones, SSL strict mode, IAM roles, GCS storage buckets | `just tf-apply` (executed only when cloud resource topologies change) |

```bash
# Deploy full stack atomically across Edge and Compute:
just deploy all
```

---

## 7. Multi-Cloud References & Provider Documentation

### 📚 Official Cloud Platform Docs
* **AWS Serverless**: [AWS ECS Fargate Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html) &bull; [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
* **Microsoft Azure**: [Azure Container Apps Serverless Overview](https://learn.microsoft.com/en-us/azure/container-apps/overview) &bull; [Azure Key Vault Secrets](https://learn.microsoft.com/en-us/azure/key-vault/secrets/quick-create-portal)
* **Hetzner Cloud**: [Hetzner Cloud ARM64 Server Instances (CAX11)](https://docs.hetzner.com/cloud/servers/overview/) &bull; [Hetzner Cloud CLI (`hcloud`)](https://github.com/hetznercloud/cli)
* **Lightweight Kubernetes**: [k3s - The Lightweight Kubernetes Distribution](https://docs.k3s.io/) &bull; [Helm Charts](https://helm.sh/docs/)
* **Cloudflare Edge**: [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/) &bull; [Cloudflare Pages](https://developers.cloudflare.com/pages/)
* **Google Cloud**: [Google Cloud Run Documentation](https://cloud.google.com/run/docs)

### 🔗 Related Architecture Guides in Credence
* ☁️ [GCP Cloud Run Reference Guide & Dual-Tier Monitoring](../deployment-cloudrun.md)
* 🔒 [Zero-Cloud Sovereign Local LLMs (Ollama & vLLM)](local-llm-airgap.md)
* 🍓 [Raspberry Pi & Homelab Node Setup ($0.00/mo)](../operations/raspberry-pi-homelab.md)
* 🤖 [Universal Agent Interoperability (Cursor, Windsurf, Cline)](universal-agent-interop.md)
* 🏛️ [3-Plane Deployment Governance & System Invariants](../invariants.md)


