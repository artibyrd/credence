---
title: Multi-Plane Pipeline & Build Optimization Handbook
description: Operational engineering reference for developer workstation tuning, multi-core
  pytest parallelization, lean container builds, and sub-40s QA gates.
since_version: v1.14.1
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Multi-Plane Pipeline & Build Optimization Handbook

This guide details the architectural optimizations, local tooling configurations, and cloud deployment pipelines that enable Credence to achieve **sub-40-second complete QA verification** and **sub-2MB container build contexts**.

---

## 1. The 5-Plane Verification Architecture (`just check`)

Every pull request and pre-commit check runs through a unified, 5-stage verification gate defined in `Justfile`:

```mermaid
flowchart LR
    A["1. Preflight<br/>(Toolchains: ~0.8s)"] --> B["2. Lint & Typing<br/>(Ruff & Mypy: ~4.2s)"]
    B --> C["3. Hermetic Pytest<br/>(pytest-xdist: ~28.4s)"]
    C --> D["4. Terraform Validation<br/>(Multi-Cloud: ~0.4s)"]
    D --> E["5. Declarative Health<br/>(AGENTS.md: ~0.1s)"]
```

To execute the entire gate locally:
```bash
just check
```

---

## 2. Test Suite Optimization & Parallelization

### Multi-Core Parallelization (`pytest-xdist`)
The default unit test suite (`tests/`) is configured to run across all available CPU cores using `pytest-xdist`:

```bash
# Run hermetic unit tests across all CPU cores
poetry run pytest tests/ -m "not integration and not e2e" -n auto --durations=10
```

### Hermetic Socket Mocking Invariant
All unit tests in `tests/` must remain **100% network-free** and execute against in-memory SQLite fixtures (`sqlite+aiosqlite:///:memory:`):
- Never issue live HTTP requests inside `tests/` unless executing the live rotating suite (`tests/test_live_rotating_suite.py`).
- Always mock network entrypoints (e.g. `fetch_and_parse_feed`, `httpx.AsyncClient`) with `AsyncMock` to avoid hitting unmocked network socket timeouts (10+ seconds per invocation).

### Concurrent Async Sockets in Swarm Simulations
When testing multi-node WebSocket networks (`MeshGossipRelay`), avoid serial loops during startup and teardown:

```python
# Startup
await asyncio.gather(*(r.start() for r in relays))

# Teardown
await asyncio.gather(*(r.stop() for r in relays))
```

---

## 3. Build Context & Cloud Build Payload Exclusion

### The < 5 MB Payload Invariant
All containerized repositories must maintain synchronized `.dockerignore` and `.gcloudignore` manifests. This ensures that bulky local files (virtual environments, Terraform states, SQLite databases, and caches) are excluded from container contexts:

```ignore
# .dockerignore & .gcloudignore
.venv
.venv/**
terraform
terraform/**
data
data/**
.pytest_cache
.mypy_cache
.ruff_cache
.coverage
htmlcov
tests
tests/**
web
web/**
docs
docs/**
```

### Measuring Build Context Size
To verify that build context remains lean:
```bash
tar --exclude-from=.gcloudignore -czf - . | wc -c
# Output should be < 3,000,000 bytes (~2-3 MB)
```

---

## 4. Lean Container Builds & BuildKit Caching

### Production Dependency Pruning (`--without dev`)
Production `Dockerfile` builds exclude development tools (`pytest`, `mypy`, `ruff`, `pytest-cov`, `pytest-xdist`) to minimize attack surface and image size:

```dockerfile
# Install production python dependencies only
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --without dev --no-root

# Install root project without dev tools
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --without dev
```

### BuildKit Cache Mounts
The `--mount=type=cache,target=/root/.cache/pypoetry` flag preserves downloaded Python wheels across incremental Docker builds, avoiding redundant network downloads.

---

## 5. Cloud Build & CI/CD Concurrency

In `cloudbuild.yaml`, independent verification steps run in parallel using `waitFor: ['-']`:

```yaml
steps:
  # Quality Gate (Ruff & Mypy)
  - name: 'python:3.12-slim'
    id: 'quality-gate'
    waitFor: ['-']
    args: ['-c', 'pip install --no-cache-dir poetry && poetry install --no-root && poetry run ruff check . && poetry run mypy credence tests']

  # Hermetic Test Gate (Pytest with -n auto)
  - name: 'python:3.12-slim'
    id: 'test-gate'
    waitFor: ['-']
    args: ['-c', 'pip install --no-cache-dir poetry && poetry install --no-root && poetry run pytest tests/ -m "not integration and not e2e" -n auto']

  # Docker Build (waits for quality and test gates)
  - name: 'gcr.io/cloud-builders/docker'
    id: 'docker-build'
    waitFor: ['quality-gate', 'test-gate']
    env: ['DOCKER_BUILDKIT=1']
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/credence-server:latest', '.']
```

---

## 6. Shell Pipefail Stream Safety

When writing shell automation in `Justfile` or scripts with `set -euo pipefail`:
- Avoid `head -n 1` on command pipelines that output multiple lines. If the upstream command produces more output after `head` closes standard input, `SIGPIPE` (exit code 141) is triggered.
- Use `sed -n '1p'` or pipe-draining constructs to safely extract the first line with exit code 0:

```bash
# Safe version check under pipefail
ver=$($version_cmd 2>&1 | sed -n '1p' || echo "installed")
```
