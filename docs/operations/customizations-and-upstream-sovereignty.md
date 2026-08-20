---
title: Managing Customizations vs. Core Upstream
description: Architectural blueprint for keeping the open-source Credence core clean,
  generic, and neutral while supporting hyper-local news monitoring, custom entity
  graphs, and sovereign organization deployments.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
---

# Managing Customizations vs. Core Upstream

When deploying **Credence** to monitor hyper-local news outlets, corporate trade publications, or regional municipal councils, operators often need custom entity relationships, localized RSS feeds, and specialized conflict-of-interest tracking.

However, an essential invariant of the Credence open-source project is that **the upstream core codebase must remain strictly generic, neutral, and uncustomized**. 

This document details the architectural boundaries and operational runbooks for maintaining total separation between **Upstream Core**, **Local Node State**, **Configuration Overlays**, and **Sovereign Production Deployments**.

---

## 🏛️ The 4-Tier Customization Architecture

Credence enforces clean separation across four distinct operational layers:

```mermaid
graph TD
    subgraph Core ["1. Core Upstream Repo (Public & Universal)"]
        Engine["Scoring & Evaluation Pipeline"]
        UnivTax["Universal Taxonomies & Subjects<br>(e.g. municipal_governance.yaml)"]
        GlobalPresets["Global Wire Presets<br>(AP, Reuters, ProPublica, Nature)"]
    end

    subgraph State ["2. Runtime Database State (Local & Ephemeral)"]
        LocalDB[("data/credence.db (Gitignored)<br>FeedSubscriptionRecord & Audits")]
        CLIAdd["CLI: credence feed add & audit"]
        CLIAdd --> LocalDB
    end

    subgraph Config ["3. Local Configuration Overlays (config/)"]
        CustomFeeds["config/feeds.local.yaml"]
        EntityGraph["config/entities/hometown.local.yaml<br>(Publisher / Council Conflict Graph)"]
    end

    subgraph Deploy ["4. Sovereign Deployments (credence init-org)"]
        InitOrg["Independent Org Workspace<br>(Terraform, Cloud Run, Cloudflare)"]
        CloudSeeds[("GCS Seed Bucket / peers.json")]
        InitOrg --> CloudSeeds
    end

    Core --> LocalDB
    Config --> Engine
    Core -.->|Upstream Dependency| InitOrg
```

### Customization Layer Separation Matrix

| Layer | Files & Paths | Git Status | Upstream Commit Policy |
| :--- | :--- | :--- | :--- |
| **1. Upstream Core** | `credence/`, `taxonomies/*.yaml` | Tracked in Git | ✅ Merged via PR (Universal standards only) |
| **2. Runtime State** | `data/credence.db`, `data/logs/` | **.gitignored** | ❌ Never committed (Local SQLite database) |
| **3. Config Overlays** | `config/*.local.yaml` | **.gitignored** | ❌ Never committed (Local town/entity graphs) |
| **4. Sovereign Orgs** | `/srv/credence-org/` | Independent Repo | 🏢 Separate sovereign git repository |

> [!WARNING]
> **Strict Upstream Neutrality**: Never commit hyper-local news outlets, local politician entity maps, or proprietary credentials to the core `credence` repository. Always use local overlays (`*.local.yaml`) or sovereign organization workspaces.

---

## 🔍 Layer Breakdown & Boundaries

### 1. Upstream Core Codebase (`credence/`)
* **What belongs here:**
  * ✅ Universal scoring math (Shannon entropy, top-token concentration, 5-factor node quality).
  * ✅ FastMCP 2.0 servers and tool definitions.
  * ✅ Generic subject domains and taxonomy catalog definitions that apply globally (e.g. `journalism.news.municipal_governance`, which defines universal concepts like *city council*, *zoning ordinances*, *mayoral decrees*, and *conflict-of-interest disclosures*).
  * ✅ Baseline global reference wire presets (AP, Reuters, ProPublica, Nature).
* **What NEVER belongs here:**
  * ❌ Specific hometown news outlets (e.g. `inmaricopa.com`, `buckeye-news.local`).
  * ❌ Specific local councilmember names or personal entity mappings.
  * ❌ Deployment-specific Cloudflare API keys or proprietary database credentials.

---

### 2. Runtime Node Database State (`data/credence.db`)
Every Credence node maintains its own local SQLite / AsyncSession database in `data/credence.db`, which is strictly excluded from version control via `.gitignore`.

* **Adding Local Feeds:**
```bash
  # Subscribe your local node to your town's local paper
  credence feed add https://inmaricopa.com/feed/ \
    --title "InMaricopa Local News" \
    --subject "journalism.news.municipal_governance" \
    --priority 1
```
* **Inspecting Local Subscriptions:**
```bash
  credence feed list
```
* All audit records, local cache entries, and syndicated subscriptions stay strictly isolated on your local workstation without touching Git.

---

### 3. Local Configuration Overlays (`config/`)
For deep conflict-of-interest audits, Credence allows operators to provide local entity knowledge graphs without modifying core catalog files.

#### Defining Local Entity Overlays (`config/entities/*.local.yaml`)
Create an uncommitted local overlay in `config/entities/inmaricopa.local.yaml`:

```yaml
# config/entities/inmaricopa.local.yaml (Gitignored)
domain: "inmaricopa.com"
publisher_entity: "InMaricopa LLC"
principals:
  - name: "Local Councilmember / Publisher"
    role: "Owner & Advertising Director"
    public_offices:
      - title: "Councilmember"
        entity: "City Council"
        jurisdiction: "City of Maricopa, AZ"
    related_interests:
      - "Municipal economic development subsidies"
      - "City advertising contracts"
mandatory_disclosure_rules:
  - "SPJ_ETHICS:TRANSPARENCY/undisclosed_governance_coi@1.0.0"
```

Credence automatically merges local entity definitions at runtime:
1. Built-in generic entities: `credence/subjects/entities/`
2. Local environment directory: `CREDENCE_ENTITIES_DIR` or `./config/entities/`

---

### 4. Sovereign Organization Deployments (`credence init-org`)
When launching a dedicated public watch organization (e.g., a statewide investigative consortium or a municipal accountability portal), do not fork or modify the core application repo. Instead, scaffold an independent sovereign organization:

```bash
credence init-org \
  --name "Maricopa Civic Integrity Watch" \
  --domain "maricopawatch.org" \
  --output "./maricopa-watch" \
  --email "security@maricopawatch.org"
```

This generates an isolated organization directory containing:
* **`terraform/`**: Multi-cloud Terraform templates (GCP Cloud Run + Cloudflare) wired to your domain.
* **`peers.json`**: Network root cryptographic seed manifest.
* **`config/feeds.yaml`**: Your custom organization-wide preset feed subscriptions.
* **`pyproject.toml`**: Points to `credence` as an upstream dependency package.

---

## 📋 Summary of Invariants

| Layer | Storage Location | Tracked in Git? | Scope |
| :--- | :--- | :---: | :--- |
| **Upstream Core** | `credence/` | **Yes** | Universal algorithms, math, & generic schemas |
| **Node State** | `data/credence.db` | **No** (`.gitignore`) | Per-node local subscriptions & cache |
| **Config Overlays** | `config/*.local.yaml` | **No** (`.gitignore`) | Hyper-local entity graphs & custom API keys |
| **Sovereign Org** | `./my-org-workspace` | **Separate Repo** | White-label production deployment & infrastructure |

By adhering to this four-tier boundary, you can turn Credence loose on any local news publication with full conflict-of-interest auditing while keeping the public codebase pure, generic, and sovereign.
