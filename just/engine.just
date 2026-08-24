# ==============================================================================
# 3. Engine, Servers, Local Feeds & Mesh [core: engine, feeds & cluster]
# ==============================================================================

# Launch complete local development stack (Backend on 8000 + Web Workstations on 8080)
[group('core: engine')]
dev backend_port="8000" web_port="8080": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    echo "================================================================="
    echo "  🚀 Starting Credence Dual-Plane Local Development Stack"
    echo "================================================================="
    echo "  ⚙️  Backend (FastMCP + REST): http://localhost:{{backend_port}}"
    echo "  🌐 Web Workstations:         http://localhost:{{web_port}}"
    echo "     👉 Home:       http://localhost:{{web_port}}/credence.run/"
    echo "     👉 Reports:    http://localhost:{{web_port}}/credence.report/"
    echo "     👉 Nexus:      http://localhost:{{web_port}}/credence.nexus/"
    echo "     👉 Admin Deck: http://localhost:{{web_port}}/credence.nexus/#admin"
    echo "     👉 Foundation: http://localhost:{{web_port}}/credence.foundation/"
    echo "================================================================="
    echo "Press CTRL+C to terminate both servers."
    trap 'kill $(jobs -p) 2>/dev/null || true' EXIT SIGINT SIGTERM
    python3 -m http.server {{web_port}} --directory web &
    poetry run credence serve --transport sse --port {{backend_port}}

# Launch server transport (sse, stdio, web) with optional port and sifter daemon
[group('core: engine')]
serve transport="sse" port="8000" sifter="false": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{transport}}" in
        sse)
            if [ "{{sifter}}" = "true" ] || [ "{{sifter}}" = "1" ]; then
                poetry run credence serve --transport sse --port {{port}} --sifter
            else
                poetry run credence serve --transport sse --port {{port}}
            fi
            ;;
        stdio)
            poetry run credence serve --transport stdio
            ;;
        web)
            poetry run python -m http.server {{port}} --directory web
            ;;
        *)
            echo "❌ Unknown transport '{{transport}}'. Valid options: sse, stdio, web."
            exit 1
            ;;
    esac

# Launch server with background feed sifter daemon
[group('core: engine')]
serve-sifter port="8000": (preflight "poetry")
    poetry run credence serve --transport sse --port {{port}} --sifter

alias sifter-once := sifter-run
alias seed-reports := sifter-bootstrap
alias export-catalog := sifter-export
alias serve-web := preview

# Preview all zero-build multi-domain web workstations locally for browser inspection
[group('core: engine')]
preview port="8080":
    @echo "🌐 Previewing Credence Multi-Domain Zero-Build Web Surfaces on http://localhost:{{port}}"
    @echo "   👉 Home:       http://localhost:{{port}}/credence.run/"
    @echo "   👉 Reports:    http://localhost:{{port}}/credence.report/"
    @echo "   👉 Nexus:      http://localhost:{{port}}/credence.nexus/"
    @echo "   👉 Admin Deck: http://localhost:{{port}}/credence.nexus/#admin"
    @echo "   👉 Foundation: http://localhost:{{port}}/credence.foundation/"
    @poetry run python3 -m http.server {{port}} --directory web

# Preview zero-build documentation portal locally on http://localhost:8081
[group('core: engine')]
preview-docs port="8081":
    @echo "📚 Previewing Credence Documentation Portal on http://localhost:{{port}}"
    @python3 -m http.server {{port}} --directory ../credence-docs

# Launch interactive Textual TUI workstation
[group('core: engine')]
tui: (preflight "poetry")
    poetry run credence tui

# Run the Golden 12 cross-profile evaluation benchmark
[group('core: engine')]
benchmark: (preflight "poetry")
    poetry run credence benchmark
    @echo -e "\033[1;32m✅ Golden 12 benchmark complete.\033[0m"

# Display Epistemic Mesh Leaderboard (quality, subjects, philanthropy, galileo, teams)
[group('core: engine')]
leaderboard category="quality": (preflight "poetry")
    poetry run credence leaderboard --category {{category}}

# Display local node Epistemic Merit card, badges, and compute odometer
[group('core: engine')]
merit: (preflight "poetry")
    poetry run credence merit

# Display Web Epistemic Analytics and Domain rankings
[group('core: engine')]
rankings type="domains" category="best": (preflight "poetry")
    poetry run credence rankings {{type}} --category {{category}}

# Display Global Epistemic Weather report
[group('core: engine')]
weather: (preflight "poetry")
    poetry run credence rankings weather

# Autonomous local node ignition (Genesis identity, peer inoculation, feed sowing, Miracle-Gro burst)
[group('core: feeds')]
germinate burst="3" sync_mesh="true": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{sync_mesh}}" = "false" ] || [ "{{sync_mesh}}" = "0" ]; then
        poetry run credence germinate --burst {{burst}} --no-mesh
    else
        poetry run credence germinate --burst {{burst}}
    fi
    echo -e "\033[1;32m🌱 Node germination complete (burst: {{burst}} items).\033[0m"
    echo -e "\033[1;36m💡 NEXT STEP: Run 'just dev' or 'just preview' to inspect inoculated feeds in the UI.\033[0m"

