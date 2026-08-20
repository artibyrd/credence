---
title: 'Cookbook: Multi-Tenant Org Subdomain Federation'
description: Recipe for configuring independent sovereign organization nodes with white-labeled dev and prod subdomains.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Cookbook: Multi-Tenant Org Subdomain Federation

Learn how to initialize a white-labeled sovereign organization and configure custom dev/prod subdomains.

---

## 1. Initialize Sovereign Organization

```bash
# Initialize organization structure
credence init-org "Acme Epistemic Desk" \
  --domain acme.org \
  --profile balanced
```

---

## 2. Configure Subdomain Routing

In Cloudflare DNS, configure CNAME records pointing `dev.acme.org` and `mcp.acme.org` to your sovereign Credence edge router.
