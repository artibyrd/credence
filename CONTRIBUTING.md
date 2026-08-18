# Contributing to Credence

Welcome to the **Credence** open-source project! We are building an autonomous epistemic evaluation engine, FastMCP server, and decentralized trust network to verify claims and protect AI agents from deceptive web content.

We welcome contributions from developers, researchers, cryptographers, and journalists of all backgrounds.

---

## 1. Cardinal Engineering Principles & Invariants

Credence is governed by **31 Formal Project Invariants** documented in [📘 `docs/agent-invariants.md`](docs/agent-invariants.md). Every contributor and pull request must strictly uphold these engineering standards:

1. **Hermetic Testing Invariant**: The default test suite (`tests/`) must execute 100% offline and network-free in under **65 seconds**. Never make external network calls in unit tests. Use `sqlite+aiosqlite:///:memory:` and static fixtures.
2. **Deterministic RFC 8785 JSON & Ed25519 Custody**: Attestations must use canonical JSON serialization (RFC 8785) with UTC timestamps for cross-language bit-for-bit parity with browser Web Cryptography API (`window.crypto.subtle`).
3. **Universal 4-Layer Feature Parity**: All major epistemic and mesh capabilities must maintain synchronous feature parity across:
   - **CLI** (`credence`)
   - **FastMCP 2.0** (`credence_` tools & `credence://` resources)
   - **Textual TUI** (`credence tui`)
   - **Zero-Build Web UI** (`web/`)
4. **Human Review Before Commits ("Mk1 Eyeball")**: Automated agents and contributors must never execute `git commit` automatically without human inspection and verification passes.
5. **Red Team Hardening & Protocol Defense**: Reject Billion Laughs XML entity expansion (`safe_parse_xml`), isolate external LLM prompts in `<untrusted_source_text>` containers, and enforce token-bucket rate limits on FastMCP and P2P WebSocket relays.

---

## 2. Quickstart Development Setup

### Prerequisites
- Python `>=3.12, <3.13`
- [Poetry](https://python-poetry.org/)
- [Just](https://github.com/casey/just) task runner
- Terraform `>=1.5.0` (for infrastructure validation)

### Setup Commands
```bash
# Clone the repository
git clone https://github.com/artibyrd/credence.git
cd credence

# Install dependencies and Playwright headless Chromium
just setup
```

---

## 3. Standard Development Workflows (`Justfile`)

We use `just` recipes to standardize development and CI execution:

| Command | Description |
| :--- | :--- |
| `just test` | Run fast, hermetic unit test suite (<65s). |
| `just test-e2e-mock` | Run hermetic offline mock 4-domain integration test. |
| `just lint` | Run `ruff check`, `ruff format --check`, and `mypy credence tests`. |
| `just format` | Autoformat code with Ruff. |
| `just tf-validate` | Validate Terraform configurations for GCP and Cloudflare. |
| `just tui` | Launch interactive Textual terminal dashboard. |
| `just serve-sse` | Launch FastMCP 2.0 server in SSE mode on port 8000. |
| `just mesh-cluster-up` | Launch local 13-node Watts-Strogatz P2P mesh cluster. |
| `just benchmark` | Execute Golden 12 epistemic cross-profile benchmark suite. |

---

## 4. Submitting a Pull Request

1. **Fork and Branch**: Create a feature branch with a descriptive name (e.g. `feat/sybil-mitigation` or `fix/feed-date-parsing`).
2. **Write Hermetic Tests**: Add comprehensive unit tests in `tests/` covering positive and negative cases.
3. **Verify Locally**: Ensure all tests and linters pass:
   ```bash
   just format && just lint && just test && just tf-validate
   ```
4. **Open a PR**: Submit a pull request against the `main` branch using our [PR Template](.github/PULL_REQUEST_TEMPLATE.md). Our automated GitHub Actions CI will run lint and test gates on your PR.

---

## 5. Community & Code of Conduct

All contributors are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) (Contributor Covenant v2.1).
