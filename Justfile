# Justfile for Credence Epistemic Ecosystem
# Canonical Parameterized Architecture & Multi-Plane Operations

set shell := ["bash", "-c"]

default:
    @just --list

# ==============================================================================
# 1. Parameterized Preflight Toolchain Gates [core: preflight]
# ==============================================================================

# Verify developer CLI dependencies (poetry, docker, gcloud, wrangler, gh, terraform, all)
preflight tool="all":
    #!/usr/bin/env bash
    set -euo pipefail

    check_binary() {
        local name="$1"
        local cmd="$2"
        local install_url="$3"
        local version_cmd="$4"
        if [ -z "$version_cmd" ]; then
            version_cmd="$cmd --version"
        fi
        if ! command -v "$cmd" &>/dev/null; then
            echo -e "\033[0;31m❌ Missing: $name ('$cmd' not found in PATH)\033[0m"
            echo "   👉 Install guide: $install_url"
            return 1
        fi
        local ver
        ver=$($version_cmd 2>&1 | sed -n '1p' || echo "installed")
        echo -e "\033[0;32m✅ $name:\033[0m $ver"
        return 0
    }

    check_gcloud() {
        if ! command -v gcloud &>/dev/null; then
            echo -e "\033[0;31m❌ Missing: Google Cloud SDK (gcloud)\033[0m"
            echo "   👉 Install: https://cloud.google.com/sdk/docs/install"
            return 1
        fi
        local acc
        acc=$(gcloud config get-value account 2>/dev/null || echo "none")
        local proj
        proj=$(gcloud config get-value project 2>/dev/null || echo "none")
        echo -e "\033[0;32m✅ Google Cloud SDK (gcloud):\033[0m Account: \033[1;36m$acc\033[0m | Project: \033[1;36m$proj\033[0m"
        return 0
    }

    check_wrangler() {
        if command -v wrangler &>/dev/null; then
            local ver
            ver=$(wrangler --version 2>&1 | sed -n '1p' || echo "installed")
            echo -e "\033[0;32m✅ Cloudflare Wrangler:\033[0m $ver"
            return 0
        elif command -v npx &>/dev/null; then
            local ver
            ver=$(npx --no-install wrangler --version 2>&1 | sed -n '1p' || echo "available via npx")
            echo -e "\033[0;32m✅ Cloudflare Wrangler (npx):\033[0m $ver"
            return 0
        else
            echo -e "\033[0;31m❌ Missing: Cloudflare Wrangler\033[0m"
            echo "   👉 Install: npm install -g wrangler"
            return 1
        fi
    }

    check_gh() {
        if ! command -v gh &>/dev/null; then
            echo -e "\033[0;31m❌ Missing: GitHub CLI (gh)\033[0m"
            echo "   👉 Install: https://cli.github.com"
            return 1
        fi
        local auth_user
        auth_user=$(gh auth status 2>&1 | grep -o "account [^ ]*" | sed -n '1p' | awk '{print $2}' || echo "authenticated")
        echo -e "\033[0;32m✅ GitHub CLI (gh):\033[0m Logged in ($auth_user)"
        return 0
    }

    case "{{tool}}" in
        poetry)
            check_binary "Poetry" "poetry" "https://python-poetry.org/docs/#installation" ""
            ;;
        docker)
            check_binary "Docker" "docker" "https://docs.docker.com/get-docker/" ""
            check_binary "Docker Compose" "docker" "https://docs.docker.com/compose/" "docker compose version"
            ;;
        gcloud|gcp)
            check_gcloud
            ;;
        wrangler|cloudflare|edge)
            check_wrangler
            ;;
        gh|github)
            check_gh
            ;;
        terraform|tf)
            check_binary "HashiCorp Terraform" "terraform" "https://developer.hashicorp.com/terraform/install" ""
            ;;
        all)
            echo "=== Credence Multi-Plane Toolchain Preflight ==="
            check_binary "Poetry" "poetry" "https://python-poetry.org" "" || true
            check_binary "Docker" "docker" "https://docs.docker.com" "" || true
            check_gcloud || true
            check_wrangler || true
            check_gh || true
            check_binary "Terraform" "terraform" "https://terraform.io" "" || true
            echo "=== Preflight Validation Complete ==="
            ;;
        *)
            echo "❌ Unknown preflight target '{{tool}}'. Valid options: poetry, docker, gcloud, wrangler, gh, terraform, all."
            exit 1
            ;;
    esac

