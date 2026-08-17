# Tutorial 03: FastMCP 2.0 Integration with Claude Desktop & Cursor

Give your AI coding assistant or autonomous research agent an epistemic brake. Learn how to configure **Credence FastMCP 2.0** so Claude Desktop and Cursor can verify web pages before ingesting text.

---

## 1. Configuring Claude Desktop

Edit your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "credence": {
      "command": "credence",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

Restart Claude Desktop. You will see 12 registered tools under `credence`:
- `credence_check_url`: Capture snapshot and run full epistemic audit on any URL.
- `credence_evaluate_text`: Audit arbitrary prose text against active taxonomies.
- `credence_get_consensus`: Check multi-peer Bayesian consensus for an audited URL.
- `credence_get_quota_status`: Check remaining token budget and cache rates.

---

## 2. Using FastMCP in Agent Prompts

When asking Claude or Cursor to research a technical claim or library:

> **User Prompt**: "Research the performance claims for Library X at `https://example.com/benchmark`. Before summarizing the article, use `credence_check_url` to audit its sourcing attribution and grounded citation score."

Claude will call the tool:
```json
{
  "url": "https://example.com/benchmark",
  "cost_profile": "BALANCED"
}
```

### Automatic Prompt Injection Neutralization (Invariant 30):
All text returned from external websites is containerized in `<untrusted_source_text>` blocks, ensuring malicious website text cannot hijack Claude's instructions.
