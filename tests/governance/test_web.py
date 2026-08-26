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
        assert "rules" in data or "clusters" in data


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
def test_web_viewer_empty_state_and_4_tab_layout(web_dir: Path) -> None:
    """Verify viewer.html renders clean empty state on parameterless load and provides 4 streamlined workspaces."""
    viewer_file = web_dir / "credence.report" / "viewer.html"
    content = viewer_file.read_text(encoding="utf-8")

    # Clean empty state on parameterless load & canonical mock corpus
    assert "renderEmptyState" in content
    assert "MOCK_CORPUS" in content

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

    # 3. Verify Dedicated Operator Admin Cockpit (admin.credence.run)
    admin_file = web_dir / "admin.credence.run" / "index.html"
    assert admin_file.exists()
    admin_content = admin_file.read_text(encoding="utf-8")
    assert "admin-locked-view" in admin_content
    assert "admin-unlocked-view" in admin_content
    assert "adm-daily-budget" in admin_content
    assert "adm-max-tokens" in admin_content
    assert "info-btn" in admin_content

    # 4. Verify Nexus Mesh Operations Observatory (credence.nexus)
    nexus_file = web_dir / "credence.nexus" / "index.html"
    assert nexus_file.exists()
    nexus_content = nexus_file.read_text(encoding="utf-8")
    assert "tab-topology" in nexus_content
    assert "tab-leaderboard" in nexus_content
    assert "tab-vitals" in nexus_content
    assert "tab-merit" in nexus_content
    assert "tab-studio" in nexus_content
    assert "tab-seeds" in nexus_content
    assert "info-btn" in nexus_content

    # 5. Verify Report Epistemic Forensic Lab
    report_file = web_dir / "credence.report" / "index.html"
    assert report_file.exists()
    report_content = report_file.read_text(encoding="utf-8")
    assert "tab-search" in report_content or "tab-inspector" in report_content
    assert "tab-browse" in report_content or "tab-dossier" in report_content
    assert "tab-dci" in report_content
    assert "tab-sifter" in report_content
    assert "deck-shell" in report_content
    assert "deck-rail" in report_content
    assert "info-btn" in report_content

    # Verify tab order: Source Dossier (#2) precedes DCI (#3)
    dossier_idx = report_content.find('id="rail-btn-dossier"')
    dci_idx = report_content.find('id="rail-btn-dci"')
    assert dossier_idx < dci_idx, "Source Dossier (#2) must logically precede DCI (#3)"


@pytest.mark.governance
def test_nexus_merit_badge_studio_governance(web_dir: Path) -> None:
    """Verify credence.nexus provides the Epistemic Merit 8-badge showcase and Universal Badge Studio."""
    nexus_file = web_dir / "credence.nexus" / "index.html"
    assert nexus_file.exists()
    content = nexus_file.read_text(encoding="utf-8")

    # 8-badge Merit matrix showcase
    assert "merit-showcase-grid" in content
    assert "merit-node-select" in content
    assert "sprout_node" in content
    assert "verified_auditor" in content

    # Universal Badge Studio 3-Modality Tabs & Panes
    assert "tab-btn-studio-node" in content
    assert "tab-btn-studio-publisher" in content
    assert "tab-btn-studio-attestation" in content
    assert "studio-pane-node" in content
    assert "studio-pane-publisher" in content
    assert "studio-pane-attestation" in content
    assert "badge-node-select" in content
    assert "badge-id-select" in content
    assert "badge-publisher-input" in content
    assert "badge-attestation-input" in content
    assert "badge-style-select" in content
    assert "badge-live-preview-container" in content
    assert "badge-embed-snippet" in content
    assert "btn-copy-embed" in content


@pytest.mark.governance
def test_web_foundation_anti_truncation_invariant(web_dir: Path) -> None:
    """Verify credence.foundation taxonomy catalog headers never truncate text with ellipsis."""
    found_file = web_dir / "credence.foundation" / "index.html"
    content = found_file.read_text(encoding="utf-8")

    # Anti-Truncation Invariant: No ellipsis truncation on catalog headers
    assert "text-overflow:ellipsis" not in content, "Foundation catalog headers must not use text-overflow:ellipsis"
    assert "text-overflow: ellipsis" not in content, "Foundation catalog headers must not use text-overflow: ellipsis"
    assert "📰 Society of Professional Journalists (SPJ) Code of Ethics" in content
    assert "🧠 Internet Encyclopedia of Philosophy (IEP) Fallacies" in content
    assert "🛑 Deceptive UI Patterns Catalog" in content


