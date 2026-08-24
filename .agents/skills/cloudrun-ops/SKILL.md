---
name: cloudrun-ops
description: Google Cloud Run compute plane operations, Workload Identity Federation (WIF) setup, automated CI/CD deployment, container troubleshooting, memory limits, and zero-downtime rollback.
---

# Google Cloud Run Compute Plane Operations Skill

Use this skill when deploying, inspecting, diagnosing, or managing the **Credence Compute Plane** on Google Cloud Run v2.

---

## 1. Quick Reference Commands (`Justfile`)

All Cloud Run operations are managed via the canonical parameterized `just gcp [action] [arg]` recipe family with automated `gcloud` preflight checks:

| Command | Action | Description |
| :--- | :--- | :--- |
| `just preflight gcloud` | Preflight Gate | Verifies `gcloud` binary installation and active authenticated account. |
| `just gcp status` | Status Table | Displays active Cloud Run revision, image tag, CPU/memory, and traffic split. |
| `just gcp logs [limit]` | Forensics | Queries structured Cloud Run logs via `gcloud logging read` (default: 30 lines). |
| `just gcp tail` | Live Stream | Streams real-time container logs via `gcloud beta run services logs tail`. |
| `just gcp revisions` | Revision History | Lists all historical revisions with author, deploy timestamp, and traffic split. |
| `just gcp describe` | Deep Specification | Dumps full JSON/YAML service specification. |
| `just gcp probe` | Multi-Probe | Probes `/health`, `/api/health`, `/sse`, `/api/reports`, and `/api/sifter/status`. |
| `just gcp germinate [burst]` | Remote Sifting | Invokes remote `/api/germinate` endpoint to trigger Miracle-Gro ignition. |
| `just gcp rollback <revision>` | Safe Revert | Rolls back 100% traffic allocation to a previous healthy revision. |
| `just deploy backend` | Safe Deployment | Submits container build via Cloud Build, deploys to Cloud Run, and executes health probe. |

---

## 2. Infrastructure & Compute Sizing Baseline

- **Resource Limits**:
  - **Memory Baseline**: **1Gi (`1024Mi`)**. Headless browser parsing (Playwright) during initial feed sifting / ignition requires ~520 MiB peak memory. Setting memory below 1Gi causes container OOM exit during cold boot.
  - **CPU Baseline**: **1.0 vCPU**.
  - **Scale-to-Zero**: `min_instance_count = 0` (idle compute cost = $0.00).
- **Canonical Container Image**:
  - `gcr.io/credence-prod-505902/credence-server:latest`

---

## 3. Workload Identity Federation (WIF) Least-Privileged Setup for CI/CD

To enable automated GitHub Actions deployment across Dev and Prod environments without long-lived keys:

### A. Dev Environment (`credence-dev-495173`)
```bash
# 1. Create Pool and Provider with repo condition
gcloud iam workload-identity-pools create "github-pool" --project="credence-dev-495173" --location="global" --display-name="GitHub Actions Pool"
gcloud iam workload-identity-pools providers create-oidc "github-provider" --project="credence-dev-495173" --location="global" --workload-identity-pool="github-pool" --display-name="GitHub Actions Provider" --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" --attribute-condition="assertion.repository=='artibyrd/credence'" --issuer-uri="https://token.actions.githubusercontent.com"

# 2. Resource-Scoped Service Account Bindings
gcloud iam service-accounts add-iam-policy-binding "credence-cloud-run-sa@credence-dev-495173.iam.gserviceaccount.com" --project="credence-dev-495173" --role="roles/iam.workloadIdentityUser" --member="principalSet://iam.googleapis.com/projects/865363499314/locations/global/workloadIdentityPools/github-pool/attribute.repository/artibyrd/credence"
gcloud iam service-accounts add-iam-policy-binding "credence-cloud-run-sa@credence-dev-495173.iam.gserviceaccount.com" --project="credence-dev-495173" --role="roles/iam.serviceAccountUser" --member="serviceAccount:credence-cloud-run-sa@credence-dev-495173.iam.gserviceaccount.com"

# 3. Project-Level Least-Privilege Roles
gcloud projects add-iam-policy-binding "credence-dev-495173" --member="serviceAccount:credence-cloud-run-sa@credence-dev-495173.iam.gserviceaccount.com" --role="roles/run.developer"
gcloud projects add-iam-policy-binding "credence-dev-495173" --member="serviceAccount:credence-cloud-run-sa@credence-dev-495173.iam.gserviceaccount.com" --role="roles/cloudbuild.builds.builder"

# 4. Storage Bucket Least-Privilege Persistence Role
gcloud storage buckets add-iam-policy-binding "gs://credence-dev-495173-seeds-nexus" --member="serviceAccount:credence-cloud-run-sa@credence-dev-495173.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"
```

