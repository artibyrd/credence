# Operational Cost Profiles & Subscription Tier Mappings

Credence provides 3 preconfigured **Operational Cost Profiles** (`FREE`, `BALANCED`, `ULTRA`) that dynamically adjust model selection, Gemini thinking token budgets, article ingestion length, concurrency limits, and in-database spending ceilings.

---

## 1. Cost Profile Comparison Matrix

| Feature / Metric | `FREE` (Zero-Cost / Free Tier) | `BALANCED` (Pay-As-You-Go Dev) *(Default)* | `ULTRA` (Gemini Ultra / High Fidelity) |
|---|---|---|---|
| **Target Audience** | Gemini Free Tier (15 RPM / 1M TPM) | Standard Pay-As-You-Go ($0.10/$0.40 per 1M) | Gemini Advanced / Newsroom Desks |
| **Primary Model** | `gemini-2.0-flash-lite` | `gemini-3.7-flash` | `gemini-3.7-flash` + `gemini-1.5-pro` |
| **Escalation Model** | `gemini-2.0-flash-lite` | `gemini-3.7-flash` | `gemini-1.5-pro` |
| **Triage Model** | `gemini-2.0-flash-lite` | `gemini-2.5-flash-lite` | `gemini-3.7-flash` |
| **Default Thinking Budget** | $0$ tokens | $1,024$ tokens | $4,096$ tokens |
| **Escalation Thinking Budget** | $0$ tokens | $4,096$ tokens | $16,384$ tokens |
| **Daily Spend Ceiling** | **$0.00 USD** (Strict Zero Spend) | **$0.50 USD/day** | **$15.00 USD/day** |
| **Hourly Token Limit** | 50,000 tokens/hr | 250,000 tokens/hr | 2,000,000 tokens/hr |
| **Daily Token Limit** | 250,000 tokens/day | 2,000,000 tokens/day | 20,000,000 tokens/day |
| **Max Article Word Count** | 1,500 words | 3,000 words | 10,000 words (deep long-form) |
| **Concurrency Limit** | 1 request | 3 concurrent requests | 8 concurrent requests |
| **Cloud Run Sizing** | `min=0, max=1, 384Mi` RAM | `min=0, max=2, 512Mi` RAM | `min=0 (or 1), max=5, 1024Mi` RAM |

---

## 2. Using Profiles

### A. Environment Variable (`.env`)
Set the default profile for your node:
```bash
CREDENCE_PROFILE=free      # Or balanced, ultra
```

### B. Command-Line Interface (CLI)
```bash
# 1. List all available cost profiles and active state
poetry run credence profile list

# 2. Inspect detailed settings for a profile
poetry run credence profile show ultra

# 3. Run a one-off audit with a specific profile
poetry run credence audit https://example.com/breaking-news --profile=ultra

# 4. Launch FastMCP server with a specific profile
poetry run credence serve --transport sse --profile=free
```

### C. FastMCP 2.0 Client Overrides
Clients can specify an operational profile per tool call:
```json
{
  "name": "credence_check_url",
  "arguments": {
    "url": "https://example.com/article",
    "profile": "ultra"
  }
}
```

---

## 3. Circuit Breaker Behavior per Profile

1. **`FREE` Profile**:
   - If any API call incurs a positive non-zero cost or token limits (50k/hr) are exceeded, the circuit breaker immediately trips into `QUOTA_PRESERVED` mode, executing offline heuristics.
2. **`BALANCED` Profile**:
   - Normal operation uses $1,024$ thinking tokens. If the score is on the boundary ($12.0 - 18.0$) or citation grounding is $< 75\%$, it dynamically escalates thinking to $4,096$ tokens while staying under the $0.50/day spend limit.
3. **`ULTRA` Profile**:
   - Subagents operate with deep reasoning ($4,096 - 16,384$ tokens) and cross-reference multi-source claims against `gemini-1.5-pro`.