# Install all dependencies and Playwright browser binaries
setup: (preflight "poetry")
    poetry install
    poetry run playwright install chromium

# ==============================================================================
# 2. Testing & Quality Assurance [core: test & quality]
# ==============================================================================

# Run targeted test suites (unit, all, mock, live, e2e, docs, docker)
test suite="unit" extra="": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{suite}}" in
        unit)
            poetry run pytest tests/ -m "unit" --durations=10 {{extra}}
            ;;
        all)
            poetry run pytest tests/ -n auto --durations=10 {{extra}}
            ;;
        mock|e2e-mock)
            poetry run pytest tests/e2e/test_mock_e2e.py -v {{extra}}
            ;;
        live)
            CREDENCE_LIVE_TESTS=1 poetry run pytest tests/e2e/test_live_rotating_suite.py -v -m e2e -s {{extra}}
            ;;
        e2e)
            CREDENCE_LIVE_TESTS=1 poetry run pytest tests/e2e/ -v -m e2e {{extra}}
            ;;
        docs)
            poetry run pytest tests/governance/test_docs_integrity.py -v {{extra}}
            ;;
        docker)
            docker compose run --rm credence poetry run pytest tests/ {{extra}}
            ;;
        *)
            echo "❌ Unknown test suite '{{suite}}'. Valid options: unit, all, mock, live, e2e, docs, docker."
            exit 1
            ;;
    esac

# Run static linting and type analysis across the codebase
lint: (preflight "poetry")
    poetry run ruff check .
    poetry run ruff format --check .
    poetry run mypy credence tests

# Autoformat code with Ruff
format: (preflight "poetry")
    poetry run ruff check --fix .
    poetry run ruff format .

# ==============================================================================
# 3. Engine, Servers & Local Feeds [core: engine & feeds]
# ==============================================================================

# Launch server transport (sse, stdio, web) with optional port and sifter daemon
serve transport="sse" port="8000" sifter="false": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{transport}}" in
        sse)
            if [ "{{sifter}}" = "true" ] || [ "{{sifter}}" = "1" ]; then
                poetry run credence serve --transport sse --port {{port}} --sifter
            else
                poetry run credence serve --transport sse --port {{port}}
            fi
            ;;
        stdio)
            poetry run credence serve --transport stdio
            ;;
        web)
            poetry run python -m http.server {{port}} --directory web
            ;;
        *)
            echo "❌ Unknown transport '{{transport}}'. Valid options: sse, stdio, web."
            exit 1
            ;;
    esac

# Preview all zero-build multi-domain web workstations locally for browser inspection
preview port="8080":
    @echo "🌐 Previewing Credence Multi-Domain Zero-Build Web Surfaces on http://localhost:{{port}}"
    @echo "   👉 Home:       http://localhost:{{port}}/credence.run/"
    @echo "   👉 Reports:    http://localhost:{{port}}/credence.report/"
    @echo "   👉 Nexus:      http://localhost:{{port}}/credence.nexus/"
    @echo "   👉 Admin Deck: http://localhost:{{port}}/credence.nexus/#admin"
    @echo "   👉 Foundation: http://localhost:{{port}}/credence.foundation/"
    @poetry run python3 -m http.server {{port}} --directory web

# Preview zero-build documentation portal locally on http://localhost:8081
preview-docs port="8081":
    @echo "📚 Previewing Credence Documentation Portal on http://localhost:{{port}}"
    @python3 -m http.server {{port}} --directory ../credence-docs

# Launch complete local development stack (Backend on 8000 + Web Workstations on 8080)
dev backend_port="8000" web_port="8080": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    echo "================================================================="
    echo "  🚀 Starting Credence Dual-Plane Local Development Stack"
    echo "================================================================="
    echo "  ⚙️  Backend (FastMCP + REST): http://localhost:{{backend_port}}"
    echo "  🌐 Web Workstations:         http://localhost:{{web_port}}"
    echo "     👉 Home:       http://localhost:{{web_port}}/credence.run/"
    echo "     👉 Reports:    http://localhost:{{web_port}}/credence.report/"
    echo "     👉 Nexus:      http://localhost:{{web_port}}/credence.nexus/"
    echo "     👉 Admin Deck: http://localhost:{{web_port}}/credence.nexus/#admin"
    echo "     👉 Foundation: http://localhost:{{web_port}}/credence.foundation/"
    echo "================================================================="
    echo "Press CTRL+C to terminate both servers."
    
    trap 'kill $(jobs -p) 2>/dev/null || true' EXIT SIGINT SIGTERM
    
    python3 -m http.server {{web_port}} --directory web &
    poetry run credence serve --transport sse --port {{backend_port}}

