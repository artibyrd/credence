---
title: 'Technical Blueprint: Zero-Build Edge Routing and Subdomain Dispatch'
description: Technical architecture of Cloudflare Anycast edge routing, multi-domain dispatching, and cache tiering across production and dev subdomains.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Technical Blueprint: Zero-Build Edge Routing and Subdomain Dispatch

This blueprint details the edge routing algorithms and cache tiering implemented in `web/_worker.js`.

---

## 1. Request Resolution Pipeline

```mermaid
flowchart TD
    Host["Host Evaluation"] -->|"dev.credence.run"| DevTarget["Dev Compute Backend (credence-dev)"]
    Host -->|"credence.run"| ProdTarget["Prod Compute Backend (credence-server)"]
    Host -->|"mcp.credence.run"| SSEProxy["FastMCP SSE Streaming Proxy"]
    Host -->|"credence.report/api/reports/*"| ImmutableCache["Edge Cache (30d Immutable)"]
    Host -->|"dev.credence.report/api/reports/*"| DevCache["Dev Cache (60s Short-Lived)"]
```

---

## 2. Zero-Build Web Assets Invariant

All HTML, CSS, and ES Modules are served directly from Cloudflare Pages / KV without any build step, bundler, or npm dependencies.
