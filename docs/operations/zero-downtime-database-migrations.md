---
title: 'Operational Guide: Zero-Downtime Database Migrations'
description: SRE runbook for executing backward-compatible database schema migrations with zero downtime on Cloud Run.
since_version: v1.17.0
verified_version: v1.21.1
last_verified: '2026-08-19'
---

# Operational Guide: Zero-Downtime Database Migrations

Running zero-downtime schema migrations across auto-scaling Cloud Run containers requires strict adherence to backward-compatible schema evolutions.

---

## 1. The 4-Phase Zero-Downtime Migration Architecture

```mermaid
flowchart TD
    subgraph Phase1 ["Phase 1: Expand (Non-Destructive DDL)"]
        DDL["Apply Additive Migration<br/>• ALTER TABLE ... ADD COLUMN ... DEFAULT ...<br/>• PRAGMA user_version = N+1"]
        WAL[("SQLite WAL Store<br/>Concurrent Readers & Writers")]
        DDL --> WAL
    end

    subgraph Phase2 ["Phase 2: Deploy & Dual-Write Revision"]
        RevOld["Revision N (Legacy Active)<br/>Reads/Writes old & new schema"]
        RevNew["Revision N+1 (Canary Deploy)<br/>Direct Virtualenv + Startup Boost"]
        Traffic{"Cloud Run Traffic Split<br/>95% Old / 5% Canary"}
        Traffic --> RevOld
        Traffic --> RevNew
        RevOld & RevNew --> WAL
    end

    subgraph Phase3 ["Phase 3: Traffic Shift & Gate"]
        Health{"Aggressive /health Probe<br/>Latencies &lt; 150ms?"}
        RevNew --> Health
        Health -- "Healthy" --> FullCut["100% Traffic Shift to Revision N+1"]
        Health -- "5xx / Latency Spill" --> Rollback["Zero-Downtime Rollback<br/>(just gcp rollback)"]
    end

    subgraph Phase4 ["Phase 4: Contract (7-Day Soak)"]
        FullCut --> Soak["7-Day Deprecation Soak<br/>(All Revision N instances terminated)"]
        Soak --> Drop["Drop Legacy Columns & Views<br/>(Vacuum & WAL Checkpoint)"]
    end

    classDef darkSlate fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef highlight fill:#1e293b,stroke:#22c55e,stroke-width:2px,color:#f8fafc;
    classDef danger fill:#1e293b,stroke:#ef4444,stroke-width:2px,color:#f8fafc;
    class Phase1,Phase2,Phase4,DDL,WAL,RevOld,RevNew,Traffic,Soak,Drop darkSlate;
    class Health,FullCut highlight;
    class Rollback danger;
```

1. **Phase 1: Expand**: Apply additive non-destructive DDL (`ALTER TABLE ... ADD COLUMN ... DEFAULT ...`).
2. **Phase 2: Migrate**: Deploy new application container revisions running `credence serve`.
3. **Phase 3: Contract**: Drop legacy columns only after all older container revisions have rolled off traffic.
