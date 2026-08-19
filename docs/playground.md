---
title: Interactive Zero-Build Playgrounds
description: In-browser WebCrypto verification, 13-node mesh gossip simulator, epistemic
  text scanner, and consensus engine.
since_version: v1.11.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Interactive Zero-Build Playgrounds 🎮

Experience Credence's core mathematical models, cryptographic verification, epistemic text heuristics, and distributed consensus in real time directly inside your browser. All tools below run **100% client-side** using standard W3C Web APIs with **zero backend roundtrips and zero external dependencies**.

:::tabs
=== 🎛️ Client-Side Runtime Guarantees
| Guarantee | Mechanism | Specification |
| :--- | :--- | :--- |
| **Zero Backend Roundtrips** | 100% Client-Side Evaluation | W3C Standard WebCrypto (`crypto.subtle`), SVG & ES Modules |
| **Hermetic Privacy** | Zero Telemetry / Analytics | No data, tokens, or plaintext leaves your browser session |
| **Deterministic Math** | Bit-for-Bit Engine Equivalence | Identical SimHash-64, saturation curves & Ed25519 verification as the Python CLI |
:::

---

### Interactive Playground Directory

| Widget | Interactive Model | Core Web Standard |
| :--- | :--- | :--- |
| **1. 13-Node Mesh Gossip** | Watts-Strogatz epidemic diffusion & splits | SVG Canvas & DOM Event Animation |
| **2. SimHash-64 & Bit-Diff** | 64-bit locality-sensitive hashing | Bitwise XOR & 64-Tile Graphical Matrix |
| **3. Grounding Validator** | $G=1.00$ character-offset substring locator | Live DOM Highlight & Whitespace Collapser |
| **4. Saturation Calculator** | Exponential asymptotic score curve | Interactive SVG Calibration Curve Plot |
| **5. WebCrypto Verifier** | RFC 8785 Ed25519 signature checks | W3C `window.crypto.subtle` & Anti-Tamper |
| **6. Taxonomy Explorer** | Real-time fuzzy rule & domain filter | JSON Catalog Client Filter Chips |
| **7. Multi-Model Comparator** | Pareto frontier cost & thinking budget | Multi-Slider Token Pricing Model |
| **8. Feed Sifter Simulator** | 4-factor dynamic feed score ($F_j$) | Real-time Slider Formula Engine |
| **9. The Galileo Rule Consensus** | Domain Authority Weighted Median vs Sybils | Weighted Median & Histogram Engine |
| **10. Epistemic Text Scanner** | Live clickbait, fallacy & urgency auditor | Client-Side Regex Pattern Tokenizer |
| **11. ClaimReview & RFC 8785** | Google Fact-Check JSON-LD & envelope builder | Schema.org JSON & Canonical RFC 8785 |
| **12. Token Governor & Circuit Breaker** | 30% Headroom quota preservation meter | Real-time Headroom Gauge & Circuit Breaker |

