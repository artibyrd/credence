---
title: 'ADR: Why Gemini 3.7 Flash as Default Engine'
description: Architectural Decision Record explaining the technical, mathematical,
  and economic rationale behind choosing Gemini 3.7 Flash.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# ADR: Why Gemini 3.7 Flash as Default Reference Engine

When designing an open epistemic evaluation engine intended to run across thousands of federated nodes, **inference economics** and **thinking token density** dictate the viability of the entire network.

This Architectural Decision Record (ADR) documents the reasons why **Google Gemini 3.7 Flash** (configured with a **4,096 thinking token budget**) was selected as the canonical reference default engine, and outlines explicit criteria for alternative providers.

---

## 1. Context & Core Constraints

Epistemic auditing is computationally intensive. A single webpage audit requires:
1. Ingesting full-page rendered DOM text (2,000 to 15,000 tokens).
2. Cross-referencing against 50+ itemized taxonomy rules across journalistic ethics, cognitive fallacies, and deceptive UI patterns.
3. Conducting multi-step chain-of-thought syllogistic deduction (1,024 to 16,384 thinking tokens).
4. Verifying exact character offset grounding ($G = 1.0$) against raw DOM trees.

If each audit costs $\$0.10 \dots \$0.50$, running a 500-article daily news feed would cost **$\$1,500 \dots \$7,500$ per month per node**, making decentralized mesh participation economically impossible for independent journalists, academics, and homelab operators.

---

## 2. Quantitative Model Comparison Matrix

| Evaluation Metric | **Google Gemini 3.7 Flash** *(Selected Default)* | **Anthropic Claude 3.7 Sonnet** | **OpenAI GPT-4o** | **DeepSeek-R1 (API)** | **Local Llama 3.3 70B (Ollama)** |
|:---|:---|:---|:---|:---|:---|
| **Input Price (per 1M tokens)** | **$0.075** | $3.00 | $2.50 | $0.55 | **$0.00** (Hardware power) |
| **Output / Thinking Price (per 1M)** | **$0.30** | $15.00 | $10.00 | $2.19 | **$0.00** (Hardware power) |
| **Context Window** | **1,048,576 tokens** | 200,000 tokens | 128,000 tokens | 64,000 tokens | 128,000 tokens |
| **Thinking Budget Control** | **Dynamic (0 to 65,536)** | Dynamic (1,024 to 64,000) | Static o-series | Continuous | Model-dependent |
| **Time to First Token (TTFT)** | **<450 ms** | ~1,200 ms | ~900 ms | ~2,500 ms | ~800 ms (local GPU) |
| **Cost for 500 Audits/Day** | **~$13.85 / month** | ~$480 / month | ~$360 / month | ~$92 / month | **~$4 / month** (Electricity) |

---

## 3. The 4k Thinking Token Pareto Invariant

In accordance with our live empirical benchmarks across the Golden 12 fixture suite:
* **The 4k Sweet Spot**: `gemini-3.7-flash` with a **4,096 thinking token budget** captures 100% citation grounding ($G=1.0$) and Poe's Law satire neutralization at **$0.34–$0.68 per 1k audits** and **2.4s–5.1s latency**.
* **Pro Model Penalty**: Flagship Pro models cost 30x more ($18.29 per 1k audits) and suffer from over-analysis penalties ($32.6\text{s}$ latency), triggering false alarms on human irony.

---

## 4. Key Decision Drivers

1. **The $15/Month Budget Invariant**: Gemini 3.7 Flash allows a full-time seed node to evaluate **500+ daily articles** while staying well under the \$15.00/month Cloud Run budget ceiling.
2. **Thinking Density Without Latency Penalties**: Gemini 3.7 Flash executes 1,024 to 4,096 thinking tokens in 2.4s to 5.1s, enabling near-instant CLI and FastMCP response times.
3. **Massive Context Headroom**: With a 1M+ token window, Credence can ingest massive 100-page regulatory filings, scientific papers, and raw DOM trees without chunking or context fragmentation.

## 5. When You Should Switch Providers

| Scenario / Constraint | Recommended Provider | Why |
|:---|:---|:---|
| **Classified / Sensitive Intelligence** | **Local Ollama (Llama 3.3 70B)** | 100% air-gapped; zero data leaves your local RAM/VRAM. |
| **Deep Legal & Philosophical Nuance** | **Claude 3.7 Sonnet (Thinking)** | Unmatched subtlety in identifying rhetoric and structural straw men. |
| **Enterprise Azure/OpenAI Existing Credits** | **OpenAI GPT-4o / o3-mini** | Direct consumption of existing enterprise volume agreements. |

---

## 6. Official Model References & Benchmark Specifications

### 📚 Official Model Provider Documentation
* **Google Gemini**: [Gemini 3.7 Flash Thinking Overview](https://ai.google.dev/gemini-api/docs/thinking) &bull; [Google AI Pricing Calculator](https://ai.google.dev/pricing)
* **Anthropic**: [Claude Extended Thinking Architecture](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking) &bull; [Claude 3.7 Sonnet Model Card](https://www.anthropic.com/news/claude-3-7-sonnet)
* **OpenAI**: [OpenAI Platform Models & Reasoning](https://platform.openai.com/docs/models) &bull; [OpenAI API Pricing](https://openai.com/api/pricing/)
* **DeepSeek**: [DeepSeek-R1 Reasoning Repository](https://github.com/deepseek-ai/DeepSeek-R1)
* **Ollama**: [Ollama Local LLM Architecture](https://ollama.com/) &bull; [Llama 3.3 70B Quantized Weights](https://ollama.com/library/llama3.3)

### 🔗 Related Epistemic Benchmarks in Credence
* 📊 [Cross-Model Pareto Benchmark: Gemini vs Claude vs GPT-4o vs DeepSeek](../protocols/cross-model-pareto-benchmark.md)
* 🎯 [Golden 12 Benchmark Suite & Standardized Rubrics](../protocols/benchmark-suite.md)
* 🛡️ [Token Safety Governor & 30% Headroom Circuit Breakers](../protocols/token-governor.md)
* 🔌 [Multi-Model Provider Adapters Implementation Guide](multi-model-adapters.md)
* 🔒 [Zero-Cloud Sovereign Local LLMs Guide](local-llm-airgap.md)
* 💰 [Cost Profiles & Token Economics Matrix](../protocols/token-governor.md)

