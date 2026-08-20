---
title: 'Operational Guide: Docker Compose 5-Minute Quickstart'
description: Quickstart guide for launching a sovereign Credence node or full-stack
  cluster locally using Docker Compose in under 5 minutes.
since_version: v1.18.0
verified_version: v1.18.2
last_verified: '2026-08-19'
---

# Operational Guide: Docker Compose 5-Minute Quickstart

Get Credence running locally on any machine (Linux, macOS, Windows) in 5 minutes with zero cloud setup.

---

## 1. Prerequisites Checklist

- **Docker Engine**: Version 24.0 or higher.
- **Docker Compose**: Version 2.20 or higher (`docker compose version`).
- **Gemini API Key**: From [Google AI Studio](https://aistudio.google.com/).

---

## 2. Launch Option A: Basic Sovereign Node ($0 Idle / SQLite)

The Basic configuration runs Credence with an embedded SQLite WAL database and local CAS snapshot filesystem:

```bash
# 1. Clone repository
git clone https://github.com/artibyrd/credence.git && cd credence

# 2. Set your Gemini API Key
export GEMINI_API_KEY="your_api_key_here"

# 3. Launch container
docker compose up -d

# 4. Verify health probe
curl -sSL http://localhost:8000/health | jq .
```

### Endpoints Available Immediately:
- **FastMCP SSE Transport**: `http://localhost:8000/sse`
- **Cost & Health Dashboard**: `http://localhost:8000/cost.html`
- **Audit Reports Viewer**: `http://localhost:8000/api/reports`
- **P2P Gossip Relay**: `ws://localhost:8765`

---

## 3. Launch Option B: Planetary Sovereign Cluster (PostgreSQL + MinIO + Valkey)

The Planetary stack provisions a multi-container sovereign cluster with enterprise database persistence, S3 CAS storage, and distributed cache:

```bash
# Launch Credence + PostgreSQL 16 + MinIO S3 + Valkey Distributed Cache
docker compose -f docker-compose.prod.yml up -d
```

### Architecture Topology:
- **`credence-server`** (Port 8000): FastMCP & REST API Engine.
- **`postgres`** (Port 5432): Async PostgreSQL 16 persistence.
- **`minio`** (Port 9000 API, Port 9001 Web Console): S3-compatible content-addressable storage.
- **`valkey`** (Port 6379): High-throughput in-memory distributed cache.

---

## 4. Operational Runbook: Logs & Teardown

```bash
# View real-time streaming logs
docker compose logs -f credence

# Stop all services (preserving data volumes)
docker compose down

# Stop services and purge data volumes (clean reset)
docker compose down -v
```
