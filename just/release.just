# ==============================================================================
# 5. Ecosystem Git Sync, Staged PR Triad & Release [core: git, pr & release]
# ==============================================================================

# Synchronize semantic version across all 7 manifests, badges, and documentation
sync-version version: (preflight "poetry")
    @echo "Syncing ecosystem version to {{version}}..."
    @poetry version {{version}}
    @sed -i -E 's/__version__ = "[^"]+"/__version__ = "{{version}}"/' credence/__init__.py
    @sed -i -E "s/export const CURRENT_ECOSYSTEM_VERSION = 'v[^']+';/export const CURRENT_ECOSYSTEM_VERSION = 'v{{version}}';/" ../credence-docs/app.js
    @sed -i -E 's/export const CREDENCE_VERSION = "v[^"]+";/export const CREDENCE_VERSION = "v{{version}}";/' web/assets/credence-workstation.js
    @find web ../credence-docs -name "*.html" -exec sed -i -E 's/Credence <span class="badge">v[^<]+<\/span>/Credence <span class="badge">v{{version}}<\/span>/g' {} +
    @sed -i -E 's/v[0-9]+\.[0-9]+\.[0-9]+ Stable/v{{version}} Stable/' web/credence.run/index.html
    @sed -i -E 's/"version": "[^"]+"/"version": "{{version}}"/' ../credence-agent/plugin.json
    @sed -i -E 's/>v[0-9]+\.[0-9]+\.[0-9]+</>v{{version}}</g' web/assets/og-card.svg ../credence-docs/assets/og-card.svg
    @rsvg-convert -w 1200 -h 630 web/assets/og-card.svg -o web/assets/og-card.png
    @rsvg-convert -w 1200 -h 630 ../credence-docs/assets/og-card.svg -o ../credence-docs/assets/og-card.png
    @poetry run pytest tests/governance/test_docs_integrity.py -k "test_ecosystem_version_parity or test_social_sharing_open_graph_parity"
    @echo -e "\033[1;32m✅ All ecosystem version manifests and social preview assets synchronized to {{version}}.\033[0m"
    @echo -e "\033[1;36m💡 REMINDER: Ensure docs/changelog.md contains release section '## [{{version}}] - YYYY-MM-DD' before running 'just release'.\033[0m"

# Coordinate multi-repository git operations (status, branch, commit, tag, push)
git-sync action="status" arg="":
    #!/usr/bin/env bash
    set -euo pipefail
    REPOS="/home/pendragon/Projects/credence-ecosystem/credence /home/pendragon/Projects/credence-ecosystem/credence-docs /home/pendragon/Projects/credence-ecosystem/credence-agent"
    case "{{action}}" in
        status)
            for r in $REPOS; do
                echo "=== Git Status: $(basename "$r") ==="
                (cd "$r" && git status -s)
            done
            ;;
        branch)
            BRANCH="{{arg}}"
            if [ -z "$BRANCH" ]; then echo "❌ Please provide a branch name. e.g. just git-sync branch feat/v2.3.0-workflow"; exit 1; fi
            for r in $REPOS; do
                echo "=== Checking out branch '$BRANCH' in $(basename "$r") ==="
                (cd "$r" && (git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH"))
            done
            echo "✅ All ecosystem repositories switched to branch '$BRANCH'."
            ;;
        commit)
            MSG="{{arg}}"
            if [ -z "$MSG" ]; then echo "❌ Please provide a commit message. e.g. just git-sync commit 'msg'"; exit 1; fi
            poetry run python -c "import re, sys; msg = sys.argv[1]; pat = r'^(\[v[0-9]+\.[0-9]+\.[0-9]+\] )?(feat|fix|docs|refactor|test|ci|chore|perf)(\((governance|forensics|mesh|crypto|ui|ops)\))?!?: .+$|^(feat|fix|docs|refactor|test|ci|chore|perf)(\((governance|forensics|mesh|crypto|ui|ops)\))?: .+'; sys.exit(0 if re.match(pat, msg) else (print(f'❌ Error: Commit message violates ecosystem convention:\n   \"{msg}\"\n   Allowed format: <type>(<scope>): <summary> OR <type>: <summary>\n   Allowed types : feat, fix, docs, refactor, test, ci, chore, perf\n   Allowed scopes: (governance), (forensics), (mesh), (crypto), (ui), (ops)') or 1))" "$MSG"
            for r in $REPOS; do
                echo "=== Committing in $(basename "$r") ==="
                (cd "$r" && (git diff --quiet && git diff --staged --quiet || (git add -A && git commit -m "$MSG")))
            done
            echo "✅ All ecosystem changes committed."
            ;;
        tag)
            VER="{{arg}}"
            if [ -z "$VER" ]; then echo "❌ Please provide a version tag. e.g. just git-sync tag 1.8.0"; exit 1; fi
            for r in $REPOS; do
                echo "=== Tagging in $(basename "$r") (v$VER) ==="
                (cd "$r" && git tag -f -a "v$VER" -m "Release v$VER")
            done
            echo "✅ Tagged v$VER across all ecosystem repositories."
            ;;
        push)
            for r in $REPOS; do
                CURRENT_BRANCH=$(cd "$r" && git rev-parse --abbrev-ref HEAD)
                echo "=== Pushing $(basename "$r") ($CURRENT_BRANCH) to origin ==="
                (cd "$r" && git push origin "$CURRENT_BRANCH" --follow-tags)
            done
            echo "✅ All ecosystem branches and tags pushed to GitHub."
            ;;
        *)
            echo "❌ Unknown git-sync action '{{action}}'. Valid options: status, branch, commit, tag, push."
            exit 1
            ;;
    esac

