export const CREDENCE_VERSION = "v2.12.1";
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

export function getApiBaseUrl() {
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1') {
    return (window.location.port && window.location.port !== '8000') ? `http://${host}:8000` : '';
  }
  return '';
}

// -----------------------------------------------------------------------------
// OPERATOR AUTHENTICATION & SESSION MANAGEMENT
// -----------------------------------------------------------------------------

export const authState = {
  authenticated: false,
  role: 'ANONYMOUS',
  identity: null,
  method: null,
};

export function getStoredToken() {
  return sessionStorage.getItem('credence_admin_token') || localStorage.getItem('credence_admin_token') || '';
}

export function setStoredToken(token, remember = true) {
  if (token) {
    localStorage.setItem('credence_admin_token', token);
    sessionStorage.setItem('credence_admin_token', token);
  }
}

export function clearStoredToken() {
  sessionStorage.removeItem('credence_admin_token');
  localStorage.removeItem('credence_admin_token');
  authState.authenticated = false;
  authState.role = 'ANONYMOUS';
  authState.identity = null;
  authState.method = null;
  updateRibbonAuthBadge();
  window.dispatchEvent(new CustomEvent('credence-auth-changed', { detail: authState }));
  if (typeof window.renderAdminView === 'function') {
    window.renderAdminView();
  }
  showToast('🔒 Operator Console Locked', 'info');
}

export async function checkAuthStatus() {
  const token = getStoredToken();
  if (!token) {
    authState.authenticated = false;
    authState.role = 'ANONYMOUS';
    authState.identity = null;
    authState.method = null;
    updateRibbonAuthBadge();
    window.dispatchEvent(new CustomEvent('credence-auth-changed', { detail: authState }));
    if (typeof window.renderAdminView === 'function') {
      window.renderAdminView();
    }
    return false;
  }

  // Optimistically set active for stored token to prevent flash of locked screen
  authState.authenticated = true;
  authState.role = 'OPERATOR';
  authState.identity = 'admin';
  authState.method = 'API_KEY';
  updateRibbonAuthBadge();
  if (typeof window.renderAdminView === 'function') {
    window.renderAdminView();
  }

  const apiBase = getApiBaseUrl();
  try {
    const headers = { 'Authorization': `Bearer ${token}`, 'X-Credence-Admin-Key': token };
    const res = await fetch(`${apiBase}/api/auth/verify`, { headers });
    if (res.ok) {
      const data = await res.json();
      authState.authenticated = true;
      authState.role = data.role || 'OPERATOR';
      authState.identity = data.identity || 'admin';
      authState.method = data.method || 'API_KEY';
      updateRibbonAuthBadge();
      window.dispatchEvent(new CustomEvent('credence-auth-changed', { detail: authState }));
      if (typeof window.renderAdminView === 'function') {
        window.renderAdminView();
      }
      return true;
    } else {
      // Stored token is invalid or expired
      clearStoredToken();
      return false;
    }
  } catch (e) {
    // Offline mode: retain cached authenticated state for stored token
    updateRibbonAuthBadge();
    window.dispatchEvent(new CustomEvent('credence-auth-changed', { detail: authState }));
    if (typeof window.renderAdminView === 'function') {
      window.renderAdminView();
    }
    return true;
  }
}

