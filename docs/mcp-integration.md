# FastMCP Server & Client Integration Guide

Credence implements a fully compliant **Model Context Protocol (FastMCP)** server ([`credence/server/app.py`](file:///home/pendragon/Projects/credence/credence/server/app.py)) allowing AI coding assistants (Antigravity, Claude Desktop, Cursor, and custom autonomous agents) to invoke epistemic tools and inspect live taxonomy resources.

---

## 1. Transports Supported

1. **Standard I/O (`stdio`)**: Best for local interactive agents and desktop tools (Antigravity, Claude Desktop).
2. **Server-Sent Events (`SSE / HTTP`)**: Best for multi-agent clusters, remote microservices, and Google Cloud Run.

---

## 2. FastMCP Tool Catalog

### `credence_check_url`
Audits a live webpage against journalistic ethics, logical fallacies, and deceptive UI patterns.
- **Parameters**: `url: str`, `force_refresh: bool = False`
- **Output**: JSON payload containing `suspicion_score`, `classification`, `is_satire`, `violations`, and Ed25519 `node_signature`.

### `credence_evaluate_text`
Audits raw prose text directly without web scraping (zero network overhead).
- **Parameters**: `text: str`, `title: str = "Pasted Text"`, `byline: Optional[str] = None`
- **Output**: Full signed `AuditReport` JSON.

### `credence_get_audit`
Queries cached audits by URL or content SHA-256 in $0$ LLM tokens.
- **Parameters**: `identifier: str` (URL or SHA-256 hash)

### `credence_verify_attestation`
Cryptographically verifies an Ed25519 signed attestation.
- **Parameters**: `signed_attestation_json: str`
- **Output**: `{ "is_valid": true, "node_pubkey": "...", "content_sha256": "..." }`

### `credence_get_quota_status`
Returns real-time token safety headroom %, daily spend, and circuit breaker health.

### `credence_get_consensus`
Calculates Bayesian multi-node consensus across peer evaluations for a given content hash.

---

## 3. Dynamic MCP Resources

- **`credence://taxonomies`**: Lists all registered taxonomy catalogs and canonical SHA-256 hashes.
- **`credence://taxonomies/{catalog_id}`**: Retrieves catalog definitions, cluster rules, and prompt checklists.
- **`credence://node/identity`**: Returns local Ed25519 node public key.

---

## 4. Dynamic FastMCP Prompts

Credence registers interactive prompt templates for AI assistants:

- **`audit_article_prompt(url)`**: Orchestrates an end-to-end epistemic audit on a target URL using `credence_check_url`.
- **`fallacy_review_prompt(text)`**: Structures a formal argument inspection against the IEP Fallacies taxonomy using `credence_evaluate_text`.
- **`dark_pattern_review_prompt(url)`**: Guides automated inspection of e-commerce checkout or signup funnels for deceptive patterns.

---

## 5. Connecting to Antigravity & Claude Desktop

Add Credence to your MCP settings configuration (`mcp_config.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "credence": {
      "command": "poetry",
      "args": ["run", "credence", "serve", "--transport", "stdio"],
      "cwd": "/home/pendragon/Projects/credence"
    }
  }
}
```

Or connect via remote SSE endpoint:

```json
{
  "mcpServers": {
    "credence_remote": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```
