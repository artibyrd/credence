---
title: 'Operational Guide: Dev Environment Setup and Homelab'
description: Step-by-step developer guide for setting up a sovereign local development workstation, test fixtures, and homelab runners.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Operational Guide: Dev Environment Setup and Homelab

Set up your local machine for Credence development and sovereign experimentation in under 2 minutes.

---

## 1. Quick Developer Onboarding

```bash
# 1. One-command onboarding sequence
just ignite 3

# 2. Run hermetic unit tests
just test unit

# 3. Launch local development server with live reload
just serve web
```

---

## 2. Testing against Dev Cloud Run Instance

```bash
# Deploy local working tree to your personal Dev Cloud Run instance
just deploy dev

# Probe live dev endpoints
just gcp probe credence-dev
```
