---
title: 'Technical Blueprint: Sovereign Data Gravity and CAS Portability'
description: Architectural blueprint on Content-Addressable Storage (CAS) portability, database migrations, and zero-loss state synchronization.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Technical Blueprint: Sovereign Data Gravity and CAS Portability

This blueprint details how Credence enforces content immutability and seamless portability between SQLite, PostgreSQL, R2, and local disk.

---

## 1. Content-Addressable Storage (CAS) Invariant

All web snapshot artifacts, HTML dumps, and verification proofs are stored under canonical SHA-256 addresses:

$$\text{Key} = \text{"cas/sha256/"} + \text{SHA256}(\text{Payload}) + \text{".ext"}$$

This guarantees that snapshots can be migrated across POSIX local filesystems, MinIO, AWS S3, and Cloudflare R2 without rewriting database records.