> ⚡ **Looking for the Live Swarm Dashboard?** Visit the zero-build **[Credence Nexus Live Dashboard](https://credence.nexus/dashboard.html)** to inspect first-person node health, BitTorrent work-sharing compute savings, and category score breakdowns across the peer-to-peer network.

---

## 1. 13-Node Watts-Strogatz Mesh Gossip Simulator

Interact with a live Watts-Strogatz small-world network ($N=13, k=4, p=0.20$). Click any node to inspect its simulated identity and reputation score ($Q_i$), simulate multi-hop epidemic gossip diffusion, and test network split tolerance:

<div class="interactive-widget" id="mesh-simulator-widget">
  <div class="widget-toolbar">
    <button type="button" id="btn-broadcast-gossip" class="widget-btn primary">Broadcast Attestation from Node 1</button>
    <button type="button" id="btn-simulate-split" class="widget-btn">Simulate Barbell Network Split</button>
    <button type="button" id="btn-reset-mesh" class="widget-btn">Reset 13-Node Cluster</button>
  </div>

  <div class="mesh-visualizer-container">
    <svg id="mesh-svg" viewBox="0 0 600 400" class="mesh-svg-canvas" style="width: 100%; height: 320px;">
      <!-- Injected dynamically by app.js -->
    </svg>
  </div>

  <div id="mesh-node-inspector" class="node-inspector-card" style="display: none;">
    <div><strong>Selected: <span id="inspector-node-id" style="color: #38bdf8;">Node 1</span></strong> | Status: <span id="inspector-node-status" style="color: #4ade80;">Healthy Peer</span></div>
    <div>Node Quality (\(Q_i\)): <strong id="inspector-node-qi" style="color: #38bdf8;">0.92</strong> | Peer Links: <strong id="inspector-node-links">4 edges</strong></div>
  </div>

  <div id="mesh-event-log" class="widget-status idle">
    <span>Ready. Click "Broadcast Attestation from Node 1" or click any node circle to inspect.</span>
  </div>
</div>

---

## 2. SimHash-64 & Hamming Distance Bit-Diff Visualizer

Compare two text snippets to compute their 64-bit SimHash fingerprints, Hamming Distance ($D_H$), and inspect the exact bit flips across all 64 bits:

<div class="interactive-widget" id="simhash-calculator-widget">
  <div class="filter-chip-group">
    <button type="button" id="btn-preset-mirror" class="filter-chip active">Scenario: Syndicated Mirror (\(D_H \le 3\))</button>
    <button type="button" id="btn-preset-plagiarism" class="filter-chip">Scenario: Paraphrased Content (\(D_H = 6\))</button>
    <button type="button" id="btn-preset-distinct" class="filter-chip">Scenario: Distinct Article (\(D_H > 15\))</button>
  </div>

  <div class="widget-row">
    <div class="widget-col">
      <label class="widget-label">Article A (Original Text):</label>
      <textarea id="simhash-text-a" class="widget-textarea" style="height: 90px;">The international monetary conference reached a historic agreement today on cross-border liquidity standards.</textarea>
    </div>
    <div class="widget-col">
      <label class="widget-label">Article B (Mirror / Revision):</label>
      <textarea id="simhash-text-b" class="widget-textarea" style="height: 90px;">The international monetary conference reached a historic agreement today on cross-border liquidity standards. [Updated with comments]</textarea>
    </div>
  </div>

  <div class="widget-toolbar" style="margin-top: 1rem;">
    <button type="button" id="btn-calc-simhash" class="widget-btn primary">Compute 64-Bit SimHash &amp; Bit-Diff</button>
  </div>

  <div id="simhash-result-box" class="widget-result-box" style="margin-top: 1rem; text-align: left;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div class="widget-metric-title">Hamming Distance (\(D_H\))</div>
        <div id="simhash-dh-val" class="widget-score-big" style="font-size: 2.25rem;">--</div>
      </div>
      <div id="simhash-verdict-badge" class="verdict-tag reliable">AWAITING INPUT</div>
    </div>

    <div style="font-size: 0.85rem; margin-top: 0.5rem; color: #cbd5e1;">
      <div>Fingerprint A: <code id="simhash-fp-a" style="font-size: 0.75rem;">--</code></div>
      <div style="margin-top: 0.25rem;">Fingerprint B: <code id="simhash-fp-b" style="font-size: 0.75rem;">--</code></div>
    </div>

    <div style="margin-top: 0.85rem;">
      <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;">64-Bit Binary Differential (<span style="color: #10b981;">■ Match</span> / <span style="color: #ef4444;">■ Flip</span>)</div>
      <div id="simhash-bitdiff-grid" class="bit-diff-grid">
        <!-- 64 bit tiles injected dynamically -->
      </div>
    </div>
  </div>
</div>

---

## 3. Verbatim Quote Grounding Validator (\(G=1.00\))

Test character-offset substring matching and Unicode normalization. If an AI model hallucinates or paraphrases even a single word, the citation is rejected ($G=0.00$):

<div class="interactive-widget" id="grounding-tester-widget">
  <div class="filter-chip-group">
    <button type="button" id="btn-preset-verbatim" class="filter-chip active">Preset: Exact Verbatim Match (\(G=1.00\))</button>
    <button type="button" id="btn-preset-paraphrase" class="filter-chip">Preset: Hallucinated Paraphrase (\(G=0.00\))</button>
  </div>

  <label class="widget-label">Source DOM Prose Text:</label>
  <textarea id="grounding-source-text" class="widget-textarea" style="height: 75px;">The company reported revenue of $4.2 billion, but declined to provide second-quarter guidance due to supply chain headwinds.</textarea>

  <label class="widget-label" style="margin-top: 0.85rem;">Candidate Violation Quote to Verify:</label>
  <input type="text" id="grounding-quote-input" class="search-input" value="declined to provide second-quarter guidance">

  <div class="widget-toolbar" style="margin-top: 1rem;">
    <button type="button" id="btn-test-grounding" class="widget-btn primary">Validate Verbatim Grounding</button>
  </div>

  <label class="widget-label" style="margin-top: 0.85rem;">Live DOM Text Highlight Preview:</label>
  <div id="grounding-preview-display" class="grounding-preview-box">
    <!-- Live highlighted source text injected here -->
  </div>

  <div id="grounding-status" class="widget-status idle">
    <span>Click "Validate Verbatim Grounding" to calculate character offsets and precision score.</span>
  </div>
</div>

---

## 4. Calibrated Saturation Curve Calculator

Credence uses an exponential saturation curve to prevent score clipping and ensure severe violations compound non-linearly:

$$S_{\text{calibrated}} = 100 \times \left(1 - e^{-S_{\text{raw}} / 12}\right)$$

<div class="interactive-widget" id="saturation-calculator-widget">
  <div class="widget-row">
    <div class="widget-col">
      <label for="calc-violations" class="widget-label">Number of Violations: <span id="val-violations" class="widget-val">3</span></label>
      <input type="range" id="calc-violations" min="1" max="10" value="3" class="widget-slider">
      
      <label for="calc-severity" class="widget-label">Average Severity (1–5): <span id="val-severity" class="widget-val">3.0</span></label>
      <input type="range" id="calc-severity" min="1.0" max="5.0" step="0.5" value="3.0" class="widget-slider">
      
      <label for="calc-confidence" class="widget-label">Model Confidence (0–1.0): <span id="val-confidence" class="widget-val">0.90</span></label>
      <input type="range" id="calc-confidence" min="0.1" max="1.0" step="0.05" value="0.90" class="widget-slider">
    </div>

    <div class="widget-col widget-result-box">
      <div class="widget-metric-title">Calibrated Suspicion Score</div>
      <div id="calc-result-score" class="widget-score-big">48.6</div>
      <div id="calc-result-badge" class="verdict-tag mixed">MIXED / QUESTIONABLE</div>
      <div class="widget-submetrics">
        <div>Raw Score (\(S_{\text{raw}}\)): <strong id="calc-raw-score">8.10</strong></div>
        <div>Saturation: <strong id="calc-saturation-pct">48.6%</strong></div>
      </div>
    </div>
  </div>

  <div style="margin-top: 1.5rem; background: rgba(5, 10, 20, 0.8); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 0.75rem;">
    <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 0.25rem;">Live Asymptotic Saturation Plot (\(y = 100(1 - e^{-x/12})\))</div>
    <svg id="calc-curve-svg" viewBox="0 0 500 160" style="width: 100%; height: 160px;">
      <!-- Dynamic SVG Plot injected here -->
    </svg>
  </div>
</div>

---

## 5. In-Browser Ed25519 WebCrypto Verifier & Anti-Tamper Test

Verify cryptographically signed audit envelopes using standard W3C WebCrypto. Test how altering a single score value causes signature verification to fail instantly:

<div class="interactive-widget" id="webcrypto-verifier-widget">
  <div class="widget-toolbar">
    <button type="button" id="btn-load-sample" class="widget-btn">Load Valid Signed Attestation</button>
    <button type="button" id="btn-tamper-sample" class="widget-btn">Tamper Payload (Inject Fake Score)</button>
    <button type="button" id="btn-verify-crypto" class="widget-btn primary">Verify Signature In-Browser</button>
  </div>

  <textarea id="crypto-json-input" class="widget-textarea" placeholder="Paste signed JSON here..."></textarea>
  
  <div id="crypto-status" class="widget-status idle">
    <span>Ready to verify. Paste JSON or load sample above.</span>
  </div>
</div>

---

## 6. Live Namespaced Taxonomy Rule Explorer

Filter and inspect rules across the Society of Professional Journalists (SPJ), Internet Encyclopedia of Philosophy (IEP) Fallacies, Deceptive UI Patterns, and Medical claims:

<div class="interactive-widget" id="taxonomy-explorer-widget">
  <div class="filter-chip-group">
    <button type="button" id="chip-tax-all" class="filter-chip active">All Catalogs (<span id="count-tax-all">46</span>)</button>
    <button type="button" id="chip-tax-spj" class="filter-chip">SPJ Journalism (<span id="count-tax-spj">12</span>)</button>
    <button type="button" id="chip-tax-iep" class="filter-chip">IEP Fallacies (<span id="count-tax-iep">21</span>)</button>
    <button type="button" id="chip-tax-deceptive" class="filter-chip">Deceptive UI (<span id="count-tax-deceptive">9</span>)</button>
    <button type="button" id="chip-tax-domain" class="filter-chip">Domain Extensions (<span id="count-tax-domain">4</span>)</button>
  </div>

  <div class="taxonomy-controls-bar">
    <div style="flex: 1; min-width: 260px;">
      <input type="text" id="taxonomy-search-input" class="search-input" placeholder="Search rules by ID, keyword, cluster, or detection signal...">
    </div>
    <div style="display: flex; gap: 0.5rem; align-items: center;">
      <select id="taxonomy-severity-filter" class="widget-select" style="padding: 0.65rem 0.85rem; background: #020617; border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 6px; color: #f8fafc; font-size: 0.85rem;">
        <option value="ALL">All Severities</option>
        <option value="5">Sev 5 (Critical)</option>
        <option value="4">Sev 4 (High)</option>
        <option value="3">Sev 3 (Moderate)</option>
        <option value="2">Sev 2 (Minor)</option>
      </select>
    </div>
  </div>

  <div class="taxonomy-stats-bar">
    <div id="taxonomy-results-count" style="font-size: 0.85rem; color: var(--text-muted);">Showing <strong style="color: var(--accent-cyan);" id="tax-visible-count">46</strong> rules</div>
    <div style="font-size: 0.78rem; color: var(--text-muted);">Click <strong>Copy URI</strong> to copy canonical namespaced URI for CLI &amp; Prompts</div>
  </div>

  <div id="taxonomy-cards-container" class="taxonomy-cards-list">
    <!-- Injected via JavaScript -->
  </div>

  <div class="taxonomy-pagination-bar" id="taxonomy-pagination">
    <button type="button" id="tax-prev-btn" class="widget-btn" disabled>&larr; Previous</button>
    <span id="tax-page-indicator" style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600;">Page 1 of 6</span>
    <button type="button" id="tax-next-btn" class="widget-btn">Next &rarr;</button>
    <button type="button" id="tax-show-all-btn" class="widget-btn" style="margin-left: 0.5rem;">Show All</button>
  </div>
</div>

---

## 7. Multi-Model Cost, Latency & Sovereignty Comparator

Compare estimated monthly operational costs, latency (TTFT), and cloud sovereignty across different frontier APIs and local models with adjustable thinking token budgets:

<div class="interactive-widget" id="model-comparator-widget">
  <div class="widget-row">
    <div class="widget-col">
      <label for="comp-articles-slider" class="widget-label">Daily Audited Articles: <span id="comp-articles-val" class="widget-val">500</span></label>
      <input type="range" id="comp-articles-slider" min="10" max="2000" step="10" value="500" class="widget-slider">

      <label for="comp-length-slider" class="widget-label">Average Article Length (Words): <span id="comp-length-val" class="widget-val">1,500</span></label>
      <input type="range" id="comp-length-slider" min="500" max="5000" step="250" value="1500" class="widget-slider">

      <label for="comp-thinking-slider" class="widget-label">Thinking Token Budget / Audit: <span id="comp-thinking-val" class="widget-val">4,096 tokens</span></label>
      <input type="range" id="comp-thinking-slider" min="0" max="16384" step="1024" value="4096" class="widget-slider">
    </div>
  </div>

  <div class="model-cards-grid" id="model-cards-container" style="margin-top: 1.5rem;">
    <!-- Injected dynamically by app.js -->
  </div>
</div>

---

## 8. Zero-Trust Dynamic Feed Discovery & Quality (\(F_j\)) Simulator

Test how Credence dynamically evaluates candidate feeds, calculates Topic Entropy (\(H_{\text{topic}}\)), detects commercial astroturfing (The "Pizza Hut Test"), and determines whether a feed is approved for active mesh rotation:

$$F_j = 0.35 (1.0 - \bar{S}_j/100) + 0.25 G_j + 0.20 H_{\text{topic}} + 0.20 T_{\text{freshness}}$$

<div class="interactive-widget" id="feed-simulator-widget">
  <div class="filter-chip-group">
    <button type="button" id="btn-preset-investigative" class="filter-chip active">Preset: High-Entropy Investigative Feed</button>
    <button type="button" id="btn-preset-astroturf" class="filter-chip">Preset: Single-Topic Astroturfing Pivot (\(H < 0.30\))</button>
  </div>

  <div class="widget-row">
    <div class="widget-col">
      <label for="feed-suspicion-slider" class="widget-label">Average Suspicion (\(\bar{S}_j\)): <span id="feed-suspicion-val" class="widget-val">12.0</span> / 100</label>
      <input type="range" id="feed-suspicion-slider" min="0" max="100" step="1" value="12" class="widget-slider">

      <label for="feed-grounding-slider" class="widget-label">Verbatim Grounding Precision (\(G_j\)): <span id="feed-grounding-val" class="widget-val">95%</span></label>
      <input type="range" id="feed-grounding-slider" min="0" max="100" step="5" value="95" class="widget-slider">

      <label for="feed-entropy-slider" class="widget-label">Topic Entropy / Diversity (\(H_{\text{topic}}\)): <span id="feed-entropy-val" class="widget-val">0.85</span></label>
      <input type="range" id="feed-entropy-slider" min="0.0" max="1.0" step="0.05" value="0.85" class="widget-slider">

      <label for="feed-freshness-slider" class="widget-label">Cadence Freshness Index (\(T_{\text{freshness}}\)): <span id="feed-freshness-val" class="widget-val">0.90</span></label>
      <input type="range" id="feed-freshness-slider" min="0.1" max="1.0" step="0.05" value="0.90" class="widget-slider">
    </div>

    <div class="widget-col widget-result-box">
      <div class="widget-metric-title">Composite Feed Quality Score (\(F_j\))</div>
      <div id="feed-result-score" class="widget-score-big" style="color: #4ade80;">0.89</div>
      <div id="feed-result-badge" class="verdict-tag reliable">ACTIVE ROTATION (APPROVED)</div>
      <div class="widget-submetrics" style="margin-top: 1rem;">
        <div>Astroturfing Alert: <strong id="feed-astroturf-status" style="color: #4ade80;">NONE (Diverse Coverage)</strong></div>
        <div>Mesh Seeding: <strong style="color: #38bdf8;">ENABLED (0-Token Work-Sharing)</strong></div>
      </div>
    </div>
  </div>
</div>

---

## 9. "The Galileo Rule" Consensus Engine Simulator (Asymmetric Grounding)

Simulate how Credence defeats Byzantine Sybil cartel attacks. In standard democratic voting, 20 ungrounded bot nodes reporting $S=0.0$ would overpower 2 domain experts reporting fraud ($S=75.0$). Under **The Galileo Rule**, verified domain experts with 100% grounded citations ($G=1.00$) cannot be outlier-dismissed:

<div class="interactive-widget" id="galileo-consensus-widget">
  <div class="widget-toolbar">
    <button type="button" id="btn-toggle-galileo" class="widget-btn primary">Mode: Galileo Rule ON (Asymmetric Grounding)</button>
  </div>

  <div class="widget-row">
    <div class="widget-col">
      <label for="galileo-sybil-slider" class="widget-label">Sybil / Bot Nodes Reporting Score 0 (Ungrounded): <span id="galileo-sybil-val" class="widget-val">12 nodes</span></label>
      <input type="range" id="galileo-sybil-slider" min="1" max="25" value="12" class="widget-slider">

      <label for="galileo-expert-slider" class="widget-label">Verified Domain Authorities Reporting Score 75 (\(G=1.00\)): <span id="galileo-expert-val" class="widget-val">2 nodes</span></label>
      <input type="range" id="galileo-expert-slider" min="1" max="10" value="2" class="widget-slider">
    </div>

    <div class="widget-col widget-result-box">
      <div class="widget-metric-title">Resolved Consensus Score</div>
      <div id="galileo-consensus-score" class="widget-score-big" style="color: #fb923c;">75.0</div>
      <div id="galileo-verdict-badge" class="verdict-tag suspicious">SUSPICIOUS (GROUNDED EXPERTS UPHELD)</div>
      <div class="widget-submetrics" style="margin-top: 0.85rem;">
        <div>Cartel Status: <strong id="galileo-rule-status" style="color: #4ade80;">Sybil Attack Neutralized</strong></div>
      </div>
    </div>
  </div>

  <div style="margin-top: 1rem;">
    <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;">Consensus Attestation Distribution Histogram</div>
    <div id="galileo-histogram" class="consensus-histogram">
      <!-- Dynamic histogram bars injected here -->
    </div>
  </div>
</div>

---

## 10. Real-Time Epistemic Heuristic Text Scanner

Type or paste any headline, promotional copy, or news excerpt below. The client-side heuristic engine parses syntax patterns in real time to spot clickbait hooks, emotional superlatives, fake urgency, and weasel words:

<div class="interactive-widget" id="epistemic-scanner-widget">
  <div class="filter-chip-group">
    <button type="button" id="btn-scan-clickbait" class="filter-chip active">Sample: Clickbait Curiosi-Trap</button>
    <button type="button" id="btn-scan-urgency" class="filter-chip">Sample: Deceptive Urgency &amp; Superlatives</button>
    <button type="button" id="btn-scan-clean" class="filter-chip">Sample: Neutral Factual Reporting</button>
  </div>

  <label class="widget-label">Input Text to Scan:</label>
  <textarea id="scanner-text-input" class="widget-textarea" style="height: 80px;">Scientists are baffled by this shocking discovery! Everyone knows you won't believe what happens next. Act now before it's banned!</textarea>

  <div class="widget-row" style="margin-top: 1rem;">
    <div class="widget-col" style="flex: 2;">
      <label class="widget-label">Live Analyzed Syntax with Highlighted Violations:</label>
      <div id="scanner-highlight-output" class="scanner-highlight-pane">
        <!-- Live highlighted output with colored spans -->
      </div>
    </div>

    <div class="widget-col widget-result-box" style="flex: 1;">
      <div class="widget-metric-title">Heuristic Suspicion</div>
      <div id="scanner-heuristic-score" class="widget-score-big" style="color: #ef4444;">68.4</div>
      <div id="scanner-verdict-badge" class="verdict-tag suspicious">SUSPICIOUS (4 PATTERNS)</div>
      <div class="widget-submetrics" style="margin-top: 0.75rem;">
        <div>Detected: <strong id="scanner-rules-detected">4 triggers</strong></div>
      </div>
    </div>
  </div>
</div>

---

## 11. Schema.org `ClaimReview` & RFC 8785 Receipt Generator

Generate Google Search-ready Schema.org `ClaimReview` JSON-LD and deterministic RFC 8785 canonical signed envelopes for any fact-checked assertion:

<div class="interactive-widget" id="claimreview-generator-widget">
  <div class="widget-row">
    <div class="widget-col">
      <label class="widget-label">Claim Text Checked:</label>
      <input type="text" id="cr-claim-text" class="search-input" value="The Mediterranean Sea dried up completely last Tuesday.">

      <label class="widget-label" style="margin-top: 0.75rem;">Claim Author / Source:</label>
      <input type="text" id="cr-author-input" class="search-input" value="Anonymous Social Post">
    </div>

    <div class="widget-col">
      <label class="widget-label">Credence Fact-Check Verdict:</label>
      <select id="cr-verdict-select" class="search-input" style="height: 42px;">
        <option value="False">False / Flagrant Disinformation</option>
        <option value="Misleading">Misleading / Deceptive Framing</option>
        <option value="Satire">Satire / Parody</option>
        <option value="True">True / Factual Reporting</option>
      </select>

      <label class="widget-label" style="margin-top: 0.75rem;">Article Source URL:</label>
      <input type="text" id="cr-source-url" class="search-input" value="https://example.com/viral-post-109">
    </div>
  </div>

  <div class="widget-toolbar" style="margin-top: 1.25rem;">
    <button type="button" id="btn-tab-claimreview" class="widget-btn primary">Schema.org ClaimReview JSON-LD</button>
    <button type="button" id="btn-tab-rfc8785" class="widget-btn">RFC 8785 Canonical Envelope</button>
    <button type="button" id="btn-cr-copy" class="widget-btn">📋 Copy JSON</button>
    <button type="button" id="btn-cr-download" class="widget-btn">💾 Download .credence.json</button>
  </div>

  <div style="margin-top: 1rem; border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; background: #020617; overflow: hidden;">
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0.85rem; background: rgba(15, 23, 42, 0.9); border-bottom: 1px solid rgba(56, 189, 248, 0.15); font-size: 0.78rem; color: var(--text-muted);">
      <span id="cr-header-badge" style="font-weight: 600; color: #38bdf8;">Schema.org ClaimReview JSON-LD</span>
      <span style="font-family: var(--font-mono, monospace);">RFC 8785 Canonical Serialization</span>
    </div>
    <pre id="cr-json-output" style="margin: 0; padding: 0.85rem 1rem; color: #38bdf8; font-family: var(--font-mono, monospace); font-size: 0.82rem; line-height: 1.45; overflow-x: auto; max-height: 380px;"></pre>
  </div>
</div>

---

## 12. Token Governor & 30% Headroom Circuit Breaker Simulator

Simulate monthly API token burn and observe the automatic circuit breaker tripping into `QUOTA_PRESERVED` mode at 30% remaining headroom:

<div class="interactive-widget" id="token-governor-widget">
  <div class="widget-row">
    <div class="widget-col">
      <label for="gov-budget-slider" class="widget-label">Monthly Token Budget: <span id="gov-budget-val" class="widget-val">$15.00</span></label>
      <input type="range" id="gov-budget-slider" min="5" max="50" step="5" value="15" class="widget-slider">

      <label for="gov-burn-slider" class="widget-label">Current Monthly Spend: <span id="gov-burn-val" class="widget-val">$11.25</span></label>
      <input type="range" id="gov-burn-slider" min="0" max="50" step="0.25" value="11.25" class="widget-slider">
    </div>

    <div class="widget-col widget-result-box">
      <div class="widget-metric-title">Remaining Budget Headroom</div>
      <div id="gov-headroom-pct" class="widget-score-big" style="color: #facc15;">25.0%</div>
      <div id="gov-state-badge" class="verdict-tag mixed">QUOTA_PRESERVED (CIRCUIT TRIPPED)</div>
      <div class="widget-submetrics" style="margin-top: 0.75rem;">
        <div id="gov-status-desc">Mode: 100% Offline Structural Heuristics ($0.00 Spend)</div>
      </div>
    </div>
  </div>

  <div style="margin-top: 1.25rem;">
    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem;">
      <span>0% (Exhausted)</span>
      <span style="color: #ef4444; font-weight: 700;">30% Safety Trip Point</span>
      <span>100% (Full Budget)</span>
    </div>
    <div class="headroom-gauge-track">
      <div class="headroom-threshold-marker"></div>
      <div id="gov-headroom-fill" class="headroom-gauge-fill" style="width: 25%; background: #f59e0b;"></div>
    </div>
  </div>
</div>
