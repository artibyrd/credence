# ==============================================================================
# 1. Parameterized Preflight Toolchain Gates [group('core: preflight')]
# ==============================================================================

# Verify developer CLI dependencies across all planes (poetry, docker, gcloud, wrangler, gh, terraform, all)
[group('core: preflight')]
preflight tool="all":
    #!/usr/bin/env bash
    set -euo pipefail

    check_binary() {
        local name="$1"
        local cmd="$2"
        local install_url="$3"
        local version_cmd="$4"
        if [ -z "$version_cmd" ]; then
            version_cmd="$cmd --version"
        fi
        if ! command -v "$cmd" &>/dev/null; then
            echo -e "\033[0;31m❌ Missing: $name ('$cmd' not found in PATH)\033[0m"
            echo "   👉 Install guide: $install_url"
            return 1
        fi
        local ver
        ver=$($version_cmd 2>&1 | sed -n '1p' || echo "installed")
        echo -e "\033[0;32m✅ $name:\033[0m $ver"
        return 0
    }

    check_gcloud() {
        if ! command -v gcloud &>/dev/null; then
            echo -e "\033[0;31m❌ Missing: Google Cloud SDK (gcloud)\033[0m"
            echo "   👉 Install: https://cloud.google.com/sdk/docs/install"
            return 1
        fi
        local acc
        acc=$(gcloud config get-value account 2>/dev/null || echo "none")
        local proj
        proj=$(gcloud config get-value project 2>/dev/null || echo "none")
        echo -e "\033[0;32m✅ Google Cloud SDK (gcloud):\033[0m Account: \033[1;36m$acc\033[0m | Project: \033[1;36m$proj\033[0m"
        return 0
    }

    check_wrangler() {
        if command -v wrangler &>/dev/null; then
            local ver
            ver=$(wrangler --version 2>&1 | sed -n '1p' || echo "installed")
            echo -e "\033[0;32m✅ Cloudflare Wrangler:\033[0m $ver"
            return 0
        elif command -v npx &>/dev/null; then
            local ver
            ver=$(npx --no-install wrangler --version 2>&1 | sed -n '1p' || echo "available via npx")
            echo -e "\033[0;32m✅ Cloudflare Wrangler (npx):\033[0m $ver"
            return 0
        else
            echo -e "\033[0;31m❌ Missing: Cloudflare Wrangler\033[0m"
            echo "   👉 Install: npm install -g wrangler"
            return 1
        fi
    }

    check_gh() {
        if ! command -v gh &>/dev/null; then
            echo -e "\033[0;31m❌ Missing: GitHub CLI (gh)\033[0m"
            echo "   👉 Install: https://cli.github.com"
            return 1
        fi
        local auth_user
        auth_user=$(gh auth status 2>&1 | grep -o "account [^ ]*" | sed -n '1p' | awk '{print $2}' || echo "authenticated")
        echo -e "\033[0;32m✅ GitHub CLI (gh):\033[0m Logged in ($auth_user)"
        return 0
    }

    case "{{tool}}" in
        poetry)
            check_binary "Poetry" "poetry" "https://python-poetry.org/docs/#installation" ""
            ;;
        docker)
            check_binary "Docker" "docker" "https://docs.docker.com/get-docker/" ""
            check_binary "Docker Compose" "docker" "https://docs.docker.com/compose/" "docker compose version"
            ;;
        gcloud|gcp)
            check_gcloud
            ;;
        wrangler|cloudflare|edge)
            check_wrangler
            ;;
        gh|github)
            check_gh
            ;;
        terraform|tf)
            check_binary "HashiCorp Terraform" "terraform" "https://developer.hashicorp.com/terraform/install" ""
            ;;
        all)
            echo "=== Credence Multi-Plane Toolchain Preflight ==="
            check_binary "Poetry" "poetry" "https://python-poetry.org" "" || true
            check_binary "Docker" "docker" "https://docs.docker.com" "" || true
            check_gcloud || true
            check_wrangler || true
            check_gh || true
            check_binary "Terraform" "terraform" "https://terraform.io" "" || true
            echo "=== Preflight Validation Complete ==="
            echo -e "\033[1;36m💡 NEXT STEP: Run 'just ignite' for one-command onboarding or 'just check' for pre-commit QA.\033[0m"
            ;;
        *)
            echo "❌ Unknown preflight target '{{tool}}'. Valid options: poetry, docker, gcloud, wrangler, gh, terraform, all."
            exit 1
            ;;
    esac

