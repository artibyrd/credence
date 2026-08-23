# ==============================================================================
# 6. Ecosystem Release Lifecycle & Workspace Bootstrap [release & bootstrap]
# ==============================================================================

# Synchronize semantic version across all 7 manifests, badges, and documentation
[group('release')]
sync-version version: (preflight "poetry")
    @echo "Syncing ecosystem version to {{version}}..."
    @poetry version {{version}}
    @sed -i -E 's/__version__ = "[^"]+"/__version__ = "{{version}}"/' credence/__init__.py
    @sed -i -E "s/export const CURRENT_ECOSYSTEM_VERSION = 'v[^']+';/export const CURRENT_ECOSYSTEM_VERSION = 'v{{version}}';/" ../credence-docs/app.js
    @sed -i -E 's/export const CREDENCE_VERSION = "v[^"]+";/export const CREDENCE_VERSION = "v{{version}}";/' web/assets/credence-workstation.js
    @find web ../credence-docs -name "*.html" -exec sed -i -E 's/<span class="badge"([^>]*)>v[^<]+<\/span>/<span class="badge"\1>v{{version}}<\/span>/g' {} +
    @sed -i -E 's/v[0-9]+\.[0-9]+\.[0-9]+ Stable/v{{version}} Stable/' web/credence.run/index.html
    @sed -i -E 's/"version": "[^"]+"/"version": "{{version}}"/' ../credence-agent/plugin.json
    @sed -i -E 's/>v[0-9]+\.[0-9]+\.[0-9]+</>v{{version}}</g' web/assets/og-card.svg ../credence-docs/assets/og-card.svg
    @just render-assets
    @poetry run pytest tests/governance/test_docs_integrity.py -k "test_ecosystem_version_parity or test_social_sharing_open_graph_parity"
    @echo -e "\033[1;32m✅ All 7 ecosystem version manifests and social preview assets synchronized to {{version}}.\033[0m"
    @echo -e "\033[1;33m⚠️ GUARDRAIL: Ensure 'docs/changelog.md' contains release section '## [{{version}}] - YYYY-MM-DD' before running 'just release'.\033[0m"
    @echo -e "\033[1;36m💡 NEXT STEP: If working on a feature branch, run 'just pr-create <title>'. If releasing on main, run 'just release {{version}} <msg>'.\033[0m"

# Render Web Open Graph card asset
[private]
render-og-web:
    @rsvg-convert -w 1200 -h 630 web/assets/og-card.svg -o web/assets/og-card.png

# Render Docs Open Graph card asset
[private]
render-og-docs:
    @rsvg-convert -w 1200 -h 630 ../credence-docs/assets/og-card.svg -o ../credence-docs/assets/og-card.png

# Render all vector SVG social sharing cards in parallel via rsvg-convert
[group('release')]
[parallel]
render-assets: render-og-web render-og-docs
    @echo -e "\033[1;32m✅ High-resolution 1200x630 social preview cards rendered in parallel.\033[0m"

# Execute full atomic ecosystem release pipeline
[group('release')]
[confirm('⚠️ Are you sure you want to execute an ATOMIC ECOSYSTEM RELEASE?')]
release version message: (auth-check "gh")
    #!/usr/bin/env bash
    set -euo pipefail
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo -e "\033[1;31m❌ Error: Working tree or staging area has uncommitted changes. Per the Commit-Before-Deploy invariant, commit changes first.\033[0m"
        exit 1
    fi
    just check
    just sync-version "{{version}}"
    just commit "feat(ops): release v{{version}} - {{message}}"
    just git-tag "{{version}}"
    just git-push
    echo -e "\033[1;32m🚀 Full Ecosystem Release v{{version}} Pushed to GitHub! Continuous deployment is being orchestrated by GitHub Actions.\033[0m"
    echo -e "\033[1;36m💡 NEXT STEP: Monitor production deployment workflows ('just ci-watch').\033[0m"
    echo -e "\033[1;36m💡 NEXT STEP: Trigger '/learn' to capture session insights and formulate the next lean patch.\033[0m"

# Interactive agent command approval bootstrapping runner for open-source developers and forks (core tools only)
[group('bootstrap')]
bootstrap-approvals scope="core":
    @python3 scripts/bootstrap_approvals.py --scope {{scope}} --execute