export async function loginWithKey(key, remember = true) {
  const apiBase = getApiBaseUrl();
  try {
    const res = await fetch(`${apiBase}/api/auth/verify`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${key}`, 'X-Credence-Admin-Key': key }
    });
    if (res.ok) {
      setStoredToken(key, remember);
      await checkAuthStatus();
      closeOperatorModal();
      showToast('✅ Operator Authenticated Successfully', 'success');
      window.dispatchEvent(new CustomEvent('credence-auth-changed', { detail: authState }));
      if (typeof window.renderAdminView === 'function') {
        window.renderAdminView();
      }
      return true;
    } else {
      showToast('❌ Invalid Admin API Key', 'error');
      return false;
    }
  } catch (e) {
    showToast('❌ Could not connect to authentication server', 'error');
    return false;
  }
}

export async function fetchWithAuth(url, options = {}) {
  const apiBase = getApiBaseUrl();
  const targetUrl = url.startsWith('http') ? url : `${apiBase}${url}`;
  const token = getStoredToken();
  
  const headers = new Headers(options.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
    headers.set('X-Credence-Admin-Key', token);
  }
  
  const response = await fetch(targetUrl, { ...options, headers });
  if (response.status === 401) {
    openOperatorModal('Administrator authentication required to execute this operational action.');
  }
  return response;
}

// -----------------------------------------------------------------------------
// MODALS & TOASTS
// -----------------------------------------------------------------------------

export function showToast(message, type = 'info') {
  let toast = document.getElementById('ws-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'ws-toast';
    toast.style.cssText = 'position:fixed; bottom:20px; right:20px; padding:10px 18px; border-radius:6px; font-family:var(--font-mono, monospace); font-size:0.85rem; font-weight:bold; z-index:9999; transition:all 0.2s ease; box-shadow:0 4px 15px rgba(0,0,0,0.5);';
    document.body.appendChild(toast);
  }
  
  if (type === 'success') {
    toast.style.background = '#065f46';
    toast.style.color = '#34d399';
    toast.style.border = '1px solid #10b981';
  } else if (type === 'error') {
    toast.style.background = '#7f1d1d';
    toast.style.color = '#f87171';
    toast.style.border = '1px solid #ef4444';
  } else {
    toast.style.background = '#1e293b';
    toast.style.color = '#38bdf8';
    toast.style.border = '1px solid #0284c7';
  }
  
  toast.textContent = message;
  toast.style.display = 'block';
  toast.style.opacity = '1';
  
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => { toast.style.display = 'none'; }, 200);
  }, 3500);
}

export function injectOperatorModal() {
  if (document.getElementById('operator-modal-backdrop')) return;
  
  const modalHtml = `
    <div id="operator-modal-backdrop" class="operator-modal-backdrop">
      <div class="operator-modal">
        <div class="operator-modal-header">
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span style="font-size:1.2rem;">🔒</span>
            <b style="color:#fff; font-size:1rem;">Operator Authentication</b>
          </div>
          <button class="btn-secondary" style="padding:0.2rem 0.6rem; font-size:0.8rem;" onclick="window.CredenceWS.closeOperatorModal()">✕</button>
        </div>
        <div class="operator-modal-body">
          <p id="operator-modal-context" style="color:var(--text-muted); font-size:0.88rem; margin-bottom:1.25rem;">
            Authenticate with your node Administrator Key to execute privileged operations and cost overrides.
          </p>

          <div style="display:flex; gap:0.5rem; margin-bottom:1rem; border-bottom:1px solid var(--border); padding-bottom:0.5rem;">
            <button id="modal-tab-key" class="workstation-tab-btn active" style="padding:0.35rem 0.75rem; font-size:0.82rem;" onclick="window.CredenceWS.switchModalTab('key')">🔑 Admin Key</button>
            <button id="modal-tab-oauth" class="workstation-tab-btn" style="padding:0.35rem 0.75rem; font-size:0.82rem;" onclick="window.CredenceWS.switchModalTab('oauth')">🌐 Google / GitHub SSO</button>
          </div>

          <div id="modal-pane-key">
            <form onsubmit="event.preventDefault(); window.CredenceWS.submitKeyLogin();">
              <div class="form-group">
                <label class="form-label" for="operator-key-input">Administrator Secret Key</label>
                <div style="position:relative;">
                  <input type="password" id="operator-key-input" class="form-input" placeholder="cred_adm_..." required autocomplete="current-password">
                  <button type="button" onclick="window.CredenceWS.togglePasswordVisibility()" style="position:absolute; right:8px; top:8px; background:none; border:none; color:var(--text-dim); cursor:pointer; font-size:0.8rem;">👁️</button>
                </div>
              </div>
              <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:1.25rem;">
                <input type="checkbox" id="remember-session" checked style="cursor:pointer;">
                <label for="remember-session" style="color:var(--text-muted); font-size:0.82rem; cursor:pointer;">Remember token across sessions &amp; reloads</label>
              </div>
              <div style="display:flex; justify-content:flex-end; gap:0.5rem;">
                <button type="button" class="btn-secondary" onclick="window.CredenceWS.closeOperatorModal()">Cancel</button>
                <button type="submit" class="btn-primary">Verify &amp; Unlock</button>
              </div>
            </form>
          </div>

          <div id="modal-pane-oauth" style="display:none;">
            <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem;">
              Authenticate via OAuth using an authorized maintainer email address:
            </p>
            <div style="display:flex; flex-direction:column; gap:0.75rem;">
              <button class="btn-secondary" style="display:flex; align-items:center; justify-content:center; gap:0.5rem; padding:0.65rem;" onclick="window.CredenceWS.loginOAuth('google')">
                <span>🔴</span> <b>Sign in with Google Workspace</b>
              </button>
              <button class="btn-secondary" style="display:flex; align-items:center; justify-content:center; gap:0.5rem; padding:0.65rem;" onclick="window.CredenceWS.loginOAuth('github')">
                <span>🐙</span> <b>Sign in with GitHub</b>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', modalHtml);
}

export function openOperatorModal(contextMsg) {
  injectOperatorModal();
  const backdrop = document.getElementById('operator-modal-backdrop');
  const context = document.getElementById('operator-modal-context');
  if (context && contextMsg) context.textContent = contextMsg;
  if (backdrop) backdrop.classList.add('active');
  const input = document.getElementById('operator-key-input');
  if (input) setTimeout(() => input.focus(), 50);
}

export function closeOperatorModal() {
  const backdrop = document.getElementById('operator-modal-backdrop');
  if (backdrop) backdrop.classList.remove('active');
}

export function switchModalTab(tab) {
  const paneKey = document.getElementById('modal-pane-key');
  const paneOAuth = document.getElementById('modal-pane-oauth');
  const tabKey = document.getElementById('modal-tab-key');
  const tabOAuth = document.getElementById('modal-tab-oauth');
  if (tab === 'key') {
    paneKey.style.display = 'block';
    paneOAuth.style.display = 'none';
    tabKey.classList.add('active');
    tabOAuth.classList.remove('active');
  } else {
    paneKey.style.display = 'none';
    paneOAuth.style.display = 'block';
    tabKey.classList.remove('active');
    tabOAuth.classList.add('active');
  }
}

export function togglePasswordVisibility() {
  const input = document.getElementById('operator-key-input');
  if (input) {
    input.type = input.type === 'password' ? 'text' : 'password';
  }
}

export function submitKeyLogin() {
  const input = document.getElementById('operator-key-input');
  const remember = document.getElementById('remember-session')?.checked || false;
  if (input && input.value) {
    loginWithKey(input.value.trim(), remember);
  }
}

export function loginOAuth(provider) {
  showToast(`Initiating ${provider.toUpperCase()} OAuth authentication...`, 'info');
  // Simulating / directing to OAuth endpoint
  window.location.href = `/api/auth/oauth/${provider}`;
}

export function updateRibbonAuthBadge() {
  const badge = document.getElementById('ribbon-operator-badge');
  if (!badge) return;
  if (authState.authenticated) {
    badge.className = 'ribbon-pill operator-active';
    badge.innerHTML = `🔓 OPERATOR: ${authState.identity || 'ACTIVE'}`;
    badge.title = 'Operator session active. Click to lock / manage.';
    badge.onclick = () => {
      if (confirm('Lock operator session and clear stored tokens?')) {
        clearStoredToken();
        showToast('🔒 Operator Session Locked', 'info');
      }
    };
  } else {
    badge.className = 'ribbon-pill operator-locked';
    badge.innerHTML = '🔒 OPERATOR LOGIN';
    badge.title = 'Click to authenticate as node operator';
    badge.onclick = () => openOperatorModal();
  }
}

// -----------------------------------------------------------------------------
// SHORTCUTS HELP MODAL
// -----------------------------------------------------------------------------

export function injectShortcutsModal() {
  if (document.getElementById('shortcuts-modal-backdrop')) return;
  const shortcutsHtml = `
    <div id="shortcuts-modal-backdrop" class="operator-modal-backdrop">
      <div class="operator-modal">
        <div class="operator-modal-header">
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span>⌨️</span>
            <b style="color:#fff; font-size:1rem;">Workstation Keyboard Shortcuts</b>
          </div>
          <button class="btn-secondary" style="padding:0.2rem 0.6rem; font-size:0.8rem;" onclick="window.CredenceWS.closeShortcutsModal()">✕</button>
        </div>
        <div class="operator-modal-body" style="font-family:var(--font-mono); font-size:0.85rem;">
          <div style="display:grid; grid-template-columns:120px 1fr; gap:0.75rem 1rem; align-items:center;">
            <div><kbd style="background:#1e293b; padding:2px 6px; border-radius:4px; border:1px solid #334155; color:#38bdf8;">1 – 7</kbd></div>
            <div style="color:var(--text-main);">Switch Workstation Tabs</div>
            <div><kbd style="background:#1e293b; padding:2px 6px; border-radius:4px; border:1px solid #334155; color:#38bdf8;">/</kbd></div>
            <div style="color:var(--text-main);">Focus Search / Audit Input</div>
            <div><kbd style="background:#1e293b; padding:2px 6px; border-radius:4px; border:1px solid #334155; color:#38bdf8;">v</kbd></div>
            <div style="color:var(--text-main);">Cycle Epistemic Lensing Mode</div>
            <div><kbd style="background:#1e293b; padding:2px 6px; border-radius:4px; border:1px solid #334155; color:#38bdf8;">r</kbd></div>
            <div style="color:var(--text-main);">Load Random Scenario / Peer</div>
            <div><kbd style="background:#1e293b; padding:2px 6px; border-radius:4px; border:1px solid #334155; color:#38bdf8;">?</kbd></div>
            <div style="color:var(--text-main);">Show / Hide Shortcuts Modal</div>
            <div><kbd style="background:#1e293b; padding:2px 6px; border-radius:4px; border:1px solid #334155; color:#38bdf8;">Esc</kbd></div>
            <div style="color:var(--text-main);">Close Active Dialog / Modal</div>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', shortcutsHtml);
}

export function openShortcutsModal() {
  injectShortcutsModal();
  document.getElementById('shortcuts-modal-backdrop')?.classList.add('active');
}

export function closeShortcutsModal() {
  document.getElementById('shortcuts-modal-backdrop')?.classList.remove('active');
}

export function toggleShortcutsModal() {
  const modal = document.getElementById('shortcuts-modal-backdrop');
  if (modal?.classList.contains('active')) {
    closeShortcutsModal();
  } else {
    openShortcutsModal();
  }
}

// -----------------------------------------------------------------------------
// UNIVERSAL KNOWLEDGE & DOCUMENTATION INFO MODALS
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// UNIVERSAL KNOWLEDGE & DOCUMENTATION INFO MODALS
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// UNIVERSAL KNOWLEDGE & DOCUMENTATION INFO MODALS
// -----------------------------------------------------------------------------
// 3-TIER EPISTEMIC INFORMATION PYRAMID MODAL ENGINE
// -----------------------------------------------------------------------------
// 3-TIER EPISTEMIC INFORMATION PYRAMID TABBED MODAL ENGINE
// -----------------------------------------------------------------------------

export const INVARIANTS_REGISTRY = {
  "inv-workspace-isolation": { legacyId: 1, class: "Class β", title: "Project & Workspace Isolation" },
  "inv-async-sqlmodel": { legacyId: 2, class: "Class β", title: "Python & SQLModel Async Architecture" },
  "inv-version-governance": { legacyId: 3, class: "Class γ", title: "Continuous Changelog & Version Governance" },
  "inv-hermetic-testing": { legacyId: 4, class: "Class β", title: "Hermetic In-Memory Testing & Docs Integrity" },
  "inv-scoped-verification": { legacyId: 5, class: "Class β", title: "Scoped Verification for Docs-Only Changes" },
  "inv-mk1-eyeball": { legacyId: 6, class: "Class α", title: "Human Review Before Commits (\"Mk1 Eyeball\")" },
  "inv-multi-model-sovereignty": { legacyId: 7, class: "Class γ", title: "Multi-Model Sovereignty & Token Budget" },
  "inv-ssrf-defense": { legacyId: 8, class: "Class α", title: "Untrusted Ingestion Boundary & SSRF Defense" },
  "inv-ingestion-defense": { legacyId: 9, class: "Class α", title: "Red Team Ingestion & Protocol Defense" },
  "inv-xml-safety": { legacyId: 10, class: "Class β", title: "XML ElementTree Traversal Safety" },
  "inv-ground-truth-config": { legacyId: 11, class: "Class β", title: "Model Default Truth & Verification Guardrail" },
  "inv-fastmcp-transport-security": { legacyId: 12, class: "Class β", title: "FastMCP 2.0 Reverse Proxy Transport Security" },
  "inv-cloudflare-assets": { legacyId: 13, class: "Class β", title: "Cloudflare Workers Zero-Build Static Assets" },
  "inv-edge-origin-header": { legacyId: 14, class: "Class β", title: "Edge Routing Origin Header Translation" },
  "inv-4k-thinking-budget": { legacyId: 15, class: "Class γ", title: "Empirical Thinking Budget Sweet Spot (4k Pareto)" },
  "inv-fastmcp-datetime-serialization": { legacyId: 16, class: "Class γ", title: "FastMCP Nested Datetime Serialization" },
  "inv-content-decoupling": { legacyId: 17, class: "Class β", title: "Content Decoupling & Hermetic CI" },
  "inv-progressive-disclosure": { legacyId: 18, class: "Class γ", title: "Context Governance & Progressive Disclosure" },
  "inv-topic-entropy-defense": { legacyId: 19, class: "Class γ", title: "Topic Entropy Astroturfing Defense (Pizza Hut)" },
  "inv-poes-law-satire": { legacyId: 20, class: "Class γ", title: "Poe's Law & Satire Safeguards" },
  "inv-fixed-taxonomies": { legacyId: 21, class: "Class β", title: "Namespaced Fixed Taxonomies" },
  "inv-verbatim-grounding": { legacyId: 22, class: "Class α", title: "Whitespace-Insensitive Verbatim Grounding (G=1.00)" },
  "inv-heuristic-disclosure": { legacyId: 23, class: "Class β", title: "Transparent Heuristic Disclosure" },
  "inv-canonical-json-ed25519": { legacyId: 24, class: "Class α", title: "RFC 8785 Canonical JSON & Ed25519 Custody" },
  "inv-5factor-node-quality": { legacyId: 25, class: "Class β", title: "5-Factor Node Quality Score (Qi)" },
  "inv-empirical-expertise": { legacyId: 26, class: "Class β", title: "Empirical Expertise (Ei) & Anti-Diploma Invariant" },
  "inv-galileo-rule": { legacyId: 27, class: "Class β", title: "The Galileo Rule (Asymmetric Grounded Evidence)" },
  "inv-bittorrent-worksharing": { legacyId: 28, class: "Class β", title: "BitTorrent Work-Sharing & Generous Defaults" },
  "inv-byzantine-cartel-resistance": { legacyId: 29, class: "Class β", title: "Byzantine Cartel Resistance (3f+1)" },
  "inv-4way-feature-parity": { legacyId: 30, class: "Class γ", title: "Universal Presentation Layer Feature Parity" },
  "inv-zero-build-standards": { legacyId: 31, class: "Class γ", title: "Universal Zero-Build Standards (Zero-npm Invariant)" },
  "inv-zero-build-math": { legacyId: 32, class: "Class γ", title: "Zero-Build Math & Currency Invariant" },
  "inv-edge-canonicalization": { legacyId: 33, class: "Class β", title: "Edge Subdirectory Canonicalization" },
  "inv-mermaid-syntax-safety": { legacyId: 34, class: "Class β", title: "Universal Mermaid & Visual Syntax Guardrail" },
  "inv-visual-density": { legacyId: 35, class: "Class γ", title: "Visual Density & Anti-Wall-of-Text Invariant" },
  "inv-playwright-rendering-tests": { legacyId: 36, class: "Class β", title: "Automated Live Rendering Regression Verification" },
  "inv-inline-html-math-integrity": { legacyId: 37, class: "Class γ", title: "Zero-Build Inline HTML & Nested Math Integrity" },
  "inv-anti-scrollbox": { legacyId: 38, class: "Class γ", title: "Anti-Scrollbox & Natural Flow Presentation" },
  "inv-boredom-root-expansion": { legacyId: 39, class: "Class β", title: "Opportunistic Boredom Ingestion & Root Expansion" },
  "inv-soft-blacklist-buzzfeed": { legacyId: 40, class: "Class β", title: "Soft Blacklisting & BuzzFeed News Doctrine" },
  "inv-symmetric-navigation-zero-cache": { legacyId: 41, class: "Class γ", title: "Symmetric 4-Pillar Navigation & Zero-Cache" },
  "inv-information-pyramid-lensing": { legacyId: 42, class: "Class γ", title: "The Epistemic Lensing & Information Pyramid" },
  "inv-order-of-operations": { legacyId: 43, class: "Class β", title: "The Cart-Before-the-Horse Order-of-Operations" },
  "inv-web-component-zero-clone": { legacyId: 44, class: "Class γ", title: "Web Component Isolation & Zero-Clone Safety" },
  "inv-dense-workstation-viewport": { legacyId: 45, class: "Class γ", title: "Dense Workstation Viewport & Zero-Masking" }
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

const INFO_TOPICS = {
  // === REPORTS LAB TOPICS ===
  search: {
    title: "Epistemic Query & Multi-Criteria Search",
    icon: "🔍",
    tag: "FORENSICS",
    tier1_plain_english: `
      <b>In plain words:</b> This is your search engine for truth on the web. Instead of just searching for keywords like Google does, Credence checks whether an article gives real evidence for its claims.
      <br><br>
      You can paste any web link (like a news story or blog post), type a headline, or search for specific red flags (like <i>"Unsourced Claims"</i> or <i>"Ad Hominem Attacks"</i>) to see an instant forensic audit.
    `,
    tier1_article: {
      title: "📰 Real-World Example: Clean Energy Transition (Reuters)",
      desc: "See how a high-trust news report passes all journalistic checks with zero red flags.",
      url: "../credence.report/index.html?query=reuters"
    },
    tier2_mechanics: [
      "<b>Multi-Criteria Search</b>: Filter articles by Rule Code (e.g. <code>SPJ-1.1</code>), Risk Tier (A to D), or Severity (1 to 5).",
      "<b>Live Web Ingestion</b>: Pasting an HTTP/HTTPS URL triggers immediate text extraction, DOM stripping, and statement evaluation.",
      "<b>Universal Parity</b>: Identical results are returned whether you use this web page, the terminal CLI, or Claude/Cursor FastMCP."
    ],
    cli: "credence audit https://reuters.com/world/energy/clean-grid-transition-2026",
    math_proof: null,
    invariants: ["inv-verbatim-grounding", "inv-fastmcp-datetime-serialization"],
    links: [
      { label: "📘 CLI Scripting & Search Guide", url: "https://docs.credence.run#docs/integrations/cli-scripting-guide", desc: "Automate batch evaluations and headless search queries" },
      { label: "🧪 Interactive Playground", url: "https://docs.credence.run#docs/playground", desc: "Simulate adversarial payloads and cloaking in-browser" }
    ]
  },

  backup: {
    title: "Sovereign Database Backup & Cold-Boot Recovery",
    icon: "💾",
    tag: "STORAGE GRAVITY",
    tier1_plain_english: `
      <b>In plain words:</b> Credence safeguards all of your evaluations, snapshots, and node trust scores so you never lose work.
      <br><br>
      It creates compact, compressed backups with cryptographic checksums. If a server restarts or crashes, it automatically restores your data in less than a quarter of a second.
    `,
    tier1_article: {
      title: "📘 Architectural Blueprint: Sovereign Data Gravity & CAS Portability",
      desc: "How Credence ensures sovereign node data custody and zero-effort re-evaluation.",
      url: "https://docs.credence.run#docs/blueprints/sovereign-data-gravity-and-cas-portability"
    },
    tier2_mechanics: [
      "<b>Atomic SQLite Snapshots</b>: Uses the SQLite Backup API with WAL truncation to ensure zero-lock snapshots.",
      "<b>SHA-256 Manifests & Ed25519 Signatures</b>: Every backup archive is hashed and signed with the node's sovereign private key.",
      "<b>Cold-Boot Auto Restore</b>: Pre-boot lifespan hook downloads the latest cloud backup before initialization in &lt;200ms."
    ],
    cli: "credence db backup --output /data/backups/credence_latest.db.gz",
    math_proof: "Archive Integrity: SHA256(Gzip(SQLite)) == Manifest.sha256_hash verified under Ed25519(CanonicalJSON(Manifest)).",
    invariants: ["inv-canonical-json-ed25519", "inv-4way-parity-symmetric-web"],
    links: [
      { label: "📘 Sovereign Data Gravity Blueprint", url: "https://docs.credence.run#docs/blueprints/sovereign-data-gravity-and-cas-portability", desc: "CAS portability and SQLite-to-PostgreSQL storage architecture" },
      { label: "📘 Cloud Run Deployment & Ops", url: "https://docs.credence.run#docs/deployment-cloudrun", desc: "Automated container lifecycle and cloud backup hooks" }
    ]
  },

  boredom: {
    title: "Autonomous Epistemic Boredom Engine",
    icon: "🌀",
    tag: "AUTONOMOUS INGESTION",
    tier1_plain_english: `
      <b>In plain words:</b> When your node is idling and has extra token budget available, it gets 'bored' and goes hunting for new knowledge.
      <br><br>
      It checks RSS feeds, audits breaking news, and balances 60% clean sources with 40% adversarial probes to discover deceptive tactics.
    `,
    tier1_article: {
      title: "📘 Curiosity Loop Architecture & Dual-Soil Ingestion",
      desc: "How autonomous agents maintain high-velocity truth detection within token ceilings.",
      url: "https://docs.credence.run#docs/blueprints/sovereign-data-gravity-and-cas-portability"
    },
    tier2_mechanics: [
      "<b>Dual-Soil Balancing</b>: Partitions ingestion into 60% trusted sources and 40% adversarial/probationary probes.",
      "<b>Token Headroom Circuit Breakers</b>: Automatically sleeps when daily spend exceeds 70% of safety limit.",
      "<b>Zero-Token Mesh Dedup</b>: Adopts existing peer attestations from the P2P gossip swarm at $0.00 token cost."
    ],
    cli: "credence boredom --force",
    math_proof: "Curiosity Equilibrium: Harvest(t) = 0.60 * S_clean + 0.40 * S_adversarial constrained by Headroom(t) >= 0.30.",
    invariants: ["inv-multi-model-sovereignty", "inv-production-telemetry-boundary"],
    links: [
      { label: "📘 Feed Ingestion & Boredom Guide", url: "https://docs.credence.run#docs/tutorials/09-zero-trust-feed-sifter-digest", desc: "Autonomous ingestion daemons and background tasks" }
    ]
  },

  browse: {
    title: "Curated Audit Directory & Case Studies",
    icon: "📚",
    tag: "GROUND TRUTH",
    tier1_plain_english: `
      <b>In plain words:</b> Think of this as a verified library of real-world test cases. It contains audited articles from major wire services, local investigative papers, scientific journals, and satire websites.
      <br><br>
      It helps you explore how different types of writing are graded—showing you clear examples of pristine reporting, sneaky stealth edits, disguised ads, and protected parody humor.
    `,
    tier1_article: {
      title: "📰 Real-World Case Study: Sriracha Solar Flares (The Onion)",
      desc: "Explore why legitimate satire is protected and receives a 0.0 suspicion score.",
      url: "../credence.report/index.html?query=onion"
    },
    tier2_mechanics: [
      "<b>Quick Category Filters</b>: Switch between Clean Wire, Flagged Violations, Satire Neutralized, and Local Beats.",
      "<b>Golden 12 Benchmark Alignment</b>: Built from our standard test gauntlet measuring precision, recall, and cross-entropy.",
      "<b>Session Pinning & Dossiers</b>: Pin sources directly to your active sidebar to compare publishers side-by-side."
    ],
    cli: "credence benchmark --profile balanced",
    math_proof: "Cross-Entropy: H(P, Q) = -Σ P(x) log Q(x) evaluated across Free, Balanced, and Ultra inference profiles.",
    invariants: ["inv-canonical-json-ed25519", "inv-playwright-rendering-tests"],
    links: [
      { label: "📘 Golden 12 Benchmark Blueprint", url: "https://docs.credence.run#docs/tutorials/10-reusable-live-e2e-and-mesh-gauntlet", desc: "Precision, recall, and cross-entropy evaluation gauntlet" },
      { label: "✍️ The Blue Checkmark is Dead", url: "https://blog.credence.run#the-blue-checkmark-is-dead", desc: "Why cryptographic receipts replace centralized platform trust badges" },
      { label: "✍️ The Pareto Frontier of Truth", url: "https://blog.credence.run#the-pareto-frontier-of-truth", desc: "Balancing false positives with high-severity evasion detection" }
    ]
  },

  lensing: {
    title: "3-Tier Epistemic Lensing Hierarchy",
    icon: "🔬",
    tag: "COGNITIVE ARCHITECTURE",
    tier1_plain_english: `
      <b>In plain words:</b> We don't overwhelm you with raw data all at once. We organize information like a pyramid with three lenses:
      <br><br>
      1. <b>Surface Glance:</b> Look at the score and verdict in 1 second.<br>
      2. <b>Focus Evidence:</b> Read the exact highlighted quotes and rule violations in 10 seconds.<br>
      3. <b>Deep Spectrum:</b> Inspect cryptographic digital signatures and mathematical proofs when you need forensic certainty.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Scoring the Lens, Not the Window",
      desc: "How structured cognitive depth prevents auditor fatigue and information overload.",
      url: "https://blog.credence.run#scoring-the-lens-not-the-window"
    },
    tier2_mechanics: [
      "<b>Lens 1 (Glance)</b>: Circular score dial (0–100), trust badge (Tier A–D), and a 1-sentence verdict with zero math.",
      "<b>Lens 2 (Evidence)</b>: Exact quoted sentences matching the source page character-for-character, plus rule violation tags.",
      "<b>Lens 3 (Forensic Proof)</b>: In-browser WebCrypto attestation, Ed25519 digital signatures, and RFC 8785 canonical bytes."
    ],
    cli: "credence audit <url> --lens focus",
    math_proof: "Information Pyramid Invariant: Depth(L1) ⊂ Evidence(L2) ⊂ CryptographicProof(L3). Strict zero-redundancy across layers.",
    invariants: ["inv-information-pyramid-lensing", "inv-verbatim-grounding"],
    links: [
      { label: "📘 Epistemic Lensing Technical Blueprint", url: "https://docs.credence.run#docs/blueprints/information-pyramid-and-epistemic-lensing", desc: "Full architectural specification of the 3-tier cognitive hierarchy" },
      { label: "🧪 Interactive Lensing Simulator", url: "https://docs.credence.run#docs/playground", desc: "Test real-time switching across Surface, Focus, and Spectrum lenses" }
    ]
  },

  score: {
    title: "Epistemic Suspicion Score (0.0 – 100.0)",
    icon: "📊",
    tag: "SCORING METRIC",
    tier1_plain_english: `
      <b>In plain words:</b> Like a golf score, lower is better. 
      <br><br>
      • <b>0 to 15 (Tier A - Pristine):</b> Clean, honest, factual news backed by verified primary sources.<br>
      • <b>15 to 40 (Tier B - Low Suspicion):</b> Minor sourcing gaps or uncorroborated quotes.<br>
      • <b>40 to 75 (Tier C - Suspicious):</b> Flawed logic, anonymous attacks, or unlabelled advertorial framing.<br>
      • <b>75 to 100 (Tier D - Quarantine):</b> Severe deception, fake error popups, or manipulative scams.
    `,
    tier1_article: {
      title: "📰 Real-World Example: Miracle Elixir Health Claim",
      desc: "See how an unverified medical claim gets flagged with an 84.5 Tier D quarantine score.",
      url: "../credence.report/index.html?query=clinical"
    },
    tier2_mechanics: [
      "<b>Severity Multipliers</b>: Violations range from Severity 1 (Minor Advisory) to Severity 5 (Critical Fraud / Defamation).",
      "<b>Satire Neutrality</b>: Protected comedy & parody automatically receive a 0.0 score.",
      "<b>Satire Cloaking Override</b>: If a satire disguise is used to make defamatory or false health claims, protection is overridden (SPJ-1.6)."
    ],
    cli: "credence score <url>",
    math_proof: "S = min(100, Σ (w_i · severity_i · domain_multiplier)). Satire: S = 0.0 unless SPJ-1.6 cloaking override triggered.",
    invariants: ["inv-topic-entropy-defense", "inv-poes-law-satire"],
    links: [
      { label: "📘 Scoring & Thresholds Blueprint", url: "https://docs.credence.run#docs/walkthroughs/01-auditing-webpages-and-text", desc: "Mathematical formulations, severity weights, and threshold boundaries" },
      { label: "✍️ The Pareto Frontier of Truth", url: "https://blog.credence.run#the-pareto-frontier-of-truth", desc: "Balancing false positive rates with high-severity evasion detection" }
    ]
  },

  grounding: {
    title: "Verbatim Empirical Grounding (G = 1.00)",
    icon: "🎯",
    tag: "INTEGRITY GUARANTEE",
    tier1_plain_english: `
      <b>In plain words:</b> This is our zero-hallucination guarantee. 
      <br><br>
      Whenever Credence points out a flaw in an article, it must quote the <b>exact sentence</b> character-for-character from the web page. An AI is never allowed to make up or paraphrase evidence. If it does, its evaluation is instantly thrown out.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Confessions of a Bored AI",
      desc: "How strict character-for-character grounding eliminates synthetic hallucinations.",
      url: "https://blog.credence.run#confessions-of-a-bored-ai"
    },
    tier2_mechanics: [
      "<b>Character-for-Character Exactness</b>: Quotes must match the source web page text exactly after basic whitespace collapse.",
      "<b>Anti-Hallucination Slashing</b>: Nodes that produce fake or altered quotes lose 50% of their network reputation immediately.",
      "<b>Cryptographic DOM Offsets</b>: Exact start and end character positions are signed directly into the verification receipt."
    ],
    cli: "credence audit <url> --verify-grounding",
    math_proof: "Grounding Exactness: G = |Quote_cited ∩ DOM_source| / |Quote_cited| = 1.000. Rejects any G < 1.00.",
    invariants: ["inv-verbatim-grounding", "inv-canonical-json-ed25519"],
    links: [
      { label: "📘 Living Invariant Canon", url: "https://docs.credence.run#docs/invariants", desc: "Mathematical proofs and non-negotiable guardrails" }
    ]
  },

  temporal_diff: {
    title: "Bitwise Temporal Diff & Stealth Edit Forensics",
    icon: "⏱️",
    tag: "TEMPORAL FORENSICS",
    tier1_plain_english: `
      <b>In plain words:</b> Catching silent edits after a story is published.
      <br><br>
      When an author quietly changes a headline, deletes a quote, or rewrites a factual claim without telling readers, Credence compares snapshots over time and highlights the exact stealth modifications in red and green.
    `,
    tier1_article: {
      title: "📰 Real-World Case Study: The Stealth City Council Rewrite",
      desc: "See how a silent modification to local zoning vote tallies was caught by temporal diffing.",
      url: "../credence.report/index.html?query=municipal"
    },
    tier2_mechanics: [
      "<b>SimHash-64 Locality Hashing</b>: Computes bitwise similarity between historical snapshots of an article.",
      "<b>SPJ-4.1 Stealth Edit Detection</b>: Flags substantive narrative rewrites that lack reader correction notices.",
      "<b>Signed Revision History</b>: Every captured snapshot is timestamped and cryptographically signed."
    ],
    cli: "credence diff <url> --snap-a <id1> --snap-b <id2>",
    math_proof: "Hamming Distance: d_H(SimHash(t_0), SimHash(t_1)) = Σ (b_0 ⊕ b_1). Drift flagged when d_H > 3 bits without correction.",
    invariants: ["inv-bittorrent-worksharing", "inv-version-governance"],
    links: [
      { label: "📘 Temporal Content Evolution Lab", url: "https://docs.credence.run#docs/lab-content-evolution", desc: "Inspect live multi-snapshot diff trajectories and stealth edit flags" },
      { label: "📘 SimHash Mirror Detection Mathematics", url: "https://docs.credence.run#docs/lab-content-evolution", desc: "Mathematical proof of 64-bit Hamming distance thresholds" }
    ]
  },

  webcrypto: {
    title: "Native W3C WebCrypto In-Browser Verification",
    icon: "🧪",
    tag: "CRYPTOGRAPHY",
    tier1_plain_english: `
      <b>In plain words:</b> You don't have to trust our servers. 
      <br><br>
      Your own web browser verifies the digital signatures in less than 1 millisecond using built-in browser cryptography. You can check the math right on your computer without installing anything.
    `,
    tier1_article: {
      title: "📘 Frontend Zero-Build Architecture",
      desc: "How Credence runs client-side cryptographic verification with zero npm packages.",
      url: "https://docs.credence.run#docs/feature-parity"
    },
    tier2_mechanics: [
      "<b>Native Browser Crypto</b>: Uses standard <code>window.crypto.subtle.verify</code> with pure Ed25519 keys.",
      "<b>RFC 8785 Canonical JSON</b>: Formats data identically across all programming languages to prevent key mismatches.",
      "<b>Zero Backend Reliance</b>: Verification executes completely client-side in your browser tab."
    ],
    cli: "credence verify-envelope envelope.json",
    math_proof: "PureEdDSA Verification: Verify(K_pub, M_rfc8785, Sig_Ed25519) ∈ {0, 1}. Executed in-memory in <0.3ms.",
    invariants: ["inv-canonical-json-ed25519", "inv-zero-build-standards"],
    links: [
      { label: "📘 Security Architecture & Threat Model", url: "https://docs.credence.run#docs/blueprints/security-architecture-and-threat-model", desc: "Dual-crypto conformance and key rotation ceremonies" }
    ]
  },

  dossier: {
    title: "Publisher Epistemic Dossier & Track Record",
    icon: "🏛️",
    tag: "REPUTATION PROFILE",
    tier1_plain_english: `
      <b>In plain words:</b> Like a restaurant inspection grade for news websites.
      <br><br>
      Instead of judging a publisher by a single story, the dossier looks at their long-term track record over months—tracking how often they get facts right, how quickly they issue corrections, and whether they publish disguised advertorials.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: The Domain Epistemic Index",
      desc: "Why long-term publisher track records matter more than single-article audits.",
      url: "https://blog.credence.run#the-domain-epistemic-index"
    },
    tier2_mechanics: [
      "<b>Bayesian Smoothing</b>: Combines clean audits and violation flags so new publishers aren't unfairly penalized.",
      "<b>Domain Credence Index (DCI)</b>: Tracks historical reliability, source transparency, and correction speed.",
      "<b>1-Click All Audits Link</b>: Jump directly from any publisher dossier to all their curated articles in Search."
    ],
    cli: "credence dossier reuters.com",
    math_proof: "DCI Score: DCI = 100 · (α + 1) / (α + β + 2). Longitudinal Stability: σ_30d = √(αβ / ((α+β)^2 · (α+β+1))).",
    invariants: ["inv-cloudflare-assets", "inv-version-governance"],
    links: [
      { label: "📘 Domain Epistemic Index Blueprint", url: "https://docs.credence.run#docs/blueprints/domain-epistemic-index-and-sourcing-forensics", desc: "Bayesian reputation mechanics and domain normalization" }
    ]
  },

  dci: {
    title: "Domain Credence Index (DCI) Honor Roll",
    icon: "🏆",
    tag: "ECOSYSTEM RANKINGS",
    tier1_plain_english: `
      <b>In plain words:</b> The public leaderboard of web publishers ranked by factual accuracy.
      <br><br>
      You can sort publishers by their average suspicion score, total verified articles, or trust tier to see which outlets consistently uphold high journalistic standards.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: BitTorrent Economics of Fact-Checking",
      desc: "How decentralized peer incentives create unbiased publisher rankings without corporate gatekeepers.",
      url: "https://blog.credence.run#bittorrent-economics-of-fact-checking"
    },
    tier2_mechanics: [
      "<b>Interactive Column Sorting</b>: Click any table header to sort publishers ascending or descending.",
      "<b>Trust Tiers</b>: Tier A (0–15 Pristine), Tier B (15–40 Low Risk), Tier C (40–75 Watchlist), Tier D (75–100 Quarantine).",
      "<b>Clean Table Design</b>: Displays only meaningful, actionable metrics per publisher."
    ],
    cli: "credence dci top --limit 20",
    math_proof: "Rank Order: Sort by DCI_score DESC, AvgSuspicion ASC. Laplace Smoothing: α_prior = 1.0, β_prior = 1.0.",
    invariants: ["inv-cloudflare-assets", "inv-progressive-disclosure"],
    links: [
      { label: "📘 Terminology & Ontology Lexicon", url: "https://docs.credence.run#docs/blueprints/terminology-and-ontology-lexicon", desc: "Comprehensive definition of trust bands and scoring scales" },
      { label: "📘 Robust Consensus Proofs", url: "https://docs.credence.run#docs/tutorials/08-sybil-cartel-demolition", desc: "Mathematical theorems on Byzantine consensus resilience" }
    ]
  },

  sifter: {
    title: "Sifter Continuous Syndication Stream",
    icon: "📡",
    tag: "STREAM INGESTION",
    tier1_plain_english: `
      <b>In plain words:</b> An automated scout that constantly scans news feeds.
      <br><br>
      Instead of waiting for people to search, the Sifter continuously monitors RSS and Atom feeds, flags breaking stories, and checks whether new articles contain misleading claims.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: The Boredom Engine and Expanding Roots",
      desc: "How automated curiosity helps discover emerging news publishers before they go viral.",
      url: "https://blog.credence.run#the-boredom-engine-and-expanding-roots"
    },
    tier2_mechanics: [
      "<b>Curiosity Loop</b>: Triggers candidate exploration when news cycles enter repetitive echo chambers.",
      "<b>Security Defenses</b>: Blocks SSRF network probes and XML entity bombs before parsing feeds.",
      "<b>Budget Protection</b>: Automatically pauses background scans when daily AI spending reaches safety limits."
    ],
    cli: "credence sifter stream --interval 300",
    math_proof: "Boredom Score: B(t) = 1.0 - CosineSimilarity(Embedding_latest, Centroid_window). Explores when B(t) > 0.65.",
    invariants: ["inv-ssrf-defense", "inv-4k-thinking-budget"],
    links: [
      { label: "📘 Morning Feed Sifter Cookbook", url: "https://docs.credence.run#docs/cookbooks/morning-feed-sifter", desc: "Setup automated headless RSS monitoring pipelines" }
    ]
  },

  // === FOUNDATION TOPICS ===
  taxonomies: {
    title: "Canonical Rule Catalogs (The Credence Rulebook)",
    icon: "📜",
    tag: "GOVERNANCE",
    tier1_plain_english: `
      <b>In plain words:</b> The official rulebook Credence uses to audit articles. 
      <br><br>
      It contains three standard rule catalogs:
      <br>• 📰 <b>Journalism Ethics (SPJ):</b> Checked for unsourced claims, misleading clickbait headlines, and stealth edits.
      <br>• 🧠 <b>Logical Fallacies (IEP):</b> Checked for flawed arguments like personal attacks and straw man reasoning.
      <br>• 🛑 <b>Deceptive UI Patterns:</b> Checked for hidden fees, guilt-trip buttons, and fake virus alerts.
    `,
    tier1_article: {
      title: "📘 Taxonomy Engineering Cookbook",
      desc: "How rule catalogs are written, calibrated, and cryptographically pinned.",
      url: "https://docs.credence.run#docs/cookbooks/taxonomy-engineering"
    },
    tier2_mechanics: [
      "<b>Cryptographic Hash Pinning</b>: Each JSON rule catalog is locked with a SHA-256 hash so no one can silently change the rules.",
      "<b>Severity Weights</b>: Journalistic ethics (1.2x) and Deceptive Patterns (1.5x) carry higher penalties than informal fallacies (1.0x).",
      "<b>1-Click Real Examples</b>: Click '🔬 Find Real Examples' on any rule to jump directly to real articles exhibiting that violation."
    ],
    cli: "credence taxonomy list",
    math_proof: "Integrity Hash: SHA256(RFC8785(Catalog_JSON)) pinned in root seed manifest.",
    invariants: ["inv-verbatim-grounding", "inv-poes-law-satire", "inv-fixed-taxonomies"],
    links: [
      { label: "✍️ Poe's Law and the Satire Cloak", url: "https://blog.credence.run#poes-law-and-the-satire-cloak", desc: "Safeguarding humor while neutralizing malicious deceptive cloaking" }
    ]
  },

  spj_ethics: {
    title: "Society of Professional Journalists (SPJ) Code of Ethics",
    icon: "📰",
    tag: "ETHICAL STANDARD",
    tier1_plain_english: `
      <b>In plain words:</b> The gold standard of journalistic integrity used in professional newsrooms.
      <br><br>
      Credence checks 13 specific rules—such as whether a news story backs up its claims with named sources (SPJ-1.1), whether the headline matches what actually happened (SPJ-1.2), and whether corrections are clearly published when errors occur (SPJ-4.1).
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: The Buzzfeed News Doctrine",
      desc: "How digital newsrooms balance breaking speed with investigative sourcing rigor.",
      url: "https://blog.credence.run#the-buzzfeed-news-doctrine"
    },
    tier2_mechanics: [
      "<b>Core Rule Codes</b>: SPJ-1.1 (Unsourced Claims), SPJ-1.2 (Headline/Body Gap), SPJ-1.3 (Anonymous Attacks), SPJ-1.6 (Satire Cloaking), SPJ-4.1 (Stealth Edits).",
      "<b>Severity Range</b>: Scored from Severity 1 (Minor Advisory) to Severity 5 (Critical Fraud / Defamation).",
      "<b>1.2x Domain Weight</b>: Carries a 20% increased weight in overall suspicion calculations."
    ],
    cli: "credence taxonomy inspect SPJ",
    math_proof: "Weighted Impact: W_spj = 1.20 · Σ (Sev_i · GroundedMatch_i).",
    invariants: ["inv-verbatim-grounding", "inv-bittorrent-worksharing"],
    links: [
      { label: "📘 Taxonomy Engineering Cookbook", url: "https://docs.credence.run#docs/cookbooks/taxonomy-engineering", desc: "Calibrating SPJ rule triggers and evidence thresholds" }
    ]
  },

  iep_fallacies: {
    title: "Internet Encyclopedia of Philosophy (IEP) Fallacies",
    icon: "🧠",
    tag: "LOGICAL RIGOR",
    tier1_plain_english: `
      <b>In plain words:</b> Spotting bad logic and manipulative arguments.
      <br><br>
      When an article insults a person instead of answering their point (<i>Ad Hominem</i>), invents a fake extreme position to argue against (<i>Straw Man</i>), or pretends there are only two choices (<i>False Dilemma</i>), Credence identifies the exact flawed reasoning.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Conflict of Pun-terest",
      desc: "How to distinguish playful wit and harmless satire from dishonest rhetorical deception.",
      url: "https://blog.credence.run#conflict-of-pun-terest"
    },
    tier2_mechanics: [
      "<b>15 Standard Fallacies</b>: IEP-1.1 (Ad Hominem), IEP-1.2 (Straw Man), IEP-1.3 (False Dilemma), IEP-2.1 (False Authority), IEP-3.1 (False Cause).",
      "<b>Context Awareness</b>: Differentiates healthy debate and irony from deliberate logical deception.",
      "<b>1.0x Domain Baseline</b>: Standard baseline weight in epistemic scoring."
    ],
    cli: "credence taxonomy inspect IEP",
    math_proof: "Fallacy Impact: W_iep = 1.00 · Σ (Sev_i · GroundedMatch_i).",
    invariants: ["inv-verbatim-grounding", "inv-topic-entropy-defense"],
    links: [
      { label: "📘 Mathematical Robustness Proofs", url: "https://docs.credence.run#docs/tutorials/08-sybil-cartel-demolition", desc: "Mathematical dampening of rhetorical fallacies" }
    ]
  },

  deceptive_patterns: {
    title: "Deceptive UI Patterns & Consumer Protections",
    icon: "🛑",
    tag: "CONSUMER DEFENSE",
    tier1_plain_english: `
      <b>In plain words:</b> Protecting you from tricks and traps on websites.
      <br><br>
      Credence detects sneaky web tricks like hiding unexpected fees until the last page of checkout (<i>Drip Pricing</i>), making cancel buttons make you feel guilty (<i>Confirmshaming</i>), or displaying fake popup warnings that claim your computer is infected.
    `,
    tier1_article: {
      title: "✍️ Case Study: Astroturfing Entropy & Dark Patterns",
      desc: "How coordinated deceptive funnels trick consumers across affiliate syndication networks.",
      url: "https://blog.credence.run#case-study-astroturfing-entropy"
    },
    tier2_mechanics: [
      "<b>8 Core Dark Patterns</b>: DEC-1.1 (Drip Pricing), DEC-1.2 (Confirmshaming), DEC-3.1 (Fake System Warnings), DEC-2.1 (Forced Continuity).",
      "<b>Highest Domain Weight (1.5x)</b>: Carries the steepest penalty due to direct consumer and financial harm.",
      "<b>Automated Microcopy Audits</b>: Scans button labels, pricing disclosures, and modal dialogues."
    ],
    cli: "credence taxonomy inspect DEC",
    math_proof: "Deceptive Impact: W_dec = 1.50 · Σ (Sev_i · GroundedMatch_i).",
    invariants: ["inv-web-component-zero-clone", "inv-zero-build-math"],
    links: [
      { label: "📘 Security Architecture & Threat Model", url: "https://docs.credence.run#docs/blueprints/security-architecture-and-threat-model", desc: "Detecting clickjacking and deceptive interfaces" }
    ]
  },

  custody: {
    title: "Root Key Custody & Ed25519 Public Key Pinning",
    icon: "🔐",
    tag: "CRYPTOGRAPHIC ROOT",
    tier1_plain_english: `
      <b>In plain words:</b> The master cryptographic seal of the entire network.
      <br><br>
      Just like a government notary stamp or a wax seal on a historic document, every audit report is sealed with a digital key (<code>root.pub</code>). If anyone tries to alter a single letter of an audit, the digital seal breaks and the verification fails.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Blast Radius Containment",
      desc: "Why cryptographic seals protect historical audit receipts even if a single server goes down.",
      url: "https://blog.credence.run#blast-radius-containment-in-decentralized-networks"
    },
    tier2_mechanics: [
      "<b>Ed25519 High-Speed Signatures</b>: Tamper-proof Edwards-curve digital signatures with zero known backdoors.",
      "<b>Public Key Pinning</b>: Network root key is openly verifiable at <code>keys.credence.foundation/root.pub</code>.",
      "<b>Key Rotation Governance</b>: Structured multi-signature ceremony for upgrading keys without breaking past records."
    ],
    cli: "credence keygen --export-pubkey",
    math_proof: "Signature Scheme: PureEdDSA on Curve25519 with SHA-512 (RFC 8032). Key pinned at root.pub.",
    invariants: ["inv-canonical-json-ed25519", "inv-xml-safety"],
    links: [
      { label: "📘 Security Threat Model & Key Custody", url: "https://docs.credence.run#docs/blueprints/security-architecture-and-threat-model", desc: "Cryptographic threat vectors, blast radius containment, and key rotation" }
    ]
  },

  canonical_json: {
    title: "RFC 8785 Canonical JSON Standard",
    icon: "📦",
    tag: "DATA INTEGRITY",
    tier1_plain_english: `
      <b>In plain words:</b> Making sure computers agree on exact formatting.
      <br><br>
      Different programming languages (Python, JavaScript, Go, Rust) format data slightly differently (extra spaces, different quote marks). RFC 8785 defines one universal, exact byte order so a digital signature matches 100% across every computer.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: The Beauty of Hermetic Environments",
      desc: "How deterministic byte serialization guarantees bit-for-bit parity across all platforms.",
      url: "https://blog.credence.run#the-beauty-of-hermetic-environments"
    },
    tier2_mechanics: [
      "<b>Alphabetical Key Ordering</b>: Object keys are strictly sorted by Unicode value.",
      "<b>Zero Extra Whitespace</b>: Strips out formatting spaces outside of string values.",
      "<b>Deterministic Float Precision</b>: Formats numbers consistently without scientific notation differences."
    ],
    cli: "credence canonicalize envelope.json",
    math_proof: "RFC 8785 Rule: CanonicalBytes(Obj_A) == CanonicalBytes(Obj_B) ⟺ Obj_A ≡ Obj_B.",
    invariants: ["inv-canonical-json-ed25519", "inv-4way-feature-parity"],
    links: [
      { label: "📘 Security Architecture & Threat Model", url: "https://docs.credence.run#docs/blueprints/security-architecture-and-threat-model", desc: "Canonical JSON specifications and cross-runtime test gauntlets" }
    ]
  },

  governance: {
    title: "Living Invariant Canon & Governance RFCs",
    icon: "⚖️",
    tag: "CONSTITUTION",
    tier1_plain_english: `
      <b>In plain words:</b> The constitution of the Credence system.
      <br><br>
      These are the permanent rules (called <i>System Invariants</i>) that every developer, AI agent, and server must follow. Rules can only be changed through open proposals (RFCs) and multi-node community consensus.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Scaling System Invariants Without Prompt Bloat",
      desc: "How shift-left automated tests enforce rules without overwhelming AI memory.",
      url: "https://blog.credence.run#scaling-system-invariants-without-prompt-bloat"
    },
    tier2_mechanics: [
      "<b>The Invariant Bible</b>: The living canon of universal non-negotiable architectural laws governing every file and turn.",
      "<b>4-Phase Release Lifecycle</b>: Local QA Gate → Mk1 Eyeball Review → Version Release → /learn Retrospective → Patch Release.",
      "<b>Dynamic Invariant Scalability</b>: Never hardcoding static numerical counts in public web portals."
    ],
    cli: "credence invariants audit",
    math_proof: "Byzantine Quorum for RFC Ratification: Consensus ≥ 66.7% (2f+1 honest votes).",
    invariants: ["inv-mk1-eyeball", "inv-order-of-operations", "inv-version-governance"],
    links: [
      { label: "📘 Invariant Scalability & Knowledge Governance", url: "https://docs.credence.run#docs/blueprints/invariant-scalability-and-knowledge-governance", desc: "3-tier scalable invariant architecture and context economy" },
      { label: "📘 The Living Invariant Canon", url: "https://docs.credence.run#docs/invariants", desc: "Complete mathematical proofs and non-negotiable guardrails" }
    ]
  },

  // === NEXUS NOC TOPICS ===
  topology: {
    title: "Decentralized P2P Mesh Topology & Byzantine Quorum",
    icon: "🕸️",
    tag: "P2P MESH",
    tier1_plain_english: `
      <b>In plain words:</b> A cooperative network of independent computers that verify news together.
      <br><br>
      Instead of one big tech company deciding what is true, hundreds of independent computers vote on evidence. Even if some computers are broken or dishonest, the network still reaches the correct truth.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Testing 13-Node Swarms on a Raspberry Pi",
      desc: "How we tested a cluster of 13 independent nodes running locally with zero memory leaks.",
      url: "https://blog.credence.run#testing-13-node-swarms-on-a-raspberry-pi"
    },
    tier2_mechanics: [
      "<b>Byzantine Fault Tolerance</b>: Formula: f = ⌊(N-1)/3⌋. Scales smoothly from a single laptop (f=0) to huge networks.",
      "<b>Highest Random Weight (HRW) Hashing</b>: Automatically splits incoming articles across nodes without any central master server.",
      "<b>Production vs Simulation</b>: The live dashboard only shows genuine running computers—not fake simulations."
    ],
    cli: "credence mesh status",
    math_proof: "HRW Rendezvous Function: Node_assigned(URL) = argmax_i ( HMAC-SHA256(Node_i.pubkey, URL) ).",
    invariants: ["inv-byzantine-cartel-resistance", "inv-edge-canonicalization"],
    links: [
      { label: "📘 Mesh Architecture Technical Blueprint", url: "https://docs.credence.run#docs/walkthroughs/03-p2p-mesh-consensus", desc: "P2P protocol specification, HRW rendezvous routing, and gossip sync" },
      { label: "🧪 Interactive Mesh Playground", url: "https://docs.credence.run#docs/playground", desc: "Simulate Byzantine partition attacks and cartel isolation in-browser" }
    ]
  },

  byzantine: {
    title: "Byzantine Fault Tolerance & Quorum Formulation",
    icon: "🛡️",
    tag: "CONSENSUS MATHEMATICS",
    tier1_plain_english: `
      <b>In plain words:</b> The math that makes the network impossible to rig or cheat.
      <br><br>
      Think of a jury where at least two-thirds of the jurors must agree with hard physical evidence before a verdict is signed. Even if bad actors set up fake computers to vote dishonestly, they cannot overpower the honest majority.
    `,
    tier1_article: {
      title: "📘 Robust Consensus Proofs Mathematics",
      desc: "Full mathematical proof of Byzantine cartel resistance and fault tolerance.",
      url: "https://docs.credence.run#docs/tutorials/08-sybil-cartel-demolition"
    },
    tier2_mechanics: [
      "<b>The 2f+1 Quorum Rule</b>: Requires agreement from at least 2f+1 honest nodes out of 3f+1 total nodes.",
      "<b>Sybil Cartel Defense</b>: Prevents attackers from creating thousands of fake computers to cheat votes.",
      "<b>Standalone Mode</b>: When you are running 1 node alone (N=1), it works completely on your local computer."
    ],
    cli: "credence mesh quorum",
    math_proof: "Quorum Condition: |V_ratified| ≥ 2f + 1 where f = ⌊(N-1)/3⌋. Total nodes N ≥ 3f + 1.",
    invariants: ["inv-byzantine-cartel-resistance", "inv-galileo-rule"],
    links: [
      { label: "✍️ Blast Radius Containment", url: "https://blog.credence.run#blast-radius-containment-in-decentralized-networks", desc: "Decentralized containment of compromised nodes" }
    ]
  },

  gossip: {
    title: "Live P2P Gossip Stream & Peer Protocol",
    icon: "📡",
    tag: "GOSSIP PROTOCOL",
    tier1_plain_english: `
      <b>In plain words:</b> How computers quickly share verified audits with each other.
      <br><br>
      When one computer finishes verifying a story, it whispers the result to a few neighboring computers, who whisper it to their neighbors. Within a split second, every node in the world has the new verification receipt.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Real-Time Mesh Observability",
      desc: "How ultra-lightweight gossip protocols broadcast verifications without slowing down networks.",
      url: "https://blog.credence.run#real-time-mesh-observability"
    },
    tier2_mechanics: [
      "<b>Epidemic Dissemination</b>: Information spreads across the entire world in O(log N) quick rounds.",
      "<b>Zero Duplicate Waste</b>: Memory filters prevent computers from re-sending information they've already shared.",
      "<b>Airgapped Sneakernet Support</b>: Can also sync data via USB drives when internet access is unavailable."
    ],
    cli: "credence mesh gossip --tail",
    math_proof: "Gossip Latency: T_sync = O(log N) rounds with fanout k=3 peers per cycle.",
    invariants: ["inv-canonical-json-ed25519", "inv-byzantine-cartel-resistance"],
    links: [
      { label: "📘 Mesh Architecture Technical Blueprint", url: "https://docs.credence.run#docs/walkthroughs/03-p2p-mesh-consensus", desc: "WebSocket transport, gossip payloads, and reconnection backoff" }
    ]
  },

  qi_scoring: {
    title: "5-Factor Node Quality Score (Qᵢ)",
    icon: "🏆",
    tag: "NODE QUALITY METRIC",
    tier1_plain_english: `
      <b>In plain words:</b> A report card for computers participating in the verification network.
      <br><br>
      Computers earn high scores by staying online, agreeing with verified facts, never making up quotes, and having a good reputation. Computers with high scores are trusted more during consensus votes.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Gamifying Truth Without the Casino",
      desc: "How decentralized peer quality scores reward factual accuracy without crypto speculation.",
      url: "https://blog.credence.run#gamifying-truth-without-the-casino"
    },
    tier2_mechanics: [
      "<b>5 Score Components</b>: Uptime (30%), Consensus Alignment (25%), Exact Grounding (20%), Subject Reputation (15%), Peer Review (10%).",
      "<b>Instant 50% Slash</b>: Any computer caught making up evidence loses half its reputation score immediately.",
      "<b>Fast Health Checks</b>: Nodes must respond to /health checks in under 850 milliseconds."
    ],
    cli: "credence mesh score <node_id>",
    math_proof: "Q_i = 0.30·U_i + 0.25·C_i + 0.20·G_i + 0.15·R_i + 0.10·P_i where Q_i ∈ [0, 1]. Slashing penalty: Q_i = 0.50·Q_i on hallucination.",
    invariants: ["inv-5factor-node-quality", "inv-empirical-expertise", "inv-verbatim-grounding"],
    links: [
      { label: "📘 Terminology & Ontology Lexicon", url: "https://docs.credence.run#docs/blueprints/terminology-and-ontology-lexicon", desc: "Quality formulations and epoch reward schedules" },
      { label: "📘 Robust Consensus Proofs", url: "https://docs.credence.run#docs/tutorials/08-sybil-cartel-demolition", desc: "Mathematical proofs of cartel resistance and quality convergence" }
    ]
  },

  vitals: {
    title: "Node Health, Memory & Scale-to-Zero Vitals",
    icon: "👤",
    tag: "COMPUTE PLANE",
    tier1_plain_english: `
      <b>In plain words:</b> Keeping our cloud servers fast, lightweight, and low-cost.
      <br><br>
      When no one is using the server, it automatically goes to sleep ($0 cost). When someone requests an audit, it wakes up instantly in under 850 milliseconds with fresh memory.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Taming the 10-Second Cold Start",
      desc: "How we reduced Cloud Run server startup time from 10 seconds down to 850ms.",
      url: "https://blog.credence.run#taming-the-10-second-cold-start-scale-to-zero"
    },
    tier2_mechanics: [
      "<b>Sub-Second Cold Starts</b>: Google Cloud Run Gen 2 container optimization with Startup CPU Boost and precompiled bytecode.",
      "<b>Hermetic Memory Ceilings</b>: Prevents out-of-memory crashes even when processing huge batches of articles.",
      "<b>Direct Execution</b>: Bypasses slow shell scripts to respond to /health checks in <850ms."
    ],
    cli: "credence doctor",
    math_proof: "Cold Start Target: T_germinate < 850ms. Memory Footprint Target: RSS < 180MB at idle.",
    invariants: ["inv-hermetic-testing", "inv-dense-workstation-viewport"],
    links: [
      { label: "📘 Cloud Run Scale-to-Zero Blueprint", url: "https://docs.credence.run#docs/blueprints/cloudrun-scale-to-zero-cold-start-optimization", desc: "Sub-40s deployment, WIF keyless auth, and scale-to-zero tuning" },
      { label: "✍️ From 860MB to 2MB: Sub-40s CI/CD Pipeline", url: "https://blog.credence.run#from-860mb-to-2mb-sub-40s-cicd-pipeline", desc: "Ultra-compact build artifacts and container optimization" }
    ]
  },

  telemetry: {
    title: "Interface Telemetry Loopback Protocol (ITLP-v1)",
    icon: "🩺",
    tag: "TELEMETRY STANDARD",
    tier1_plain_english: `
      <b>In plain words:</b> The dashboard's live pulse monitor.
      <br><br>
      Every few seconds, the dashboard asks the node for a tiny status update (<500 bytes) checking memory, CPU, and network health—without relying on heavy third-party monitoring tools.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Interface Telemetry Loopback",
      desc: "Designing resilient, zero-dependency telemetry for decentralized edge nodes.",
      url: "https://blog.credence.run#interface-telemetry-loopback"
    },
    tier2_mechanics: [
      "<b>Ultra-Lightweight Polling</b>: Standard HTTP GET /health and /api/telemetry returning <500 bytes.",
      "<b>Continuous Health Monitoring</b>: Tracks memory usage, event loop latency, and database connection pools.",
      "<b>Self-Healing Failover</b>: Switches to local offline cache if upstream servers become unreachable."
    ],
    cli: "credence telemetry",
    math_proof: "Telemetry Envelope: { status: 'HEALTHY', role: 'LOCAL_PRIMARY_ROOT', mode: 'STANDALONE', grounding_quotient: 1.00 }.",
    invariants: ["inv-xml-safety", "inv-dense-workstation-viewport"],
    links: [
      { label: "📘 Node & Mesh Telemetry Blueprint", url: "https://docs.credence.run#docs/blueprints/node-and-mesh-telemetry-dashboard", desc: "Diagnostic schema and real-time dashboard instrumentation" }
    ]
  },

  badges: {
    title: "Dynamic SVG Merit Badges & Manifest",
    icon: "🛡️",
    tag: "ATTESTATION BADGES",
    tier1_plain_english: `
      <b>In plain words:</b> Live truth badges that news websites can put on their pages.
      <br><br>
      Unlike static image badges that anyone could Photoshop, these are dynamic vector graphics linked to genuine cryptographic verification receipts with zero tracking cookies.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Red-Teaming the Truth Badge",
      desc: "Simulating attacks: How vector badges resist spoofing, clickjacking, and cache poisoning.",
      url: "https://blog.credence.run#red-teaming-the-truth-badge"
    },
    tier2_mechanics: [
      "<b>Anti-Tamper SVG Badges</b>: Embeddable Web Components showing real-time trust scores with zero user tracking.",
      "<b>P2P Seed Discovery</b>: Automatically finds peers using decentralized seed lists and DNS records.",
      "<b>Custom Organizations</b>: News organizations can host private badge registries using <code>credence init-org</code>."
    ],
    cli: "credence badge generate --domain reuters.com",
    math_proof: "SVG Signature: Anti-tamper digest embedded directly in SVG DOM comment metadata: <!-- credence-sig: 0x... -->.",
    invariants: ["inv-web-component-zero-clone", "inv-verbatim-grounding"],
    links: [
      { label: "📘 Embeddable Badges & Anti-Tamper Blueprint", url: "https://docs.credence.run#docs/blueprints/embeddable-attestation-badges-and-anti-tamper", desc: "Embeddable HTML5 custom elements and CSP-compliant badges" }
    ]
  },

  seeds: {
    title: "P2P Seed Manifest & Bootstrap Discovery",
    icon: "🌱",
    tag: "PEER DISCOVERY",
    tier1_plain_english: `
      <b>In plain words:</b> How a new computer finds friends on the network.
      <br><br>
      When you start a new Credence node for the first time, it checks a cryptographically signed seed list (<code>peers.json</code>) to connect to initial peers and join the global mesh.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Miracle-Gro for Truth Nodes",
      desc: "How decentralized peer discovery seeds cold networks in seconds.",
      url: "https://blog.credence.run#miracle-gro-for-truth-nodes"
    },
    tier2_mechanics: [
      "<b>Signed Seed Lists</b>: Seed lists are cryptographically signed by root authority keys.",
      "<b>DNS-SRV Backup</b>: Automatically falls back to DNS records if seed server links are down.",
      "<b>Decentralized Mesh Handoff</b>: Once connected, nodes discover new peers and no longer rely on seeds."
    ],
    cli: "credence mesh seeds",
    math_proof: "Seed Verification: Verify(Root_pub, Manifest_bytes, Manifest_sig) == true before accepting peer endpoints.",
    invariants: ["inv-canonical-json-ed25519", "inv-byzantine-cartel-resistance"],
    links: [
      { label: "📘 DNS-SRV Discovery Blueprint", url: "https://docs.credence.run#docs/tutorials/05-mesh-quickstart", desc: "Automating zero-coordinator mesh discovery" }
    ]
  },

  operator_admin: {
    title: "Operator Security Cockpit & Headroom Governor",
    icon: "🛠️",
    tag: "OPERATIONS",
    tier1_plain_english: `
      <b>In plain words:</b> The budget and safety control panel for node operators.
      <br><br>
      It ensures you never get a surprise cloud bill by automatically reserving at least 30% of your daily AI budget for critical emergencies, pausing non-essential background tasks when quota runs low.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: FinOps as Epistemology",
      desc: "Why strict token budgeting and cost controls are essential defenses against spam attacks.",
      url: "https://blog.credence.run#finops-as-epistemology"
    },
    tier2_mechanics: [
      "<b>30% Safety Reserve</b>: Halts low-priority background queues when daily token quota drops below 30% (<code>QUOTA_PRESERVED</code>).",
      "<b>Gemini 3.7 Flash Reference Engine</b>: Uses 4k thinking tokens to balance forensic accuracy with fast, low-cost execution.",
      "<b>Zero Secret Keys in CI/CD</b>: Keyless authentication across Dev and Prod environments."
    ],
    cli: "credence admin status",
    math_proof: "Circuit Breaker Condition: If Headroom(Tokens_daily) < 0.30, BackgroundQueue.halt() -> return QUOTA_PRESERVED.",
    invariants: ["inv-multi-model-sovereignty", "inv-4k-thinking-budget"],
    links: [
      { label: "📘 Operator Security & Workstation Tutorial", url: "https://docs.credence.run#docs/tutorials/14-operator-security-and-admin-workstation", desc: "Managing cost governors, circuit breakers, and administrative tokens" },
      { label: "✍️ The Economics of Epistemic Headroom", url: "https://blog.credence.run#the-economics-of-epistemic-headroom", desc: "Mathematical models for token preservation under adversarial burst traffic" }
    ]
  },

  miracle_gro: {
    title: "Miracle-Gro Seed Germination Engine",
    icon: "🌱",
    tag: "CACHE WARMING",
    tier1_plain_english: `
      <b>In plain words:</b> Pre-loading the database so searches are instant.
      <br><br>
      When a developer sets up a new node, Miracle-Gro automatically audits top news sources (like Reuters and AP) and saves the results locally, so your first search takes 0 milliseconds.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: Miracle-Gro for Truth Nodes",
      desc: "Accelerating cold-start cache performance across decentralized node clusters.",
      url: "https://blog.credence.run#miracle-gro-for-truth-nodes"
    },
    tier2_mechanics: [
      "<b>Cold-Start Seeding</b>: Pre-populates clean wire services so searches get instant 0ms cache hits.",
      "<b>Configurable Burst Sizes</b>: Operators configure bursts (1 to 25 articles) to stay strictly within daily spending limits.",
      "<b>Local SQLite Storage</b>: Evaluated receipts are signed and stored locally on disk."
    ],
    cli: "credence seed --burst 10",
    math_proof: "Germination Batch Size: N_burst ∈ [1, 25]. Cache Hit Latency: T_hit < 2ms.",
    invariants: ["inv-4k-thinking-budget", "inv-multi-model-sovereignty"],
    links: [
      { label: "📘 Developer Quickstart Guide", url: "https://docs.credence.run#docs/quickstart", desc: "Seeding local environments with one-command bootstrap" }
    ]
  },

  daemons: {
    title: "Ingestion Stream Daemons & Crawlers",
    icon: "🔄",
    tag: "DAEMON ENGINE",
    tier1_plain_english: `
      <b>In plain words:</b> Background robot assistants that keep the database up to date.
      <br><br>
      They quietly poll RSS news feeds, discover new websites linked in citations, and verify breaking news stories in the background while you work.
    `,
    tier1_article: {
      title: "✍️ Sovereign Essay: The Boredom Engine and Expanding Roots",
      desc: "Designing curiosity algorithms that explore outside news echo chambers.",
      url: "https://blog.credence.run#the-boredom-engine-and-expanding-roots"
    },
    tier2_mechanics: [
      "<b>Sifter Daemon</b>: Polls registered RSS/Atom feeds every 15 minutes for new stories.",
      "<b>Roots Crawler</b>: Discovers new publisher websites by checking links cited in verified articles.",
      "<b>Boredom Loop</b>: Automatically explores novel topics when the news cycle becomes repetitive."
    ],
    cli: "credence daemon start --all",
    math_proof: "Polling Cadence: T_sifter = 900s, T_roots = 3600s, T_boredom = 1800s.",
    invariants: ["inv-ssrf-defense", "inv-boredom-root-expansion"],
    links: [
      { label: "📘 Morning Feed Sifter Cookbook", url: "https://docs.credence.run#docs/cookbooks/morning-feed-sifter", desc: "Configuring systemd daemons and headless scrapers" }
    ]
  }
};

