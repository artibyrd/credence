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
        ver=$($version_cmd 2>&1 | head -n 1)
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
            ver=$(wrangler --version 2>&1 | head -n 1)
            echo -e "\033[0;32m✅ Cloudflare Wrangler:\033[0m $ver"
            return 0
        elif command -v npx &>/dev/null; then
            local ver
            ver=$(npx --no-install wrangler --version 2>&1 | head -n 1 || echo "available via npx")
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
        auth_user=$(gh auth status 2>&1 | grep -o "account [^ ]*" | head -n 1 | awk '{print $2}' || echo "authenticated")
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
            poetry run pytest tests/ -m "not integration and not e2e" --durations=10 {{extra}}
            ;;
        all)
            poetry run pytest tests/ --durations=10 {{extra}}
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
            poetry run pytest tests/test_docs_integrity.py -v {{extra}}
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
            poetry run python -m http.server {{port}} --directory web/credence.run
            ;;
        *)
            echo "❌ Unknown transport '{{transport}}'. Valid options: sse, stdio, web."
            exit 1
            ;;
    esac

# Launch interactive Textual TUI workstation
tui: (preflight "poetry")
    poetry run credence tui

# Run the Golden 12 cross-profile evaluation benchmark
benchmark: (preflight "poetry")
    poetry run credence benchmark

# Display Epistemic Mesh Leaderboard (quality, subjects, philanthropy, galileo, teams)
leaderboard category="quality": (preflight "poetry")
    poetry run credence leaderboard --category {{category}}

# Display local node Epistemic Merit card, badges, and compute odometer
merit: (preflight "poetry")
    poetry run credence merit

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
            echo "=== Probing Live Cloud Run Endpoints ==="
            poetry run python -c "import textwrap; exec(textwrap.dedent('''
                import httpx, time
                BASE = 'https://credence-server-663899237633.us-central1.run.app'
                endpoints = [
                    ('/health', 'GET'),
                    ('/api/health', 'GET'),
                    ('/sse', 'STREAM'),
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
tf action="validate" extra="": (preflight "terraform")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        validate)
            terraform -chdir=terraform init -backend=false
            terraform -chdir=terraform fmt -check
            terraform -chdir=terraform validate
            ;;
        plan)
            terraform -chdir=terraform plan {{extra}}
            ;;
        apply)
            terraform -chdir=terraform apply {{extra}}
            ;;
        output)
            terraform -chdir=terraform output {{extra}}
            ;;
        *)
            echo "❌ Unknown tf action '{{action}}'. Valid options: validate, plan, apply, output."
            exit 1
            ;;
    esac

# ==============================================================================
# 5. Compound Operational Workflows [core: ops & release]
# ==============================================================================

# Comprehensive pre-commit / pre-push QA verification gate (<75s)
check:
    @echo "=== [1/6] Preflight Toolchain Verification ==="
    @just preflight all
    @echo ""
    @echo "=== [2/6] Linting & Static Analysis ==="
    @just lint
    @echo ""
    @echo "=== [3/6] Hermetic Unit Pytest Gauntlet ==="
    @just test unit
    @echo ""
    @echo "=== [4/6] Docs & Frontmatter Integrity Verification ==="
    @just test docs
    @echo ""
    @echo "=== [5/6] Terraform Multi-Cloud Validation ==="
    @just tf validate
    @echo ""
    @echo "=== [6/6] Declarative Antigravity Workspace Health ==="
    @just agent-check
    @echo ""
    @echo -e "\033[1;32m🎉 Complete QA Verification Passed Cleanly!\033[0m"

# One-command developer onboarding: setup dependencies, preflight, germinate node, and verify
ignite burst="3":
    @just setup
    @just preflight all
    @just germinate {{burst}}
    @just test mock
    @just doctor
    @echo -e "\033[1;32m🌱 Credence Node Ignited & Ready for Operations!\033[0m"

