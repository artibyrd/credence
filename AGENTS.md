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

## Standard Task Commands (`Justfile`)
- `just test`: Run fast hermetic test suite (<2s).
- `just lint`: Run `ruff check`, `ruff format --check`, and `mypy credence tests`.
- `just format`: Autoformat code with Ruff.
