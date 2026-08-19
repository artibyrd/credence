---
title: Token Safety Governor
description: In-database token buckets, spending ceilings, thinking token accounting,
  and automated circuit breakers.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
sidebar:
  order: 1
---

# Token Safety Governor Specification

The **TokenBudgetGovernor** manages LLM token consumption, cost caps, and reasoning quality to ensure autonomous audits never exhaust shared API quotas or starve interactive developer pairing sessions.

---

## 1. The Token Coexistence Challenge

When developing autonomous AI pipelines that make repeated LLM calls, sharing a single `GEMINI_API_KEY` across background workers and interactive developer pairing creates high operational risk:
- A large scraping run could consume all **TPM (Tokens Per Minute)** or **RPD (Requests Per Day)** quota.
- Interactive pairing with Antigravity encounters unexpected `429 ResourceExhausted` errors, grinding development to a halt.

---

## 2. 5-Layer Token Safety Architecture

```mermaid
graph TD
    A["Incoming Audit Request"] --> B{"1. Local Cache Check"}
    B -- "SHA-256 Hit" --> C["Instant 0-Token Attestation"]
    B -- "Cache Miss" --> D{"2. Token Governor & Budget Check"}
    D -- "Daily/Hourly Limit Reached" --> E["Trip Circuit Breaker (QUOTA_PRESERVED Mode)"]
    D -- "Budget Available" --> F["3. Fast Triage & Satire Filter (Flash-Lite)"]
    F -- "Is Authentic Satire" --> G["Short-Circuit Pipeline (Save 75% Tokens)"]
    F -- "Requires Full Audit" --> H["4. Truncate Input Prose (Max 2.5k words)"]
    H --> I["5. Dispatch Specialists (Gemini 3.7 Flash + Thinking)"]
    I --> J{"6. Response Quality Gate"}
    J -- "Citation Grounding < 75% / Ambiguous Margin" --> K["Dynamic Thinking Escalation"]
    J -- "Passes" --> L["Record Token Usage in SQLite & Sign Attestation"]
    K --> L
```

---

## 3. Configuration Parameters (`.env`)

| Variable | Default | Description |
|---|---|---|
| `CREDENCE_GEMINI_API_KEY` | `None` | **Isolated API Key** (Prioritized over `GEMINI_API_KEY` to separate project quota). |
| `MAX_TOKENS_PER_HOUR` | `100,000` | Hourly safety ceiling. Reaching this triggers offline fallback. |
| `MAX_TOKENS_PER_DAY` | `1,000,000` | Rolling 24-hour token consumption cap. |
| `MAX_DAILY_BUDGET_USD` | `$0.50` | Maximum estimated USD spend allowed in a 24-hour window. |
| `ENABLE_CIRCUIT_BREAKER` | `True` | Automatically enables graceful offline heuristic fallback when limits are reached. |
| `DEFAULT_SPECIALIST_MODEL` | `gemini-3.7-flash` | Primary workhorse for specialist auditors. |
| `DEFAULT_THINKING_BUDGET` | `1024` | Thinking/reasoning tokens allocated for deep syllogistic dissection. |
| `ESCALATION_THINKING_BUDGET` | `4096` | High-thinking budget allocated for ambiguous or contested boundary scores. |

---

## 4. Thinking Token Allocation & Cost Profiles

Reasoning models like **Gemini 3.7 Flash with Thinking** generate internal reasoning traces billed at completion token rates:

* **FREE Profile**: 0 thinking tokens, $0.00 ceiling, max speed.
* **BALANCED Profile**: 1,024 thinking tokens, $0.50/day spend cap.
* **ULTRA Profile**: 4,096–16,384 thinking tokens, deep philosophical syllogism extraction.
