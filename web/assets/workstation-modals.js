/**
 * Credence Workstation Modals, Toasts & Epistemic Information Pyramid
 * Zero-npm native ES module.
 */

import { authState, setStoredToken, checkAuthStatus, updateRibbonAuthBadge } from './workstation-auth.js';
import { INFO_TOPICS } from './workstation-topics.js';
import { resolveInvariant } from './credence-workstation.js';
import { normalizeLocalLinks } from './workstation-nav.js';

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
        url: `https://docs.credence.run/?query=${encodeURIComponent(topicKey || "")}`,
        desc: "Open live instant documentation search across all blueprints, guides, and invariants.",
      },
      tier2_mechanics: [
        "Inspect and audit this metric via CLI or query the FastMCP 2.0 reverse proxy.",
        "All metrics are bound by RFC 8785 canonical JSON and Ed25519 root signatures.",
      ],
      cli: `credence audit --topic ${topicKey || "metric"}`,
      invariants: ["inv-verbatim-grounding", "inv-4way-feature-parity"],
      links: [
        { label: "📘 Master Topic Index", url: "https://docs.credence.run/topic-index" },
        { label: "🏛️ The Invariant Bible", url: "https://docs.credence.run/invariants" },
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
        <a href="https://docs.credence.run/invariants#${inv.slug}" target="_blank" rel="noopener" class="invariant-link-badge" style="display:inline-flex; align-items:center; gap:6px;">
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

