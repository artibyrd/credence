---
name: white-label-ops
description: Scaffold independent sovereign federation organizations (credence init-org), validate multi-cloud Terraform templates (GCP and Cloudflare), and deploy zero-build multi-domain edge routing.
---

# White-Label Federation & Multi-Cloud Infrastructure Skill

Use this skill when deploying, provisioning, or scaffolding sovereign federated Credence networks.

---

## Core Commands
- `credence init-org <org-name> --domain <domain> --region us-central1`: Scaffold turnkey organization.
- `just gcp-build`: Build container image on Google Cloud Build and push to GCR.
- `just tf-plan` / `just tf-apply`: Plan and apply multi-cloud Terraform configurations across Cloudflare and GCP.
- `just seed-sync`: Synchronize signed genesis seeds (`peers.json`) and taxonomy catalogs to GCS origin buckets.
- `just tf-validate`: Validate Terraform configurations across Cloudflare and GCP modules.
- `just serve-web`: Launch local preview server for visual Mk1 Eyeball review of web artifacts.

---

## Multi-Cloud Architecture & Edge Topology
- **Google Cloud Platform (GCP)**:
  - **Cloud Run v2**: Compute engine for FastMCP 2.0 SSE (`/sse`) with scale-to-zero compute savings and IAM public invoker policy.
  - **Secret Manager**: Secure custody for reasoning engine API keys (`credence-gemini-api-key`).
  - **Google Cloud Storage (GCS)**: Durable origins for genesis seeds (`peers.json`) and taxonomy catalogs (`/v1/*.json`).
- **Cloudflare (Zero-Build Edge Network)**:
  - **Zero-Build Static Assets**: Native ES Modules with zero npm dependencies, zero build toolchains.
  - **Multi-Domain Edge Router (`_worker.js`)**: Single edge worker routing across apex domains and subdomains (`credence.run`, `credence.nexus`, `credence.foundation`, `credence.report`).
  - **FastMCP Reverse Proxy**: Intercepts `mcp.<domain>` traffic, rewrites internal `Host` header to Cloud Run service URL, and streams real-time Server-Sent Events with global CORS headers.

---

## Production Edge Router Invariants
1. **Worker Asset Binding**: Always specify `binding = "ASSETS"` in `wrangler.toml` when using `_worker.js` alongside static assets.
2. **Asset Boundary Protection**: Include `.assetsignore` containing `_worker.js` and `wrangler.toml` to prevent server-side code from being exposed as static files.
3. **FastMCP Transport Security**: Always configure `TransportSecuritySettings(enable_dns_rebinding_protection=False, allowed_hosts=["*"], allowed_origins=["*"])` on FastMCP SSE servers behind Cloudflare.
4. **Origin Header Translation**: Rewrite `Host` header to `<service>.run.app` in `_worker.js` to bypass Google Search Console TXT domain verification roadblocks.

---

## 4. Multi-Environment Boundary & State Isolation

1. **State Isolation**:
   Always isolate Terraform state per environment (`-state="terraform.{{env}}.tfstate"`), ensuring `terraform.dev.tfstate` and `terraform.prod.tfstate` never collide or cross boundaries.
2. **Dual-Project GCP Setup**:
   - Dev Project: `credence-dev-XXXXXX` (Basic Dev, SQLite WAL, 512Mi, Simple Alert Tier).
   - Prod Project: `credence-prod-XXXXXX` (Advanced Prod, PostgreSQL/R2, 1Gi, Advanced SRE Alert Suite).
3. **Pre-Existing Secret Import**:
   When secrets (such as `credence-gemini-api-key`) are pre-created manually, import them into the environment's state before running `apply`:

```bash
terraform -chdir=terraform import -state=terraform.<env>.tfstate -var-file=terraform.<env>.tfvars google_secret_manager_secret.gemini_api_key projects/<project_id>/secrets/credence-gemini-api-key
```
4. **Launch Parity Deployment Workflow**:
   Sequential release progression: Dev deployment $\rightarrow$ Automated Health Probe $\rightarrow$ Prod deployment $\rightarrow$ Edge Plane Anycast deployment.
5. **Storage Gravity Bucket IAM Policy**:
   Ensure sovereign organization Terraform templates bind `roles/storage.objectAdmin` on the seeds/backups bucket to the compute runtime service account:

```hcl
resource "google_storage_bucket_iam_member" "seeds_sa_admin" {
  bucket = google_storage_bucket.seeds_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}
```

---

## 5. Multi-Domain Edge Routing & Zero-Cache CDN Governance

### Complete Multi-Domain Route Matrix
Every sovereign domain must declare explicit route patterns in `wrangler.toml` across all zones:
- `credence.run`: `credence.run/*`, `admin.credence.run/*`, `docs.credence.run/*`, `blog.credence.run/*`, `mcp.credence.run/*` (and `dev.` counterparts)
- `credence.nexus`: `credence.nexus/*`, `seeds.credence.nexus/*` (and `dev.` counterparts)
- `credence.foundation`: `credence.foundation/*`, `keys.credence.foundation/*` (and `dev.` counterparts)
- `credence.report`: `credence.report/*` (and `dev.` counterparts)

### Edge Worker Routing & Header Invariants
1. **Dynamic Pages Proxying (`_worker.js`)**: Decoupled doc and blog runtimes (`docs.credence.run`, `blog.credence.run`) must proxy to `credence-docs.pages.dev` with `Host: credence-docs.pages.dev` and downstream `Cache-Control: no-cache, no-store, must-revalidate` to prevent edge POP staleness.
2. **Dedicated Root File Mapping**:
   - `seeds.credence.nexus/` maps to `/peers.json`.
   - `keys.credence.foundation/` maps to `/root.pub`.
3. **Static Asset Zero-Cache Policy**: All HTML, JS, JSON, and CSS assets must return `Cache-Control: public, max-age=0, must-revalidate` to ensure instant global deployment propagation.
4. **CI/CD Automated Zone Purge**: Edge deployment workflows must execute automated Cloudflare zone cache purging (`purge_everything: true`) to invalidate stale POP caches.
5. **Dual-Plane DNS & Worker Binding**: Every domain/subdomain route declared in `wrangler.toml` must have a corresponding CNAME record in Terraform (`terraform/cloudflare.tf`) with `proxied = true`. Edge worker asset lookups via `env.ASSETS.fetch()` must target explicit `.html` files (e.g. `/${prefix}/index.html`) using the incoming `request.url` origin to prevent internal 307 redirect cascades.
6. **Cloudflare Pages & Workers Dual-Build Compatibility**: Standalone documentation or static site repositories (`credence-docs`) deployed via Cloudflare Pages or Cloudflare Workers Git integration must provide a minimal `_worker.js` delegating to `env.ASSETS.fetch(request)` and configure `main = "_worker.js"` with `[assets] directory = "."` in `wrangler.toml` to satisfy both Pages and Workers build runners seamlessly without `package.json` build errors.




