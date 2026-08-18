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

# Run live end-to-end integration tests against online production domains
test-e2e:
    poetry run pytest tests/e2e/test_live_domains.py -v -m e2e

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

# Build and submit Cloud Run container image via Google Cloud Build
gcp-build project_id="credence-prod-505902":
    gcloud builds submit --project={{project_id}} --tag gcr.io/{{project_id}}/credence-server:latest

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

