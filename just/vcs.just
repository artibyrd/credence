# ==============================================================================
# 4. Version Control, Staged PR Triad & Governance [vcs: safe & gated]
# ==============================================================================

# Display git status across all 3 ecosystem repositories (credence, docs, agent)
[group('vcs: safe')]
status:
    #!/usr/bin/env bash
    set -euo pipefail
    REPOS="/home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent"
    for r in $REPOS; do
        echo "=== Git Status: $(basename "$r") ==="
        (cd "$r" && git status -s)
    done

# Display uncommitted diffs across ecosystem repositories
[group('vcs: safe')]
git-diff repo="all":
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{repo}}" in
        all)
            for r in /home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent; do
                echo "=== Git Diff: $(basename "$r") ==="
                (cd "$r" && git diff)
            done
            ;;
        credence|docs|agent)
            TARGET_DIR="/home/pendragon/Projects/credence-ecosystem/{{repo}}"
            if [ "{{repo}}" = "docs" ]; then TARGET_DIR="/home/pendragon/Projects/credence-ecosystem/credence-docs"; fi
            if [ "{{repo}}" = "agent" ]; then TARGET_DIR="/home/pendragon/Projects/credence-ecosystem/credence-agent"; fi
            (cd "$TARGET_DIR" && git diff)
            ;;
        *)
            echo "❌ Unknown repo target '{{repo}}'. Valid options: all, credence, docs, agent."
            exit 1
            ;;
    esac

# Display compact commit history across ecosystem repositories
[group('vcs: safe')]
git-log n="10" repo="all":
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{repo}}" in
        all)
            for r in /home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent; do
                echo "=== Recent Commits: $(basename "$r") (limit: {{n}}) ==="
                (cd "$r" && git log -n {{n}} --oneline)
            done
            ;;
        credence|docs|agent)
            TARGET_DIR="/home/pendragon/Projects/credence-ecosystem/{{repo}}"
            if [ "{{repo}}" = "docs" ]; then TARGET_DIR="/home/pendragon/Projects/credence-ecosystem/credence-docs"; fi
            if [ "{{repo}}" = "agent" ]; then TARGET_DIR="/home/pendragon/Projects/credence-ecosystem/credence-agent"; fi
            (cd "$TARGET_DIR" && git log -n {{n}} --oneline)
            ;;
        *)
            echo "❌ Unknown repo target '{{repo}}'. Valid options: all, credence, docs, agent."
            exit 1
            ;;
    esac

# Display active checked-out branch across all ecosystem repositories
[group('vcs: safe')]
git-branches:
    #!/usr/bin/env bash
    set -euo pipefail
    for r in /home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent; do
        BRANCH=$(cd "$r" && git rev-parse --abbrev-ref HEAD)
        echo -e "🌿 \033[1;36m$(basename "$r"):\033[0m $BRANCH"
    done

# View active Pull Request triad status and review approvals
[group('vcs: safe')]
pr-status:
    @python3 ../credence-agent/scripts/manage_pr.py status

# View detailed markdown summary and diff of open Pull Requests
[group('vcs: safe')]
pr-view pr_num="":
    @gh pr view ${pr_num:+"$pr_num"}

# Inspect CI/CD check runs and status on open Pull Requests
[group('vcs: safe')]
pr-checks pr_num="":
    @gh pr checks ${pr_num:+"$pr_num"}

# Switch or create feature branch across all 3 ecosystem repositories
[group('vcs: gated')]
branch name:
    #!/usr/bin/env bash
    set -euo pipefail
    for r in /home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent; do
        echo "=== Switching branch in $(basename "$r") ==="
        (cd "$r" && (git checkout "{{name}}" 2>/dev/null || git checkout -b "{{name}}"))
    done
    echo -e "\033[1;32m✅ All ecosystem repositories switched to branch '{{name}}'.\033[0m"
    echo -e "\033[1;33m⚠️ GUARDRAIL: All new files must obey the 500 LOC Ceiling Law (Invariant 1).\033[0m"
    echo -e "\033[1;36m💡 NEXT STEP: Make atomic edits, then run 'just commit <message>'.\033[0m"