### B. Production Environment (`credence-prod-505902`)
```bash
# 1. Create Pool and Provider with repo condition
gcloud iam workload-identity-pools create "github-pool" --project="credence-prod-505902" --location="global" --display-name="GitHub Actions Pool"
gcloud iam workload-identity-pools providers create-oidc "github-provider" --project="credence-prod-505902" --location="global" --workload-identity-pool="github-pool" --display-name="GitHub Actions Provider" --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" --attribute-condition="assertion.repository=='artibyrd/credence'" --issuer-uri="https://token.actions.githubusercontent.com"

# 2. Resource-Scoped Service Account Bindings
gcloud iam service-accounts add-iam-policy-binding "credence-cloud-run-sa@credence-prod-505902.iam.gserviceaccount.com" --project="credence-prod-505902" --role="roles/iam.workloadIdentityUser" --member="principalSet://iam.googleapis.com/projects/663899237633/locations/global/workloadIdentityPools/github-pool/attribute.repository/artibyrd/credence"
gcloud iam service-accounts add-iam-policy-binding "credence-cloud-run-sa@credence-prod-505902.iam.gserviceaccount.com" --project="credence-prod-505902" --role="roles/iam.serviceAccountUser" --member="serviceAccount:credence-cloud-run-sa@credence-prod-505902.iam.gserviceaccount.com"

# 3. Project-Level Least-Privilege Roles
gcloud projects add-iam-policy-binding "credence-prod-505902" --member="serviceAccount:credence-cloud-run-sa@credence-prod-505902.iam.gserviceaccount.com" --role="roles/run.developer"
gcloud projects add-iam-policy-binding "credence-prod-505902" --member="serviceAccount:credence-cloud-run-sa@credence-prod-505902.iam.gserviceaccount.com" --role="roles/cloudbuild.builds.builder"

# 4. Storage Bucket Least-Privilege Persistence Role
gcloud storage buckets add-iam-policy-binding "gs://credence-prod-505902-seeds-nexus" --member="serviceAccount:credence-cloud-run-sa@credence-prod-505902.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"
```

### C. Configure GitHub Repository Secrets
```bash
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER -R artibyrd/credence -b "projects/663899237633/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
gh secret set GCP_SERVICE_ACCOUNT -R artibyrd/credence -b "credence-cloud-run-sa@credence-prod-505902.iam.gserviceaccount.com"
gh secret set GCP_PROJECT_ID -R artibyrd/credence -b "credence-prod-505902"
gh secret set GCP_DEV_WORKLOAD_IDENTITY_PROVIDER -R artibyrd/credence -b "projects/865363499314/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
gh secret set GCP_DEV_SERVICE_ACCOUNT -R artibyrd/credence -b "credence-cloud-run-sa@credence-dev-495173.iam.gserviceaccount.com"
gh secret set GCP_DEV_PROJECT_ID -R artibyrd/credence -b "credence-dev-495173"
```

---

## 4. Troubleshooting & Disaster Recovery

- **Cold Boot Timeouts**: Ensure Starlette lifespan auto-germination executes in a background `asyncio.create_task` so the HTTP server yields immediately.
- **Container OOM (Exit 137)**: If container exits with `Memory limit exceeded`, increase memory with `gcloud run deploy credence-server --memory 1Gi`.
- **Instant Rollback**: If a newly deployed revision has issues:

```bash
just gcp revisions
just gcp rollback credence-server-00004-xxx
```