# Launch interactive Textual TUI workstation
tui: (preflight "poetry")
    poetry run credence tui

# Run the Golden 12 cross-profile evaluation benchmark
benchmark: (preflight "poetry")
    poetry run credence benchmark

# Automated dual-tier environment configuration verifier (dev vs prod)
config-verify dev_url="http://localhost:8000" prod_url="https://credence-server-663899237633.us-central1.run.app": (preflight "poetry")
    poetry run python -m credence.experiments.env_verifier --dev-url="{{dev_url}}" --prod-url="{{prod_url}}"

# Run bicameral experiments and differential benchmarks (shadow-audit, federation-bridge, env-verify)
experiment name="shadow-audit" arg="": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{name}}" in
        shadow-audit)
            echo "=== Running Bicameral Differential Shadow Audit ==="
            poetry run python -m credence.experiments.shadow_audit {{arg}}
            ;;
        federation-bridge)
            echo "=== Running Sovereign White-Label Federation Bridge Simulator ==="
            poetry run python -m credence.experiments.federation_bridge {{arg}}
            ;;
        env-verify|verify)
            echo "=== Verifying Dev vs. Prod Environment Configurations ==="
            poetry run python -m credence.experiments.env_verifier {{arg}}
            ;;
        *)
            echo "❌ Unknown experiment '{{name}}'. Valid options: shadow-audit, federation-bridge, env-verify."
            exit 1
            ;;
    esac


# Display Epistemic Mesh Leaderboard (quality, subjects, philanthropy, galileo, teams)
leaderboard category="quality": (preflight "poetry")
    poetry run credence leaderboard --category {{category}}

# Display local node Epistemic Merit card, badges, and compute odometer
merit: (preflight "poetry")
    poetry run credence merit

# Self-audit documentation and blog articles with cryptographic attestations
audit-docs action="check": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        check)
            echo "=== Auditing Documentation Integrity & Epistemic Self-Score ==="
            poetry run credence audit-docs --check
            ;;
        update)
            echo "=== Updating Documentation Verified Frontmatter & Minting Attestations ==="
            poetry run credence audit-docs --update
            ;;
        *)
            echo "=== Running Documentation Audit ==="
            poetry run credence audit-docs --lens {{action}}
            ;;
    esac

# Display Web Epistemic Analytics and Domain rankings (domains, rules, weather, bounties)
rankings type="domains" category="best": (preflight "poetry")
    poetry run credence rankings {{type}} --category {{category}}


# Display Global Epistemic Weather report
weather: (preflight "poetry")
    poetry run credence rankings weather

# Manage syndicated feed sifter and catalog export (once, bootstrap, export)
sifter action="once": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        once)
            poetry run credence sifter --once
            ;;
        bootstrap)
            poetry run credence feeds bootstrap-presets
            poetry run credence sifter --once
            poetry run credence export-catalog
            ;;
        export)
            poetry run credence export-catalog
            ;;
        *)
            echo "❌ Unknown sifter action '{{action}}'. Valid options: once, bootstrap, export."
            exit 1
            ;;
    esac

# Autonomous node ignition (Genesis identity, Genesis peer inoculation, feed sowing, Miracle-Gro burst)
germinate burst="3" sync_mesh="true": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{sync_mesh}}" = "false" ] || [ "{{sync_mesh}}" = "0" ]; then
        poetry run credence germinate --burst {{burst}} --no-mesh
    else
        poetry run credence germinate --burst {{burst}}
    fi

