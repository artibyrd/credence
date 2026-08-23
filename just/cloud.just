# ==============================================================================
# 5. Hosted Cloud, Edge & Terraform Operations [hosted: safe & gated]
# ==============================================================================

# Maintainer GCP and Cloudflare environment defaults
GCP_PROD_PROJECT := env_var_or_default("CREDENCE_GCP_PROD_PROJECT", "credence-prod-505902")
GCP_DEV_PROJECT  := env_var_or_default("CREDENCE_GCP_DEV_PROJECT", "credence-dev-495173")
GCP_REGION       := env_var_or_default("CREDENCE_GCP_REGION", "us-central1")
EDGE_DOMAIN      := env_var_or_default("CREDENCE_EDGE_DOMAIN", "credence.run")

# Google Cloud Run compute plane status and traffic distribution
[group('hosted: safe')]
cloud-status env="prod": (preflight "gcloud")
    #!/usr/bin/env bash
    set -euo pipefail
    PROJECT="{{ if env == 'dev' { GCP_DEV_PROJECT } else { GCP_PROD_PROJECT } }}"
    SERVICE="{{ if env == 'dev' { 'credence-dev' } else { 'credence-server' } }}"
    echo "=== Cloud Run Compute Plane Status: $SERVICE ($PROJECT / {{GCP_REGION}}) ==="
    if ! gcloud run services describe "$SERVICE" --region "{{GCP_REGION}}" --project "$PROJECT" \
        --format="table(metadata.name:label=SERVICE, status.url:label=URL, status.latestReadyRevisionName:label=LATEST_REVISION, spec.template.spec.containers[0].image:label=CONTAINER_IMAGE, spec.template.spec.containers[0].resources.limits.cpu:label=CPU, spec.template.spec.containers[0].resources.limits.memory:label=MEMORY, status.traffic[0].percent:label=TRAFFIC_PCT)" 2>/dev/null; then
        echo -e "\033[1;33mℹ️ Local gcloud session requires re-auth. Verifying live HTTP endpoint directly:\033[0m"
        just cloud-probe "$SERVICE" "{{env}}"
    fi

# Read recent Cloud Run logs
[group('hosted: safe')]
cloud-logs limit="30" env="prod": (preflight "gcloud")
    #!/usr/bin/env bash
    set -euo pipefail
    PROJECT="{{ if env == 'dev' { GCP_DEV_PROJECT } else { GCP_PROD_PROJECT } }}"
    SERVICE="{{ if env == 'dev' { 'credence-dev' } else { 'credence-server' } }}"
    echo "=== Recent Cloud Run Logs (limit: {{limit}}) ==="
    gcloud logging read "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE\"" \
        --project "$PROJECT" --limit "{{limit}}" \
        --format="table(timestamp.date('%Y-%m-%d %H:%M:%S'):label=TIME, severity:label=SEV, textPayload:label=MESSAGE, httpRequest.status:label=HTTP, httpRequest.requestUrl:label=URL)"

# Stream live Cloud Run logs (Ctrl+C to stop)
[group('hosted: safe')]
cloud-tail env="prod": (preflight "gcloud")
    #!/usr/bin/env bash
    set -euo pipefail
    PROJECT="{{ if env == 'dev' { GCP_DEV_PROJECT } else { GCP_PROD_PROJECT } }}"
    SERVICE="{{ if env == 'dev' { 'credence-dev' } else { 'credence-server' } }}"
    echo "=== Streaming Live Cloud Run Logs ($SERVICE / $PROJECT) ==="
    gcloud beta run services logs tail "$SERVICE" --region "{{GCP_REGION}}" --project "$PROJECT"

# Cloud Run revision deployment history
[group('hosted: safe')]
cloud-revisions env="prod": (preflight "gcloud")
    #!/usr/bin/env bash
    set -euo pipefail
    PROJECT="{{ if env == 'dev' { GCP_DEV_PROJECT } else { GCP_PROD_PROJECT } }}"
    SERVICE="{{ if env == 'dev' { 'credence-dev' } else { 'credence-server' } }}"
    echo "=== Cloud Run Revision History ($SERVICE) ==="
    gcloud run revisions list --service "$SERVICE" --region "{{GCP_REGION}}" --project "$PROJECT" \
        --format="table(metadata.name:label=REVISION, status.conditions[0].status:label=READY, spec.containers[0].image:label=IMAGE, metadata.creationTimestamp.date('%Y-%m-%d %H:%M:%S'):label=DEPLOYED_AT)"

