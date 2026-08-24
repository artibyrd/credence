# ==============================================================================
# 2. Testing, Static Analysis & Invariant Quality Gates [core: quality & test]
# ==============================================================================

# Run in-memory hermetic unit test gauntlet (<35s, 100% offline, $0.00 tokens)
[group('core: test')]
test-unit extra="": (preflight "poetry")
    poetry run pytest tests/ -m "unit" --durations=10 {{extra}}
    @echo -e "\033[1;32m✅ Hermetic unit tests passed cleanly.\033[0m"
    @echo -e "\033[1;36m💡 NEXT STEP: Run 'just check' for full multi-plane pre-commit validation.\033[0m"

alias test := test-unit
alias test-e2e := test-mock

# Run documentation integrity, frontmatter, parity, and living canon test suite
[group('core: test')]
test-docs extra="": (preflight "poetry")
    poetry run pytest tests/governance/test_docs_integrity.py -v {{extra}}
    @echo -e "\033[1;32m✅ Documentation & living canon integrity verified.\033[0m"

# Run mock end-to-end integration tests
[group('core: test')]
test-mock extra="": (preflight "poetry")
    poetry run pytest tests/e2e/test_mock_e2e.py -v {{extra}}
    @echo -e "\033[1;32m✅ Mock E2E integration tests passed.\033[0m"

# Run live rotating public web syndication and extraction tests
[group('core: test')]
[env('CREDENCE_LIVE_TESTS', '1')]
test-live extra="": (preflight "poetry")
    poetry run pytest tests/e2e/test_live_rotating_suite.py -v -m e2e -s {{extra}}
    @echo -e "\033[1;32m✅ Live rotating E2E suite passed.\033[0m"

# Run full parallel test suite across all available cores
[group('core: test')]
test-all extra="": (preflight "poetry")
    poetry run pytest tests/ -n auto --durations=10 {{extra}}
    @echo -e "\033[1;32m✅ Complete test suite passed.\033[0m"

# Run test suite inside isolated Docker container
[group('core: test')]
test-docker extra="": (preflight "docker")
    docker compose run --rm credence poetry run pytest tests/ {{extra}}
    @echo -e "\033[1;32m✅ Docker container test suite passed.\033[0m"

# Run static linting and type analysis across the codebase
[group('core: quality')]
lint: (preflight "poetry")
    poetry run ruff check .
    poetry run ruff format --check .
    poetry run mypy credence tests
    @echo -e "\033[1;32m✅ Static linting and typing checks passed cleanly.\033[0m"

# Autoformat code with Ruff
[group('core: quality')]
format: (preflight "poetry")
    poetry run ruff check --fix .
    poetry run ruff format .
    @echo -e "\033[1;32m✅ Code formatted cleanly with Ruff.\033[0m"

# High-speed parallel pre-commit / pre-push QA verification gate (<3s)
[group('core: quality')]
[parallel]
check: lint test-unit test-docs tf-validate agent-check
    @echo ""
    @echo -e "\033[1;32m🎉 Complete Multi-Plane QA Verification Passed Cleanly in Parallel!\033[0m"
    @echo -e "\033[1;36m💡 NEXT STEP: If on a feature branch, run 'just sync-version <vX.Y.Z>' and 'just pr-create <title>'.\033[0m"

# Verify Antigravity declarative workspace configuration, skills schema, and prompt economy
[group('core: quality')]
agent-check:
    @test -f ../AGENTS.md && echo "✅ Universal root AGENTS.md verified." || (echo "❌ Missing root AGENTS.md"; exit 1)
    @test -f ../.agents/skills.json && echo "✅ Declarative .agents/skills.json verified." || (echo "❌ Missing .agents/skills.json"; exit 1)
    @test -d ../credence-agent/.agents/skills && echo "✅ Native skills repository verified." || (echo "❌ Missing credence-agent skills"; exit 1)
    @python3 ../credence-agent/scripts/lint_skills.py
    @python3 ../credence-agent/scripts/audit_demotions.py
    @echo -e "\033[1;32m✅ Declarative Antigravity Workspace & Invariant Engine Verified Cleanly!\033[0m"

# Audit skills schema, frontmatter, and token economy
[group('core: quality')]
audit-skills:
    @python3 ../credence-agent/scripts/lint_skills.py

# Audit invariant demotion candidates and token savings
[group('core: quality')]
audit-demotions:
    @python3 ../credence-agent/scripts/audit_demotions.py

# Run forensic challenge analysis on a specific system invariant
[group('core: quality')]
challenge-invariant slug="inv-verbatim-grounding":
    @python3 ../credence-agent/scripts/challenge_invariant.py "{{slug}}"

# Synchronize Workstation Info Modals with documentation index
[group('core: quality')]
sync-topics:
    @python3 scripts/sync_info_topics.py
    @echo -e "\033[1;32m✅ Workstation info topics synchronized with topic index.\033[0m"
