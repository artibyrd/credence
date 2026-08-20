---
title: 'Antigravity Pair-Programming: Planning Mode, Background Tasks, & Mk1 Eyeball'
description: How human-agent pair programming with Google Antigravity accelerates
  complex software engineering through planning mode, asynchronous background tasks,
  and human gating.
since_version: v1.0.0
verified_version: v1.15.0
last_verified: '2026-08-19'
tags:
- antigravity
- pair-programming
- agentic-workflow
- planning-mode
- subagents
interfaces:
- CLI
- FastMCP 2.0
- Python SDK
invariants:
- 1
- 4
- 6
- 18
difficulty: Intermediate
read_time: 7 min
---

# Antigravity Pair-Programming: Planning Mode, Background Tasks, & Mk1 Eyeball

Explore the operational methodology developed during the creation of Credence using **Google Antigravity (AGY)**—combining rigorous planning mode, non-blocking asynchronous task orchestration, and human-in-the-loop review ("Mk1 Eyeball").

```mermaid
flowchart TD
    User["Human Operator Request"] --> Research["1. Research Phase<br/>(Read-only tools & static analysis)"]
    Research --> Plan["2. Planning Mode<br/>(implementation_plan.md artifact)"]
    Plan --> Gate["3. 'Mk1 Eyeball' Human Review Gate<br/>(Explicit approval required)"]
    Gate -->|Approved| Exec["4. Autonomous Parallel Execution<br/>(Subagents & background tasks)"]
    Exec --> Verify["5. Hermetic Verification<br/>(Playwright, pytest, static audits)"]
    Verify --> Walkthrough["6. Walkthrough Artifact<br/>(walkthrough.md + visual screenshots)"]
```

> [!IMPORTANT]
> **[Invariant 6: Human Review Before Commits ("Mk1 Eyeball")](../invariants.md#invariant-6)**: Agents must never execute `git commit` or apply infrastructure changes autonomously without presenting live verification results for human approval first.

---

## 1. The Planning Mode Design Pattern

Complex features and architectural refactors should never be written blindly. When a task involves architectural updates or multi-step changes:

1. **Research First**: Explore codebase dependencies without modifying code files.
2. **Author Implementation Plan Artifact**: Create `implementation_plan.md` with:
   - User Review Required items highlighted with GitHub alerts.
   - Exact file-by-file changes (`[MODIFY]`, `[NEW]`, `[DELETE]`).
   - Automated and manual verification plans.
   - Set `RequestFeedback: true` to prompt human review in the IDE.
3. **Wait for Approval**: Execution is blocked until the operator clicks **Proceed**.

---

## 2. Non-Blocking Task Execution & Reactive Messaging

Traditional agent loops frequently fail due to poll-loop timeouts or freezing terminal windows while long tests run. Antigravity introduces asynchronous task backgrounding:

:::tabs
=== Background Command Launch
```bash
# Long-running Playwright browser suite launched asynchronously
pytest tests/test_docs_rendering.py -v
# Returns task ID: task-610 immediately without blocking agent context
```

=== Reactive Notification
```json
{
  "sender": "task-610",
  "priority": "MESSAGE_PRIORITY_HIGH",
  "content": "Task completed: 11 passed in 18.88s"
}
```
:::

```mermaid
sequenceDiagram
    participant Agent as Antigravity Agent
    participant Task as Background Worker
    participant IDE as Developer IDE
    
    Agent->>Task: launch_command(pytest test_docs_rendering.py)
    Task-->>Agent: Returns Task ID (task-610)
    Agent-->>IDE: Update status (waiting asynchronously)
    Task->>Task: Executes Playwright Chromium tests (18s)
    Task-->>Agent: Reactive Wakeup Message (11 passed)
    Agent->>IDE: Present Walkthrough & Screenshots
```

---

## 3. Subagent Delegation: Research vs Coding

For broad surveys of large codebases, Antigravity delegates exploration to specialized subagents:

| Agent Type | Capabilities | Typical Use Cases |
| :--- | :--- | :--- |
| **`research`** | Read-only tools, web search, file view | Deep taxonomy searches, dependency audits |
| **`self`** | Inherited tools, edit, write, run | Multi-repo sync, release coordination |
| **`cortex`** | Core planner, artifact authoring | Implementation plans, walkthroughs, review |

> [!TIP]
> Use read-only `research` subagents when auditing large codebases to prevent polluting the main agent's working context memory.
