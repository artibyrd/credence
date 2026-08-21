"""Unit tests for the Zero-Build Web Presentation Layer (Invariant 20).

Validates:
1. All public frontends use vanilla HTML5/CSS/ES Modules with zero npm dependencies.
2. Report viewer contains valid attestation rendering and Ed25519 verification elements.
3. Seed manifests and taxonomy mirrors contain valid JSON schemas.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def web_dir() -> Path:
    """Return path to web presentation directory."""
    return Path(__file__).resolve().parents[2] / "web"


@pytest.mark.governance
def test_web_run_landing_hub(web_dir: Path) -> None:
    """Verify credence.run landing page structure and zero-build integrity."""
    index_file = web_dir / "credence.run" / "index.html"
    assert index_file.exists(), "credence.run/index.html must exist"

    content = index_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Credence" in content
    assert "FastMCP" in content
    assert "epistemic" in content.lower()

    # Invariant 20: Zero npm/node JS frameworks (no react, vue, angular bundles)
    assert "react.production.min.js" not in content
    assert "vue.global.js" not in content
    assert "bundle.js" not in content


@pytest.mark.governance
def test_web_report_viewer_web_crypto(web_dir: Path) -> None:
    """Verify credence.report viewer implements zero-build attestation rendering and human-friendly features."""
    viewer_file = web_dir / "credence.report" / "viewer.html"
    assert viewer_file.exists(), "credence.report/viewer.html must exist"

    content = viewer_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "ED25519 VERIFIED" in content
    assert "RFC 8785" in content
    assert "violations-container" in content
    assert "score-big" in content

    # Human-First & Discovery Features
    assert "exec-summary-card" in content, "Executive summary card must be present"
    assert "trust-signals" in content, "Trust signals container must be present"
    assert "tab-reader" in content, "In-context reading mode tab must be present"
    assert "reader-article-body" in content, "Article body container must be present"
    assert "tab-findings" in content, "Itemized findings tab must be present"
    assert "filter-chip" in content, "Interactive filter chips must be present"
    assert "tab-export" in content, "Export tab must be present"
    assert "copyMarkdownSummary" in content, "1-click Markdown export must be present"
    assert "dim-ethics-score" in content, "Trust dimensions breakdown must be present"

    # Enhanced v1.5.1 Layout & Ingestion Features
    assert "mode-switcher" in content, "View mode switcher must be present"
    assert "btn-mode-human" in content, "Human view button must be present"
    assert "btn-mode-compact" in content, "Compact view button must be present"
    assert "btn-mode-raw" in content, "Machine view button must be present"
    assert "discover-toolbar" in content, "Quick discovery toolbar must be present"
    assert "pill-random" in content, "Random surprise pill must be present"
    assert "discovery-drawer" in content, "Interactive discovery drawer must be present"
    assert "export-stack" in content, "Stacked export layout must replace squished grid"
    assert "view-compact" in content, "Compact dense view container must be present"
    assert "view-raw" in content, "Machine raw view container must be present"
    assert "schema-claim-review" in content, "Schema.org ClaimReview LD+JSON must be present"

    # Zero-Build Invariant 20: 0 npm packages
    assert "node_modules" not in content
    assert "package.json" not in content
    assert "npm install" not in content

    # Dynamic API Auto-Discovery & Live Sifter Bridge
    assert "getApiBaseUrl" in content, "Dynamic API base URL detection must be present"
    assert "fetchDynamicCorpus" in content, "Dynamic corpus fetcher must be present"
    assert "checkUrlHashData" in content, "Direct URL hash payload loader must be present"


@pytest.mark.governance
def test_web_edge_router_api_proxy(web_dir: Path) -> None:
    """Verify Cloudflare Worker edge router proxies /api/* requests to backend."""
    worker_file = web_dir / "_worker.js"
    assert worker_file.exists(), "_worker.js must exist"

    content = worker_file.read_text(encoding="utf-8")
    assert "url.pathname.startsWith('/api/')" in content, "_worker.js must proxy /api/ routes"
    assert "credence-server" in content, "Cloud Run backend origin must be configured"


@pytest.mark.governance
def test_web_nexus_peers_manifest(web_dir: Path) -> None:
    """Verify seeds.credence.nexus peers.json manifest format."""
    peers_file = web_dir / "credence.nexus" / "peers.json"
    assert peers_file.exists(), "credence.nexus/peers.json must exist"

    data = json.loads(peers_file.read_text(encoding="utf-8"))
    assert "generated_at" in data
    assert "canonical_domain" in data
    assert "seed_nodes" in data
    assert isinstance(data["seed_nodes"], list)
    assert len(data["seed_nodes"]) >= 1


@pytest.mark.governance
def test_web_foundation_taxonomies_and_keys(web_dir: Path) -> None:
    """Verify credence.foundation static taxonomy mirrors and public key custody."""
    foundation_dir = web_dir / "credence.foundation"
    assert foundation_dir.exists()

    # Verify root.pub exists
    root_pub = foundation_dir / "keys" / "root.pub"
    assert root_pub.exists()
    assert len(root_pub.read_text(encoding="utf-8").strip()) == 64

    # Verify v1 JSON taxonomy catalogs
    v1_dir = foundation_dir / "v1"
    for cat_name in ("spj_ethics.json", "iep_fallacies.json", "deceptive_patterns.json"):
        cat_file = v1_dir / cat_name
        assert cat_file.exists(), f"Catalog {cat_name} must exist"
        data = json.loads(cat_file.read_text(encoding="utf-8"))
        assert "catalog_id" in data
        assert "clusters" in data


@pytest.mark.governance
def test_web_reports_json_schema_completeness(web_dir: Path) -> None:
    """Verify web/credence.report/reports.json contains rich fields for all catalog records."""
    reports_file = web_dir / "credence.report" / "reports.json"
    assert reports_file.exists(), "reports.json must exist"

    data = json.loads(reports_file.read_text(encoding="utf-8"))
    assert data.get("status") == "ready"
    assert "reports" in data
    assert isinstance(data["reports"], list)
    assert len(data["reports"]) >= 1

    for r in data["reports"]:
        assert "id" in r
        assert "url" in r
        assert "title" in r
        assert "category" in r
        assert "content_sha256" in r
        assert len(r["content_sha256"]) > 0
        assert "simhash_64" in r
        assert "suspicion_score" in r
        assert "classification" in r
        assert "audited_at" in r
        assert "violations" in r
        assert isinstance(r["violations"], list)

        if len(r["violations"]) > 0:
            for v in r["violations"]:
                assert "rule_id" in v
                assert "domain" in v
                assert "severity" in v
                assert "reasoning" in v


@pytest.mark.governance
def test_web_viewer_heuristic_suspicion_safeguards(web_dir: Path) -> None:
    """Verify viewer.html enforces dimension score capping, template grammar checks, and zero false green tags on high suspicion."""
    viewer_file = web_dir / "credence.report" / "viewer.html"
    content = viewer_file.read_text(encoding="utf-8")

    # Guard against broken executive summary template gap "identified . Readers"
    assert "elevated heuristic suspicion" in content, "Viewer must include descriptive fallback for summary audits"
    assert "High Deception Risk" in content, "Viewer must flag high deception risk signals"

    # Guard against 100/100 trust dimensions on high suspicion
    assert "decScore = Math.min(decScore" in content or "Math.max(0, Math.round(100 - suspScore))" in content, (
        "Viewer must discount trust dimensions when suspicion score is high"
    )

    # Informative fallback in findings list for summary audits
    assert "Heuristic Deception Signals Detected" in content, (
        "Findings list must explain summary audits with elevated suspicion"
    )


@pytest.mark.governance
def test_web_viewer_css_tab_and_hash_integrity(web_dir: Path) -> None:
    """Verify styles.css enforces responsive tabs and clean monospace hash wrapping."""
    css_file = web_dir / "credence.report" / "styles.css"
    content = css_file.read_text(encoding="utf-8")

    # Responsive tab bar & scrollbar
    assert "scrollbar-width: thin" in content
    assert "flex-shrink: 0" in content

    # Clean monospace hash wrapping
    assert "overflow-wrap: anywhere" in content

    # Sub-view toggle styling
    assert ".findings-subnav-toggle" in content
    assert ".view-toggle-btn" in content


@pytest.mark.governance
def test_web_viewer_randomized_default_selection_and_4_tab_layout(web_dir: Path) -> None:
    """Verify viewer.html randomizes default report selection on load and provides 4 streamlined workspaces."""
    viewer_file = web_dir / "credence.report" / "viewer.html"
    content = viewer_file.read_text(encoding="utf-8")

    # Randomized default report selection
    assert "Math.random() * dynamicCorpus.length" in content
    assert "Math.random() * MOCK_CORPUS.length" in content

    # 4-Tab consolidated navigation
    assert "tab-overview" in content
    assert "tab-findings" in content
    assert "tab-publisher" in content
    assert "tab-crypto" in content

    # Sub-view toggle between Cards and In-Context Reader
    assert "toggleFindingsView" in content
    assert "findings-cards-view" in content
    assert "findings-reader-view" in content
    assert "findings-toggle-cards" in content
    assert "findings-toggle-reader" in content

    # Share & Export consolidated in Cryptographic Proof & Export tab
    assert "export-stack" in content
    assert "copyMarkdownSummary" in content
    assert "copyJsonAttestation" in content
    assert "copyBadgeSnippet" in content


@pytest.mark.governance
def test_web_workstation_architecture_and_admin_deck(web_dir: Path) -> None:
    """Verify zero-build Workstation architecture, Admin Command Deck, and shared JS engine."""
    # 1. Verify shared workstation engine
    ws_js = web_dir / "assets" / "credence-workstation.js"
    assert ws_js.exists(), "assets/credence-workstation.js must exist"
    ws_content = ws_js.read_text(encoding="utf-8")
    assert "initWorkstation" in ws_content
    assert "checkAuthStatus" in ws_content
    assert "fetchWithAuth" in ws_content
    assert "verifyEd25519Signature" in ws_content
    assert "toggleTuiMode" in ws_content
    assert "openInfoModal" in ws_content
    assert "closeInfoModal" in ws_content

    # 2. Verify Foundation Constitutional Vault
    found_file = web_dir / "credence.foundation" / "index.html"
    assert found_file.exists()
    found_content = found_file.read_text(encoding="utf-8")
    assert "tab-taxonomies" in found_content
    assert "tab-custody" in found_content
    assert "tab-sandbox" in found_content
    assert "verifyEd25519Signature" in found_content
    assert "v1/spj_ethics.json" in found_content
    assert "info-btn" in found_content

    # 3. Verify Nexus Mesh Operations & Admin Command Deck
    nexus_file = web_dir / "credence.nexus" / "index.html"
    assert nexus_file.exists()
    nexus_content = nexus_file.read_text(encoding="utf-8")
    assert "tab-topology" in nexus_content
    assert "tab-leaderboard" in nexus_content
    assert "tab-vitals" in nexus_content
    assert "tab-admin" in nexus_content
    assert "admin-cockpit-grid" in nexus_content
    assert "adm-daily-budget" in nexus_content
    assert "adm-max-tokens" in nexus_content
    assert "triggerEmergencyStop" in nexus_content
    assert "info-btn" in nexus_content

    # 4. Verify Report Epistemic Forensic Lab
    report_file = web_dir / "credence.report" / "index.html"
    assert report_file.exists()
    report_content = report_file.read_text(encoding="utf-8")
    assert "tab-inspector" in report_content
    assert "tab-dossier" in report_content
    assert "tab-dci" in report_content
    assert "tab-sifter" in report_content
    assert "article-subview-diff" in report_content
    assert "deck-shell" in report_content
    assert "deck-rail" in report_content
    assert "pinned-sources-container" in report_content
    assert "pinCurrentSource" in report_content
    assert "info-btn" in report_content

    # Verify tab order: Source Dossier (#2) precedes DCI (#3)
    dossier_idx = report_content.find('id="rail-btn-dossier"')
    dci_idx = report_content.find('id="rail-btn-dci"')
    assert dossier_idx < dci_idx, "Source Dossier (#2) must logically precede DCI (#3)"
