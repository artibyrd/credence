# Credence Agent Invariants & Architectural Rules

This document outlines mandatory rules and design invariants for human contributors and AI agents working on Credence.

## 1. Extensible Taxonomy Invariant
- Taxonomies live in `credence/taxonomies/*.yaml`.
- Every rule must have: `rule_id`, `name`, `severity` (1..5), `description`, `evidence_guidelines`, and a computed `namespaced_uri`.
- The `TaxonomyRegistry` must dynamically discover all YAML files without code changes.

## 2. Ingestion & Memory Safeguards
- All Playwright snapshot executions must pass through the `asyncio.Semaphore(1)` gate (`MAX_CONCURRENT_SNAPSHOTS`) to prevent Chromium OOM spikes.
- Both a visual full-page screenshot (`.png`) and rendered DOM (`.html`) are persisted alongside normalized SHA-256 and SimHash-64.

## 3. Storage & Async ORM Rules
- Use `SQLModel` with SQLite WAL mode in production and in-memory for testing.
- When creating tables with relationships, do not use `from __future__ import annotations` to avoid mapper resolution bugs in Python 3.12.

## 4. Satire Classification Rules
- Check masthead, Schema.org metadata, and text indicators for satire cues.
- Set `is_satire = True` and `suspicion_score = 0.0` for authentic humor publications.
- Flag bad-faith weaponized fake news claiming satire under `SPJ-1.6` (Severity 4).
