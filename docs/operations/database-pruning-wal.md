---
title: Database Pruning & SQLite WAL Maintenance
description: SQLite write-ahead logging tuning, checkpointing strategies, and automated
  30-day retention pruning.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Database Pruning & SQLite WAL Maintenance

Credence nodes use embedded **SQLite** with Write-Ahead Logging (WAL) via SQLModel and `aiosqlite`.

When running 24/7 nodes that ingest hundreds of daily news feeds, database files and rendered DOM snapshots must be maintained to ensure fast query response times and prevent disk bloat.

---

## 1. SQLite WAL Pragmas & Configuration

Credence automatically sets these high-concurrency pragmas on engine startup:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA cache_size = -64000; -- 64MB memory page cache
PRAGMA busy_timeout = 5000;  -- 5-second lock timeout
```

---

## 2. Automated Retention Pruning (`credence db clean`)

To prune historical audit records, DOM caches, and raw screenshots older than a retention window:

```bash
# Prune records older than 30 days
credence db clean --retention-days 30

# Dry-run inspection
credence db clean --retention-days 30 --dry-run
```

### Output:
```text
🧹 Credence Database Cleaner
Retention Policy: 30 Days (Older than 2026-07-18)
Records Removed: 1,420 AuditRecords, 4,890 Violations
DOM Snapshots Pruned: 1,420 files (184.2 MB freed)
Vacuum Executed: Database shrunk from 240 MB to 56 MB
```

---

## 3. Manual WAL Checkpointing & Vacuuming

If a node experiences sudden power loss or intense feed writes:

```bash
# Force full checkpoint of WAL log into main DB
poetry run python -c "
import sqlite3
conn = sqlite3.connect('data/credence.db')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE);')
conn.execute('VACUUM;')
conn.close()
print('✅ Database Checkpoint & Vacuum Complete.')
"
```

---

## 4. SQLite References & Operational Runbooks

### 📚 Official SQLite & SQLModel Specifications
* **SQLite Official Documentation**: [Write-Ahead Logging (WAL) Mode](https://www.sqlite.org/wal.html) &bull; [PRAGMA Statements & Concurrency Tuning](https://www.sqlite.org/pragma.html)
* **SQLModel**: [SQLModel Async Sessions & Declarative Models](https://sqlmodel.tiangolo.com/)
* **aiosqlite**: [aiosqlite Async SQLite Driver for Python](https://github.com/omnilib/aiosqlite)

### 🔗 Related Infrastructure Guides in Credence
* 🍓 [Raspberry Pi & Homelab 24/7 Operations](raspberry-pi-homelab.md)
* 📋 [Bootstrap Operator Guide & SRE Maintenance](../operator-guide.md)
* ☁️ [GCP Cloud Run Serverless Persistence](../deployment-cloudrun.md)
* 🏛️ [System Invariants: Database Concurrency & AsyncSession Rules](../invariants.md)

