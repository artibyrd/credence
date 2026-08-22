# Justfile for Credence Epistemic Ecosystem
# Canonical Parameterized Architecture & Modular 500 LOC Subfiles
# Invariant: 500 LOC Ceiling Law & Shift-Left Intelligent Guidance Highway

set shell := ["bash", "-c"]

# Modular Category Imports (Strictly < 300 LOC each)
import "just/preflight.just"
import "just/quality.just"
import "just/engine.just"
import "just/deploy.just"
import "just/release.just"

default:
    @just --list
