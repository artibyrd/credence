---
title: 'Cookbook: Browser Extension MV3 Zero-Hop Edge Verification'
description: Recipe for integrating Chrome Extension Manifest V3 with Cloudflare Anycast Edge for sub-20ms instant trust badges.
since_version: v1.17.0
verified_version: v1.17.0
last_verified: '2026-08-19'
---

# Cookbook: Browser Extension MV3 Zero-Hop Edge Verification

This cookbook demonstrates how Chrome Extension Manifest V3 queries cached epistemic attestations directly from Cloudflare's Anycast Edge in $<20\text{ms}$ with zero origin compute overhead.

---

## 1. The Zero-Hop Query Flow

```mermaid
sequenceDiagram
    autonumber
    participant Browser as Chrome Browser (MV3 Content Script)
    participant Edge as Cloudflare Anycast Edge (300+ PoPs)
    participant Origin as Cloud Run Compute Plane

    Browser->>Edge: GET /api/reports/{content_sha256}
    alt Edge Cache Hit (95%+ of traffic)
        Edge-->>Browser: 200 OK (Cached Ed25519 Signed Report, <20ms)
    else Edge Cache Miss (5% novel content)
        Edge->>Origin: Forward Request to Origin
        Origin-->>Edge: 200 OK (Cache-Control: immutable)
        Edge-->>Browser: 200 OK
```

---

## 2. Client-Side Implementation

```javascript
// content-script.js
async function checkCurrentPageTrust(pageSha256) {
  const edgeEndpoint = `https://credence.report/api/reports/${pageSha256}`;
  const response = await fetch(edgeEndpoint, {
    headers: { "Accept": "application/json" },
    cache: "force-cache"
  });

  if (response.ok) {
    const report = await response.json();
    renderTrustPill(report.suspicion_score, report.classification);
  }
}
```
