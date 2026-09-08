export const CREDENCE_VERSION = "v2.21.0";
/**
 * Credence Workstation Engine & Shared Zero-Build Controller (credence-workstation.js)
 * 
 * Provides:
 * 1. Global Keyboard Navigation ([1-5] tabs, [/] search, [v] view mode, [r] random, [?] shortcuts, [Esc] close)
 * 2. Pluggable Admin Authentication & Operator Session Management (Key / OAuth / 401 Interception)
 * 3. Terminal Scanline / Monospace TUI HUD Mode Switcher
 * 4. In-Browser WebCrypto Ed25519 Signature Verification
 * 5. Dynamic API Resolution & Transparent Request Interception (fetchWithAuth)
 */


// Re-export authentication subsystem
export * from './workstation-auth.js';

// Re-export modals, toasts & epistemic information pyramid
export * from './workstation-modals.js';

// Re-export WebCrypto Ed25519 verification
export * from './workstation-crypto.js';

// Re-export navigation & TUI helpers
export * from './workstation-nav.js';

// Re-export info topics
export * from './workstation-topics.js';

export const INVARIANTS_REGISTRY = {
  "inv-workspace-isolation": { legacyId: 1, class: "Class β", scope: "universal", title: "Project & Workspace Isolation" },
  "inv-async-sqlmodel": { legacyId: 2, class: "Class β", scope: "universal", title: "Python & SQLModel Async Architecture" },
  "inv-version-governance": { legacyId: 3, class: "Class γ", scope: "universal", title: "Continuous Changelog & Semantic Version Governance" },
  "inv-hermetic-unit-tests": { legacyId: 4, class: "Class β", scope: "universal", title: "Hermetic Unit Test Isolation & Zero-Browser CI" },
  "inv-scoped-verification": { legacyId: 5, class: "Class β", scope: "universal", title: "Scoped Verification for Docs-Only Changes" },
  "inv-mk1-eyeball": { legacyId: 6, class: "Class α", scope: "universal", title: "Human Review Gate (\"Mk1 Eyeball\")" },
  "inv-clean-scratch-scripts": { legacyId: 46, class: "Class α", scope: "universal", title: "Clean Brain Scratch Script Approvals" },
  "inv-untrusted-ingestion": { legacyId: 8, class: "Class α", scope: "universal", title: "Untrusted Ingestion Boundary & Network Defense" },
  "inv-xml-safety": { legacyId: 10, class: "Class β", scope: "universal", title: "XML ElementTree Traversal Safety" },
  "inv-ground-truth-config": { legacyId: 11, class: "Class β", scope: "universal", title: "Model Default Truth & Verification Guardrail" },
  "inv-fastmcp-transport-security": { legacyId: 12, class: "Class β", scope: "universal", title: "FastMCP 2.0 Reverse Proxy Transport Security" },
  "inv-fastmcp-datetime-serialization": { legacyId: 16, class: "Class γ", scope: "universal", title: "FastMCP Nested Datetime Serialization" },
  "inv-content-decoupling": { legacyId: 17, class: "Class β", scope: "universal", title: "Content Decoupling & Hermetic CI" },
  "inv-progressive-disclosure": { legacyId: 18, class: "Class γ", scope: "universal", title: "Context Governance & Progressive Disclosure" },
  "inv-cart-before-horse": { legacyId: 43, class: "Class β", scope: "universal", title: "The Cart-Before-the-Horse Order-of-Operations Invariant" },
  "inv-commit-before-deploy": { legacyId: 47, class: "Class β", scope: "universal", title: "Commit-Before-Deploy & Push-and-Delegate CI/CD Gate" },
  "inv-incremental-commits-staging": { legacyId: 48, class: "Class β", scope: "universal", title: "Incremental Commits & Staging Topology" },
  "inv-4phase-release-learning": { legacyId: 49, class: "Class β", scope: "universal", title: "4-Phase Release & Lean Learning Lifecycle" },
  "inv-3plane-governance": { legacyId: 50, class: "Class β", scope: "universal", title: "3-Plane Deployment Governance" },
  "inv-dual-env-least-privilege-cicd": { legacyId: 51, class: "Class β", scope: "universal", title: "Dual-Environment Least-Privilege CI/CD & Dev Preview Isolation" },
  "inv-multi-model-sovereignty": { legacyId: 7, class: "Class γ", scope: "universal", title: "Multi-Model Sovereignty & Token Circuit Breakers" },
  "inv-verbatim-anti-truncation": { legacyId: 52, class: "Class α", scope: "universal", title: "Universal Verbatim Anti-Truncation UI" },
  "inv-documentation-expansion": { legacyId: 53, class: "Class γ", scope: "universal", title: "Session-Driven Documentation Expansion" },
  "inv-living-canon": { legacyId: 54, class: "Class γ", scope: "universal", title: "Dynamic Invariant Canon (\"The Invariant Bible\")" },
  "inv-production-telemetry-boundary": { legacyId: 55, class: "Class γ", scope: "universal", title: "Production Telemetry vs. Simulation Boundary" },
  "inv-clean-slug-routing": { legacyId: 56, class: "Class γ", scope: "universal", title: "Zero-Hash Clean URL Routing & Canonical Slugs" },
  "inv-article-h1-header": { legacyId: 57, class: "Class γ", scope: "universal", title: "Anti-Headless Article Invariant" },
  "inv-topic-entropy-defense": { legacyId: 19, class: "Class γ", scope: "domain", title: "Topic Entropy Astroturfing Defense (The Pizza Hut Problem)" },
  "inv-poes-law-satire": { legacyId: 20, class: "Class γ", scope: "domain", title: "Poe's Law & Satire Safeguards" },
  "inv-fixed-taxonomies": { legacyId: 21, class: "Class β", scope: "domain", title: "Namespaced Fixed Taxonomies" },
  "inv-verbatim-grounding": { legacyId: 22, class: "Class α", scope: "domain", title: "Whitespace-Insensitive Grounding ($G=1.00$)" },
  "inv-heuristic-disclosure": { legacyId: 23, class: "Class β", scope: "domain", title: "Transparent Heuristic Disclosure" },
  "inv-4k-thinking-budget": { legacyId: 15, class: "Class γ", scope: "domain", title: "Empirical Thinking Budget Sweet Spot (4k Invariant)" },
  "inv-audit-entity-persistence": { legacyId: 58, class: "Class γ", scope: "domain", title: "Audit Entity & Violation Persistence" },
  "inv-canonical-json-ed25519": { legacyId: 24, class: "Class α", scope: "domain", title: "RFC 8785 Canonical JSON & Ed25519 Custody" },
  "inv-5factor-node-quality": { legacyId: 25, class: "Class β", scope: "domain", title: "5-Factor Node Quality ($Q_i$)" },
  "inv-empirical-expertise": { legacyId: 26, class: "Class β", scope: "domain", title: "Empirical Expertise ($E_i$) & Anti-Diploma Invariant" },
  "inv-galileo-rule": { legacyId: 27, class: "Class β", scope: "domain", title: "The Galileo Rule (Asymmetric Grounded Evidence)" },
  "inv-bittorrent-worksharing": { legacyId: 28, class: "Class β", scope: "domain", title: "BitTorrent Work-Sharing & Generous Defaults" },
  "inv-byzantine-cartel-resistance": { legacyId: 29, class: "Class β", scope: "domain", title: "Byzantine Cartel Resistance ($3f+1$)" },
  "inv-boredom-root-expansion": { legacyId: 39, class: "Class β", scope: "domain", title: "Opportunistic Boredom Ingestion & Root Expansion" },
  "inv-soft-blacklist-buzzfeed": { legacyId: 40, class: "Class β", scope: "domain", title: "Soft Blacklisting & BuzzFeed News Doctrine" },
  "inv-multi-interface-parity": { legacyId: 30, class: "Class γ", scope: "universal", title: "Universal Multi-Interface Feature Parity" },
  "inv-zero-build-standards": { legacyId: 31, class: "Class γ", scope: "universal", title: "Universal Zero-Build Standards (Zero-npm Invariant)" },
  "inv-zero-build-math": { legacyId: 32, class: "Class γ", scope: "universal", title: "Zero-Build Math & Currency Invariant" },
  "inv-cloudflare-assets": { legacyId: 13, class: "Class β", scope: "domain", title: "Cloudflare Workers Zero-Build Static Assets" },
  "inv-edge-origin-header": { legacyId: 14, class: "Class β", scope: "domain", title: "Edge Routing Origin Header Translation" },
  "inv-edge-canonicalization": { legacyId: 33, class: "Class β", scope: "domain", title: "Edge Subdirectory Canonicalization" },
  "inv-mermaid-syntax-safety": { legacyId: 34, class: "Class β", scope: "universal", title: "Universal Technical Schematic & Visual Syntax Guardrail" },
  "inv-visual-density": { legacyId: 35, class: "Class γ", scope: "universal", title: "Visual Density & Anti-Wall-of-Text Invariant" },
  "inv-playwright-rendering-tests": { legacyId: 36, class: "Class β", scope: "universal", title: "Automated Live Rendering Regression Verification" },
  "inv-inline-html-math-integrity": { legacyId: 37, class: "Class γ", scope: "universal", title: "Zero-Build Inline HTML & Nested Math Integrity" },
  "inv-anti-scrollbox": { legacyId: 38, class: "Class γ", scope: "universal", title: "Anti-Scrollbox & Natural Flow Presentation" },
  "inv-symmetric-navigation-zero-cache": { legacyId: 41, class: "Class γ", scope: "domain", title: "Symmetric 4-Pillar Navigation & Zero-Cache Edge" },
  "inv-epistemic-lensing": { legacyId: 42, class: "Class γ", scope: "universal", title: "The Epistemic Lensing & Information Pyramid Invariant" },
  "inv-web-component-isolation": { legacyId: 44, class: "Class γ", scope: "universal", title: "Web Component Isolation & Zero-Clone Safety" },
  "inv-dense-workstation-viewport": { legacyId: 45, class: "Class γ", scope: "domain", title: "Dense Workstation Viewport & Zero-Masking Invariant" },
  "inv-sovereign-config-decoupling": { legacyId: 59, class: "Class α", scope: "universal", title: "Sovereign Multi-Tenant Decoupling & Zero Hardcoded Tenant Config" },
  "inv-artifact-curation": { legacyId: 60, class: "Class γ", scope: "universal", title: "The Artifact Archival & Anti-Wipe Invariant (\"That Belongs in a Museum!\")" },
  "inv-narrative-plot-fidelity": { legacyId: 61, class: "Class γ", scope: "universal", title: "Universal Narrative Plot Fidelity & Anti-Boilerplate Invariant (\"Never Lose the Plot\")" },
};

