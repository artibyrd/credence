# Multi-stage Dockerfile for Credence with Python 3.12 & Playwright Chromium
FROM python:3.12-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

ENV PATH="$POETRY_HOME/bin:$PATH"

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

# Install python dependencies (excluding root package)
RUN poetry install --no-root

# Install Playwright browser and OS dependencies
RUN poetry run playwright install --with-deps chromium

# Copy application source code
COPY . .

# Install root project
RUN poetry install

EXPOSE 8000
CMD ["poetry", "run", "python", "-m", "credence.server.app"]
