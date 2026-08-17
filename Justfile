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

# Run fastmcp dev server
dev:
    poetry run python -m credence.server.app