# Describe Cloud Run service configuration
[group('hosted: safe')]
cloud-describe env="prod": (preflight "gcloud")
    #!/usr/bin/env bash
    set -euo pipefail
    PROJECT="{{ if env == 'dev' { GCP_DEV_PROJECT } else { GCP_PROD_PROJECT } }}"
    SERVICE="{{ if env == 'dev' { 'credence-dev' } else { 'credence-server' } }}"
    gcloud run services describe "$SERVICE" --region "{{GCP_REGION}}" --project "$PROJECT"

# Probe live HTTP/SSE endpoints with response latency benchmarks
[group('hosted: safe')]
cloud-probe service="credence-server" env="prod": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    PROJECT="{{ if env == 'dev' { GCP_DEV_PROJECT } else { GCP_PROD_PROJECT } }}"
    DEFAULT_URL="{{ if env == 'dev' { 'https://credence-dev-865363499314.us-central1.run.app' } else { 'https://credence-server-663899237633.us-central1.run.app' } }}"
    SVC_URL=$(gcloud run services describe "{{service}}" --region "{{GCP_REGION}}" --project "$PROJECT" --format="value(status.url)" 2>/dev/null || echo "$DEFAULT_URL")
    echo "=== Probing Live Cloud Run Endpoints ({{service}} [{{env}}] -> $SVC_URL) ==="
    poetry run python scripts/probe_cloud_endpoints.py "$SVC_URL"

# Cloudflare Edge Plane deployment and worker router status
[group('hosted: safe')]
edge-status: (preflight "wrangler")
    #!/usr/bin/env bash
    set -euo pipefail
    echo "=== Cloudflare Edge Plane Status ==="
    if (cd web && npx wrangler whoami 2>&1 | grep -q "You are logged in"); then
        (cd web && npx wrangler whoami)
        echo ""
        echo "=== Edge Router Deployments ({{EDGE_DOMAIN}}) ==="
        (cd web && npx wrangler deployments list)
        echo ""
        echo "=== Docs Pages Deployments (docs.{{EDGE_DOMAIN}}) ==="
        (cd ../credence-docs && npx wrangler pages deployment list --project-name=credence-docs)
    else
        echo "⚠️ Cloudflare Wrangler not logged in locally. Run 'just edge-login' or configure CLOUDFLARE_API_TOKEN."
    fi

# Stream live Cloudflare Worker edge router logs
[group('hosted: safe')]
edge-logs: (preflight "wrangler")
    (cd web && npx wrangler tail)

# GitHub Actions CI/CD pipeline run status
[group('hosted: safe')]
ci-status repo="all": (preflight "gh")
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{repo}}" = "all" ] || [ "{{repo}}" = "credence" ]; then
        echo "=== CI/CD Runs: artibyrd/credence ==="
        gh run list -R artibyrd/credence --limit 5 || true
    fi
    if [ "{{repo}}" = "all" ] || [ "{{repo}}" = "docs" ] || [ "{{repo}}" = "credence-docs" ]; then
        echo ""
        echo "=== Pages Deploy Runs: artibyrd/credence-docs ==="
        gh run list -R artibyrd/credence-docs --limit 5 || true
    fi

# Watch live GitHub Actions workflow execution
[group('hosted: safe')]
ci-watch repo="credence": (preflight "gh")
    gh run watch -R "artibyrd/{{repo}}"

# List configured repository secrets across the ecosystem
[group('hosted: safe')]
ci-secrets: (preflight "gh")
    gh secret list -R artibyrd/credence || true
    gh secret list -R artibyrd/credence-docs || true

# Validate Terraform formatting and multi-cloud configurations
[group('hosted: safe')]
tf-validate: (preflight "terraform")
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -d terraform/.terraform ]; then
        terraform -chdir=terraform init -backend=false
    fi
    terraform -chdir=terraform fmt -check
    terraform -chdir=terraform validate
    echo -e "\033[1;32m✅ Terraform configurations validated successfully.\033[0m"