export function resolveInvariant(slugOrId) {
  if (INVARIANTS_REGISTRY[slugOrId]) {
    return { slug: slugOrId, ...INVARIANTS_REGISTRY[slugOrId] };
  }
  const clean = String(slugOrId).replace(/^invariant-/, '');
  const num = parseInt(clean, 10);
  if (!isNaN(num)) {
    for (const [slug, item] of Object.entries(INVARIANTS_REGISTRY)) {
      if (item.legacyId === num) {
        return { slug, ...item };
      }
    }
  }
  return { slug: String(slugOrId), legacyId: 0, class: "Living Canon", title: String(slugOrId) };
}


export function initWorkstation(config = {}) {
  const options = typeof config === 'string' ? { defaultTab: config } : (config || {});
  const {
    tabButtonsSelector = '[data-tab], .deck-nav-item, .workstation-tab-btn, .deck-admin-link',
    tabPanelsSelector = '.tab-panel',
    defaultTab = null,
    onTabChange = null,
  } = options;

  initTuiMode();
  injectOperatorModal();
  injectShortcutsModal();
  checkAuthStatus();
  normalizeLocalLinks();

  function switchTab(tabId, pushHistory = false, updateHash = true) {
    if (!tabId) return;

    const btns = document.querySelectorAll(tabButtonsSelector);
    const panels = document.querySelectorAll(tabPanelsSelector);

    btns.forEach(btn => {
      const btnTab = btn.getAttribute('data-tab') || btn.getAttribute('href')?.replace(/^#/, '');
      const match = btnTab === tabId;
      btn.classList.toggle('active', match);
    });

    panels.forEach(p => {
      const match = p.id === `tab-${tabId}` || p.getAttribute('data-tab') === tabId;
      p.classList.toggle('active', match);
      if (match) p.style.display = 'flex';
      else p.style.display = 'none';
    });

    if (updateHash) {
      const currentHash = (window.location.hash || '').replace(/^#/, '');
      const isDeepLinkForTab = (
        (tabId === 'browse' && (currentHash.startsWith('analytics/') || currentHash.startsWith('dossier/') || currentHash.startsWith('publisher/') || currentHash.startsWith('browse/'))) ||
        (tabId === 'search' && (currentHash.startsWith('report/') || currentHash.startsWith('inspect/') || currentHash.startsWith('search'))) ||
        (tabId === 'merit' && (currentHash.startsWith('merit') || currentHash.startsWith('badges'))) ||
        (tabId === 'governance' && (currentHash.startsWith('governance') || currentHash.startsWith('invariants')))
      );

      if (!isDeepLinkForTab && window.location.hash !== `#${tabId}`) {
        if (pushHistory) {
          history.pushState({ tab: tabId }, '', `#${tabId}`);
        } else {
          history.replaceState({ tab: tabId }, '', `#${tabId}`);
        }
      }
    }

    normalizeLocalLinks();

    if (typeof onTabChange === 'function') {
      onTabChange(tabId);
    }
  }

  // Expose switchTab on global controller
  window.CredenceWS.switchTab = switchTab;

  // Handle hash changes or default tab
  const initialHash = window.location.hash.replace(/^#/, '');
  let initialTab = defaultTab;
  if (initialHash) {
    if (initialHash.startsWith('analytics/') || initialHash.startsWith('dossier/') || initialHash.startsWith('publisher/') || initialHash.startsWith('browse')) {
      initialTab = 'browse';
    } else if (initialHash.startsWith('report/') || initialHash.startsWith('inspect/') || initialHash.startsWith('audit/') || initialHash.startsWith('search')) {
      initialTab = 'search';
    } else if (initialHash.startsWith('merit') || initialHash.startsWith('badges')) {
      initialTab = 'merit';
    } else if (initialHash.startsWith('nodes') || initialHash.startsWith('mesh') || initialHash.startsWith('peers')) {
      initialTab = 'nodes';
    } else if (initialHash.startsWith('governance') || initialHash.startsWith('taxonomies') || initialHash.startsWith('custody') || initialHash.startsWith('invariants')) {
      initialTab = 'governance';
    } else {
      initialTab = initialHash.split('/')[0] || defaultTab;
    }
  }
  if (initialTab) {
    switchTab(initialTab, false);
  }

  // Bind click handlers to tab buttons
  document.querySelectorAll(tabButtonsSelector).forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const targetTab = btn.getAttribute('data-tab') || btn.getAttribute('href')?.replace(/^#/, '');
      if (targetTab && !targetTab.startsWith('http') && !targetTab.startsWith('/') && !targetTab.includes('.')) {
        e.preventDefault();
        switchTab(targetTab, true);
      }
    });
  });

  // Reactive popstate handler for forward/back browser buttons
  window.addEventListener('popstate', () => {
    if (typeof window.handleLocationRouting === 'function') {
      window.handleLocationRouting();
    }
  });

  // Global Keyboard Navigation
  window.addEventListener('keydown', (e) => {
    // Ignore when user is typing in an input, textarea, or contentEditable element
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName) || e.target.isContentEditable) {
      if (e.key === 'Escape') {
        e.target.blur();
        closeOperatorModal();
        closeShortcutsModal();
      }
      return;
    }

    if (e.key === 'Escape') {
      closeOperatorModal();
      closeShortcutsModal();
      return;
    }

    if (e.key === '?') {
      e.preventDefault();
      toggleShortcutsModal();
      return;
    }

    if (e.key === '/') {
      const search = document.querySelector('input[type="text"], input[type="search"]');
      if (search) {
        e.preventDefault();
        search.focus();
        search.select();
      }
      return;
    }

    // Number keys 1-7 for tab switching
    if (['1', '2', '3', '4', '5', '6', '7'].includes(e.key)) {
      const idx = parseInt(e.key, 10) - 1;
      const tabBtns = document.querySelectorAll(tabButtonsSelector);
      if (tabBtns[idx]) {
        e.preventDefault();
        tabBtns[idx].click();
      }
    }
  });

  return {
    switchTab,
    checkAuthStatus,
    openOperatorModal,
    closeOperatorModal,
    showToast,
    toggleTuiMode,
    fetchWithAuth,
  };
}

// Global export for inline HTML event bindings
window.CredenceWS = window.CredenceWS || {};
Object.assign(window.CredenceWS, {
  authState,
  initWorkstation,
  getApiBaseUrl,
  checkAuthStatus,
  loginWithKey,
  submitKeyLogin,
  loginOAuth,
  switchModalTab,
  togglePasswordVisibility,
  openOperatorModal,
  closeOperatorModal,
  clearStoredToken,
  getStoredToken,
  setStoredToken,
  openShortcutsModal,
  closeShortcutsModal,
  toggleShortcutsModal,
  openInfoModal,
  closeInfoModal,
  switchModalLens,
  toggleTuiMode,
  showToast,
  fetchWithAuth,
  verifyEd25519Signature,
  INFO_TOPICS,
});
