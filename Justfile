# Justfile for Credence Epistemic Ecosystem
# Canonical Modular Architecture (<300 LOC per category) & Modern Just 1.58.0 Engine
# Invariant: 500 LOC Ceiling Law & Shift-Left Intelligent Guidance Highway

set shell := ["bash", "-c"]
set dotenv-load := true

# Core Ecosystem Modules (For all developers & forks)
import "just/preflight.just"
import "just/quality.just"
import "just/engine.just"
import "just/vcs.just"

# Hosted Operations & Infrastructure Modules (Artibyrd maintainer infrastructure & releases)
import "just/cloud.just"
import "just/release.just"

# Display available recipes and organized categories
[default]
[group('help')]
default:
    @echo -e "\033[1;36m🧭 CREDENCE ECOSYSTEM OPERATIONAL COMPASS:\033[0m"
    @echo "  1. Plan Approved       -> 'just branch feat/<name>' (Immediate branching before edits)"
    @echo "  2. Workspace Scratch   -> '/scratch/<name>.py' (3-Step Scratch Ritual, zero inline blobs)"
    @echo "  3. Incremental Edits   -> 'just commit <msg>' (Frequent discrete verified commits)"
    @echo "  4. Pre-PR QA Gate      -> 'just check' (Parallel test & lint verification)"
    @echo "  5. Staged Triad        -> 'just pr-create <title>' (Open cross-repo PRs)"
    @echo "  6. CI/CD & Dev Deploy  -> 'just ci-watch' -> Automated live HTTP dev probe"
    @echo "  7. Cumulative Records  -> Update walkthrough.md (Museum Invariant: do NOT wipe earlier phases!)"
    @echo "  8. Mk1 Eyeball Review  -> 'just pr-merge' -> 'just release <version> <msg>' -> '/learn'"
    @echo ""
    @just --list
