---
title: 'Operational Guide: Zero-Downtime Canary and Blue-Green Deployments'
description: Operational procedures for performing gradual canary traffic shifting and instantaneous blue-green rollbacks on Google Cloud Run.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Operational Guide: Zero-Downtime Canary and Blue-Green Deployments

Learn how to safely deploy new revisions to production with fractional canary traffic splitting and instantaneous 1-command rollback.

---

## 1. Canary Traffic Splitting

Deploy a new revision without routing 100% of traffic immediately:

```bash
# 1. Deploy new revision without routing traffic
gcloud run deploy credence-server \
  --image gcr.io/credence-prod-505902/credence-server:v1.18.0 \
  --no-traffic

# 2. Shift 10% of traffic to the new revision for telemetry observation
gcloud run services update-traffic credence-server \
  --to-revisions LATEST=10

# 3. Monitor P95 latency and 5xx error rate
just gcp probe
```

---

## 2. Instantaneous Rollback

If errors occur, revert traffic 100% back to the prior known-good revision:

```bash
just gcp rollback credence-server-00042-xyz
```
