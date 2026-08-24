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
    @just --list