---

## 5. Build Context Optimization & Fast Remote Builds

- **Context Exclusion Payload (<5 MB)**:
  - Always maintain synchronized `.dockerignore` and `.gcloudignore` manifests.
  - Exclude `.venv/`, `terraform/`, `data/`, `.mypy_cache/`, `.pytest_cache/`, `tests/`, `docs/`, and `web/` so upload archives remain ~2 MB instead of 800+ MB.
- **Lean Container Builds (`--without dev`)**:
  - Production `Dockerfile` stages must invoke `poetry install --without dev --no-root` and `poetry install --without dev`.
  - Avoid BuildKit-specific cache mounts (`--mount=type=cache`) in standard `Dockerfile` to maintain 100% compatibility across Cloud Build default builders, local Docker, and GitHub Actions.
- **Cloud Build Concurrency**:
  - In `cloudbuild.yaml`, configure `waitFor: ['-']` on independent validation stages (`quality-gate` Ruff/Mypy and `test-gate` Pytest) to run them concurrently before container compilation.

---

## 6. Scale-to-Zero Cold Start Optimization Invariants

When deploying containers under `min_instance_count = 0`:

1. **Startup CPU Boost (`startup_cpu_boost = true` / `--cpu-boost`)**:
   Always enable Startup CPU Boost in Terraform and `gcloud run deploy`. This dynamically allocates 2–4 vCPUs during container boot to accelerate CPU-bound Python imports and AST compilation at $0.00 idle cost.
2. **Direct Virtualenv Binary Invocation (`PATH="/app/.venv/bin:$PATH"`)**:
   Execute `credence serve` directly rather than wrapping in `poetry run credence serve`, eliminating ~800–1,000ms of Poetry CLI environment resolution overhead.
3. **Build-Time Bytecode Precompilation (`compileall`)**:
   Images must precompile bytecode (`RUN python -m compileall -q /app/.venv /app/credence`) to eliminate on-the-fly AST compilation on cold boots.
4. **Aggressive HTTP Readiness Probing**:
   Configure `startup_probe` with `initial_delay_seconds = 0`, `period_seconds = 2`, `timeout_seconds = 2`, `failure_threshold = 30`, and `http_get` against `/health`. This provides a 60s grace window for initial background node germination (sowing preset feeds across tiers) while detecting readiness within ~1.5–2.0s once Uvicorn opens its port.
5. **Execution Environment Gen 2 (`--execution-environment=gen2`)**:
   Always enforce Second Generation execution environment for dedicated Linux kernel performance and faster filesystem page caching.

---

## 7. Cloud Monitoring & Alerting Filter Invariants

1. **Uptime Check Alert Filters**:
   Alert policies tracking `monitoring.googleapis.com/uptime_check/check_passed` MUST include `AND resource.type="uptime_url"` in the filter constraint. Omitting `resource.type` results in GCP Error 400.
2. **Cloud Scheduler Failure Alerts (Log-Based Metrics)**:
   Do not use unpopulated system metric descriptors like `cloudscheduler.googleapis.com/job/attempt_count` (which fail validation with Error 404 until first scheduled execution). Instead, declare a `google_logging_metric` filtering `resource.type="cloud_scheduler_job" AND (severity>=ERROR OR jsonPayload.status!="SUCCESS")` and alert on the log metric.
3. **API Activation Prerequisites**:
   Ensure `cloudscheduler.googleapis.com` is enabled (`gcloud services enable cloudscheduler.googleapis.com`) prior to deploying scheduler resources.

---

## 8. Commit-Before-Deploy Invariant

1. **Immutable Build Provenance**:
   Cloud Build container images (`gcr.io/.../credence-server:<tag>`) and Cloud Run revisions must strictly correspond to an immutable Git commit SHA (`git rev-parse HEAD`).
2. **Zero Dirty Deploys**:
   Never execute `gcloud builds submit`, `gcloud run deploy`, or `just deploy` with unstaged or uncommitted changes in the working tree (`git diff --quiet && git diff --cached --quiet`).
