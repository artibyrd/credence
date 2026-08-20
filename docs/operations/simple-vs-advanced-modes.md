---
title: 'Operational Guide: Simple vs Advanced Operating Modes'
description: Comprehensive operational guide comparing Simple Sovereign Mode (SQLite/Local) and Advanced Planetary Cloud Mode (PostgreSQL/Cloud Run/R2).
since_version: v1.17.0
verified_version: v1.17.0
last_verified: '2026-08-19'
---

# Operational Guide: Simple vs Advanced Operating Modes

Credence operates in two distinct operational topologies sharing the exact same codebase and business logic.

---

## 1. Topologies at a Glance

### Topology A: Simple Mode (Sovereign Local)
- **Database**: Embedded SQLite WAL (`data/credence.db`).
- **State**: In-memory Python structures.
- **Blobs**: Local directory (`data/snapshots/`).
- **Monthly Cost**: **$0.00 / month**.
- **Ideal For**: Developers, single-workstation newsrooms, Raspberry Pi homelabs.

### Topology B: Advanced Mode (Planetary Cloud)
- **Compute**: Google Cloud Run v2 (0 to 500 container replicas).
- **Database**: Managed Serverless PostgreSQL (Neon / Cloud SQL).
- **State**: Serverless Redis / Valkey (Upstash / Memorystore).
- **Blobs**: Cloudflare R2 (`credence-snapshots`) with $0 egress fees.
- **Edge**: Cloudflare Anycast CDN & Worker Edge Router ($<20\text{ms}$ global read latency).
- **Monthly Cost**: **~$5 – $40 / month**.
- **Ideal For**: High-throughput public nodes, browser extension backends, multi-tenant organizations.

---

## 2. Quickstart Runbooks

### Simple Mode (60 Seconds)
```bash
just setup
just ignite
just tui
```

### Advanced Mode (Cloud Deployment)
```bash
# Set production secrets
export DATABASE_URL="postgresql+asyncpg://user:pass@ep-cool.neon.tech/credencedb?ssl=require"
export REDIS_URL="rediss://default:pass@us1-upstash.io:6379"
export STORAGE_BACKEND="s3"
export S3_BUCKET_NAME="credence-snapshots"

# Deploy Compute and Edge
just deploy backend
just deploy edge
```
