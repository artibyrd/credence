---
title: 'Zero-Cloud Sovereign Operations: Local LLMs'
description: Running a 100% private, offline Credence node using local open-weights
  models with Ollama or vLLM on Mac Studio / RTX 4090.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Zero-Cloud Sovereign Operations: Local LLMs

Investigative journalists, corporate internal audit teams, and defense analysts often work with confidential whistleblower documents, unredacted legal filings, or trade secrets that **can never be transmitted to third-party cloud AI APIs**.

Credence supports **100% Zero-Cloud, Air-Gapped Local Inference** using open-weights models (such as **Llama 3.3 70B** or **Qwen 2.5 72B**) executed locally via **Ollama** or **vLLM**.

---

## 1. Hardware Requirements

| Hardware Configuration | Model Target | Inference Speed | Use Case |
|:---|:---|:---|:---|
| **Apple Mac Studio (M2/M3/M4 Max with 64GB+ RAM)** | Llama 3.3 70B (4-bit Q4_K_M) | ~25 tokens/sec | Desktop investigative workstation |
| **Workstation with NVIDIA RTX 4090 (24GB VRAM)** | Qwen 2.5 32B (Q4) or DeepSeek-R1-Distill-32B | ~45 tokens/sec | Fast newsroom desktop node |
| **Server with 2x RTX 3090 / A5000 (48GB VRAM)** | Llama 3.3 70B (AWQ / GPTQ) | ~35 tokens/sec | Multi-user local newsroom server |

---

## 2. Setting Up Ollama with Open-Weights Models

1. **Install Ollama**:
```bash
   curl -fsSL https://ollama.com/install.sh | sh
```

2. **Pull the Epistemic Audit Model**:
```bash
   # Llama 3.3 70B Instruct (Recommended for high nuance)
   ollama pull llama3.3:70b-instruct-q4_K_M
   
   # Or Qwen 2.5 32B for lower VRAM environments
   ollama pull qwen2.5:32b
```

3. **Verify Local Inference**:
```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "llama3.3:70b-instruct-q4_K_M",
     "prompt": "Explain the difference between formal and informal fallacies."
   }'
```

---

## 3. Configuring Credence for Local Inference

Configure your environment to route all evaluation requests to your local Ollama instance:

```bash
export CREDENCE_LLM_PROVIDER=ollama
export OLLAMA_HOST=http://localhost:11434
export CREDENCE_MODEL=llama3.3:70b-instruct-q4_K_M

# Run an audit completely offline
credence audit https://example.com/sensitive-investigation \
  --profile BALANCED
```

---

## 4. Total Air-Gap Isolation Guarantee

When running in this mode:
- **Zero Outbound LLM API Calls**: All embeddings, tokenization, and model inference occur in local GPU VRAM / Apple Unified Memory.
- **Local Ed25519 Custody**: Private keys never leave the local encrypted SQLite keystore.
- **100% Privacy Compliance**: Safe for GDPR, HIPAA, attorney-client privileged materials, and confidential journalist source protection.
