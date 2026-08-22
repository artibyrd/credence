# ==============================================================================
# 2. Testing & Quality Assurance [core: test & quality]
# ==============================================================================

# Run targeted test suites (unit, all, mock, live, e2e, docs, docker)
test suite="unit" extra="": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{suite}}" in
        unit)
            poetry run pytest tests/ -m "unit" --durations=10 {{extra}}
            ;;
        all)
            poetry run pytest tests/ -n auto --durations=10 {{extra}}
            ;;
        mock|e2e-mock)
            poetry run pytest tests/e2e/test_mock_e2e.py -v {{extra}}
            ;;
        live)
            CREDENCE_LIVE_TESTS=1 poetry run pytest tests/e2e/test_live_rotating_suite.py -v -m e2e -s {{extra}}
            ;;
        e2e)
            CREDENCE_LIVE_TESTS=1 poetry run pytest tests/e2e/ -v -m e2e {{extra}}
            ;;
        docs)
            poetry run pytest tests/governance/test_docs_integrity.py -v {{extra}}
            ;;
        docker)
            docker compose run --rm credence poetry run pytest tests/ {{extra}}
            ;;
        *)
            echo "❌ Unknown test suite '{{suite}}'. Valid options: unit, all, mock, live, e2e, docs, docker."
            exit 1
            ;;
    esac

# Run static linting and type analysis across the codebase
lint: (preflight "poetry")
    poetry run ruff check .
    poetry run ruff format --check .
    poetry run mypy credence tests

# Autoformat code with Ruff
format: (preflight "poetry")
    poetry run ruff check --fix .
    poetry run ruff format .

# Comprehensive pre-commit / pre-push QA verification gate (<20s)
check:
    @echo "=== [1/5] Preflight Toolchain Verification ==="
    @just preflight all
    @echo ""
    @echo "=== [2/5] Linting & Static Analysis ==="
    @just lint
    @echo ""
    @echo "=== [3/5] Hermetic Unit & Integrity Pytest Gauntlet ==="
    @just test unit
    @echo ""
    @echo "=== [4/5] Terraform Multi-Cloud Validation ==="
    @just tf validate
    @echo ""
    @echo "=== [5/5] Declarative Antigravity Workspace Health ==="
    @just agent-check
    @echo ""
    @echo -e "\033[1;32m🎉 Complete QA Verification Passed Cleanly!\033[0m"
    @echo -e "\033[1;36m💡 NEXT STEP: If working on a feature branch, run 'just pr create <title>' to stage PRs across the triad and deploy to Cloud Run Dev.\033[0m"

# Verify Antigravity declarative workspace configuration, skills schema, and prompt economy
agent-check:
    @echo "=== Credence Antigravity Declarative Health Check ==="
    @test -f ../AGENTS.md && echo "✅ Universal root AGENTS.md verified." || (echo "❌ Missing root AGENTS.md"; exit 1)
    @test -f ../.agents/skills.json && echo "✅ Declarative .agents/skills.json verified." || (echo "❌ Missing .agents/skills.json"; exit 1)
    @test -d ../credence-agent/.agents/skills && echo "✅ Native skills repository verified." || (echo "❌ Missing credence-agent skills"; exit 1)
    @python3 ../credence-agent/scripts/lint_skills.py
    @python3 ../credence-agent/scripts/audit_demotions.py
    @echo -e "\033[1;32m✅ Declarative Antigravity Workspace & Invariant Engine Verified Cleanly!\033[0m"

# Audit skills schema, frontmatter, and token economy
audit-skills:
    @python3 ../credence-agent/scripts/lint_skills.py

# Audit invariant demotion candidates and token savings
audit-demotions:
    @python3 ../credence-agent/scripts/audit_demotions.py