3. **Release Progression Protocol**:
   - **Step 1**: Run local test gauntlet (`just check` $\rightarrow$ 100% passing).
   - **Step 2**: Present working-tree diff & version bump for user Mk1 Eyeball review.
   - **Step 3**: User approves and commits (`git add -A && git commit -m "..."`).
   - **Step 4**: Submit Cloud Build and deploy Cloud Run from the clean commit SHA.
   - **Step 5**: Execute live health probe (`just gcp probe`) and telemetry observation.
   - **Step 6**: Tag release (`git tag vX.Y.Z`).
---

## 5. Multi-Plane Live Deployment Verification Gate

Prior to finalizing any release, verify live health across both Cloud Run compute instances and Cloudflare Edge custom domains using automated Python probe scripts with cache-busting headers (`Cache-Control: no-cache`):
- Dev Cloud Run: `https://credence-dev-wukzqiyqbq-uc.a.run.app/health`
- Prod Cloud Run: `https://credence-server-psgqr4nwoq-uc.a.run.app/health`
- Edge Apex: `https://credence.run/`
- Edge Docs: `https://docs.credence.run/app.js`
- Edge Nexus / Reports: `https://credence.nexus/`, `https://credence.report/`

### 5.1 Dev Environment Staging & Live Walkthrough Verification
When preparing milestone reviews:
1. Every PR opened against `main` automatically triggers `deploy-dev.yml` to build and deploy the compute container to `credence-dev-495173`.
2. Monitor the run via `gh run watch` to confirm container build, deployment, and live health check step pass.
3. Construct an Interactive Verification Matrix in `walkthrough.md` linking live Dev endpoints:
   - Base Service Health: `https://credence-dev-wukzqiyqbq-uc.a.run.app/health`
   - Dynamic Mesh Status: `https://credence-dev-wukzqiyqbq-uc.a.run.app/api/v1/mesh/status`
   - SRE & Topology Telemetry: `https://credence-dev-wukzqiyqbq-uc.a.run.app/api/v1/mesh/stats`
   - SQL Aggregate Rankings: `https://credence-dev-wukzqiyqbq-uc.a.run.app/api/rankings/rules`
4. Confirm live response payloads before presenting `walkthrough.md` for human Mk1 Eyeball review.

### 5.2 Push-and-Delegate CI/CD Governance
- Never execute manual local deploy commands (`just deploy`, `gcloud run deploy`) following a `just git-sync push`.
- All production and dev deployments are authoritatively executed via GitHub Actions CI/CD using Workload Identity Federation.

### 5.3 The CI/CD Verification Gate
- After pushing commits and tags (`just git-sync push`), run `gh run list --limit 1` and `gh run watch` to monitor the GitHub Actions workflow.
- Only announce release completion after the remote workflow exits with success.

---

## 9. Hermetic Docker Buildx & Stale Secret Purging (`--clear-secrets`)

In automated CI/CD workflows (`deploy-dev.yml`, `deploy-backend.yml`), container builds are executed hermetically on the GitHub runner using `docker buildx` rather than invoking remote `gcloud builds submit`. This eliminates WIF permission requirements on default Google Cloud log buckets.

```yaml
# 1. Build and Push directly to GCR via Buildx
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and Push Container Image
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: gcr.io/${{ env.GCP_PROJECT_ID }}/credence-server:${{ github.sha }}

# 2. Deploy to Cloud Run with --clear-secrets
- name: Deploy to Cloud Run
  run: |
    gcloud run deploy ${{ env.CLOUD_RUN_SERVICE }} \
      --image="gcr.io/${{ env.GCP_PROJECT_ID }}/credence-server:${{ github.sha }}" \
      --region="us-central1" \
      --platform="managed" \
      --allow-unauthenticated \
      --clear-secrets \
      --set-env-vars="CREDENCE_ENV=production"
```
Passing `--clear-secrets` ensures that stale secret references from earlier revisions are safely purged before applying fresh environment variables.


