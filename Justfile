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
    poetry run pytest tests/ -m "not integration" --durations=10

# Run all tests including integration
test-all:
    poetry run pytest tests/ --durations=10

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

