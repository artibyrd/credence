---
title: Universal Agent Interoperability (Claude, Cursor, Cline, Windsurf)
description: Connecting Credence FastMCP 2.0 to Claude Desktop, Cursor, Windsurf,
  Cline, LangGraph, and CrewAI without vendor lock-in.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Universal Agent Interoperability (Claude, Cursor, Cline, Windsurf)

Credence implements the open **Model Context Protocol (FastMCP 2.0)** standard. While our developer kit repository (`credence-agent`) includes Google Antigravity IDE integrations, Credence is **100% interoperable with every major AI agent and IDE framework**.

This guide demonstrates setting up Credence across all non-Google AI environments.

---

## 1. Claude Desktop Setup

Add Credence to your `claude_desktop_config.json`:

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

### In Claude Desktop Chat:
> *"Audit the claims in this blog post before incorporating its advice: `https://example.com/fastapi-performance-tricks`"*

Claude invokes `credence_check_url`, inspects the grounded findings, and provides a verified response.

---

## 2. Cursor & Windsurf IDE Setup

In your project root or global settings, add the MCP server configuration:

```json
{
  "mcpServers": {
    "credence-remote": {
      "url": "https://mcp.credence.run/sse"
    }
  }
}
```

### Adding Cursor Rules (`.cursorrules`):
```markdown
# Epistemic Citation Invariant
Whenever you retrieve external documentation or packages from the web:
1. Invoke the `credence_check_url` MCP tool.
2. If the suspicion score is >= 45.0, reject the source and search for the primary official documentation.
3. Always verify that package recommendations exist in official package registries.
```

---

## 3. Cline / Roo Code (VS Code Extension)

In VS Code with the Cline/Roo Code extension:
1. Open Cline Settings $\to$ **MCP Servers**.
2. Add a new server:
   - **Name**: `credence`
   - **Type**: `stdio`
   - **Command**: `credence`
   - **Args**: `["serve", "--transport", "stdio"]`

---

## 4. LangGraph & CrewAI Python Integration

Connect autonomous multi-agent pipelines to Credence via the standard MCP SSE transport:

```python
from langgraph.prebuilt import ToolNode
import httpx

def credence_audit_tool(url: str) -> dict:
    """Audits a URL against journalistic ethics and logical fallacies."""
    with httpx.Client() as client:
        res = client.post("http://localhost:8000/api/audit", json={"url": url})
        return res.json()

# Attach tool to LangGraph agent
tools = [credence_audit_tool]
tool_node = ToolNode(tools)
```

---

## 5. External Specifications & Agent Ecosystem References

### 📚 Official AI Agent & IDE Documentation
* **Model Context Protocol**: [Official MCP Specification](https://modelcontextprotocol.io/) &bull; [MCP Architecture Overview](https://modelcontextprotocol.io/docs/concepts/architecture)
* **Anthropic**: [Claude Desktop MCP Quickstart](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
* **Cursor**: [Cursor AI Editor & MCP Tools](https://docs.cursor.com/context/model-context-protocol)
* **Windsurf**: [Codeium Windsurf IDE Cascade Architecture](https://codeium.com/windsurf)
* **Cline**: [Cline Autonomous Coding Agent on GitHub](https://github.com/cline/cline)
* **LangGraph**: [LangGraph Multi-Agent Workflows (LangChain)](https://langchain-ai.github.io/langgraph/)
* **CrewAI**: [CrewAI Autonomous Agent Framework](https://docs.crewai.com/)

### 🔗 Related Agentic Guides in Credence
* 🛑 [Cookbook: Agentic Epistemic Brake for AI Workflows](../cookbooks/agentic-epistemic-brake.md)
* ⚡ [FastMCP 2.0 Protocol & SSE Streaming Specification](../protocols/fastmcp.md)
* 🔄 [Multi-Model Adapters (Gemini, Claude, GPT-4o, DeepSeek, Ollama)](multi-model-adapters.md)
* 🤖 [Antigravity Pair-Programming Paradigm](../agentic/01-antigravity-pair-programming-paradigm.md)
* 🎮 [Interactive Playground: In-Browser Text Scanner](../playground.md)