# Multi-plane deployment pipeline with automated post-flight verification (backend, edge, all)
deploy target="backend" project_id="credence-prod-505902":
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{target}}" in
        backend)
            just preflight gcloud
            echo "=== [1/3] Building & Submitting Cloud Run Container via Cloud Build ==="
            gcloud builds submit --project={{project_id}} --tag gcr.io/{{project_id}}/credence-server:latest
            echo "=== [2/3] Deploying Container to Google Cloud Run ==="
            gcloud run deploy credence-server \
                --image gcr.io/{{project_id}}/credence-server:latest \
                --region us-central1 \
                --project {{project_id}} \
                --memory 1Gi \
                --cpu 1 \
                --allow-unauthenticated
            echo "=== [3/3] Executing Post-Deployment Live Health Probe ==="
            just gcp probe
            ;;
        edge)
            just preflight wrangler
            echo "=== Deploying Cloudflare Edge Router ==="
            just edge deploy
            ;;
        all)
            just deploy edge
            just deploy backend "{{project_id}}"
            ;;
        *)
            echo "❌ Unknown deploy target '{{target}}'. Valid options: backend, edge, all."
            exit 1
            ;;
    esac

# Comprehensive multi-plane diagnostic health check across Edge, Compute, Infra, and Agents
doctor:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "================================================================="
    echo "         🩺 Credence Multi-Plane Health Diagnostic              "
    echo "================================================================="
    echo ""
    echo "--- 1. Declarative Agent & Workspace Plane ---"
    just agent-check || true
    echo ""
    echo "--- 2. Compute Plane (Google Cloud Run) ---"
    just gcp status || true
    echo ""
    just gcp probe || true
    echo ""
    echo "--- 3. Edge Plane (Cloudflare Workers & Pages) ---"
    just edge status || true
    echo ""
    echo "--- 4. Infrastructure Plane (Terraform) ---"
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
    @sed -i -E 's/Credence <span class="badge">v[^<]+<\/span>/Credence <span class="badge">v{{version}}<\/span>/' ../credence-docs/index.html web/credence.run/index.html
    @sed -i -E 's/v[0-9]+\.[0-9]+\.[0-9]+ Stable/v{{version}} Stable/' web/credence.run/index.html
    @sed -i -E "s/brandBadge\.textContent = isBlog \? 'Editorial' : 'v[^']+'/brandBadge.textContent = isBlog ? 'Editorial' : 'v{{version}}'/" ../credence-docs/app.js
    @sed -i -E 's/"version": "[^"]+"/"version": "{{version}}"/' ../credence-agent/plugin.json
    @poetry run pytest tests/test_docs_integrity.py -k test_ecosystem_version_parity
    @echo "✅ All ecosystem version badges and manifests synchronized to {{version}}."

# Coordinate multi-repository git operations (status, commit, tag, push)
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
        commit)
            MSG="{{arg}}"
            if [ -z "$MSG" ]; then echo "❌ Please provide a commit message. e.g. just git-sync commit 'msg'"; exit 1; fi
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
                echo "=== Pushing $(basename "$r") to origin ==="
                (cd "$r" && git push origin main --follow-tags)
            done
            echo "✅ All ecosystem branches and tags pushed to GitHub."
            ;;
        *)
            echo "❌ Unknown git-sync action '{{action}}'. Valid options: status, commit, tag, push."
            exit 1
            ;;
    esac

# Execute full atomic ecosystem release pipeline
release version message:
    @just check
    @just sync-version {{version}}
    @just git-sync commit "feat(ecosystem): release v{{version}} - {{message}}"
    @just git-sync tag {{version}}
    @just git-sync push
    @just deploy all
    @echo -e "\033[1;32m🚀 Full Ecosystem Release v{{version}} Completed Successfully!\033[0m"

# Verify Antigravity declarative workspace configuration and skills registration
agent-check:
    @echo "=== Credence Antigravity Declarative Health Check ==="
    @test -f ../AGENTS.md && echo "✅ Universal root AGENTS.md verified." || (echo "❌ Missing root AGENTS.md"; exit 1)
    @test -f ../.agents/skills.json && echo "✅ Declarative .agents/skills.json verified." || (echo "❌ Missing .agents/skills.json"; exit 1)
    @test -d ../credence-agent/.agents/skills && echo "✅ Native skills repository verified." || (echo "❌ Missing credence-agent skills"; exit 1)
    @echo "=== All Declarative Antigravity Configs Verified ==="