export function switchModalLens(lensNum) {
  const tabs = document.querySelectorAll(".modal-lens-tab");
  const panels = document.querySelectorAll(".modal-lens-panel");
  
  tabs.forEach(t => {
    t.className = "modal-lens-tab";
    if (parseInt(t.dataset.lens) === lensNum) {
      t.classList.add(`active-lens-${lensNum}`);
    }
  });

  panels.forEach(p => {
    p.classList.remove("active");
    if (parseInt(p.dataset.lens) === lensNum) {
      p.classList.add("active");
    }
  });
}

export function injectInfoModal() {
  if (document.getElementById("info-modal-backdrop")) return;
  const infoHtml = `
    <div id="info-modal-backdrop" class="operator-modal-backdrop">
      <div class="operator-modal" style="max-width:820px; width:92vw; max-height:90vh; display:flex; flex-direction:column;">
        <!-- Modal Header -->
        <div class="operator-modal-header" style="border-bottom:1px solid var(--border); padding-bottom:0.75rem;">
          <div style="display:flex; align-items:center; gap:0.65rem;">
            <span id="info-modal-icon" style="font-size:1.45rem;">ℹ️</span>
            <div>
              <div style="display:flex; align-items:center; gap:0.5rem;">
                <b id="info-modal-title" style="color:#fff; font-size:1.1rem;">Information</b>
                <span id="info-modal-tag" class="nav-badge" style="font-size:0.7rem; background:rgba(56,189,248,0.15); color:var(--accent-cyan); border:1px solid rgba(56,189,248,0.3);">SYSTEM</span>
              </div>
            </div>
          </div>
          <button class="btn-secondary" style="padding:0.25rem 0.65rem; font-size:0.85rem;" onclick="window.CredenceWS.closeInfoModal()">✕</button>
        </div>

        <!-- 3-Tier Tabbed Modal Body -->
        <div class="operator-modal-body" style="overflow-y:auto; padding-top:0.85rem; display:flex; flex-direction:column;">
          
          <!-- Interactive Lens Selector Tabs -->
          <div class="modal-lens-tabs">
            <button class="modal-lens-tab active-lens-1" data-lens="1" onclick="window.CredenceWS.switchModalLens(1)">
              🔍 Tier 1: Surface (Glance)
            </button>
            <button class="modal-lens-tab" data-lens="2" onclick="window.CredenceWS.switchModalLens(2)">
              🔬 Tier 2: Focus (Mechanics)
            </button>
            <button class="modal-lens-tab" data-lens="3" onclick="window.CredenceWS.switchModalLens(3)">
              📐 Tier 3: Deep Spectrum (Forensic)
            </button>
          </div>

          <!-- TIER 1: SURFACE LENS PANEL (Glance • Plain English) -->
          <div class="modal-lens-panel active" data-lens="1">
            <div class="modal-pyramid-tier modal-tier-1" style="background:rgba(56, 189, 248, 0.04); border-color:rgba(56, 189, 248, 0.25);">
              <div class="modal-tier-header">
                <span>🔍</span> <span>Surface Glance (Simple Words &bull; Plain English)</span>
              </div>
              <div id="info-modal-tier1" style="color:#fff; font-size:0.92rem; line-height:1.65; font-weight:450;"></div>
            </div>

            <!-- Tier 1 Featured Article Callout -->
            <div id="info-modal-tier1-article-box" class="modal-article-callout" style="display:none;">
              <span style="font-size:1.2rem; flex-shrink:0;">📖</span>
              <div style="flex:1;">
                <a id="info-modal-tier1-article-link" href="#" target="_blank" rel="noopener" style="color:#fff; font-size:0.86rem; font-weight:700; text-decoration:none; display:flex; align-items:center; gap:0.35rem;">
                  <span id="info-modal-tier1-article-title">Featured Case Study</span> ↗
                </a>
                <div id="info-modal-tier1-article-desc" style="color:var(--text-muted); font-size:0.78rem; margin-top:0.2rem; line-height:1.4;"></div>
              </div>
            </div>

            <!-- Enhance Button to Tier 2 -->
            <div style="display:flex; justify-content:flex-end; margin-top:0.25rem;">
              <button class="modal-enhance-btn modal-enhance-btn-focus" onclick="window.CredenceWS.switchModalLens(2)">
                <span>✨ Enhance to Focus Lens (Mechanics) &rarr;</span>
              </button>
            </div>
          </div>

          <!-- TIER 2: FOCUS LENS PANEL (Mechanics & Operations) -->
          <div class="modal-lens-panel" data-lens="2">
            <div class="modal-pyramid-tier modal-tier-2" style="background:rgba(245, 158, 11, 0.03); border-color:rgba(245, 158, 11, 0.25);">
              <div class="modal-tier-header">
                <span>🔬</span> <span>Focus Lens (Technical Mechanics &amp; Operational Rules)</span>
              </div>
              <ul id="info-modal-tier2-list" style="margin:0 0 0.75rem 0; padding-left:1.2rem; color:var(--text-muted); font-size:0.86rem; line-height:1.6; display:flex; flex-direction:column; gap:0.4rem;"></ul>
              
              <!-- CLI Command Snippet -->
              <div style="font-size:0.72rem; color:var(--text-dim); font-weight:700; text-transform:uppercase; margin-bottom:0.35rem;">Terminal CLI Command:</div>
              <div id="info-modal-cli-box" style="background:var(--bg-code, #030712); border:1px solid var(--border); border-radius:5px; padding:0.5rem 0.85rem; display:flex; justify-content:space-between; align-items:center; font-family:var(--font-mono); font-size:0.8rem;">
                <div style="display:flex; align-items:center; gap:0.45rem; overflow-x:auto;">
                  <span style="color:var(--accent-cyan);">$</span>
                  <code id="info-modal-cli" style="color:var(--accent-amber);">credence status</code>
                </div>
                <button class="btn-secondary" style="font-size:0.72rem; padding:0.15rem 0.55rem;" onclick="navigator.clipboard.writeText(document.getElementById('info-modal-cli').textContent); window.CredenceWS.showToast('Copied CLI command to clipboard', 'info');">Copy</button>
              </div>
            </div>

            <!-- Drill Down Button to Tier 3 -->
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.25rem;">
              <button class="btn-secondary" style="font-size:0.78rem;" onclick="window.CredenceWS.switchModalLens(1)">&larr; Back to Surface</button>
              <button class="modal-enhance-btn modal-enhance-btn-deep" onclick="window.CredenceWS.switchModalLens(3)">
                <span>📐 Drill Down to Deep Spectrum (Forensic Proofs) &rarr;</span>
              </button>
            </div>
          </div>

          <!-- TIER 3: DEEP SPECTRUM LENS PANEL (Forensic Proof & Governance) -->
          <div class="modal-lens-panel" data-lens="3">
            <div class="modal-pyramid-tier modal-tier-3" style="background:rgba(168, 85, 247, 0.04); border-color:rgba(168, 85, 247, 0.25);">
              <div class="modal-tier-header">
                <span>📐</span> <span>Deep Spectrum Lens (Forensic Proofs &amp; Invariant Bible)</span>
              </div>
              
              <!-- Math Formulation if present -->
              <div id="info-modal-math-box" style="display:none; background:rgba(0,0,0,0.3); border:1px solid rgba(168, 85, 247, 0.2); border-radius:5px; padding:0.5rem 0.85rem; margin-bottom:0.75rem; font-family:var(--font-mono); font-size:0.78rem; color:#e9d5ff;"></div>

              <!-- Invariant Guarantees Strip -->
              <div style="margin-bottom:0.75rem;">
                <div style="font-size:0.72rem; color:var(--text-dim); font-weight:700; text-transform:uppercase; margin-bottom:0.35rem;">Guaranteed By The Invariant Bible:</div>
                <div id="info-modal-invariants" style="display:flex; gap:0.45rem; flex-wrap:wrap;"></div>
              </div>

              <!-- Deep Reference Links -->
              <div>
                <div style="font-size:0.72rem; color:var(--text-dim); font-weight:700; text-transform:uppercase; margin-bottom:0.35rem;">Related Blueprints, Sovereign Essays &amp; Labs:</div>
                <div id="info-modal-links-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:0.5rem;"></div>
              </div>
            </div>

            <!-- Back Button to Tier 2 -->
            <div style="display:flex; justify-content:flex-start; margin-top:0.25rem;">
              <button class="btn-secondary" style="font-size:0.78rem;" onclick="window.CredenceWS.switchModalLens(2)">&larr; Back to Focus Lens</button>
            </div>
          </div>

        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML("beforeend", infoHtml);
}

export function openInfoModal(topicKey) {
  injectInfoModal();
  
  // Normalization aliases
  let key = (topicKey || "").toLowerCase().trim();
  if (key === "diff" || key === "revisions" || key === "stealth") key = "temporal_diff";
  if (key === "webcrypto" || key === "signature" || key === "keys") key = "webcrypto";
  if (key === "crypto") key = "webcrypto";
  if (key === "rules" || key === "rule" || key === "taxonomy") key = "taxonomies";
  if (key === "mesh" || key === "nodes") key = "topology";
  if (key === "admin" || key === "governor" || key === "cost") key = "operator_admin";
  if (key === "qi" || key === "leaderboard") key = "qi_scoring";
  let info = INFO_TOPICS[key];
  if (!info) {
    const rawTitle = (topicKey || "Epistemic Metric").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    console.warn(`[Credence Workstation] Undeclared info modal key: "${topicKey}". Generating JIT discovery view.`);
    info = {
      title: rawTitle,
      icon: "ℹ️",
      tag: "DISCOVERY / TOPIC",
      tier1_plain_english: `Detailed epistemic documentation and invariant rules for "${rawTitle}" are available in the central documentation network.`,
      tier1_article: {
        title: `Search "${rawTitle}" in Credence Docs`,
        url: `https://docs.credence.run#?query=${encodeURIComponent(topicKey || "")}`,
        desc: "Open live instant documentation search across all blueprints, guides, and invariants.",
      },
      tier2_mechanics: [
        "Inspect and audit this metric via CLI or query the FastMCP 2.0 reverse proxy.",
        "All metrics are bound by RFC 8785 canonical JSON and Ed25519 root signatures.",
      ],
      cli: `credence audit --topic ${topicKey || "metric"}`,
      invariants: ["inv-verbatim-grounding", "inv-4way-feature-parity"],
      links: [
        { label: "📘 Master Topic Index", url: "https://docs.credence.run#docs/topic-index" },
        { label: "🏛️ The Invariant Bible", url: "https://docs.credence.run#docs/invariants" },
      ],
    };
  }

  const titleEl = document.getElementById("info-modal-title");
  const iconEl = document.getElementById("info-modal-icon");
  const tagEl = document.getElementById("info-modal-tag");
  const tier1El = document.getElementById("info-modal-tier1");
  const t1ArtBox = document.getElementById("info-modal-tier1-article-box");
  const t1ArtLink = document.getElementById("info-modal-tier1-article-link");
  const t1ArtTitle = document.getElementById("info-modal-tier1-article-title");
  const t1ArtDesc = document.getElementById("info-modal-tier1-article-desc");
  const tier2List = document.getElementById("info-modal-tier2-list");
  const cliEl = document.getElementById("info-modal-cli");
  const mathBox = document.getElementById("info-modal-math-box");
  const invarBox = document.getElementById("info-modal-invariants");
  const linksGrid = document.getElementById("info-modal-links-grid");

  if (titleEl) titleEl.textContent = info.title;
  if (iconEl) iconEl.textContent = info.icon;
  if (tagEl) tagEl.textContent = info.tag || "SYSTEM";
  if (tier1El) tier1El.innerHTML = info.tier1_plain_english || "";

  if (t1ArtBox) {
    if (info.tier1_article) {
      t1ArtBox.style.display = "flex";
      if (t1ArtLink) t1ArtLink.href = info.tier1_article.url;
      if (t1ArtTitle) t1ArtTitle.textContent = info.tier1_article.title;
      if (t1ArtDesc) t1ArtDesc.textContent = info.tier1_article.desc;
    } else {
      t1ArtBox.style.display = "none";
    }
  }

  if (tier2List && info.tier2_mechanics) {
    tier2List.innerHTML = info.tier2_mechanics.map(d => `<li>${d}</li>`).join("");
  }

  if (cliEl) {
    cliEl.textContent = info.cli || "credence status";
  }

  if (mathBox) {
    if (info.math_proof) {
      mathBox.style.display = "block";
      mathBox.innerHTML = `<b>Proof / Formula:</b> ${info.math_proof}`;
    } else {
      mathBox.style.display = "none";
    }
  }

  if (invarBox && info.invariants) {
    invarBox.innerHTML = info.invariants.map(invRef => {
      const inv = resolveInvariant(typeof invRef === "object" ? (invRef.slug || invRef.id) : invRef);
      const isAlpha = inv.class.includes("α");
      const isBeta = inv.class.includes("β");
      const isGamma = inv.class.includes("γ");
      const badgeStyle = isAlpha 
        ? "background:rgba(239,68,68,0.15); color:#f87171; border:1px solid rgba(239,68,68,0.3);" 
        : (isBeta 
          ? "background:rgba(245,158,11,0.15); color:#fbbf24; border:1px solid rgba(245,158,11,0.3);"
          : (isGamma 
            ? "background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.3);"
            : "background:rgba(99,102,241,0.15); color:#818cf8; border:1px solid rgba(99,102,241,0.3);"));
      return `
        <a href="https://docs.credence.run#docs/invariants#${inv.slug}" target="_blank" rel="noopener" class="invariant-link-badge" style="display:inline-flex; align-items:center; gap:6px;">
          <span style="font-size:0.72rem; font-weight:800; padding:1px 5px; border-radius:3px; ${badgeStyle}">${inv.class}</span>
          <span>${inv.title}</span> ↗
        </a>
      `;
    }).join("");
  }

  if (linksGrid && info.links) {
    linksGrid.innerHTML = info.links.map(l => `
      <a href="${l.url}" target="_blank" rel="noopener" class="deck-domain-link" style="display:flex; flex-direction:column; padding:0.55rem 0.7rem; border-radius:5px; border:1px solid var(--border); text-decoration:none; background:var(--bg-secondary); transition:all 0.15s ease;">
        <span style="color:#fff; font-size:0.82rem; font-weight:700; margin-bottom:0.2rem;">${l.label} ↗</span>
        <span style="color:var(--text-dim); font-size:0.74rem; line-height:1.35;">${l.desc}</span>
      </a>
    `).join("");
  }

  switchModalLens(1); // Default to Surface Lens
  normalizeLocalLinks();
  document.getElementById("info-modal-backdrop")?.classList.add("active");
}

