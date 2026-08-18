# Justfile for Credence Project Tasks

set shell := ["bash", "-c"]

default:
    @just --list

# Install all dependencies and playwright browsers
setup:
    poetry install
    poetry run playwright install chromium

# Run all unit tests
test:
    poetry run pytest tests/ -m "not integration and not e2e" --durations=10

# Run all tests including integration
test-all:
    poetry run pytest tests/ --durations=10

# Run reusable rotating live end-to-end test gauntlet
test-live:
    CREDENCE_LIVE_TESTS=1 poetry run pytest tests/e2e/test_live_rotating_suite.py -v -m e2e -s

# Run all live end-to-end integration tests (rotating suite, domains, mcp, mesh)
test-e2e:
    CREDENCE_LIVE_TESTS=1 poetry run pytest tests/e2e/ -v -m e2e

# Run hermetic offline mock end-to-end integration test
test-e2e-mock:
    poetry run pytest tests/e2e/test_mock_e2e.py -v

# Run code linters and type checkers
lint:
    poetry run ruff check .
    poetry run ruff format --check .
    poetry run mypy credence tests

# Autoformat code
format:
    poetry run ruff check --fix .
    poetry run ruff format .

# Build local Docker image
docker-build:
    docker compose build

# Run tests inside Docker
docker-test:
    docker compose run --rm credence poetry run pytest tests/

# Run interactive Textual TUI dashboard
tui:
    poetry run credence tui

# Run FastMCP server
serve-stdio:
    poetry run credence serve --transport stdio

serve-sse:
    poetry run credence serve --transport sse --port 8000

# Run server with background feed sifter enabled
serve-sifter:
    poetry run credence serve --transport sse --port 8000 --sifter

# Run single sifter cycle
sifter-once:
    poetry run credence sifter --once

# Export stored SQLite audits to static web reports.json catalog
export-catalog:
    poetry run credence export-catalog

# Seed initial reports into local SQLite and export static reports.json
seed-reports:
    poetry run credence feeds bootstrap-presets
    poetry run credence sifter --once
    poetry run credence export-catalog

# Run the Golden 12 epistemic cross-profile benchmark
benchmark:
    poetry run credence benchmark

# Credence Mesh 13-Node Heterogeneous Cluster Management
mesh-cluster-up:
    poetry run python -c "from credence.mesh.hardware_guard import recommend_cluster_size; recommend_cluster_size(13)"
    docker compose -f docker-compose.mesh.yml up -d --build

mesh-cluster-down:
    docker compose -f docker-compose.mesh.yml down -v

mesh-cluster-logs:
    docker compose -f docker-compose.mesh.yml logs -f

# Run fastmcp dev server
dev:
    poetry run credence serve --transport sse --port 8000

# Launch local preview server for Mk1 Eyeball visual review of web artifacts
serve-web:
    poetry run python -m http.server 8080 --directory web/credence.run

# Validate Terraform configuration for GCP and Cloudflare
tf-validate:
    terraform -chdir=terraform init -backend=false
    terraform -chdir=terraform validate
    terraform -chdir=terraform fmt -check

# Execute Terraform plan across GCP and Cloudflare
tf-plan:
    terraform -chdir=terraform plan

# Apply Terraform infrastructure across GCP and Cloudflare
tf-apply:
    terraform -chdir=terraform apply

# Germinate fresh node identity, preset feeds, mesh peer attestations, and initial sifting burst
germinate burst="3":
    poetry run credence germinate --burst {{burst}}

# Build and submit Cloud Run container image via Google Cloud Build
gcp-build project_id="credence-prod-505902":
    gcloud builds submit --project={{project_id}} --tag gcr.io/{{project_id}}/credence-server:latest

# Authenticate local Wrangler with Cloudflare
edge-login:
    cd web && npx wrangler login

# Check Cloudflare Edge router & Pages deployment status
edge-status:
    @echo "=== Cloudflare Edge Plane Status ==="
    @cd web && npx wrangler whoami || true
    @echo ""
    @echo "=== Edge Router Deployments (credence.run) ==="
    @cd web && npx wrangler deployments list || true
    @echo ""
    @echo "=== Docs Pages Deployments (docs.credence.run) ==="
    @cd ../credence-docs && npx wrangler pages deployment list --project-name=credence-docs || true

# Stream live real-time request logs from Cloudflare Edge router
edge-logs:
    cd web && npx wrangler tail

# Deploy Cloudflare Edge router and web assets
deploy-edge:
    cd web && npx wrangler deploy

# Build and deploy backend Cloud Run container
deploy-backend project_id="credence-prod-505902":
    gcloud builds submit --project={{project_id}} --tag gcr.io/{{project_id}}/credence-server:latest
    gcloud run deploy credence-server --image gcr.io/{{project_id}}/credence-server:latest --region us-central1 --project {{project_id}}

# Atomic full-stack deployment across Edge and Cloud Run
deploy-all: deploy-edge deploy-backend

