---
title: CLI Automation & Shell Scripting Guide
description: Advanced shell automation using JSON output, jq filtering, parallel batch
  processing with xargs, and CI/CD PR review gates.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

The **`credence` CLI** is built with rich formatting for human terminals and structured JSON streams for shell automation, CI/CD pipelines, and data processing.

```mermaid
flowchart LR
    A["Input Stream<br>(URLs / RSS / Text)"] --> B["credence audit --json"]
    B --> C{"Score Evaluation"}
    C -- "Score < 25.0 (Reliable)" --> D["Pass CI Gate (Exit 0)"]
    C -- "Score >= 50.0 (Flagged)" --> E["Block / Alert (Exit 1)"]
    B --> F["jq / xargs Automation"]
    F --> G["Slack Webhooks / JSON DB"]
```

### CLI Exit Codes & CI Behavior

| Exit Code | Classification | Meaning & Recommended CI Action |
| :--- | :--- | :--- |
| **`0`** | `RELIABLE / GROUNDED` | Suspicion score $< 25.0$, all citations verified. Pass PR. |
| **`1`** | `QUESTIONABLE / DECEPTIVE` | Suspicion score $\ge 50.0$, fallacies or deceptive patterns detected. Fail PR. |
| **`2`** | `OFFLINE HEURISTIC` | Evaluated under offline structural rules (quota preserved). |
| **`3`** | `INGESTION ERROR` | Network timeout, SSRF rejection, or invalid target format. |

> [!TIP]
> **Zero-Cost CI Runs**: Use `--profile FREE` in GitHub Actions and GitLab CI to run 100% offline structural heuristic audits in $< 0.1\text{s}$ at **$0.00 token cost**.

---

## 1. JSON Output & `jq` Filtering

Extract specific fields from an audit report using `--json`:

```bash
# Get the calibrated suspicion score
credence audit https://example.com/article --json | jq '.suspicion_score'
# Output: 42.5

# List all grounded violation quotes
credence audit https://example.com/article --json | jq -r '.violations[].quote'

# Extract the Ed25519 signature and evaluator key
credence audit https://example.com/article --json | jq '{evaluator: .evaluator_pubkey, sig: .signature_ed25519}'
```

---

## 2. Parallel Batch Processing with `xargs`

To audit an entire list of URLs in parallel using local multi-core concurrency:

```bash
# urls.txt contains 50 target links
cat urls.txt | xargs -n 1 -P 4 -I {} credence audit {} --profile FREE --quiet
```

---

## 3. GitHub Actions CI PR Review Gate

Add an epistemic check to pull requests modifying documentation or external citations:

```yaml
name: Epistemic Link Verification

on:
  pull_request:
    paths: ['docs/**', 'README.md']

jobs:
  verify-links:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Credence
        run: pip install credence

      - name: Audit Extracted URLs
        run: |
          # Extract all http links from markdown and audit
          grep -oP 'https?://[^\s\)]+' README.md | while read -r url; do
            score=$(credence audit "$url" --profile FREE --json | jq '.suspicion_score')
            echo "Audited $url: Score $score"
          done
```

---

## 4. Automated Feed Discovery & Sifter Management

Automate dynamic RSS/Atom discovery and run real-time background sifting:

```bash
# Autodiscover feed endpoints dynamically from a website
credence feed discover https://arstechnica.com

# Pre-flight forensic audit on a candidate feed
credence feed inspect https://example.com/rss.xml

# View live feed health rankings (F_j score, topic entropy, suspicion)
credence feed health

# Launch real-time background sifter daemon
credence sifter --interval 300 --profile balanced
```

---

## 5. Daily Morning Epistemic Digest Generation

Compile daily intelligence briefings for newsletters, Slack webhooks, or automated reports:

```bash
# Terminal high-contrast view
credence digest --format terminal

# Export to clean Markdown for static sites / newsletters
credence digest --format markdown --output /srv/web/morning_brief.md --hours 24

# Stream JSON for custom alerting pipes
credence digest --format json | jq '{clean: .clean_articles_count, flagged: .flagged_articles_count, tokens_saved: .estimated_tokens_saved}'
```