### 6. Scale-to-Zero Decoupled Heartbeat Pattern (`min_instances = 0`)
- **Principle**: Never set `min_instances > 0` solely for background cron/daemon tasks (avoids ~$35–$60/mo fixed compute costs).
- **Pattern**: Pair scale-to-zero Cloud Run with Google Cloud Scheduler. Cloud Scheduler sends periodic authenticated OIDC requests (`POST /cron/boredom`) to wake the container, execute the batch, and let it scale back to 0.
- **Required GCP APIs**:
```bash
gcloud services enable cloudscheduler.googleapis.com run.googleapis.com --project="<PROJECT_ID>"
```
- **Least-Privilege Invoker IAM**:
```bash
gcloud run services add-iam-policy-binding credence-server \
    --member="serviceAccount:credence-boredom-cron-sa@<PROJECT_ID>.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --region="us-central1"
```
- **Hermetic Testing Guardrail**:
When testing ASGI endpoints with background lifespans, always use `httpx.AsyncClient(transport=ASGITransport(app=app))` with `unittest.mock.patch(..., new_callable=AsyncMock)` to bypass external network calls and prevent test timeouts.

---

## 10. Serverless Storage Gravity & Cold-Boot Recovery Pattern

When operating stateful, scale-to-zero workloads on Google Cloud Run:

1. **Bundled Cloud SDK Dependencies**:
   Container images must include cloud storage SDKs (`google-cloud-storage`) in production runtime dependencies (`pyproject.toml`) to prevent silent import failures during container boot.
2. **Dual-Pointer Cloud Uploads**:
   Autonomous backup cycles and shutdown hooks must upload both:
   - An immutable timestamped archive: `gs://<BUCKET>/backups/credence_YYYYMMDD_HHMMSS.db.gz` (and `.manifest.json`)
   - The canonical pointer: `gs://<BUCKET>/backups/credence_latest.db.gz` (and `.manifest.json`)
3. **Pre-Boot Hydration & Dynamic Fallback Listing**:
   On cold container startup, pre-boot restoration hooks must inspect local SQLite audit counts (`<= 10`). If a restore is needed:
   - First attempt to download `backups/credence_latest.db.gz`.
   - If `credence_latest.db.gz` is not yet indexed, execute a fallback GCS list query for `backups/credence_*.db.gz` and select the newest timestamped archive.
   - Verify SHA-256 hash, Ed25519 signature, and `PRAGMA integrity_check;` before hydrating local SQLite WAL storage.
4. **Dynamic Bucket Auto-Discovery**:
   Compute instances should dynamically discover `<PROJECT_ID>-seeds-nexus` via GCP instance metadata when `CREDENCE_BACKUP_BUCKET` is not explicitly set in the environment.
5. **Non-Blocking Asynchronous WAL Checkpointing**:
   Periodic backups and SIGTERM lifespan shutdown hooks must invoke awaitable asynchronous backups (`create_database_backup_async(upload_cloud=True)`) using `asyncio.to_thread` to isolate SQLite `.backup()` and gzip compression from the ASGI event loop and ensure cloud uploads finish before container shutdown.
6. **Storage Bucket Least-Privilege IAM**:
   The Cloud Run runtime service account (`credence-cloud-run-sa`) must possess `roles/storage.objectAdmin` on the seeds and backup bucket (`gs://<PROJECT_ID>-seeds-nexus`).

---

## 11. Serverless Cold-Boot Node Vitals & Uptime Guard

When computing SRE metrics and telemetry on scale-to-zero serverless platforms (Google Cloud Run):

1. **The Cold-Boot Division Trap**:
   - On fresh container wake-up or scale-out, `uptime_seconds` can be sub-second or fractional (e.g. 5ms).
   - Never compute throughput velocity by dividing cumulative historical database records (from SQLite genesis germination) by transient process boot uptime. This causes astronomical rate spikes ($12 / 0.005\text{s} = 144,000\text{--}150,000\text{ audits/min}$).
2. **Rated Pipeline Capacity Velocity**:
   - Node throughput velocity must report **Rated Pipeline Capacity**:
     $$\text{Capacity Velocity} = \frac{60,000\text{ ms / min}}{\text{Pipeline Latency per Audit (ms)}}$$
   - Profile benchmarks: `FREE` ($120\text{ms} \to 500\text{ audits/min}$), `BALANCED` ($145\text{ms} \to 413.8\text{ audits/min}$), `ULTRA` ($850\text{ms} \to 70.6\text{ audits/min}$).
