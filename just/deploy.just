# ==============================================================================
# 4. Multi-Plane Vendor Operations [vendor: gcloud, cloudflare, github, terraform]
# ==============================================================================

# Google Cloud Platform & Cloud Run operations (status, logs, tail, revisions, describe, probe, germinate, rollback)
gcp action="status" arg="": (preflight "gcloud")
    #!/usr/bin/env bash
    set -euo pipefail
    SERVICE="credence-server"
    REGION="us-central1"
    PROJECT="credence-prod-505902"

    case "{{action}}" in
        status)
            echo "=== Cloud Run Compute Plane Status: $SERVICE ($REGION) ==="
            gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" \
                --format="table(metadata.name:label=SERVICE, status.url:label=URL, status.latestReadyRevisionName:label=LATEST_REVISION, spec.template.spec.containers[0].image:label=CONTAINER_IMAGE, spec.template.spec.containers[0].resources.limits.cpu:label=CPU, spec.template.spec.containers[0].resources.limits.memory:label=MEMORY, status.traffic[0].percent:label=TRAFFIC_PCT)"
            ;;
        logs)
            LIMIT="{{arg}}"
            if [ -z "$LIMIT" ]; then LIMIT="30"; fi
            echo "=== Recent Cloud Run Logs (limit: $LIMIT) ==="
            gcloud logging read "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$SERVICE\"" \
                --project "$PROJECT" --limit "$LIMIT" \
                --format="table(timestamp.date('%Y-%m-%d %H:%M:%S'):label=TIME, severity:label=SEV, textPayload:label=MESSAGE, httpRequest.status:label=HTTP, httpRequest.requestUrl:label=URL)"
            ;;
        tail)
            echo "=== Streaming Live Cloud Run Logs (Ctrl+C to stop) ==="
            gcloud beta run services logs tail "$SERVICE" --region "$REGION" --project "$PROJECT"
            ;;
        revisions)
            echo "=== Cloud Run Revision History ==="
            gcloud run revisions list --service "$SERVICE" --region "$REGION" --project "$PROJECT" \
                --format="table(metadata.name:label=REVISION, status.conditions[0].status:label=READY, spec.containers[0].image:label=IMAGE, metadata.creationTimestamp.date('%Y-%m-%d %H:%M:%S'):label=DEPLOYED_AT)"
            ;;
        describe)
            gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT"
            ;;
        probe)
            TARGET_SVC="{{arg}}"
            if [ -z "$TARGET_SVC" ]; then TARGET_SVC="$SERVICE"; fi
            echo "=== Probing Live Cloud Run Endpoints ($TARGET_SVC) ==="
            SVC_URL=$(gcloud run services describe "$TARGET_SVC" --region "$REGION" --project "$PROJECT" --format="value(status.url)" 2>/dev/null || echo "https://credence-server-663899237633.us-central1.run.app")
            TARGET_URL="$SVC_URL" poetry run python -c "import os, textwrap; exec(textwrap.dedent('''
                import os, httpx, time
                BASE = os.environ.get('TARGET_URL', 'https://credence-server-663899237633.us-central1.run.app').rstrip('/')
                endpoints = [
                    ('/health', 'GET'),
                    ('/api/health', 'GET'),
                    ('/sse', 'STREAM'),
                    ('/api/cost/telemetry', 'GET'),
                    ('/api/reports?limit=3', 'GET'),
                    ('/api/sifter/status', 'GET'),
                    ('/api/feeds/stream?limit=3', 'GET'),
                ]
                with httpx.Client() as client:
                    for path, method in endpoints:
                        t0 = time.perf_counter()
                        try:
                            if method == 'STREAM':
                                with client.stream('GET', BASE + path, timeout=15.0) as r:
                                    dt = (time.perf_counter() - t0) * 1000
                                    icon = '🟢' if r.status_code == 200 else '🔴'
                                    print(icon + ' ' + str(r.status_code) + ' [' + method + '] ' + path.ljust(28) + ' (' + str(round(dt, 1)) + 'ms)')
                            else:
                                r = client.request(method, BASE + path, timeout=15.0)
                                dt = (time.perf_counter() - t0) * 1000
                                icon = '🟢' if r.status_code == 200 else ('🟡' if r.status_code < 500 else '🔴')
                                print(icon + ' ' + str(r.status_code) + ' [' + method + '] ' + path.ljust(28) + ' (' + str(round(dt, 1)) + 'ms)')
                        except Exception as e:
                            print('🔴 ERR [' + method + '] ' + path.ljust(28) + ' (' + str(e) + ')')
            '''))"
            ;;
        germinate)
            BURST="{{arg}}"
            if [ -z "$BURST" ]; then BURST="3"; fi
            echo "=== Invoking Remote Miracle-Gro Germination Burst ($BURST items) ==="
            BURST_VAL="$BURST" poetry run python -c "import textwrap; exec(textwrap.dedent('''
                import os, httpx, json
                base = 'https://credence-server-663899237633.us-central1.run.app'
                burst = os.environ.get('BURST_VAL', '3')
                url = base + '/api/germinate?burst=' + burst
                try:
                    r = httpx.post(url, timeout=120.0)
                    print('Status: ' + str(r.status_code))
                    print(json.dumps(r.json(), indent=2))
                except Exception as e:
                    print('Germination failed: ' + str(e))
            '''))"
            ;;
        rollback)
            REV="{{arg}}"
            if [ -z "$REV" ]; then
                echo "❌ Please provide a revision name to rollback to. e.g. just gcp rollback credence-server-00001-ck8"
                exit 1
            fi
            echo "Rolling back traffic 100% to revision: $REV"
            gcloud run services update-traffic "$SERVICE" --region "$REGION" --project "$PROJECT" --to-revisions="$REV=100"
            ;;
        *)
            echo "❌ Unknown gcp action '{{action}}'. Valid options: status, logs, tail, revisions, describe, probe, germinate, rollback."
            exit 1
            ;;
    esac

# Cloudflare Edge Plane operations (status, logs, login, deploy)
edge action="status": (preflight "wrangler")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        status)
            echo "=== Cloudflare Edge Plane Status ==="
            if (cd web && npx wrangler whoami 2>&1 | grep -q "You are logged in"); then
                (cd web && npx wrangler whoami)
                echo ""
                echo "=== Edge Router Deployments (credence.run) ==="
                (cd web && npx wrangler deployments list)
                echo ""
                echo "=== Docs Pages Deployments (docs.credence.run) ==="
                (cd ../credence-docs && npx wrangler pages deployment list --project-name=credence-docs)
            else
                echo "⚠️  Cloudflare Wrangler not logged in locally. Run 'just edge login' or configure CLOUDFLARE_API_TOKEN."
            fi
            ;;
        logs|tail)
            echo "=== Streaming Cloudflare Edge Router Logs ==="
            (cd web && npx wrangler tail)
            ;;
        login)
            (cd web && npx wrangler login)
            ;;
        deploy)
            if [ "${FORCE_PROD_DEPLOY:-false}" != "true" ]; then
                echo -e "\033[1;33m⚠️  ========================================================================\033[0m"
                echo -e "\033[1;33m⚠️  CLOUDFLARE EDGE PRODUCTION DEPLOYMENT WARNING\033[0m"
                echo -e "\033[1;33m⚠️  ========================================================================\033[0m"
                echo -e "\033[1;33m⚠️  Target Domain     : credence.run (Cloudflare Workers Anycast Router)\033[0m"
                echo -e "\033[1;33m⚠️  Standard Process  : Deploy via GitHub Actions PR merge to 'main'.\033[0m"
                echo -e "\033[1;33m⚠️  ========================================================================\033[0m"
                read -r -p "Type 'DEPLOY-PROD' to confirm edge deployment: " CONFIRM_STR
                if [ "$CONFIRM_STR" != "DEPLOY-PROD" ]; then
                    echo -e "\033[1;31m❌ Edge deployment cancelled.\033[0m"
                    exit 1
                fi
            fi
            echo "=== Deploying Cloudflare Edge Router & Web Assets ==="
            (cd web && npx wrangler deploy)
            ;;
        *)
            echo "❌ Unknown edge action '{{action}}'. Valid options: status, logs, login, deploy."
            exit 1
            ;;
    esac

# GitHub Actions CI/CD pipeline monitoring (status, watch, secrets)
pipeline action="status" repo="all": (preflight "gh")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        status)
            if [ "{{repo}}" = "all" ] || [ "{{repo}}" = "credence" ]; then
                echo "=== CI/CD Runs: artibyrd/credence ==="
                gh run list -R artibyrd/credence --limit 5 || true
            fi
            if [ "{{repo}}" = "all" ] || [ "{{repo}}" = "docs" ] || [ "{{repo}}" = "credence-docs" ]; then
                echo ""
                echo "=== Pages Deploy Runs: artibyrd/credence-docs ==="
                gh run list -R artibyrd/credence-docs --limit 5 || true
            fi
            ;;
        watch)
            gh run watch -R artibyrd/credence
            ;;
        secrets)
            echo "=== Secrets: artibyrd/credence ==="
            gh secret list -R artibyrd/credence || true
            echo ""
            echo "=== Secrets: artibyrd/credence-docs ==="
            gh secret list -R artibyrd/credence-docs || true
            ;;
        *)
            echo "❌ Unknown pipeline action '{{action}}'. Valid options: status, watch, secrets."
            exit 1
            ;;
    esac

# Multi-Cloud Terraform Infrastructure (validate, plan, apply, output)
tf action="validate" env="prod" extra="": (preflight "terraform")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        validate)
            if [ ! -d terraform/.terraform ]; then
                terraform -chdir=terraform init -backend=false
            fi
            terraform -chdir=terraform fmt -check
            terraform -chdir=terraform validate
            ;;
        plan)
            VAR_FILE="terraform.{{env}}.tfvars"
            STATE_FILE="terraform.{{env}}.tfstate"
            if [ ! -f "terraform/${VAR_FILE}" ]; then VAR_FILE="terraform.tfvars"; fi
            terraform -chdir=terraform plan -var-file="${VAR_FILE}" -state="${STATE_FILE}" {{extra}}
            ;;
        apply)
            VAR_FILE="terraform.{{env}}.tfvars"
            STATE_FILE="terraform.{{env}}.tfstate"
            if [ ! -f "terraform/${VAR_FILE}" ]; then VAR_FILE="terraform.tfvars"; fi
            terraform -chdir=terraform apply -var-file="${VAR_FILE}" -state="${STATE_FILE}" {{extra}}
            ;;
        output)
            STATE_FILE="terraform.{{env}}.tfstate"
            terraform -chdir=terraform output -state="${STATE_FILE}" {{extra}}
            ;;
        *)
            echo "❌ Unknown tf action '{{action}}'. Valid options: validate, plan, apply, output."
            exit 1
            ;;
    esac

# Bootstrap and manage operator administrative authentication credentials
auth-bootstrap env="local":
    @poetry run python3 scripts/bootstrap_admin_auth.py {{env}}

# Print the active local operator admin authentication token
auth-token:
    @poetry run python3 scripts/bootstrap_admin_auth.py local --print-token

# One-command developer onboarding: setup dependencies, preflight, bootstrap admin key, germinate node, and verify
ignite burst="3":
    @just setup
    @just preflight all
    @just auth-bootstrap local
    @just germinate {{burst}}
    @just test mock
    @just doctor
    @echo -e "\033[1;32m🌱 Credence Node Ignited & Ready for Operations!\033[0m"

# Comprehensive multi-plane diagnostic health check across Edge, Compute, Infra, and Agents
doctor env="prod":
    #!/usr/bin/env bash
    set -euo pipefail
    TARGET_SERVICE="credence-server"
    if [ "{{env}}" = "dev" ] || [ "{{env}}" = "basic" ]; then TARGET_SERVICE="credence-dev"; fi
    echo "================================================================="
    echo "         🩺 Credence Multi-Plane Health Diagnostic ({{env}})    "
    echo "================================================================="
    echo ""
    echo "--- 1. Declarative Agent & Workspace Plane ---"
    just agent-check || true
    echo ""
    echo "--- 2. Compute Plane (Google Cloud Run: ${TARGET_SERVICE}) ---"
    just gcp status || true
    echo ""
    just gcp probe "${TARGET_SERVICE}" || true
    echo ""
    echo "--- 3. Edge Plane (Cloudflare Workers & Pages) ---"
    just edge status || true
    echo ""
    echo "--- 4. Infrastructure Plane (Terraform: {{env}}) ---"
    just tf validate || true
    echo ""
    echo "================================================================="
    echo "                  Diagnostic Audit Complete                      "
    echo "================================================================="

# Multi-plane deployment pipeline with automated post-flight verification (backend, edge, compose, dev, prod, all)
deploy target="backend" env="dev" project_id="auto":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{target}}" != "compose" ] && [ -n "$(git status --porcelain)" ]; then
        echo -e "\033[1;31m❌ Working tree is dirty. Per the Commit-Before-Deploy invariant, all changes must be committed before deploying to the cloud.\033[0m"
        git status -s
        exit 1
    fi

    # Determine if this deploy targets production
    IS_PROD=false
    if [ "{{target}}" = "prod" ] || [ "{{target}}" = "all" ] || [ "{{env}}" = "prod" ] || [ "{{env}}" = "advanced" ]; then
        IS_PROD=true
    fi

    # Resolve target project ID
    ACTUAL_PROJECT_ID="{{project_id}}"
    if [ "$ACTUAL_PROJECT_ID" = "auto" ] || [ -z "$ACTUAL_PROJECT_ID" ]; then
        if [ "$IS_PROD" = "true" ]; then
            ACTUAL_PROJECT_ID="credence-prod-505902"
        else
            ACTUAL_PROJECT_ID="credence-dev-495173"
        fi
    fi

    # Safety Gate for Local Production Deployments
    if [ "$IS_PROD" = "true" ]; then
        if [ "${FORCE_PROD_DEPLOY:-false}" != "true" ]; then
            echo -e "\033[1;33m⚠️  ========================================================================\033[0m"
            echo -e "\033[1;33m⚠️  PRODUCTION DEPLOYMENT WARNING (LOCAL OVERRIDE)\033[0m"
            echo -e "\033[1;33m⚠️  ========================================================================\033[0m"
            echo -e "\033[1;33m⚠️  Target Environment : PRODUCTION (${ACTUAL_PROJECT_ID} / Cloudflare Edge)\033[0m"
            echo -e "\033[1;33m⚠️  Standard Process   : Use Pull Request merge to 'main' for production releases.\033[0m"
            echo -e "\033[1;33m⚠️  Local Execution    : Strictly reserved for testing, diagnostics & emergency fixes.\033[0m"
            echo -e "\033[1;33m⚠️  ========================================================================\033[0m"
            read -r -p "Type 'DEPLOY-PROD' to confirm local production deployment: " CONFIRM_STR
            if [ "$CONFIRM_STR" != "DEPLOY-PROD" ]; then
                echo -e "\033[1;31m❌ Local production deployment cancelled. Rely on standard PR merge workflow.\033[0m"
                exit 1
            fi
            echo -e "\033[1;32m✅ Production deployment confirmed by operator.\033[0m"
        else
            echo "ℹ️  FORCE_PROD_DEPLOY=true detected. Bypassing interactive production confirmation prompt."
        fi
    fi

    case "{{target}}" in
        backend)
            just preflight gcloud
            SERVICE_NAME="credence-server"
            PROFILE="balanced"
            MEM="1Gi"
            if [ "{{env}}" = "dev" ] || [ "{{env}}" = "basic" ]; then
                SERVICE_NAME="credence-dev"
                PROFILE="economy"
                MEM="512Mi"
                echo "🚀 Deploying in BASIC / DEV Mode (${SERVICE_NAME}, profile: ${PROFILE}, memory: ${MEM}, project: ${ACTUAL_PROJECT_ID})..."
            else
                echo "🚀 Deploying in ADVANCED / PRODUCTION Mode (${SERVICE_NAME}, profile: ${PROFILE}, memory: ${MEM}, project: ${ACTUAL_PROJECT_ID})..."
            fi
            echo "=== [1/3] Building & Submitting Cloud Run Container via Cloud Build ==="
            gcloud builds submit --project=${ACTUAL_PROJECT_ID} --tag gcr.io/${ACTUAL_PROJECT_ID}/${SERVICE_NAME}:latest
            echo "=== [2/3] Deploying Container to Google Cloud Run ==="
            gcloud run deploy "${SERVICE_NAME}" \
                --image gcr.io/${ACTUAL_PROJECT_ID}/${SERVICE_NAME}:latest \
                --region us-central1 \
                --project ${ACTUAL_PROJECT_ID} \
                --memory "${MEM}" \
                --cpu 1 \
                --execution-environment gen2 \
                --cpu-boost \
                --set-env-vars="ENV={{env}},CREDENCE_PROFILE=${PROFILE},CREDENCE_BACKUP_ENABLED=true,CREDENCE_BOREDOM_ENABLED=true,CREDENCE_SIFTER_ENABLED=true" \
                --allow-unauthenticated
            echo "=== [3/3] Executing Post-Deployment Live Health Probe ==="
            just gcp probe "${SERVICE_NAME}"
            ;;
        edge)
            just preflight wrangler
            echo "=== Deploying Cloudflare Edge Router ==="
            just edge deploy
            ;;
        compose)
            MODE="{{env}}"
            if [ "$MODE" = "prod" ] || [ "$MODE" = "advanced" ]; then
                echo "🚀 Launching Planetary Sovereign Stack (Credence + Postgres + MinIO + Valkey)..."
                docker compose -f docker-compose.prod.yml up -d
            else
                echo "🚀 Launching Basic Sovereign Node (Credence + SQLite)..."
                docker compose up -d
            fi
            ;;
        dev)
            just deploy backend "dev" "credence-dev-495173"
            ;;
        prod)
            just deploy backend "prod" "credence-prod-505902"
            ;;
        all)
            echo "=== [Phase 1/3] Deploying Dev Environment ==="
            just deploy backend "dev" "credence-dev-495173"
            echo "=== [Phase 2/3] Deploying Production Environment ==="
            just deploy backend "prod" "credence-prod-505902"
            echo "=== [Phase 3/3] Deploying Cloudflare Anycast Edge Router ==="
            just deploy edge
            ;;
        *)
            echo "❌ Unknown deploy target '{{target}}'. Valid options: backend, edge, compose, dev, prod, all."
            exit 1
            ;;
    esac