# Perform incremental verified atomic commit across ecosystem repositories
[group('vcs: gated')]
commit message:
    #!/usr/bin/env bash
    set -euo pipefail
    MSG="{{message}}"
    poetry run python -c "import re, sys; msg = sys.argv[1]; pat = r'^(\[v[0-9]+\.[0-9]+\.[0-9]+\] )?(feat|fix|docs|refactor|test|ci|chore|perf)(\((governance|forensics|mesh|crypto|ui|ops)\))?!?: .+$|^(feat|fix|docs|refactor|test|ci|chore|perf)(\((governance|forensics|mesh|crypto|ui|ops)\))?: .+'; sys.exit(0 if re.match(pat, msg) else (print(f'❌ Error: Commit message violates ecosystem convention:\n   \"{msg}\"\n   Allowed format: <type>(<scope>): <summary> OR <type>: <summary>\n   Allowed types : feat, fix, docs, refactor, test, ci, chore, perf\n   Allowed scopes: (governance), (forensics), (mesh), (crypto), (ui), (ops)') or 1))" "$MSG"
    REPOS="/home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent"
    for r in $REPOS; do
        echo "=== Committing in $(basename "$r") ==="
        (cd "$r" && (git diff --quiet && git diff --staged --quiet || (git add -A && git commit -m "$MSG")))
    done
    echo -e "\033[1;32m✅ All ecosystem changes committed.\033[0m"
    echo -e "\033[1;36m💡 NEXT STEP: Run 'just check' to verify pre-commit QA gates before opening PRs.\033[0m"

# Create annotated version tag across all 3 ecosystem repositories
[group('vcs: gated')]
git-tag version:
    #!/usr/bin/env bash
    set -euo pipefail
    for r in /home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent; do
        echo "=== Tagging $(basename "$r") (v{{version}}) ==="
        (cd "$r" && git tag -f -a "v{{version}}" -m "Release v{{version}}")
    done
    echo -e "\033[1;32m✅ Tagged v{{version}} across all ecosystem repositories.\033[0m"

# Push current branches and tags to GitHub origin
[group('vcs: gated')]
git-push:
    #!/usr/bin/env bash
    set -euo pipefail
    for r in /home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent; do
        CURRENT_BRANCH=$(cd "$r" && git rev-parse --abbrev-ref HEAD)
        echo "=== Pushing $(basename "$r") ($CURRENT_BRANCH) to origin ==="
        (cd "$r" && git push origin "$CURRENT_BRANCH" --follow-tags)
    done
    echo -e "\033[1;32m✅ All ecosystem branches and tags pushed to GitHub.\033[0m"

# Create staged Pull Request triad with cross-repo links and automated Dev deployment trigger
[group('vcs: gated')]
pr-create title:
    #!/usr/bin/env bash
    set -euo pipefail
    python3 ../credence-agent/scripts/manage_pr.py "create" "{{title}}"
    echo -e "\033[1;33m⚠️ GUARDRAIL: Pre-staging version sync invariant requires all 7 manifests to match target version.\033[0m"
    echo -e "\033[1;36m💡 NEXT STEP: Monitor Cloud Run Dev deployment ('just ci-watch') and probe live links ('just cloud-probe').\033[0m"

# Update description and companion links across open PR triad
[group('vcs: gated')]
pr-update title:
    #!/usr/bin/env bash
    set -euo pipefail
    python3 ../credence-agent/scripts/manage_pr.py "update" "{{title}}"

# Merge Pull Request triad into main following human Mk1 Eyeball sign-off
[group('vcs: gated')]
pr-merge pr_num="":
    #!/usr/bin/env bash
    set -euo pipefail
    python3 ../credence-agent/scripts/manage_pr.py merge ${pr_num:+"$pr_num"}
    echo -e "\033[1;32m✅ PR triad merged into main.\033[0m"
    echo -e "\033[1;36m💡 NEXT STEP: Switch to main ('just branch main'), pull changes, and run 'just sync-version <version>'.\033[0m"

# Force merge Pull Request triad bypassing check gates (emergency use only)
[group('vcs: gated')]
pr-merge-force pr_num="":
    @python3 ../credence-agent/scripts/manage_pr.py merge ${pr_num:+"$pr_num"} --force

# Apply GitHub branch protection rules on main branch across triad
[group('vcs: gated')]
branch-protect:
    @python3 ../credence-agent/scripts/configure_branch_protection.py

# Install conventional commit pre-commit hooks across all 3 ecosystem repositories
[group('vcs: gated')]
install-hooks:
    @python3 ../credence-agent/scripts/install_hooks.py
