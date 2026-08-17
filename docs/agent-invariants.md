# Credence Agent Invariants & Architectural Rules

This document outlines mandatory rules and design invariants for human contributors and AI agents working on Credence.

---

## 1. Project Isolation Invariant
- Credence is an autonomous project living exclusively at `/home/pendragon/Projects/credence/`.
- Never reference or import modules from external repositories.

---

## 2. Python & Database Invariants
- **Python Version**: `>=3.12,<3.13`.
- **SQLModel Async**: Always use `sqlmodel.ext.asyncio.session.AsyncSession` combined with `sqlalchemy.ext.asyncio.async_sessionmaker`.
- **Avoid string forward references**: Never use `from __future__ import annotations` in `credence/models.py` to prevent SQLAlchemy mapper resolution bugs in Python 3.12.
- **SQLite Database Isolation**: All automated unit tests must use in-memory SQLite (`sqlite+aiosqlite:///:memory:`).
- **SQLite Performance Pragmas**: The production engine operates in WAL mode (`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`).

---

## 3. Extensible Taxonomy Invariants
- Taxonomies reside in [`credence/taxonomies/*.yaml`](file:///home/pendragon/Projects/credence/credence/taxonomies).
- Every rule must define: `rule_id`, `name`, `severity` ($1 \dots 5$), `description`, `evidence_guidelines`, and a computed `namespaced_uri` (`domain:cluster/rule_id@version`).
- The `TaxonomyRegistry` must dynamically discover all YAML files without code changes.
- Never hardcode rule names in pipeline scoring math. Always use namespaced URIs and generic numerical severity/confidence inputs.

---

## 4. Ingestion & Memory Safeguards
- All Playwright snapshot executions must pass through the `asyncio.Semaphore(1)` gate (`MAX_CONCURRENT_SNAPSHOTS`) to prevent Chromium OOM spikes.
- Both a visual full-page screenshot (`.png`) and rendered DOM (`.html`) are persisted alongside normalized SHA-256 and SimHash-64.

---

## 5. Poe's Law & Satire Safeguards
- Always classify satirical content (`is_satire=True`, `SATIRE_PARODY`) before calculating suspicion scores.
- Legitimate satire is neutralized to score `0.0`, while cloaked bad-faith disinformation is penalized under `SPJ-1.6`.

---

## 6. Grounded Citation & Text Normalization Rules
- Grounded citation matching must normalize all whitespace sequences (`\s+` $\to$ ` `) in both the extracted DOM prose and cited excerpts before matching.
- Any ungrounded (hallucinated) citation is stripped from scoring math.

---

## 7. Token Safety & Development Coexistence Invariant
- Always prioritize `CREDENCE_GEMINI_API_KEY` over shared dev keys.
- Enforce hourly/daily token budgets and automatic offline circuit-breaker fallbacks (`QUOTA_PRESERVED`) to guarantee that autonomous auditing never starves interactive Antigravity development sessions.
- Factor Gemini 3.7 Flash **thinking tokens** into all cost and budget calculations.

---

## 8. Human Review Before Commits ("Mk1 Eyeball")
- Never execute `git commit` automatically. Always present changes and live verification results for human review first, and only commit when explicitly requested by the user.

---

## 9. Textual & Rich Markup Escaping
- Never use unescaped `[/]` or bracket shortcuts in Textual/Rich widget strings; format as `[bold]/[/bold]` or escape as `[\]`.
