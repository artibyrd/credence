---
title: 'Operational Guide: Disaster Recovery and Failover Procedures'
description: Comprehensive disaster recovery runbook covering database backups, R2 bucket replication, and multi-region failover.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Operational Guide: Disaster Recovery and Failover Procedures

Runbook for recovering from major cloud provider outages, corrupted databases, and edge DNS failures.

---

## 1. Database Backups & Point-in-Time Recovery

### SQLite WAL Backups
```bash
# Atomic online backup of SQLite database
sqlite3 data/credence.db ".backup 'data/backup_$(date +%Y%m%d_%H%M%S).db'"
```

### PostgreSQL Backups
```bash
pg_dump -Fc -v -d "$DATABASE_URL" -f "credence_backup_$(date +%Y%m%d).dump"
```

---

## 2. Edge DNS Failover

If the primary Cloud Run region experiences a total outage, re-route Cloudflare Worker upstream traffic to the secondary failover region:

```bash
# Update secondary region backend URL in Cloudflare Worker
wrangler secret put PROD_BACKEND_URL --env production
```
