---
title: 'Cookbook: Local Dev to Cloud Run Fast-Path Workflow'
description: Step-by-step developer recipe for editing locally, testing with basic SQLite, and pushing revisions to dev Cloud Run in seconds.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Cookbook: Local Dev to Cloud Run Fast-Path Workflow

Follow this practical workflow for rapid daily coding and immediate testing on your dev Cloud Run instance.

---

## 1. Edit and Test Locally

```bash
# 1. Edit code and run targeted unit tests
poetry run pytest tests/test_multi_env_routing.py -v

# 2. Run fast pre-commit check
just check
```

---

## 2. Push to Dev Cloud Run

```bash
# Deploy instantly to dev
just deploy dev

# Probe live endpoints
just gcp probe credence-dev
```
