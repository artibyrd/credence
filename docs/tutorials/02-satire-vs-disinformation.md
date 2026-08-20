---
title: 'Tutorial 02: Poe''s Law & Satire Cloaking'
description: How Credence protects legitimate parody while stripping satire protection
  from cloaked disinformation under SPJ-1.6.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
sidebar:
  order: 2
---

# Tutorial 02: Poe's Law & Satire Cloaking

Explore how **Credence** handles the nuance between legitimate satire (like *The Onion*) and deceptive "satire-cloaked" disinformation that advances harmful medical or civic falsehoods.

---

## The Challenge: Poe's Law in Automated Systems

**Poe's Law** observes that without clear intent indicators, it is impossible to author an exaggeration so absurd that someone will not mistake it for a sincere statement. 

Adversaries exploit this by publishing dangerous falsehoods (e.g. fabricated election fraud or lethal health claims) behind tiny "satire" disclaimers in the footer to evade legal and platform accountability.

---

## 1. Legitimate Satire Detection

When Credence encounters legitimate satire (e.g., an article from *The Onion* or a site with explicit `SatiricalArticle` Schema.org markup):

```bash
credence audit https://theonion.com/example-satire-story
```

### The Result:
- **Structural Cue Recognized**: Credence extracts masthead cues and Schema.org metadata.
- **Score Neutralization**: Suspicion score is neutralized to **`0.00 / 100`** with `is_satire: true`.
- Honest parody is protected from automated penalties.

---

## 2. Satire Cloaking Override (`SPJ-1.6`)

When an article claims to be "satire" but contains **unfounded factual allegations regarding public health, financial fraud, or election results**:

```bash
credence audit https://deceptive-site.test/fake-vaccine-claim
```

### The Invariant in Action (Invariant 13 & 28):
- The `SPJ-1.6` (Cloaked Disinformation) specialist rule triggers.
- Satire immunity is **immediately stripped**.
- The suspicion score is penalized to **`90.0+ / 100`**, and the finding is flagged:
```text
  [SPJ-1.6] Satire Cloaking Hard-Override Triggered
  Finding: Unsubstantiated lethal medical allegation cannot be cloaked as satire.
  Satire Protection: DISABLED
```

---

## 3. Inspecting Satire Neutralization in the TUI

Launch `credence tui` to view how legitimate parody is visually represented in the terminal workstation:

![TUI Satire View](../../assets/tui/04-inspector-satire.svg)

* The top status banner prominently displays the cyan badge `[🎭 SATIRE / PARODY (Poe's Law Neutralized)]`.
* The executive summary confirms the neutralization rationale, explaining that legitimate exaggeration is not penalized with epistemic suspicion points.

