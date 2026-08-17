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
Calculates Bayesian multi-node consensus across peer evaluations for a given content hash, with optional empirical subject-weighted scoring.
- **Parameters**: `content_sha256: str`, `subject_id: Optional[str] = None`

### `credence_sync_feeds`
Polls all active syndicated RSS/Atom/JSON feeds, executes mesh effort avoidance, and adopts peer attestations at $0.00 token cost.
- **Parameters**: `dry_run: bool = False`, `evaluate_novel: bool = True`

### `credence_add_feed_subscription`
Registers a new syndicated RSS 2.0, Atom 1.0, or JSON Feed subscription.
- **Parameters**: `feed_url: str`, `title: str = ""`, `priority_tier: int = 2`, `subject_tag: str = "journalism.news"`, `is_satire: bool = False`

### `credence_list_feeds`
Lists all active syndicated feed subscriptions with priority tier, subject tags, and polling states.

### `credence_remove_feed_subscription`
Unsubscribes from a syndicated feed by URL.
- **Parameters**: `feed_url: str`

### `credence_get_feed_stats`
Returns aggregate statistics on discovered feed items, zero-token mesh adoptions, and total tokens saved.

### `credence_get_seed_nodes`
Retrieves verified bootstrap seed nodes from `seeds.credence.nexus` or fallback sources.
- **Parameters**: `seed_url: Optional[str] = None`

---

## 3. Dynamic MCP Resources

- **`credence://profiles`**: Lists operational cost profiles (Free, Balanced, Ultra), budget limits, and thinking token allocations.
- **`credence://taxonomies`**: Lists all registered taxonomy catalogs and canonical SHA-256 hashes.
- **`credence://taxonomies/{catalog_id}`**: Retrieves catalog definitions, cluster rules, and prompt checklists.
- **`credence://subjects/registry`**: Full hierarchical epistemic subject registry tree.
- **`credence://subjects/{subject_id}`**: Detailed metadata, taxonomies, and keyword triggers for a specific subject namespace.
- **`credence://subjects/leaderboard`**: Leaderboard of nodes with empirical domain expertise track records.
- **`credence://feeds/status`**: Active feed subscriptions count, discovered articles, and mesh tokens saved.
- **`credence://mesh/seeds`**: Canonical bootstrap seed nodes from `seeds.credence.nexus`.
- **`credence://node/identity`**: Local Ed25519 node public key.

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
