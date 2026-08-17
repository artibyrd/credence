# Agent Guidelines & Project Invariants for Credence

Welcome to the **Credence** codebase (`/home/pendragon/Projects/credence`).

## Core Invariants
1. **Isolated Workspace**: Credence is an autonomous project completely decoupled from other repositories.
2. **Python & Database Invariants**:
   - Python version: `>=3.12,<3.13`.
   - SQLModel Async: Always use `sqlmodel.ext.asyncio.session.AsyncSession` and `async_sessionmaker`.
   - Avoid `from __future__ import annotations` in `models.py` to prevent string relationship mapper issues.
3. **Poe's Law & Satire Safeguards**:
   - Always classify satirical content (`is_satire=True`, `SATIRE_PARODY`) before calculating suspicion scores.
   - Legitimate satire is neutralized, while cloaked bad-faith disinformation is penalized under `SPJ-1.6`.
4. **Hermetic Testing**:
   - Never add network-dependent tests to the default unit test suite (`tests/`).
   - Use `sqlite+aiosqlite:///:memory:` and offline HTML fixtures.
5. **Taxonomy Registries**:
   - Never hardcode rule names in pipeline scoring math. Always use namespaced URIs (`domain:cluster/rule_id@version`) and generic numerical severity/confidence inputs.
6. **Human Review Before Commits ("Mk1 Eyeball")**:
   - Never execute `git commit` automatically. Always present changes and live verification results for human review first, and only commit when explicitly requested by the user.
7. **Token Budget & Development Coexistence Invariant**:
   - Always prioritize `CREDENCE_GEMINI_API_KEY` over shared dev keys.
   - Enforce hourly/daily token budgets and automatic offline circuit-breaker fallbacks (`QUOTA_PRESERVED`) to guarantee that autonomous auditing never starves interactive Antigravity development sessions.
8. **Textual & Rich Markup Escaping**:
   - Never use unescaped `[/]` or bracket shortcuts in Textual/Rich widget strings; format as `[bold]/[/bold]` or escape as `[\]`.
9. **Whitespace-Insensitive Citation Grounding**:
   - Grounded quote validators must collapse all whitespace sequences (`\s+` -> ` `) in both citations and source HTML text before substring matching.
10. **FastMCP 2.0 & Datetime Serialization**:
    - Always use `model_dump(mode="json")` for Pydantic models containing datetimes before calling `json.dumps()` in FastMCP tool handlers and tests.
11. **Mesh Network Topology & Multi-Hop Testing ($N \ge 7$)**:
    - Realistic mesh testing requires $N \ge 7$ nodes arranged in non-trivial graph topologies ($d \ge 3$) to verify relay TTL decrements and $N \ge 3f + 1$ ($f = 2$) Byzantine Sybil collusion isolation.
12. **Operational Cost Profile Enforcement**:
    - The `FREE` profile strictly enforces a $0.00 daily spend ceiling with $0$ thinking tokens. The `BALANCED` profile operates at a $0.50/day cap with $1,024$ thinking tokens, while `ULTRA` enables deep reasoning ($4,096 - 16,384$ tokens) and 10,000-word ingestion limits.
13. **Cloud Run Cost Capping & Scale-to-Zero Invariant**:
    - Production Cloud Run v2 services must configure `min_instance_count = 0` (scale-to-zero), `cpu_idle = true`, a **$15.00 USD/month Cloud Billing Budget ceiling** with automated 50%, 80%, 100% threshold alarms, and Secret Manager API key references.

## Standard Task Commands (`Justfile`)
- `just test`: Run fast hermetic test suite (<2s).
- `just lint`: Run `ruff check`, `ruff format --check`, and `mypy credence tests`.
- `just format`: Autoformat code with Ruff.
- `just tui`: Launch interactive Textual terminal workstation.
- `just mesh-cluster-up`: Launch 7-node local P2P mesh cluster.
- `just serve-sse`: Start FastMCP server in SSE mode on port 8000.