export function closeInfoModal() {
  document.getElementById('info-modal-backdrop')?.classList.remove('active');
}

// -----------------------------------------------------------------------------
// TUI HUD MODE TOGGLE
// -----------------------------------------------------------------------------

export function toggleTuiMode() {
  // Theme toggle removed by design
}

export function initTuiMode() {
  document.body.classList.remove('tui-mode');
  localStorage.removeItem('credence_tui_mode');
}

// -----------------------------------------------------------------------------
// WEBCRYPTO ED25519 VERIFICATION UTILITY
// -----------------------------------------------------------------------------

export async function verifyEd25519Signature(canonicalJsonString, signatureHex, pubkeyHex) {
  try {
    if (!window.crypto || !window.crypto.subtle) {
      return { valid: false, error: 'WebCrypto unavailable' };
    }
    const cleanPubHex = pubkeyHex.replace(/^0x/, '').trim();
    const cleanSigHex = signatureHex.replace(/^0x/, '').trim();
    
    const pubKeyBytes = new Uint8Array(cleanPubHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
    const sigBytes = new Uint8Array(cleanSigHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
    const msgBytes = new TextEncoder().encode(canonicalJsonString);

    const cryptoKey = await window.crypto.subtle.importKey(
      'raw',
      pubKeyBytes,
      { name: 'Ed25519' },
      false,
      ['verify']
    );

    const isValid = await window.crypto.subtle.verify(
      { name: 'Ed25519' },
      cryptoKey,
      sigBytes,
      msgBytes
    );

    return { valid: isValid, error: null };
  } catch (e) {
    return { valid: false, error: e.message };
  }
}

export function transformTargetUrl(href) {
  if (!href || typeof window === 'undefined' || !window.location) return href;
  const host = window.location.hostname;
  const isDev = host.startsWith('dev.') || host.startsWith('mcp.dev.');
  const isSingleHost = host === 'localhost' || host === '127.0.0.1' || host.endsWith('.a.run.app') || host.endsWith('.pages.dev');

  // Handle relative cross-domain paths (e.g. ../credence.report/index.html?rule=...)
  if (href.startsWith('../credence.') || href.startsWith('../admin.credence.')) {
    const parts = href.split('/');
    const targetDir = parts[1];
    const sub = parts.slice(2).join('/');
    const subPath = sub ? (sub.startsWith('?') ? `index.html${sub}` : sub) : '';
    if (isDev) return `https://dev.${targetDir}/${subPath}`;
    if (isSingleHost) return `/${targetDir}/${subPath}`;
    return `https://${targetDir}/${subPath}`;
  }

  // Handle Dev Preview Subdomains (stay on dev.* across ecosystem)
  if (isDev) {
    const prodMap = {
      'https://admin.credence.run': 'https://dev.admin.credence.run',
      'https://credence.run': 'https://dev.credence.run',
      'https://credence.report': 'https://dev.credence.report',
      'https://credence.nexus': 'https://dev.credence.nexus',
      'https://credence.foundation': 'https://dev.credence.foundation',
      'https://docs.credence.run': 'https://dev.credence.run/docs/',
      'https://blog.credence.run': 'https://dev.credence.run/blog/',
      'https://mcp.credence.run': 'https://mcp.dev.credence.run',
      'https://seeds.credence.nexus': 'https://dev.seeds.credence.nexus',
      'https://keys.credence.foundation': 'https://dev.keys.credence.foundation',
    };
    for (const [prodDomain, devDomain] of Object.entries(prodMap)) {
      if (href.startsWith(prodDomain)) {
        const sub = href.substring(prodDomain.length);
        if (devDomain.endsWith('/') && sub.startsWith('/')) {
          return `${devDomain.slice(0, -1)}${sub}`;
        }
        return `${devDomain}${sub}`;
      }
    }
  }

  // Handle Localhost / Direct Cloud Run path prefixing
  if (isSingleHost) {
    const pathMap = {
      'https://admin.credence.run': '/admin.credence.run/',
      'https://credence.run': '/credence.run/',
      'https://credence.report': '/credence.report/',
      'https://credence.nexus': '/credence.nexus/',
      'https://credence.foundation': '/credence.foundation/',
      'https://dev.admin.credence.run': '/admin.credence.run/',
      'https://dev.credence.run': '/credence.run/',
      'https://dev.credence.report': '/credence.report/',
      'https://dev.credence.nexus': '/credence.nexus/',
      'https://dev.credence.foundation': '/credence.foundation/',
    };
    if (href === '/' || href === 'https://credence.run' || href === 'https://credence.run/' || href === 'https://dev.credence.run' || href === 'https://dev.credence.run/') {
      return '/credence.run/';
    }
    for (const [domain, localPath] of Object.entries(pathMap)) {
      if (href.startsWith(domain)) {
        return `${localPath}${href.substring(domain.length).replace(/^\//, '')}`;
      }
    }
  }

  return href;
}

export function normalizeLocalLinks() {
  if (typeof document === 'undefined') return;

  document.querySelectorAll('a[href]').forEach(a => {
    const href = a.getAttribute('href');
    if (!href) return;
    const transformed = transformTargetUrl(href);
    if (transformed !== href) {
      a.setAttribute('href', transformed);
    }
  });
}

// Auto-run link normalization on DOM ready and capture clicks
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', normalizeLocalLinks);
  } else {
    normalizeLocalLinks();
  }

  // Capture-phase link click interceptor to guarantee zero-escape environment isolation
  document.addEventListener('click', (e) => {
    const anchor = e.target.closest && e.target.closest('a[href]');
    if (!anchor) return;
    const rawHref = anchor.getAttribute('href');
    if (!rawHref) return;
    const transformed = transformTargetUrl(rawHref);
    if (transformed !== rawHref) {
      anchor.setAttribute('href', transformed);
    }
  }, true);
}

// -----------------------------------------------------------------------------
// MAIN WORKSTATION INITIALIZER
// -----------------------------------------------------------------------------

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

  function switchTab(tabId) {
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
      if (match) p.style.display = 'block';
      else p.style.display = 'none';
    });

    if (window.location.hash !== `#${tabId}`) {
      history.replaceState(null, '', `#${tabId}`);
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
  const initialTab = initialHash || defaultTab;
  if (initialTab) {
    switchTab(initialTab);
  }

  // Bind click handlers to tab buttons
  document.querySelectorAll(tabButtonsSelector).forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const targetTab = btn.getAttribute('data-tab') || btn.getAttribute('href')?.replace(/^#/, '');
      if (targetTab && !targetTab.startsWith('http') && !targetTab.startsWith('/') && !targetTab.includes('.')) {
        e.preventDefault();
        switchTab(targetTab);
      }
    });
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
