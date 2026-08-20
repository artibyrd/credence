---
title: 'Operational Guide: Content-Addressable Blob Storage with Cloudflare R2'
description: Operational guide for configuring S3-compatible zero-egress Cloudflare
  R2 storage for HTML DOM captures and visual screenshots.
since_version: v1.17.0
verified_version: v1.18.2
last_verified: '2026-08-19'
---

# Operational Guide: Content-Addressable Blob Storage with Cloudflare R2

Credence stores raw captured HTML DOM trees and visual PNG screenshots in **Content-Addressable Storage (CAS)**. This guide details how to configure zero-egress Cloudflare R2 (or any S3-compatible storage engine) for production snapshot persistence.

---

## 1. Zero-Egress Economics

Traditional cloud providers (AWS S3, GCP Cloud Storage) charge between $0.08 and $0.12 per GB of internet egress. In contrast, **Cloudflare R2** charges **$0.00 egress fees**, enabling infinite public inspection of verified forensic snapshots at zero marginal cost.

---

## 2. Cloudflare R2 Setup Runbook

### Step 1: Create R2 Bucket
1. Go to **Cloudflare Dashboard $\rightarrow$ R2 Object Storage $\rightarrow$ Create bucket**.
2. Name the bucket: `credence-snapshots`.
3. Select Location: **Automatic** (or preferred geographic region).
4. Click **Create Bucket**.

### Step 2: Generate S3-Compatible API Credentials
1. Under **R2 Object Storage**, click **Manage R2 API Tokens $\rightarrow$ Create API Token**.
2. Permissions: **Object Read & Write**.
3. Apply to specific bucket: `credence-snapshots`.
4. Copy the generated credentials:
   - **Access Key ID**: `S3_ACCESS_KEY_ID`
   - **Secret Access Key**: `S3_SECRET_ACCESS_KEY`
   - **Jurisdiction / S3 Endpoint URL**: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`

---

## 3. Configuration & Environment Variables

Configure your Credence environment or Cloud Run service with:

```bash
STORAGE_BACKEND=s3
S3_BUCKET_NAME=credence-snapshots
S3_ENDPOINT_URL=https://f1e95c67a1e06db65efa5aaf7a92b38e.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID="your_r2_access_key_id"
S3_SECRET_ACCESS_KEY="your_r2_secret_access_key"
S3_REGION_NAME=auto
```

---

## 4. Key Structure & CAS Path Traversal Defenses

All stored forensic snapshots use cryptographic Content-Addressable Storage keys:
- HTML Snapshot: `cas/sha256/{content_sha256}.html`
- Visual Screenshot: `cas/sha256/{content_sha256}.png`

The storage adapter validates every key against the strict regex `^cas/sha256/[a-f0-9]{64}\.(html|png)$` prior to executing any disk or S3 operations, completely neutralizing directory traversal attacks (`../`).