3. **Runtime Steady-State Guard**:
   - Historical rolling throughput calculations strictly require $\ge 10\text{ minutes}$ ($600\text{s}$) of sustained container uptime before factoring in daily audit volumes.
4. **Pipeline Duration Floor**:
   - Enforce a minimum duration floor ($\ge 10\text{ms}$) on pipeline duration to prevent sub-millisecond static proxy latencies from rounding down to `0ms / audit`.

---

## 12. Multi-Plane Edge Routing & Dev Preview Isolation Playbook

When deploying decoupled edge routing between Production and Dev environments on Cloudflare Workers and Cloudflare Pages:

1. **Wrangler Route Decoupling**:
   - Top-level `routes = [...]` in `web/wrangler.toml` MUST contain ONLY production apex and production subdomains (`credence.run/*`, `credence.nexus/*`, `credence.report/*`, `credence.foundation/*`, `admin.credence.run/*`, `docs.credence.run/*`).
   - Dev preview routes (`dev.credence.run/*`, `dev.credence.nexus/*`, etc.) MUST be strictly isolated under `[env.dev]` block. Never mix dev routes in top-level production routes to prevent worker route assignment collisions.
2. **Cloudflare Pages Branch Isolation**:
   - Feature branches and dev preview CI (`deploy-dev.yml`) MUST deploy using `--branch=dev` (or `--branch=${{ github.head_ref }}`), publishing exclusively to `https://dev.credence-docs.pages.dev`.
   - Only production releases (`deploy-edge.yml`) on `main` may pass `--branch=main` (publishing to `https://docs.credence.run`).
3. **Edge Worker Reverse Proxying for Sub-Subdomains**:
   - Cloudflare Pages custom domains cannot bind to multi-level subdomains (`dev.docs.credence.run`) without zone-level DNS permissions.
   - The Edge Worker (`web/_worker.js`) transparently proxies `https://dev.credence.run/docs/` and `/blog/` directly to `https://dev.credence-docs.pages.dev/` with zero-cache headers (`Cache-Control: no-cache, no-store, must-revalidate`).
4. **Shared Assets Routing & Fallback**:
   - Requests for `/assets/*` in `_worker.js` MUST bypass hostname domain prefixing (e.g. `reqPath.startsWith('/assets/')`) to prevent stylesheets and shared scripts from 404ing on custom apex subdomains.
   - Workers should fall back to the root `reqPath` if a domain-prefixed path returns 404.
5. **Bi-Directional Link Confinement**:
   - Workstation (`credence-workstation.js`) and documentation router (`app.js`) MUST dynamically normalize cross-station hyperlinks (`transformTargetUrl` / click listeners) to keep reviewers within `dev.*` subdomains during staging reviews.

---

## 13. Cross-Repo Edge Deployment & Secret Topology

When operating across decoupled ecosystem repositories (`credence`, `credence-docs`, `credence-agent`):

1. **Cloudflare Secret Centralization**:
   - `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` are centralized exclusively in the primary `credence` repository.
   - Pushing isolated commits to `credence-docs` runs a workflow that skips Cloudflare deployment. Full edge preview deployments must be dispatched via the `credence` repository workflow:
     `gh workflow run "Deploy Dev Environment to Google Cloud Run" --ref <branch>`
2. **Edge API Network Resilience**:
   - When querying or purging Cloudflare zone caches via curl in GitHub Actions, always use `--retry 3 --retry-delay 2` and default fallback outputs (`|| echo "{}"` / `|| true`) to prevent transient exit code 56 connection resets from breaking releases.
3. **Decoupled Docs & Blog Domain Routing**:
   - `docs.credence.run` and `blog.credence.run` are proxied to Cloudflare Pages via `web/_worker.js`.
   - `app.js` enforces subdomain routing separation: `docs.credence.run` routes technical reference, and `blog.credence.run` routes sovereign essays, bouncing across subdomains dynamically when cross-plane links are activated.