# Run syndicated feed sifter once
[group('core: feeds')]
sifter-run: (preflight "poetry")
    poetry run credence sifter --once
    @echo -e "\033[1;32m✅ Feed sifter pass completed.\033[0m"

# Bootstrap feed presets, run sifter, and export catalog
[group('core: feeds')]
sifter-bootstrap: (preflight "poetry")
    poetry run credence feeds bootstrap-presets
    poetry run credence sifter --once
    poetry run credence export-catalog
    @echo -e "\033[1;32m✅ Feed presets bootstrapped and catalog exported.\033[0m"

# Export syndicated feed catalog
[group('core: feeds')]
sifter-export: (preflight "poetry")
    poetry run credence export-catalog

# Generate official static JSON taxonomies and root public keys
[group('core: feeds')]
publish-taxonomies dry_run="true": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{dry_run}}" = "false" ] || [ "{{dry_run}}" = "0" ]; then
        poetry run python3 scripts/publish_taxonomies.py --live
    else
        poetry run python3 scripts/publish_taxonomies.py --dry-run
    fi

# Generate cryptographically signed bootstrap seed file manifest (RFC 8785)
[group('core: feeds')]
publish-seeds dry_run="true": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{dry_run}}" = "false" ] || [ "{{dry_run}}" = "0" ]; then
        poetry run python3 scripts/publish_seeds.py --live
    else
        poetry run python3 scripts/publish_seeds.py --dry-run
    fi

# Regenerate curated vector SVG architectural schematics
[group('core: feeds')]
illustrations: (preflight "poetry")
    poetry run python3 scripts/generate_illustrations.py
    @echo -e "\033[1;32m✅ Architectural SVG schematics regenerated.\033[0m"

# Self-audit documentation and blog articles with cryptographic attestations
[group('core: feeds')]
audit-docs action="check": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        check)
            poetry run credence audit-docs --check
            ;;
        update)
            poetry run credence audit-docs --update
            ;;
        *)
            poetry run credence audit-docs --lens {{action}}
            ;;
    esac

# Launch local 13-node Watts-Strogatz P2P mesh cluster simulation
[group('core: cluster')]
mesh-up nodes="13": (preflight "poetry") (preflight "docker")
    poetry run python -c "from credence.mesh.hardware_guard import recommend_cluster_size; recommend_cluster_size({{nodes}})"
    docker compose -f docker-compose.mesh.yml up -d --build
    @echo -e "\033[1;32m🌐 13-Node Watts-Strogatz Mesh Cluster is UP.\033[0m"
    @echo -e "\033[1;36m💡 NEXT STEP: View cluster state with 'just mesh-status' or stream logs with 'just mesh-logs'.\033[0m"

alias mesh-cluster-up := mesh-up

# Tear down local P2P mesh cluster simulation
[group('core: cluster')]
mesh-down: (preflight "docker")
    docker compose -f docker-compose.mesh.yml down -v
    @echo -e "\033[1;32m🛑 Mesh cluster torn down.\033[0m"

alias mesh-cluster-down := mesh-down

# View P2P mesh cluster container status
[group('core: cluster')]
mesh-status: (preflight "docker")
    docker compose -f docker-compose.mesh.yml ps

# Stream P2P mesh cluster logs
[group('core: cluster')]
mesh-logs: (preflight "docker")
    docker compose -f docker-compose.mesh.yml logs -f

# Build local Docker container image
[group('core: cluster')]
docker-build: (preflight "docker")
    docker compose build
    @echo -e "\033[1;32m✅ Docker image built successfully.\033[0m"

# Test inside local Docker container
[group('core: cluster')]
docker-test: (preflight "docker")
    docker compose run --rm credence poetry run pytest tests/

# Bootstrap and manage operator administrative authentication credentials
[group('core: cluster')]
auth-bootstrap env="local":
    @poetry run python3 scripts/bootstrap_admin_auth.py {{env}}

# Print the active local operator admin authentication token
[group('core: cluster')]
auth-token:
    @poetry run python3 scripts/bootstrap_admin_auth.py local --print-token

# One-command developer onboarding: setup dependencies, preflight, bootstrap admin key, germinate, and verify
[group('core: cluster')]
ignite burst="3":
    @just setup
    @just preflight all
    @just auth-bootstrap local
    @just germinate {{burst}}
    @just test-mock
    @just doctor
    @echo -e "\033[1;32m🌱 Credence Node Ignited & Ready for Operations!\033[0m"
    @echo -e "\033[1;36m💡 NEXT STEP: Run 'just dev' to launch the dual-plane stack on http://localhost:8000 and http://localhost:8080.\033[0m"

# Run bicameral experimentation and shadow audit suites
[group('core: engine')]
experiment task="shadow-audit" *args="": (preflight "poetry")
    poetry run python -m credence.experiments.{{replace(task, "-", "_")}} {{args}}