# Manage local P2P mesh cluster simulation (up, down, logs, status)
mesh action="up" nodes="13": (preflight "poetry") (preflight "docker")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        up)
            poetry run python -c "from credence.mesh.hardware_guard import recommend_cluster_size; recommend_cluster_size({{nodes}})"
            docker compose -f docker-compose.mesh.yml up -d --build
            ;;
        down)
            docker compose -f docker-compose.mesh.yml down -v
            ;;
        logs)
            docker compose -f docker-compose.mesh.yml logs -f
            ;;
        status)
            docker compose -f docker-compose.mesh.yml ps
            ;;
        *)
            echo "❌ Unknown mesh action '{{action}}'. Valid options: up, down, logs, status."
            exit 1
            ;;
    esac

# Manage local Docker container operations (build, test)
docker action="build": (preflight "docker")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        build)
            docker compose build
            ;;
        test)
            docker compose run --rm credence poetry run pytest tests/
            ;;
        *)
            echo "❌ Unknown docker action '{{action}}'. Valid options: build, test."
            exit 1
            ;;
    esac

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

# ==============================================================================
# 5. Compound Operational Workflows [core: ops & release]
# ==============================================================================

# Comprehensive pre-commit / pre-push QA verification gate (<20s)
check:
    @echo "=== [1/5] Preflight Toolchain Verification ==="
    @just preflight all
    @echo ""
    @echo "=== [2/5] Linting & Static Analysis ==="
    @just lint
    @echo ""
    @echo "=== [3/5] Hermetic Unit & Integrity Pytest Gauntlet ==="
    @just test unit
    @echo ""
    @echo "=== [4/5] Terraform Multi-Cloud Validation ==="
    @just tf validate
    @echo ""
    @echo "=== [5/5] Declarative Antigravity Workspace Health ==="
    @just agent-check
    @echo ""
    @echo -e "\033[1;32m🎉 Complete QA Verification Passed Cleanly!\033[0m"

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

# Multi-plane deployment pipeline with automated post-flight verification (backend, edge, compose, dev, prod, all)
deploy target="backend" env="dev" project_id="credence-prod-505902":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{target}}" != "compose" ] && [ -n "$(git status --porcelain)" ]; then
        echo -e "\033[1;31m❌ Working tree is dirty. Per the Commit-Before-Deploy invariant, all changes must be committed before deploying to the cloud.\033[0m"
        git status -s
        exit 1
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
                echo "🚀 Deploying in BASIC / DEV Mode (${SERVICE_NAME}, profile: ${PROFILE}, memory: ${MEM})..."
            else
                echo "🚀 Deploying in ADVANCED / PRODUCTION Mode (${SERVICE_NAME}, profile: ${PROFILE}, memory: ${MEM})..."
            fi
            echo "=== [1/3] Building & Submitting Cloud Run Container via Cloud Build ==="
            gcloud builds submit --project={{project_id}} --tag gcr.io/{{project_id}}/${SERVICE_NAME}:latest
            echo "=== [2/3] Deploying Container to Google Cloud Run ==="
            gcloud run deploy "${SERVICE_NAME}" \
                --image gcr.io/{{project_id}}/${SERVICE_NAME}:latest \
                --region us-central1 \
                --project {{project_id}} \
                --memory "${MEM}" \
                --cpu 1 \
                --execution-environment gen2 \
                --cpu-boost \
                --set-env-vars="ENV={{env}},CREDENCE_PROFILE=${PROFILE}" \
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
            just deploy backend "dev" "{{project_id}}"
            ;;
        prod)
            just deploy backend "prod" "{{project_id}}"
            ;;
        all)
            echo "=== [Phase 1/3] Deploying Dev Environment ==="
            just deploy backend "dev" "{{project_id}}"
            echo "=== [Phase 2/3] Deploying Production Environment ==="
            just deploy backend "prod" "{{project_id}}"
            echo "=== [Phase 3/3] Deploying Cloudflare Anycast Edge Router ==="
            just deploy edge
            ;;
        *)
            echo "❌ Unknown deploy target '{{target}}'. Valid options: backend, edge, compose, dev, prod, all."
            exit 1
            ;;
    esac

# Run comprehensive invariant token budget, dynamic naming, lifecycle, and parity audit
audit-invariants:
    @echo "=== Credence Living Invariant & Governance Audit ==="
    @just agent-check
    @poetry run pytest tests/governance/test_docs_integrity.py -k "learning_lifecycle or ecosystem_version_parity or zero_npm or code_fences"
    @poetry run pytest tests/integration/test_ci_cd_workflows.py
    @echo -e "\033[1;32m✅ All Ecosystem Invariants & Lifecycle Governance Contracts Passed Cleanly!\033[0m"

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

