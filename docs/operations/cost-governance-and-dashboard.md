---
title: 'Operational Guide: Cost Governance, Dashboard & AI Optimizer'
description: Comprehensive operational guide for managing operational cost profiles, live budget overrides, Emergency Brake controls, and the Autonomous AI Cost Optimizer.
since_version: v1.17.0
verified_version: v1.17.0
last_verified: '2026-08-19'
---

# Operational Guide: Cost Governance, Dashboard & AI Optimizer

Credence incorporates an autonomous **Cost Governance & Resource Optimization** engine designed to prevent runaway cloud bills while maintaining full multi-agent reasoning fidelity ($G=1.00$).

---

## 1. The 5 Operational Cost Profiles

Credence provides 5 distinct cost profiles, defaulting to **`ECONOMY`**—the most conservative profile that is 100% fully functional with Gemini 3.7 Flash reasoning:

```mermaid
flowchart LR
    subgraph ProfileSpectrum ["Operational Cost Profiles"]
        P0["1. OFFLINE ($0.00)<br/>Local Rules Only"]
        P1["2. FREE ($0.00)<br/>Gemini 2.0 Flash-Lite"]
        P2["3. ECONOMY ($0.15/d)<br/>Gemini 3.7 Flash (512 Thinking)"]
        P3["4. BALANCED ($0.50/d)<br/>Gemini 3.7 Flash (1024 Thinking)"]
        P4["5. ULTRA ($5.00/d)<br/>Gemini 3.7 Flash + 1.5 Pro"]
    end
```

| Profile | Target Audience | Primary Model | Thinking Budget | Max Daily Budget | Max Tokens / Hour | Concurrency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`OFFLINE`** | Air-gapped testing | *Local Rules* | 0 tokens | **$0.00** | 0 tokens | 1 |
| **`FREE`** | Zero-marginal-cost | `gemini-2.0-flash-lite` | 0 tokens | **$0.00** | 50,000 | 1 |
| 🏆 **`ECONOMY` (DEFAULT)** | **Conservative Developer** | **`gemini-3.7-flash`** | **512 tokens** | **$0.15 / day** | **50,000** | **2** |
| **`BALANCED`** | Production Developer | `gemini-3.7-flash` | 1,024 tokens | **$0.50 / day** | 100,000 | 3 |
| **`ULTRA`** | Investigative Desk | `gemini-3.7-flash` | 4,096 tokens | **$5.00 / day** | 2,000,000 | 8 |

---

## 2. Deploy-Time Defaults vs Live Runtime Controls

- **Deploy-Time Defaults**: Defined in `.env` (`CREDENCE_PROFILE=economy`, `MAX_DAILY_BUDGET_USD=0.15`).
- **Live Dynamic Runtime Controls**: Stored in Redis (`credence:settings:cost`) or database table, enabling zero-downtime updates across 500+ Cloud Run replicas in $<5\text{ms}$.

---

## 3. The 1-Click Emergency Brake

The Emergency Brake is a failsafe lever that instantly trips the circuit breaker into `QUOTA_PRESERVED` mode across all nodes:

```bash
# Pull emergency brake via CLI
credence cost stop --reason "Suspected billing anomaly"

# Resume normal operations
credence cost resume
```

---

## 4. Autonomous AI Cost Optimizer

The Cost Optimizer continuously analyzes 24-hour and 7-day rolling telemetry:
- **Upgrade Suggestions**: Triggered when a node trips the circuit breaker $\ge 3$ times or has $>20$ deferred RSS feed items.
- **Downgrade Suggestions**: Triggered when a node utilizes $<15\%$ of budget over 7 days or achieves $>85\%$ P2P mesh attestation adoption.

```bash
# View recommendation
credence cost optimize

# Apply recommendation
credence cost optimize --apply
```