# Install all dependencies and Playwright browser binaries
[group('core: preflight')]
setup: (preflight "poetry")
    poetry install
    poetry run playwright install chromium
    @echo -e "\033[1;32m✅ Development environment dependencies installed.\033[0m"
    @echo -e "\033[1;36m💡 NEXT STEP: Run 'just check' to verify QA gates or 'just dev' to launch local services.\033[0m"

# Verify that active authentication sessions and credentials are warm and unexpired
[group('core: preflight')]
auth-check target="all":
    #!/usr/bin/env bash
    set -euo pipefail

    check_auth_gh() {
        if ! command -v gh &>/dev/null; then
            echo -e "\033[0;31m❌ GitHub CLI (gh) not installed.\033[0m"
            return 1
        fi
        if gh auth status &>/dev/null; then
            local user
            user=$(gh api user -q .login 2>/dev/null || echo "active")
            echo -e "\033[0;32m✅ GitHub CLI Auth:\033[0m Warm & authenticated (@$user)"
            return 0
        else
            echo -e "\033[0;31m❌ GitHub CLI Auth:\033[0m Expired or not logged in. Run '\033[1;36mgh auth login\033[0m'."
            return 1
        fi
    }

    check_auth_gcloud() {
        if ! command -v gcloud &>/dev/null; then
            echo -e "\033[0;31m❌ Google Cloud SDK (gcloud) not installed.\033[0m"
            return 1
        fi
        if gcloud auth print-access-token &>/dev/null; then
            local acc proj
            acc=$(gcloud config get-value account 2>/dev/null || echo "unknown")
            proj=$(gcloud config get-value project 2>/dev/null || echo "unknown")
            echo -e "\033[0;32m✅ Google Cloud Auth:\033[0m Warm ($acc / $proj)"
            return 0
        else
            local acc
            acc=$(gcloud config get-value account 2>/dev/null || echo "unknown")
            echo -e "\033[0;31m❌ Google Cloud Auth:\033[0m Session expired for $acc. Run '\033[1;36mgcloud auth login\033[0m'."
            return 1
        fi
    }

    check_auth_wrangler() {
        if (cd web && npx wrangler whoami 2>&1 | grep -q "You are logged in"); then
            local who
            who=$(cd web && npx wrangler whoami 2>&1 | grep "You are logged in" | head -n 1)
            echo -e "\033[0;32m✅ Cloudflare Wrangler Auth:\033[0m Warm ($who)"
            return 0
        elif [ -n "${CLOUDFLARE_API_TOKEN:-}" ]; then
            echo -e "\033[0;32m✅ Cloudflare Auth:\033[0m Warm (via CLOUDFLARE_API_TOKEN)"
            return 0
        else
            echo -e "\033[0;31m❌ Cloudflare Wrangler Auth:\033[0m Not logged in. Run '\033[1;36mjust edge-login\033[0m' or set CLOUDFLARE_API_TOKEN."
            return 1
        fi
    }

    check_auth_docker() {
        if ! command -v docker &>/dev/null; then
            echo -e "\033[0;31m❌ Docker not installed.\033[0m"
            return 1
        fi
        if docker info &>/dev/null; then
            echo -e "\033[0;32m✅ Docker Daemon:\033[0m Reachable and active"
            return 0
        else
            echo -e "\033[0;31m❌ Docker Daemon:\033[0m Not running or inaccessible. Start Docker daemon."
            return 1
        fi
    }

    check_auth_env() {
        echo "=== Environment Secrets & API Keys ==="
        for var in GEMINI_API_KEY ANTHROPIC_API_KEY OPENAI_API_KEY; do
            if [ -n "${!var:-}" ]; then
                echo -e "\033[0;32m✅ $var:\033[0m Set (${#var} chars)"
            else
                echo -e "\033[0;33m⚠️ $var:\033[0m Unset (optional for local mock tests, required for live LLM calls)"
            fi
        done
    }

    case "{{target}}" in
        gh|github)
            check_auth_gh
            ;;
        gcloud|gcp)
            check_auth_gcloud
            ;;
        wrangler|cloudflare|edge)
            check_auth_wrangler
            ;;
        docker)
            check_auth_docker
            ;;
        env|llm)
            check_auth_env
            ;;
        all)
            echo "=== Credence Authentication Freshness Preflight ==="
            check_auth_gh || true
            check_auth_gcloud || true
            check_auth_wrangler || true
            check_auth_docker || true
            check_auth_env || true
            echo "=== Authentication Check Complete ==="
            ;;
        *)
            echo "❌ Unknown auth-check target '{{target}}'. Valid options: gh, gcloud, wrangler, docker, env, all."
            exit 1
            ;;
    esac

