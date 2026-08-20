---
title: 'Technical Blueprint: Universal 4-Way Parity and Environment Governance'
description: Architectural blueprint specifying how CLI, FastMCP 2.0, Textual TUI, and Web UI maintain simultaneous feature parity across Dev and Prod.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Technical Blueprint: Universal 4-Way Parity and Environment Governance

Credence strictly maintains simultaneous 4-way feature parity across all user interfaces regardless of whether running in Dev or Production.

---

## 1. Interface Parity Matrix

```mermaid
flowchart LR
    Core["Credence Core Kernel"]
    Core --> CLI["1. CLI (credence cost / serve)"]
    Core --> MCP["2. FastMCP 2.0 (credence_ tools & resources)"]
    Core --> TUI["3. Textual TUI (credence tui)"]
    Core --> WEB["4. Zero-Build Web UI (web/credence.nexus)"]
```

Every new operational control (such as Emergency Brake, Cost Optimization, or Subdomain Routing) must expose functional bindings across all 4 interfaces simultaneously.