@pytest.mark.governance
def test_web_vanilla_js_syntax_integrity(web_dir: Path) -> None:
    """Verify all inline <script> tags in web HTML files are free of JS syntax errors."""
    import re
    import subprocess

    for html_file in web_dir.glob("*/*.html"):
        content = html_file.read_text(encoding="utf-8")
        script_matches = re.finditer(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", content, re.DOTALL)
        for idx, match in enumerate(script_matches):
            attrs = match.group("attrs")
            clean_script = match.group("body").strip()
            if not clean_script or "src=" in attrs:
                continue

            if "application/ld+json" in attrs or "application/json" in attrs:
                try:
                    json.loads(clean_script)
                except Exception as e:
                    pytest.fail(f"Invalid JSON in {html_file.name} (script #{idx + 1}): {e}")
                continue

            is_module = 'type="module"' in attrs or "type='module'" in attrs
            cmd = ["node", "--check"]
            if is_module:
                cmd.extend(["--input-type=module"])

            res = subprocess.run(
                cmd,
                input=clean_script,
                capture_output=True,
                text=True,
            )
            assert res.returncode == 0, f"JS syntax error in {html_file.name} (script #{idx + 1}):\n{res.stderr}"


@pytest.mark.governance
def test_web_credence_widget_epistemic_integrity(web_dir: Path) -> None:
    """Verify credence-widget.js implements genuine WebCrypto DOM hashing and zero dummy data."""
    import subprocess

    widget_file = web_dir / "assets" / "credence-widget.js"
    assert widget_file.exists(), "web/assets/credence-widget.js must exist"
    content = widget_file.read_text(encoding="utf-8")

    # 1. Zero dummy fake fallback strings
    assert "ed25519:e3b0c44...41a7" not in content, "Must not contain fake dummy Ed25519 fallback key"
    assert "+2.4 pts (Improving)" not in content, "Must not contain fake static trajectory string"
    assert "M 10 28 L 60 22 L 120 16 L 180 8" not in content, "Must not contain hardcoded fake sparkline"

    # 2. Live WebCrypto DOM Hashing Integration
    assert "crypto.subtle.digest" in content, "Must implement live WebCrypto SHA-256 DOM hashing"
    assert "computeLiveDomHash" in content, "Must provide computeLiveDomHash method"

    # 3. Modality-Specific 3-Tier Lensing
    assert "renderNodeLens" in content, "Must provide dedicated Node Epistemic Merit lens"
    assert "renderPublisherLens" in content, "Must provide dedicated Publisher Reputation lens"
    assert "renderAttestationLens" in content, "Must provide dedicated Article Attestation lens"

    # 4. Zero npm dependencies & pure ES Module syntax
    res = subprocess.run(
        ["node", "--check", "--input-type=module"],
        input=content,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"JS syntax error in credence-widget.js:\n{res.stderr}"


@pytest.mark.governance
def test_zero_mock_production_boundary(web_dir: Path) -> None:
    """Assert zero synthetic mock data, dummy keys, or fallback placeholder arrays exist in production web workstations."""
    banned_tokens = [
        "MOCK_NODES",
        "mock_nodes",
        "MOCK_REPORTS",
        "mock_reports",
        "dummy_key",
        "fake_key",
        "ed25519:e3b0c44...41a7",
        "+2.4 pts (Improving)",
        "synthetic_digest",
        "placeholder_sparkline",
    ]
    for ext in ["*.js", "*.html"]:
        for file_path in web_dir.rglob(ext):
            content = file_path.read_text(encoding="utf-8")
            for token in banned_tokens:
                assert token not in content, (
                    f"Violation of inv-production-telemetry-boundary: Banned mock token '{token}' "
                    f"found in production web surface: {file_path.relative_to(web_dir.parent)}"
                )


@pytest.mark.governance
def test_workstation_scroll_and_lensing_governance(web_dir: Path) -> None:
    """Verify workstation vertical scrollability and human-readable surface lensing with rich cross-links."""
    css_file = web_dir / "assets" / "credence-ui.css"
    assert css_file.exists(), "web/assets/credence-ui.css must exist"
    css_content = css_file.read_text(encoding="utf-8")

    # Invariant: Active tab panel must natively permit vertical scrolling
    assert ".tab-panel.active" in css_content
    assert "overflow-y: auto" in css_content

    report_index = web_dir / "credence.report" / "index.html"
    assert report_index.exists(), "web/credence.report/index.html must exist"
    report_content = report_index.read_text(encoding="utf-8")

    # Invariant: Surface glance lens must have human-readable cards and rich cross-links
    assert "insp-surface-verdict-badge" in report_content
    assert "insp-surface-takeaways" in report_content
    assert "insp-surface-publisher-title" in report_content
    assert "insp-surface-dossier-btn" in report_content
    assert "insp-surface-related-list" in report_content
    assert "insp-surface-viewer-link" in report_content
    assert "insp-surface-history-link" in report_content

    # Invariant: Search landing prompt must feature case studies and quick publisher/issue shortcuts
    assert "search-landing-prompt" in report_content
    assert "applyQuickFilter" in report_content
    assert "reuters.com" in report_content
    assert "inmaricopa.com" in report_content


@pytest.mark.governance
def test_universal_scrollbar_styling_invariant(web_dir: Path) -> None:
    """Verify universal custom scrollbar styling across all workstation surfaces and search/audit views."""
    css_file = web_dir / "assets" / "credence-ui.css"
    assert css_file.exists(), "web/assets/credence-ui.css must exist"
    css_content = css_file.read_text(encoding="utf-8")

    # 1. Standard CSS Scrollbars (Firefox / Standard)
    assert "scrollbar-width: thin" in css_content, "Missing universal scrollbar-width: thin"
    assert "scrollbar-color:" in css_content, "Missing universal scrollbar-color definition"
    assert "rgba(56, 189, 248" in css_content, "Scrollbar must use cyan design system accent"

    # 2. WebKit / Blink Pseudo-Elements
    assert "*::-webkit-scrollbar" in css_content, "Universal *::-webkit-scrollbar rule missing"
    assert "*::-webkit-scrollbar-track" in css_content, "Universal *::-webkit-scrollbar-track rule missing"
    assert "*::-webkit-scrollbar-thumb" in css_content, "Universal *::-webkit-scrollbar-thumb rule missing"
    assert "*::-webkit-scrollbar-thumb:hover" in css_content, "Universal *::-webkit-scrollbar-thumb:hover rule missing"

    # 3. Explicit Workstation & Search Containers
    required_selectors = [
        "#tab-search",
        "#search-results-list",
        ".tab-panel",
        ".tab-panel.active",
        "#tab-browse",
        "#tab-dci",
        "#tab-sifter",
        ".ws-scroll-pane",
        ".ws-table-container",
        "#sifter-stream-container",
        ".log-terminal-body",
    ]
    for sel in required_selectors:
        assert sel in css_content, f"Selector {sel} missing from scrollbar styling rules"