# Generate Terraform execution plan against target environment
[group('hosted: safe')]
tf-plan env="prod" extra="": (preflight "terraform")
    #!/usr/bin/env bash
    set -euo pipefail
    VAR_FILE="terraform.{{env}}.tfvars"
    STATE_FILE="terraform.{{env}}.tfstate"
    if [ ! -f "terraform/${VAR_FILE}" ]; then VAR_FILE="terraform.tfvars"; fi
    terraform -chdir=terraform plan -var-file="${VAR_FILE}" -state="${STATE_FILE}" {{extra}}

# Display Terraform output variables
[group('hosted: safe')]
tf-output env="prod": (preflight "terraform")
    terraform -chdir=terraform output -state="terraform.{{env}}.tfstate"

# Comprehensive multi-plane diagnostic health check across Edge, Compute, Infra, and Agents
[group('hosted: safe')]
doctor env="prod":
    #!/usr/bin/env bash
    set -euo pipefail
    TARGET_SERVICE="credence-server"
    if [ "{{env}}" = "dev" ]; then TARGET_SERVICE="credence-dev"; fi
    echo "================================================================="
    echo "         🩺 Credence Multi-Plane Health Diagnostic ({{env}})    "
    echo "================================================================="
    echo "--- 1. Declarative Agent & Workspace Plane ---"
    just agent-check || true
    echo ""
    echo "--- 2. Compute Plane (Google Cloud Run: ${TARGET_SERVICE}) ---"
    just cloud-status "{{env}}" || true
    echo ""
    just cloud-probe "${TARGET_SERVICE}" "{{env}}" || true
    echo ""
    echo "--- 3. Edge Plane (Cloudflare Workers & Pages) ---"
    just edge-status || true
    echo ""
    echo "--- 4. Infrastructure Plane (Terraform: {{env}}) ---"
    just tf-validate || true
    echo "================================================================="
    echo "                  Diagnostic Audit Complete                      "
    echo "================================================================="

# Build container and deploy backend to Cloud Run Dev environment (credence-dev-495173)
[group('hosted: gated')]
cloud-deploy-dev: (preflight "gcloud") (auth-check "gcloud")
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "\033[1;31m❌ Working tree is dirty. Per the Commit-Before-Deploy invariant, commit changes before deploying.\033[0m"
        git status -s
        exit 1
    fi
    echo "🚀 Deploying to Google Cloud Run DEV (credence-dev / {{GCP_DEV_PROJECT}})..."
    gcloud builds submit --project={{GCP_DEV_PROJECT}} --tag gcr.io/{{GCP_DEV_PROJECT}}/credence-dev:latest
    gcloud run deploy "credence-dev" \
        --image gcr.io/{{GCP_DEV_PROJECT}}/credence-dev:latest \
        --region {{GCP_REGION}} \
        --project {{GCP_DEV_PROJECT}} \
        --memory 512Mi \
        --cpu 1 \
        --execution-environment gen2 \
        --cpu-boost \
        --set-env-vars="ENV=dev,CREDENCE_PROFILE=economy,CREDENCE_BACKUP_ENABLED=true,CREDENCE_BOREDOM_ENABLED=true,CREDENCE_SIFTER_ENABLED=true" \
        --allow-unauthenticated
    echo "=== Executing Post-Deployment Live Health Probe ==="
    just cloud-probe "credence-dev" "dev"
    echo -e "\033[1;32m✅ Cloud Run Dev deployment successful.\033[0m"
    echo -e "\033[1;36m💡 NEXT STEP: Probe live Dev links and present walkthrough for Mk1 Eyeball review.\033[0m"

# Build container and deploy backend to Cloud Run Production (credence-prod-505902)
[group('hosted: gated')]
[confirm('⚠️ Are you sure you want to execute a LOCAL PRODUCTION deployment to Cloud Run?')]
cloud-deploy-prod: (preflight "gcloud") (auth-check "gcloud")
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "\033[1;31m❌ Working tree is dirty. Per the Commit-Before-Deploy invariant, commit changes before deploying.\033[0m"
        git status -s
        exit 1
    fi
    echo "🚀 Deploying to Google Cloud Run PRODUCTION (credence-server / {{GCP_PROD_PROJECT}})..."
    gcloud builds submit --project={{GCP_PROD_PROJECT}} --tag gcr.io/{{GCP_PROD_PROJECT}}/credence-server:latest
    gcloud run deploy "credence-server" \
        --image gcr.io/{{GCP_PROD_PROJECT}}/credence-server:latest \
        --region {{GCP_REGION}} \
        --project {{GCP_PROD_PROJECT}} \
        --memory 1Gi \
        --cpu 1 \
        --execution-environment gen2 \
        --cpu-boost \
        --set-env-vars="ENV=prod,CREDENCE_PROFILE=balanced,CREDENCE_BACKUP_ENABLED=true,CREDENCE_BOREDOM_ENABLED=true,CREDENCE_SIFTER_ENABLED=true" \
        --allow-unauthenticated
    echo "=== Executing Post-Deployment Live Health Probe ==="
    just cloud-probe "credence-server" "prod"
    echo -e "\033[1;32m✅ Production Cloud Run deployment successful.\033[0m"

