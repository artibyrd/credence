---
title: 'Technical Blueprint: Dual-Environment Project and Domain Isolation'
description: Deep security architecture blueprint specifying blast radius containment, IAM least-privilege policies, and cryptographic isolation between dev and prod.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Technical Blueprint: Dual-Environment Project and Domain Isolation

This blueprint specifies the security isolation guarantees, network topology boundaries, and least-privilege IAM matrices enforced between Credence Development and Production environments.

---

## 1. Threat Model & Blast Radius Containment

The dual-environment architecture prevents three primary attack vectors:
1. **Accidental Production Data Mutation**: Dev workloads cannot access production PostgreSQL connection strings or production R2 buckets.
2. **Secret Bleed**: Dev service accounts hold zero IAM roles in the production GCP project.
3. **Cache Poisoning & SSRF Escalation**: Dev subdomains (`dev.credence.*`) isolate browser cookies, LocalStorage, and origin caches from canonical production origins.

---

## 2. Cryptographic & State Isolation

- **Ed25519 Custody**: Dev nodes sign audit records with ephemeral or dev-scoped private keys; production root keys remain isolated in dedicated HSM / KMS vaults.
- **CAS Immutability**: Production blob storage enforces strict write-once SHA-256 verification (`cas/sha256/<hash>.<ext>`).
