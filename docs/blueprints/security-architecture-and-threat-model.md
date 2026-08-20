---
title: 'Technical Blueprint: Security Architecture & Threat Model'
description: Adversarial threat model and zero-trust security architecture for planetary scale Credence deployments.
since_version: v1.17.0
verified_version: v1.17.0
last_verified: '2026-08-19'
---

# Technical Blueprint: Security Architecture & Threat Model

This document establishes the zero-trust security controls protecting Credence nodes against network exploitation, state poisoning, and prompt injection.

---

## 1. Threat Vector & Countermeasure Matrix

```mermaid
flowchart TD
    subgraph Vectors ["Adversarial Vectors"]
        V1["SSRF & DNS Rebinding"]
        V2["Edge Cache Poisoning"]
        V3["Redis State Tampering"]
        V4["Blob Directory Traversal"]
        V5["Decompression Bombs"]
    end

    subgraph Defenses ["Zero-Trust Defenses"]
        D1["Single-Resolution DNS Pinning & RFC 1918 Filter"]
        D2["Ed25519 Cryptographic Origin Signature Lock"]
        D3["Constant-Time Admin Bearer Auth & Parameter Clamping"]
        D4["Strict Hex Regex Validation & Write-Once Immutability"]
        D5["10MB Streaming Caps & DefusedXML Parsing"]
    end

    V1 --> D1
    V2 --> D2
    V3 --> D3
    V4 --> D4
    V5 --> D5
```

---

## 2. Ingestion Defense Specifications
- **Single-Resolution DNS Pinning**: Resolves host IP once, validates non-routable ranges, and opens raw sockets directly to the pinned IP with `Host:` attached.
- **Decompression Caps**: Enforces `max_content_length = 10_485_760` (10MB) on chunked streams.
- **External Text Isolation**: Untrusted scraped prose is wrapped in `<untrusted_source_text>` XML containers before entering subagent context.
