---
title: 'Operational Guide: PostgreSQL Cloud Scaling & Connection Pooling'
description: Operational guide for configuring managed PostgreSQL with SQLModel and asyncpg connection pooling under high-concurrency Cloud Run deployments.
since_version: v1.17.0
verified_version: v1.17.0
last_verified: '2026-08-19'
---

# Operational Guide: PostgreSQL Cloud Scaling & Connection Pooling

When scaling Credence beyond a single machine, migrating from embedded SQLite to **Managed PostgreSQL** via `asyncpg` enables horizontal container replica concurrency.

---

## 1. Connection Pool Architecture

Credence configures `AsyncAdaptedQueuePool` for PostgreSQL:

```python
_engine = create_async_engine(
    DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=1800,
)
```

- **`pool_size=20`**: Baseline open persistent database connections per container replica.
- **`max_overflow=30`**: Burst headroom under sudden traffic spikes (up to 50 active connections).
- **`pool_pre_ping=True`**: Eliminates stale connection errors across serverless container freeze/thaw cycles.
- **`pool_recycle=1800`**: Recycles connections every 30 minutes to prevent backend connection leaks.

---

## 2. Recommended Cloud Providers
1. **Neon Serverless PostgreSQL**: Auto-suspends compute when idle ($0.00 compute at rest).
2. **Google Cloud SQL**: High-availability dedicated PostgreSQL in `us-central1` with Private Service Access VPC connector.