# Roll back Cloud Run traffic 100% to a specified revision
[group('hosted: gated')]
[confirm('⚠️ Are you sure you want to roll back Cloud Run traffic?')]
cloud-rollback revision env="prod": (preflight "gcloud") (auth-check "gcloud")
    #!/usr/bin/env bash
    set -euo pipefail
    PROJECT="{{ if env == 'dev' { GCP_DEV_PROJECT } else { GCP_PROD_PROJECT } }}"
    SERVICE="{{ if env == 'dev' { 'credence-dev' } else { 'credence-server' } }}"
    echo "Rolling back traffic 100% to revision: {{revision}}"
    gcloud run services update-traffic "$SERVICE" --region "{{GCP_REGION}}" --project "$PROJECT" --to-revisions="{{revision}}=100"
    echo -e "\033[1;32m✅ Traffic rolled back to revision {{revision}}.\033[0m"

# Invoke remote Miracle-Gro germination burst on Cloud Run instance
[group('hosted: gated')]
cloud-germinate burst="3" env="prod": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    PROJECT="{{ if env == 'dev' { GCP_DEV_PROJECT } else { GCP_PROD_PROJECT } }}"
    SERVICE="{{ if env == 'dev' { 'credence-dev' } else { 'credence-server' } }}"
    SVC_URL=$(gcloud run services describe "$SERVICE" --region "{{GCP_REGION}}" --project "$PROJECT" --format="value(status.url)" 2>/dev/null || echo "https://credence-server-663899237633.us-central1.run.app")
    echo "=== Invoking Remote Miracle-Gro Germination Burst ({{burst}} items -> $SVC_URL) ==="
    poetry run python -c "import httpx, json, os, sys; r = httpx.post('$SVC_URL/api/germinate?burst={{burst}}', timeout=120.0); print('Status: ' + str(r.status_code)); print(json.dumps(r.json(), indent=2)) if r.status_code == 200 else sys.exit(1)"

# Deploy Cloudflare Edge Router and Web Assets
[group('hosted: gated')]
[confirm('⚠️ Are you sure you want to deploy Cloudflare Edge Router & Web Assets?')]
edge-deploy: (preflight "wrangler") (auth-check "wrangler")
    #!/usr/bin/env bash
    set -euo pipefail
    echo "=== Deploying Cloudflare Edge Router & Web Assets ==="
    (cd web && npx wrangler deploy)
    echo -e "\033[1;32m✅ Cloudflare Edge Router deployed.\033[0m"

# Interactive Cloudflare Wrangler authentication login
[group('hosted: gated')]
edge-login: (preflight "wrangler")
    (cd web && npx wrangler login)

# Apply Terraform infrastructure changes to target cloud environment
[group('hosted: gated')]
[confirm('⚠️ Apply Terraform infrastructure changes?')]
tf-apply env="prod" extra="": (preflight "terraform")
    #!/usr/bin/env bash
    set -euo pipefail
    VAR_FILE="terraform.{{env}}.tfvars"
    STATE_FILE="terraform.{{env}}.tfstate"
    if [ ! -f "terraform/${VAR_FILE}" ]; then VAR_FILE="terraform.tfvars"; fi
    terraform -chdir=terraform apply -var-file="${VAR_FILE}" -state="${STATE_FILE}" {{extra}}
    echo -e "\033[1;32m✅ Terraform infrastructure applied successfully.\033[0m"

# Interactive agent command approval bootstrapping runner for maintainer cloud & URL telemetry
[group('bootstrap')]
bootstrap-approvals-hosted:
    @python3 scripts/bootstrap_approvals.py --scope hosted --execute