# Create or switch feature branch across all ecosystem repositories
branch name:
    @just git-sync branch {{name}}
    @echo -e "\033[1;36m💡 REMINDER: Ensure all new files obey the 500 LOC Ceiling Law. Run 'just check' before opening PRs.\033[0m"

# Perform incremental verified atomic commit across ecosystem repositories
commit message:
    @just git-sync commit "{{message}}"
    @echo -e "\033[1;36m💡 NEXT STEP: Run 'just check' to verify pre-commit integrity before pushing.\033[0m"

# Install conventional commit pre-commit hooks across all 3 ecosystem repositories
install-hooks:
    @python3 ../credence-agent/scripts/install_hooks.py

# Manage GitHub Pull Requests across the ecosystem with rich markdown and approval gating
pr action="status" arg="":
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        create|update)
            TITLE="{{arg}}"
            if [ -z "$TITLE" ]; then echo "❌ Please provide a PR title. e.g. just pr create 'feat: v2.3.0 workflow'"; exit 1; fi
            python3 ../credence-agent/scripts/manage_pr.py "{{action}}" "$TITLE"
            echo -e "\033[1;36m💡 NEXT STEP: Monitor Cloud Run Dev deployment ('deploy-dev.yml' via 'gh run watch').\033[0m"
            echo -e "\033[1;36m💡 REMINDER: Probe live Dev links before presenting walkthrough for human Mk1 review.\033[0m"
            ;;
        status)
            python3 ../credence-agent/scripts/manage_pr.py status
            ;;
        view)
            PR_NUM="{{arg}}"
            gh pr view ${PR_NUM:+"$PR_NUM"}
            ;;
        checks)
            PR_NUM="{{arg}}"
            gh pr checks ${PR_NUM:+"$PR_NUM"}
            ;;
        merge)
            PR_NUM="{{arg}}"
            python3 ../credence-agent/scripts/manage_pr.py merge ${PR_NUM:+"$PR_NUM"}
            echo -e "\033[1;36m💡 NEXT STEP: Switch to main, pull latest changes, and sync version before releasing.\033[0m"
            ;;
        merge-force)
            PR_NUM="{{arg}}"
            python3 ../credence-agent/scripts/manage_pr.py merge ${PR_NUM:+"$PR_NUM"} --force
            ;;
        lock-branch)
            python3 ../credence-agent/scripts/configure_branch_protection.py
            ;;
        *)
            echo "❌ Unknown pr action '{{action}}'. Valid options: create, update, status, view, checks, merge, merge-force, lock-branch."
            exit 1
            ;;
    esac

# Execute full atomic ecosystem release pipeline
release version message:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "❌ Error: Working tree or staging area has uncommitted changes. Please commit before releasing."
        exit 1
    fi
    just check
    just sync-version "{{version}}"
    just git-sync commit "feat(ops): release v{{version}} - {{message}}"
    just git-sync tag "{{version}}"
    just git-sync push
    echo -e "\033[1;32m🚀 Full Ecosystem Release v{{version}} Pushed to GitHub! Continuous deployment is being orchestrated by GitHub Actions.\033[0m"
    echo -e "\033[1;36m💡 NEXT STEP: Monitor production deployment workflows ('gh run watch').\033[0m"
    echo -e "\033[1;36m💡 NEXT STEP: Trigger '/learn' to capture session insights and formulate the next lean patch.\033[0m"
