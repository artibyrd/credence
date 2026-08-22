# ==============================================================================
# 3. Engine, Servers & Local Feeds [core: engine & feeds]
# ==============================================================================

# Launch server transport (sse, stdio, web) with optional port and sifter daemon
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

# Preview all zero-build multi-domain web workstations locally for browser inspection
preview port="8080":
    @echo "🌐 Previewing Credence Multi-Domain Zero-Build Web Surfaces on http://localhost:{{port}}"
    @echo "   👉 Home:       http://localhost:{{port}}/credence.run/"
    @echo "   👉 Reports:    http://localhost:{{port}}/credence.report/"
    @echo "   👉 Nexus:      http://localhost:{{port}}/credence.nexus/"
    @echo "   👉 Admin Deck: http://localhost:{{port}}/credence.nexus/#admin"
    @echo "   👉 Foundation: http://localhost:{{port}}/credence.foundation/"
    @poetry run python3 -m http.server {{port}} --directory web

# Preview zero-build documentation portal locally on http://localhost:8081
preview-docs port="8081":
    @echo "📚 Previewing Credence Documentation Portal on http://localhost:{{port}}"
    @python3 -m http.server {{port}} --directory ../credence-docs

# Launch complete local development stack (Backend on 8000 + Web Workstations on 8080)
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

# Launch interactive Textual TUI workstation
tui: (preflight "poetry")
    poetry run credence tui

# Run the Golden 12 cross-profile evaluation benchmark
benchmark: (preflight "poetry")
    poetry run credence benchmark

# Automated dual-tier environment configuration verifier (dev vs prod)
config-verify dev_url="http://localhost:8000" prod_url="https://credence-server-663899237633.us-central1.run.app": (preflight "poetry")
    poetry run python -m credence.experiments.env_verifier --dev-url="{{dev_url}}" --prod-url="{{prod_url}}"

# Run bicameral experiments and differential benchmarks (shadow-audit, federation-bridge, env-verify)
experiment name="shadow-audit" arg="": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{name}}" in
        shadow-audit)
            echo "=== Running Bicameral Differential Shadow Audit ==="
            poetry run python -m credence.experiments.shadow_audit {{arg}}
            ;;
        federation-bridge)
            echo "=== Running Sovereign White-Label Federation Bridge Simulator ==="
            poetry run python -m credence.experiments.federation_bridge {{arg}}
            ;;
        env-verify|verify)
            echo "=== Verifying Dev vs. Prod Environment Configurations ==="
            poetry run python -m credence.experiments.env_verifier {{arg}}
            ;;
        *)
            echo "❌ Unknown experiment '{{name}}'. Valid options: shadow-audit, federation-bridge, env-verify."
            exit 1
            ;;
    esac


# Display Epistemic Mesh Leaderboard (quality, subjects, philanthropy, galileo, teams)
leaderboard category="quality": (preflight "poetry")
    poetry run credence leaderboard --category {{category}}

# Display local node Epistemic Merit card, badges, and compute odometer
merit: (preflight "poetry")
    poetry run credence merit

# Self-audit documentation and blog articles with cryptographic attestations
audit-docs action="check": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        check)
            echo "=== Auditing Documentation Integrity & Epistemic Self-Score ==="
            poetry run credence audit-docs --check
            ;;
        update)
            echo "=== Updating Documentation Verified Frontmatter & Minting Attestations ==="
            poetry run credence audit-docs --update
            ;;
        *)
            echo "=== Running Documentation Audit ==="
            poetry run credence audit-docs --lens {{action}}
            ;;
    esac

# Display Web Epistemic Analytics and Domain rankings (domains, rules, weather, bounties)
rankings type="domains" category="best": (preflight "poetry")
    poetry run credence rankings {{type}} --category {{category}}


# Display Global Epistemic Weather report
weather: (preflight "poetry")
    poetry run credence rankings weather

# Manage syndicated feed sifter and catalog export (once, bootstrap, export)
sifter action="once": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        once)
            poetry run credence sifter --once
            ;;
        bootstrap)
            poetry run credence feeds bootstrap-presets
            poetry run credence sifter --once
            poetry run credence export-catalog
            ;;
        export)
            poetry run credence export-catalog
            ;;
        *)
            echo "❌ Unknown sifter action '{{action}}'. Valid options: once, bootstrap, export."
            exit 1
            ;;
    esac

# Autonomous node ignition (Genesis identity, Genesis peer inoculation, feed sowing, Miracle-Gro burst)
germinate burst="3" sync_mesh="true": (preflight "poetry")
    #!/usr/bin/env bash
    set -euo pipefail
    if [ "{{sync_mesh}}" = "false" ] || [ "{{sync_mesh}}" = "0" ]; then
        poetry run credence germinate --burst {{burst}} --no-mesh
    else
        poetry run credence germinate --burst {{burst}}
    fi

# Manage local P2P mesh cluster simulation (up, down, logs, status)
mesh action="up" nodes="13": (preflight "poetry") (preflight "docker")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        up)
            poetry run python -c "from credence.mesh.hardware_guard import recommend_cluster_size; recommend_cluster_size({{nodes}})"
            docker compose -f docker-compose.mesh.yml up -d --build
            ;;
        down)
            docker compose -f docker-compose.mesh.yml down -v
            ;;
        logs)
            docker compose -f docker-compose.mesh.yml logs -f
            ;;
        status)
            docker compose -f docker-compose.mesh.yml ps
            ;;
        *)
            echo "❌ Unknown mesh action '{{action}}'. Valid options: up, down, logs, status."
            exit 1
            ;;
    esac

# Manage local Docker container operations (build, test)
docker action="build": (preflight "docker")
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{action}}" in
        build)
            docker compose build
            ;;
        test)
            docker compose run --rm credence poetry run pytest tests/
            ;;
        *)
            echo "❌ Unknown docker action '{{action}}'. Valid options: build, test."
            exit 1
            ;;
    esac