# Sync signed genesis seeds and taxonomy catalogs to GCS origin buckets
seed-sync project_id="credence-prod-505902":
    gcloud storage rsync -r web/credence.nexus/ gs://{{project_id}}-seeds-nexus/
    gcloud storage rsync -r web/credence.foundation/ gs://{{project_id}}-taxonomies-foundation/

# Verify Antigravity declarative workspace configuration and skills registration
agent-check:
    @echo "=== Credence Antigravity Declarative Health Check ==="
    @test -f ../AGENTS.md && echo "✅ Universal root AGENTS.md verified." || (echo "❌ Missing root AGENTS.md"; exit 1)
    @test -f ../.agents/skills.json && echo "✅ Declarative .agents/skills.json verified." || (echo "❌ Missing .agents/skills.json"; exit 1)
    @test -d ../credence-agent/.agents/skills && echo "✅ Native skills repository verified." || (echo "❌ Missing credence-agent skills"; exit 1)
    @echo "=== All Declarative Antigravity Configs Verified ==="

# Bump and synchronize semantic version across all ecosystem repositories and web surfaces
bump-version version:
    @echo "Syncing ecosystem version to {{version}}..."
    @poetry version {{version}}
    @sed -i -E 's/__version__ = "[^"]+"/__version__ = "{{version}}"/' credence/__init__.py
    @sed -i -E 's/Credence <span class="badge">v[^<]+<\/span>/Credence <span class="badge">v{{version}}<\/span>/' ../credence-docs/index.html web/credence.run/index.html
    @sed -i -E 's/v[0-9]+\.[0-9]+\.[0-9]+ Stable/v{{version}} Stable/' web/credence.run/index.html
    @sed -i -E "s/brandBadge\.textContent = isBlog \? 'Editorial' : 'v[^']+'/brandBadge.textContent = isBlog ? 'Editorial' : 'v{{version}}'/" ../credence-docs/app.js
    @sed -i -E 's/"version": "[^"]+"/"version": "{{version}}"/' ../credence-agent/plugin.json
    @poetry run pytest tests/test_docs_integrity.py -k test_ecosystem_version_parity
    @echo "✅ All ecosystem version badges and manifests synchronized to {{version}}."

# Stage and commit changes across all modified ecosystem repositories
commit-all message:
    @echo "=== Committing across credence ecosystem ==="
    @cd /home/pendragon/Projects/credence-ecosystem/credence && (git diff --quiet && git diff --staged --quiet || (git add -A && git commit -m "{{message}}"))
    @cd /home/pendragon/Projects/credence-ecosystem/credence-docs && (git diff --quiet && git diff --staged --quiet || (git add -A && git commit -m "{{message}}"))
    @cd /home/pendragon/Projects/credence-ecosystem/credence-agent && (git diff --quiet && git diff --staged --quiet || (git add -A && git commit -m "{{message}}"))
    @echo "✅ All ecosystem changes committed."

# Tag release across all ecosystem repositories
tag-all version message:
    @echo "=== Tagging v{{version}} across credence ecosystem ==="
    @cd /home/pendragon/Projects/credence-ecosystem/credence && git tag -f -a v{{version}} -m "{{message}}"
    @cd /home/pendragon/Projects/credence-ecosystem/credence-docs && git tag -f -a v{{version}} -m "{{message}}"
    @cd /home/pendragon/Projects/credence-ecosystem/credence-agent && git tag -f -a v{{version}} -m "{{message}}"
    @echo "✅ Tagged v{{version}} across all ecosystem repositories."

# Push changes and tags across all ecosystem repositories to GitHub
push-all:
    @echo "=== Pushing changes across credence ecosystem ==="
    @cd /home/pendragon/Projects/credence-ecosystem/credence && git push origin main --follow-tags
    @cd /home/pendragon/Projects/credence-ecosystem/credence-docs && git push origin main --follow-tags
    @cd /home/pendragon/Projects/credence-ecosystem/credence-agent && git push origin main --follow-tags
    @echo "✅ All ecosystem branches and tags pushed to GitHub."

# Complete atomic ecosystem release
release version message:
    @just bump-version {{version}}
    @just commit-all "feat(ecosystem): release v{{version}} - {{message}}"
    @just tag-all {{version}} "Release v{{version}}: {{message}}"
    @just push-all
    @echo "🚀 Full ecosystem release v{{version}} completed successfully."

# Monitor and verify live GitHub Actions workflow runs across the ecosystem
pipeline-status:
    @echo "=== Credence CI/CD Pipeline Runs ==="
    @gh run list -R artibyrd/credence --limit 5
    @echo ""
    @echo "=== Credence Docs Deployment Runs ==="
    @gh run list -R artibyrd/credence-docs --limit 5

# Watch recent workflow run on credence until completion
pipeline-watch:
    @gh run watch -R artibyrd/credence