# Synchronize semantic version across all 7 manifests, badges, and documentation
sync-version version: (preflight "poetry")
    @echo "Syncing ecosystem version to {{version}}..."
    @poetry version {{version}}
    @sed -i -E 's/__version__ = "[^"]+"/__version__ = "{{version}}"/' credence/__init__.py
    @sed -i -E "s/export const CURRENT_ECOSYSTEM_VERSION = 'v[^']+';/export const CURRENT_ECOSYSTEM_VERSION = 'v{{version}}';/" ../credence-docs/app.js
    @sed -i -E 's/Credence <span class="badge">v[^<]+<\/span>/Credence <span class="badge">v{{version}}<\/span>/g' ../credence-docs/index.html web/credence.run/index.html web/credence.nexus/index.html web/credence.nexus/dashboard.html web/credence.nexus/mesh.html web/credence.nexus/cost.html web/credence.report/index.html web/credence.report/viewer.html web/credence.foundation/index.html
    @sed -i -E 's/v[0-9]+\.[0-9]+\.[0-9]+ Stable/v{{version}} Stable/' web/credence.run/index.html
    @sed -i -E 's/"version": "[^"]+"/"version": "{{version}}"/' ../credence-agent/plugin.json
    @poetry run pytest tests/governance/test_docs_integrity.py -k test_ecosystem_version_parity
    @echo "✅ All ecosystem version badges and manifests synchronized to {{version}}."

# Coordinate multi-repository git operations (status, branch, commit, tag, push)
git-sync action="status" arg="":
    #!/usr/bin/env bash
    set -euo pipefail
    REPOS="/home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent"
    case "{{action}}" in
        status)
            for r in $REPOS; do
                echo "=== Git Status: $(basename "$r") ==="
                (cd "$r" && git status -s)
            done
            ;;
        branch)
            BRANCH="{{arg}}"
            if [ -z "$BRANCH" ]; then echo "❌ Please provide a branch name. e.g. just git-sync branch feat/v2.3.0-workflow"; exit 1; fi
            for r in $REPOS; do
                echo "=== Checking out branch '$BRANCH' in $(basename "$r") ==="
                (cd "$r" && (git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH"))
            done
            echo "✅ All ecosystem repositories switched to branch '$BRANCH'."
            ;;
        commit)
            MSG="{{arg}}"
            if [ -z "$MSG" ]; then echo "❌ Please provide a commit message. e.g. just git-sync commit 'msg'"; exit 1; fi
            python3 -c '
            import re, sys
            msg = sys.argv[1]
            pat = r"^(\[v[0-9]+\.[0-9]+\.[0-9]+\] )?(feat|fix|docs|refactor|test|ci|chore|perf)(\((governance|forensics|mesh|crypto|ui|ops)\))?!?: .+$"
            if not re.match(pat, msg):
                print(f"❌ Error: Commit message violates ecosystem convention:\n   \"{msg}\"")
                print("   Allowed format: <type>(<scope>): <summary> OR <type>: <summary>")
                print("   Allowed types : feat, fix, docs, refactor, test, ci, chore, perf")
                print("   Allowed scopes: (governance), (forensics), (mesh), (crypto), (ui), (ops)")
                sys.exit(1)
            ' "$MSG"
            for r in $REPOS; do
                echo "=== Committing in $(basename "$r") ==="
                (cd "$r" && (git diff --quiet && git diff --staged --quiet || (git add -A && git commit -m "$MSG")))
            done
            echo "✅ All ecosystem changes committed."
            ;;
        tag)
            VER="{{arg}}"
            if [ -z "$VER" ]; then echo "❌ Please provide a version tag. e.g. just git-sync tag 1.8.0"; exit 1; fi
            for r in $REPOS; do
                echo "=== Tagging in $(basename "$r") (v$VER) ==="
                (cd "$r" && git tag -f -a "v$VER" -m "Release v$VER")
            done
            echo "✅ Tagged v$VER across all ecosystem repositories."
            ;;
        push)
            for r in $REPOS; do
                CURRENT_BRANCH=$(cd "$r" && git rev-parse --abbrev-ref HEAD)
                echo "=== Pushing $(basename "$r") ($CURRENT_BRANCH) to origin ==="
                (cd "$r" && git push origin "$CURRENT_BRANCH" --follow-tags)
            done
            echo "✅ All ecosystem branches and tags pushed to GitHub."
            ;;
        *)
            echo "❌ Unknown git-sync action '{{action}}'. Valid options: status, branch, commit, tag, push."
            exit 1
            ;;
    esac

