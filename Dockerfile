# syntax=docker/dockerfile:1
# Multi-stage Dockerfile for Credence with Python 3.12 & Playwright Chromium
FROM python:3.12-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH="/app/.venv/bin:/opt/poetry/bin:$PATH"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy dependency specifications
COPY pyproject.toml poetry.lock* ./

# Install production python dependencies (excluding dev tools and root package)
RUN poetry install --without dev --no-root

# Install Playwright browser and OS dependencies
RUN playwright install --with-deps chromium

# Copy application source code
COPY . .

# Install root project without development dependencies
RUN poetry install --without dev

# Precompile bytecode to eliminate Python AST compilation overhead during cold boot
RUN python -m compileall -q /app/.venv /app/credence

EXPOSE 8000

# Container Healthcheck (fast non-blocking /health probe)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Direct virtualenv execution bypassing poetry CLI process wrapper
CMD ["credence", "serve", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
