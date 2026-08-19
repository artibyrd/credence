---
title: Zero-Build Web Architecture
description: Architectural decisions, W3C WebCrypto in-browser verification, and zero
  supply-chain attack surface.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Zero-Build Web Architecture

This document records the architectural decisions and invariants governing the public web surfaces across the **Credence** ecosystem (`credence.run`, `credence.nexus`, `credence.foundation`, `credence.report`).

---

## 1. Architectural Invariant (Invariant 20)

> **[Invariant 20](invariants.md#invariant-20): Web Frontend Zero-Build & Web Crypto Verification Invariant**
> - All public web frontends across the Credence ecosystem must be built strictly using **vanilla modern web standards** (Semantic HTML5, CSS Custom Properties, and native ES Modules) with **zero Node.js/npm build dependencies**.
> - Client-side cryptographic verification of signed audit reports must strictly use the native W3C **Web Cryptography API** (`window.crypto.subtle`) rather than external JavaScript crypto libraries.

---

## 2. In-Browser Trustless Verification via WebCrypto

When an auditor or reader inspects a report at `https://credence.report/viewer.html`:
1. The browser retrieves the raw signed `AuditReport` JSON.
2. The browser executes native in-browser cryptographic verification via `window.crypto.subtle.verify(...)` using the author's public Ed25519 key.
3. The reader achieves **true trustless client-side verification** without trusting the web hosting server or loading third-party crypto scripts.

---

## 3. Comparative Architecture Matrix

| Evaluation Dimension | **Vanilla Web Standards** *(Credence Standard)* | **Full-Stack Next.js / React** |
|---|---|---|
| **Build Toolchain** | **Zero Build Tools** (0 npm packages) | Heavy Node.js + npm build step |
| **PageSpeed / Lighthouse** | **100 / 100** (<30KB payload, <15ms TTFB) | **70–85** (Heavy JS hydration) |
| **Edge Hosting Cost** | **$0.00** on Cloudflare Pages edge | Server compute / container costs |

---

## 4. W3C Standards & External Documentation

### 📚 Official Web Standards Specifications
* **W3C Standards**: [W3C Web Cryptography API Specification](https://www.w3.org/TR/WebCryptoAPI/) &bull; [MDN Web Crypto API Guide](https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API)
* **Modern JavaScript**: [Native ES Modules in Modern Browsers (MDN)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
* **Cloudflare Workers**: [Zero-Build Static Assets with `env.ASSETS`](https://developers.cloudflare.com/workers/static-assets/) &bull; [Cloudflare Pages](https://developers.cloudflare.com/pages/)
* **Performance & Accessibility**: [Google Core Web Vitals (web.dev)](https://web.dev/explore/learn-core-web-vitals) &bull; [W3C Web Content Accessibility Guidelines (WCAG 2.1)](https://www.w3.org/WAI/standards-guidelines/wcag/)

### 🔗 Related Presentation Guides in Credence
* 🎮 [Interactive Zero-Build Playgrounds (12 Live WebCrypto Tools)](playground.md)
* 🧩 [Vanilla Manifest V3 Browser Extension](integrations/browser-extension-mv3.md)
* 🔬 [Case Study: Conflict of Pun-terest Forensics](../blog/conflict-of-pun-terest.md)
* 🏛️ [System Invariant 20 & 21: Zero-npm & Multi-Domain Edge Routing](invariants.md)