# Create or switch feature branch across all ecosystem repositories
branch name:
    @just git-sync branch {{name}}

# Perform incremental verified atomic commit across ecosystem repositories
commit message:
    @just git-sync commit "{{message}}"

# Manage GitHub Pull Requests across the ecosystem via GitHub CLI (gh)
pr action="status" arg="":
    #!/usr/bin/env bash
    set -euo pipefail
    REPOS="/home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent"
    case "{{action}}" in
        create)
            TITLE="{{arg}}"
            if [ -z "$TITLE" ]; then echo "❌ Please provide a PR title. e.g. just pr create 'feat: v2.3.0 workflow'"; exit 1; fi
            for r in $REPOS; do
                BRANCH=$(cd "$r" && git rev-parse --abbrev-ref HEAD)
                if [ "$BRANCH" != "main" ]; then
                    echo "=== Creating PR for $(basename "$r") ($BRANCH -> main) ==="
                    (cd "$r" && gh pr create --title "$TITLE" --body "Automated ecosystem PR for branch $BRANCH." --base main --head "$BRANCH" || true)
                fi
            done
            ;;
        status)
            for r in $REPOS; do
                echo "=== PR Status: $(basename "$r") ==="
                (cd "$r" && gh pr list || true)
            done
            ;;
        view)
            PR_NUM="{{arg}}"
            gh pr view ${PR_NUM:+"$PR_NUM"}
            ;;
        checks)
            PR_NUM="{{arg}}"
            gh pr checks ${PR_NUM:+"$PR_NUM"}
            ;;
        merge)
            PR_NUM="{{arg}}"
            for r in $REPOS; do
                BRANCH=$(cd "$r" && git rev-parse --abbrev-ref HEAD)
                if [ "$BRANCH" != "main" ]; then
                    echo "=== Merging PR for $(basename "$r") ==="
                    (cd "$r" && gh pr merge ${PR_NUM:+"$PR_NUM"} --merge --auto || true)
                fi
            done
            ;;
        *)
            echo "❌ Unknown pr action '{{action}}'. Valid options: create, status, view, checks, merge."
            exit 1
            ;;
    esac

# Execute full atomic ecosystem release pipeline
release version message:
    @git diff --quiet || (echo "❌ Error: Working tree has unstaged changes. Please commit or stash before releasing." && exit 1)
    @git diff --cached --quiet || (echo "❌ Error: Staging area has uncommitted changes. Please commit before releasing." && exit 1)
    @just check
    @just sync-version {{version}}
    @just git-sync commit "feat(ecosystem): release v{{version}} - {{message}}"
    @just git-sync tag {{version}}
    @just git-sync push
    @echo -e "\033[1;32m🚀 Full Ecosystem Release v{{version}} Pushed to GitHub! Continuous deployment is being orchestrated by GitHub Actions.\033[0m"

# Verify Antigravity declarative workspace configuration, skills schema, and prompt economy
agent-check:
    @echo "=== Credence Antigravity Declarative Health Check ==="
    @test -f ../AGENTS.md && echo "✅ Universal root AGENTS.md verified." || (echo "❌ Missing root AGENTS.md"; exit 1)
    @test -f ../.agents/skills.json && echo "✅ Declarative .agents/skills.json verified." || (echo "❌ Missing .agents/skills.json"; exit 1)
    @test -d ../credence-agent/.agents/skills && echo "✅ Native skills repository verified." || (echo "❌ Missing credence-agent skills"; exit 1)
    @python3 ../credence-agent/scripts/lint_skills.py
    @python3 ../credence-agent/scripts/audit_demotions.py
    @echo -e "\033[1;32m✅ Declarative Antigravity Workspace & Invariant Engine Verified Cleanly!\033[0m"

# Audit skills schema, frontmatter, and token economy
audit-skills:
    @python3 ../credence-agent/scripts/lint_skills.py

# Audit invariant demotion candidates and token savings
audit-demotions:
    @python3 ../credence-agent/scripts/audit_demotions.py



