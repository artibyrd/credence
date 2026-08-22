# ==============================================================================
# 1. Parameterized Preflight Toolchain Gates [core: preflight]
# ==============================================================================

# Verify developer CLI dependencies (poetry, docker, gcloud, wrangler, gh, terraform, all)
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
            ;;
        *)
            echo "❌ Unknown preflight target '{{tool}}'. Valid options: poetry, docker, gcloud, wrangler, gh, terraform, all."
            exit 1
            ;;
    esac

# Install all dependencies and Playwright browser binaries
setup: (preflight "poetry")
    poetry install
    poetry run playwright install chromium

