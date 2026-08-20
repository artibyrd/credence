---
title: 'FastMCP 2.0 Substrate: Dual Transports & 4-Way Synchronous Parity'
description: Architecture of the FastMCP 2.0 dual stdio/SSE server, Cloudflare edge
  proxying, and maintaining synchronous feature parity across CLI, FastMCP, TUI, and
  Web.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
tags:
- fastmcp
- sse
- mcp
- feature-parity
- cloud-run
- cloudflare
interfaces:
- CLI
- FastMCP 2.0
- Python SDK
- Zero-Build Web UI
- Textual TUI
invariants:
- 12
- 14
- 16
- 30
difficulty: Advanced
read_time: 8 min
---

# FastMCP 2.0 Substrate: Dual Transports & 4-Way Synchronous Parity

Explore the communication architecture powering Credence's **FastMCP 2.0 server**, providing unified tool and resource access to Claude Desktop, Cursor, and Antigravity while maintaining 4-way synchronous feature parity.

```mermaid
flowchart TD
    Client["AI Agents & Developers<br/>(Claude, Cursor, Antigravity, Shell, Web)"] --> Gateway{"FastMCP 2.0 Gateway"}
    
    Gateway -->|Local Process IPC| Stdio["stdio Transport<br/>(High-speed pipe)"]
    Gateway -->|Remote Mesh HTTP| SSE["SSE Transport<br/>(mcp.credence.run/sse)"]
    
    Stdio & SSE --> Core["Credence Epistemic Core Engine"]
    
    Core --> Parity1["1. CLI (credence)"]
    Core --> Parity2["2. FastMCP (credence_*)"]
    Core --> Parity3["3. Textual TUI (credence tui)"]
    Core --> Parity4["4. Zero-Build Web (credence.report)"]
```

> [!IMPORTANT]
> **[Invariant 30: Universal Feature Parity](../invariants.md#invariant-30)**: Every capability in Credence must be synchronously accessible across all 4 surfaces: CLI (`credence`), FastMCP 2.0 tools and resources, Textual TUI (`credence tui`), and the Zero-Build Web UI.

---

## 1. Dual Transport Architecture: stdio vs. Server-Sent Events (SSE)

Credence implements dual FastMCP transports to support both local IDE pair-programming and remote decentralized mesh querying:

| Feature | `stdio` Transport | `sse` Transport |
| :--- | :--- | :--- |
| **Primary Use Case** | Local Claude Desktop & Cursor IDE | Multi-cloud mesh nodes & Webhooks |
| **Network Overhead** | **0ms** (Kernel UNIX pipes) | ~15–45ms (HTTPS / HTTP/3) |
| **Authentication** | Local OS User Permissions | Ed25519 Signed Session Handshake |
| **Launch Command** | `credence serve --transport stdio` | `credence serve --transport sse --port 8000` |

---

## 2. Reverse Proxy Security & Edge Header Rewriting

When deploying FastMCP servers behind Cloudflare and Google Cloud Run, default DNS rebinding protections reject custom domain host headers.

To ensure seamless production routing:
1. **Configure Transport Security Settings**:
   ```python
   # In credence/mcp/server.py
   TransportSecuritySettings(
       enable_dns_rebinding_protection=False,
       allowed_hosts=["*"],
       allowed_origins=["*"]
   )
   ```
2. **[Invariant 14: Edge Routing Origin Header Translation](../invariants.md#invariant-14)**: Cloudflare Worker edge routers rewrite `Host` headers to native Cloud Run URLs (`<service>.run.app`) to preserve live Server-Sent Events (SSE) streaming and global CORS headers.

---

## 3. FastMCP Nested Datetime Serialization Invariant

JSON cannot natively represent Python `datetime` objects. To prevent serialization runtime crashes during MCP payload marshalling:

```python
# In models and digest export dictionaries
# [Invariant 16](../invariants.md#invariant-16): FastMCP Nested Datetime Serialization
def to_dict(self) -> dict:
    return {
        "content_sha256": self.content_sha256,
        "evaluated_at": self.evaluated_at.isoformat() if isinstance(self.evaluated_at, datetime) else self.evaluated_at,
        "violations": [v.to_dict() for v in self.violations]
    }
```

> [!TIP]
> Always verify FastMCP payloads against standard JSON schema validators before publishing new tools or resources.
