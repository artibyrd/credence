/**
 * Credence Workstation: Volunteer Worker Fleet Leaderboard & Contributor Dossiers
 * Zero-npm native ES module.
 * 
 * Governed by Theme 1: Botanical Network & Lifecycle & Theme 4: Sovereign Governance.
 */

import { getApiBaseUrl } from './workstation-auth.js';
import { showToast } from './workstation-modals.js';

let cachedWorkers = [];
let currentFilterFamily = 'all';
let currentSearchQuery = '';

/**
 * Fetch and render the volunteer worker leaderboard.
 */
export async function fetchWorkerLeaderboard(search = '', family = 'all') {
  currentSearchQuery = search;
  currentFilterFamily = family;

  const base = getApiBaseUrl();
  const lBody = document.getElementById('worker-leaderboard-body');
  const countPill = document.getElementById('worker-count-pill');

  try {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (family && family !== 'all') params.append('family', family);
    params.append('limit', '50');

    let res = await fetch(`${base}/api/workers/leaderboard?${params.toString()}`);
    if ((!res.ok || res.status === 404) && !base) {
      try {
        const devRes = await fetch(`https://credence-dev-865363499314.us-central1.run.app/api/workers/leaderboard?${params.toString()}`);
        if (devRes.ok) res = devRes;
      } catch (_) {}
    }
    if (res.ok) {
      const data = await res.json();
      cachedWorkers = data.workers || [];
      if (countPill) {
        countPill.textContent = `${data.total_workers || cachedWorkers.length} Active Workers`;
      }
      renderWorkerLeaderboard(cachedWorkers);
      return;
    }
  } catch (e) {
    console.debug('Worker leaderboard live fetch fallback:', e);
  }

  // Fallback demo/genesis data if offline or local preview
  if (cachedWorkers.length === 0) {
    cachedWorkers = [
      {
        worker_pubkey: "4f8a19b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abc",
        worker_alias: "arbiter-alpha", model_family: "google/gemini", model_slug: "google/gemini-3.8-flash",
        total_completed: 142, bounties_cleared: 142, tokens_donated: 213000, tokens_saved_usd: 0.0724, quality_score: 0.98,
        badges: [{ badge_id: "bounty_hunter", name: "Bounty Hunter", icon: "🏹", description: "Cleared 50+ bounties" }, { badge_id: "precision_striker", name: "Precision Striker", icon: "🎯", description: "Perfect G=1.00 grounding" }],
        last_seen: new Date().toISOString()
      },
      {
        worker_pubkey: "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b",
        worker_alias: "deepseek-runner", model_family: "deepseek/deepseek", model_slug: "deepseek/deepseek-r1",
        total_completed: 88, bounties_cleared: 88, tokens_donated: 132000, tokens_saved_usd: 0.0449, quality_score: 0.92,
        badges: [{ badge_id: "first_bounty", name: "First Bounty", icon: "🌱", description: "Fulfilled first audit" }, { badge_id: "speed_demon", name: "Speed Demon", icon: "⚡", description: "Sub-5s turnaround" }],
        last_seen: new Date().toISOString()
      }
    ];
  }

  renderWorkerLeaderboard(cachedWorkers);
}

/**
 * Filter cached workers locally on keystrokes.
 */
export function filterWorkerLeaderboard() {
  const sInput = document.getElementById('worker-search-input');
  const fSelect = document.getElementById('worker-family-select');
  const q = (sInput ? sInput.value : '').trim().toLowerCase();
  const fam = fSelect ? fSelect.value : 'all';

  const filtered = cachedWorkers.filter(w => {
    const matchSearch = !q || w.worker_alias.toLowerCase().includes(q) || w.worker_pubkey.toLowerCase().includes(q);
    const matchFam = fam === 'all' || w.model_family.toLowerCase().includes(fam);
    return matchSearch && matchFam;
  });
  renderWorkerLeaderboard(filtered);
}

/**
 * Render worker leaderboard rows.
 */
export function renderWorkerLeaderboard(workers) {
  const lBody = document.getElementById('worker-leaderboard-body');
  if (!lBody) return;

  if (!workers || workers.length === 0) {
    lBody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align:center; padding:2rem; color:var(--text-muted);">
          No volunteer workers found matching criteria. Run <code>uvx credence worker</code> to join the fleet!
        </td>
      </tr>
    `;
    return;
  }

  lBody.innerHTML = workers.map((w, idx) => {
    const badgesHtml = (w.badges || []).map(b => 
      `<span title="${b.name}: ${b.description}" style="cursor:help; font-size:1.1rem; margin-right:2px;">${b.icon || '🏅'}</span>`
    ).join('');

    const shortPub = w.worker_pubkey.slice(0, 16);

    return `
      <tr style="cursor:pointer;" onclick="window.CredenceWS.openWorkerDossier('${w.worker_pubkey}')" title="Click to inspect contributor dossier">
        <td style="text-align:center;"><b style="color:var(--accent-amber);">#${idx + 1}</b></td>
        <td>
          <b style="color:#fff;">${w.worker_alias || 'volunteer'}</b><br>
          <span style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-dim); word-break:break-all;">${shortPub}</span>
        </td>
        <td>
          <span class="ribbon-pill ready" style="font-size:0.72rem;">${w.model_family}</span><br>
          <span style="font-family:var(--font-mono); font-size:0.72rem; color:var(--text-muted); word-break:break-all;" title="${w.model_slug || ''}">${w.model_slug || ''}</span>
        </td>
        <td><b style="color:var(--accent-green); font-family:var(--font-mono);">${(w.quality_score * 10).toFixed(1)} / 10</b></td>
        <td><b style="color:var(--accent-cyan); font-family:var(--font-mono);">${w.bounties_cleared}</b></td>
        <td style="font-family:var(--font-mono);">${(w.tokens_donated || 0).toLocaleString()}</td>
        <td style="font-family:var(--font-mono); color:var(--accent-green);">$${(w.tokens_saved_usd || 0).toFixed(4)}</td>
        <td>${badgesHtml || '<span style="color:var(--text-dim); font-size:0.75rem;">None yet</span>'}</td>
        <td style="text-align:center;">
          <button class="btn-secondary" style="font-size:0.72rem; padding:0.2rem 0.5rem; color:var(--accent-cyan);" onclick="event.stopPropagation(); window.CredenceWS.openWorkerDossier('${w.worker_pubkey}')">
            Dossier ↗
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Open Worker Dossier modal.
 */
export async function openWorkerDossier(pubkey) {
  let modal = document.getElementById('worker-dossier-modal');
  if (!modal) {
    injectWorkerDossierModal();
    modal = document.getElementById('worker-dossier-modal');
  }

  modal.style.display = 'flex';
  const base = getApiBaseUrl();

  // Populate basic info while loading
  document.getElementById('wd-pubkey').textContent = pubkey;
  document.getElementById('wd-alias').textContent = 'Loading';
  document.getElementById('wd-family').textContent = 'Loading';
  document.getElementById('wd-qscore').textContent = '--';
  document.getElementById('wd-bounties').textContent = '--';
  document.getElementById('wd-tokens').textContent = '--';
  document.getElementById('wd-savings').textContent = '--';
  document.getElementById('wd-badges-gallery').innerHTML = '<p style="color:var(--text-dim);">Loading badges</p>';
  const aCountInit = document.getElementById('wd-audits-count');
  if (aCountInit) aCountInit.textContent = 'Loading';
  document.getElementById('wd-audits-body').innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-dim);">Loading audit history</td></tr>';

  // SVG badge preview URL
  const badgeBase = base || (window.location.hostname.includes('credence.nexus') ? 'https://credence-dev-865363499314.us-central1.run.app' : '');
  const badgeUrl = `${badgeBase}/api/badge/worker/${pubkey}.svg`;
  const badgeImg = document.getElementById('wd-badge-img');
  if (badgeImg) badgeImg.src = badgeUrl;

  const mdSnippet = `[![Credence Worker](${badgeUrl})](https://credence.nexus/#worker/${pubkey})`;
  const snippetInput = document.getElementById('wd-embed-snippet');
  if (snippetInput) snippetInput.value = mdSnippet;

  try {
    let res = await fetch(`${base}/api/worker/${pubkey}`);
    if ((!res.ok || res.status === 404) && !base) {
      try {
        const devRes = await fetch(`https://credence-dev-865363499314.us-central1.run.app/api/worker/${pubkey}`);
        if (devRes.ok) res = devRes;
      } catch (_) {}
    }
    if (res.ok) {
      const data = await res.json();
      document.getElementById('wd-alias').textContent = data.worker_alias || 'Volunteer Contributor';
      document.getElementById('wd-family').textContent = `${data.model_family} (${data.model_slug})`;
      document.getElementById('wd-qscore').textContent = `${(data.quality_score * 10).toFixed(1)} / 10`;
      document.getElementById('wd-bounties').textContent = data.bounties_cleared;
      document.getElementById('wd-tokens').textContent = (data.tokens_donated || 0).toLocaleString();
      document.getElementById('wd-savings').textContent = `$${(data.tokens_saved_usd || 0).toFixed(4)}`;

      // Render Badges Gallery
      const gallery = document.getElementById('wd-badges-gallery');
      if (gallery) {
        if (!data.badges || data.badges.length === 0) {
          gallery.innerHTML = '<p style="color:var(--text-dim); font-size:0.85rem;">No achievement badges unlocked yet. Keep fulfilling bounties!</p>';
        } else {
          gallery.innerHTML = data.badges.map(b => `
            <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:6px; padding:0.65rem 0.85rem; display:flex; align-items:center; gap:0.6rem;">
              <span style="font-size:1.6rem;">${b.icon || '🏅'}</span>
              <div>
                <b style="color:#fff; font-size:0.85rem;">${b.name}</b>
                <p style="color:var(--text-dim); font-size:0.75rem; margin:0;">${b.description}</p>
              </div>
            </div>
          `).join('');
        }
      }

      // Render Audits Table and Reconciled Bounty Count
      const aBody = document.getElementById('wd-audits-body');
      const aCount = document.getElementById('wd-audits-count');
      const audits = data.recent_audits || [];
      if (aCount) {
        aCount.textContent = `Showing ${audits.length} of ${data.bounties_cleared || audits.length} completed bounties`;
      }
      if (aBody) {
        if (audits.length === 0) {
          aBody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-dim); padding:1rem;">No verified mempool audits recorded yet.</td></tr>';
        } else {
          aBody.innerHTML = data.recent_audits.map(a => `
            <tr>
              <td style="font-size:0.78rem; font-family:var(--font-mono);">${a.audited_at.slice(0, 19).replace('T', ' ')}</td>
              <td style="max-width:240px; word-break:break-all;">
                <a href="${a.url}" target="_blank" rel="noopener" style="color:var(--accent-cyan); text-decoration:none;">${a.url}</a>
              </td>
              <td><b style="font-family:var(--font-mono); color:${a.suspicion_score > 50 ? 'var(--accent-red)' : 'var(--accent-green)'}">${a.suspicion_score.toFixed(1)}</b></td>
              <td><span class="ribbon-pill ready" style="font-size:0.7rem;">${a.classification}</span></td>
              <td style="font-family:var(--font-mono); font-size:0.72rem; color:var(--text-dim);">${a.node_signature ? a.node_signature.slice(0, 16) : '--'}</td>
            </tr>
          `).join('');
        }
      }
    }
  } catch (err) {
    console.debug('Worker dossier fetch failed:', err);
  }
}

/**
 * Close Worker Dossier modal.
 */
export function closeWorkerDossier() {
  const modal = document.getElementById('worker-dossier-modal');
  if (modal) modal.style.display = 'none';
}

/**
 * Open Worker Getting Started modal.
 */
export function openWorkerStartModal() {
  let modal = document.getElementById('worker-start-modal');
  if (!modal) {
    injectWorkerStartModal();
    modal = document.getElementById('worker-start-modal');
  }
  modal.style.display = 'flex';
}

/**
 * Close Worker Getting Started modal.
 */
export function closeWorkerStartModal() {
  const modal = document.getElementById('worker-start-modal');
  if (modal) modal.style.display = 'none';
}

/**
 * Copy text to clipboard and show toast.
 */
export function copyToClipboard(text, label = 'Copied to clipboard!') {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => showToast(label, 'success'));
  }
}

/**
 * Inject the Worker Dossier Modal HTML.
 */
function injectWorkerDossierModal() {
  if (document.getElementById('worker-dossier-modal')) return;

  const html = `
    <div id="worker-dossier-modal" class="operator-modal-backdrop" style="display:none; z-index:10000;">
      <div class="operator-modal" style="max-width:780px; max-height:90vh; overflow-y:auto;">
        <div class="operator-modal-header" style="position:sticky; top:0; background:var(--bg-secondary); z-index:10;">
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span style="font-size:1.3rem;">🐝</span>
            <div>
              <b id="wd-alias" style="color:#fff; font-size:1.1rem;">Contributor Dossier</b>
              <div id="wd-family" style="color:var(--accent-cyan); font-size:0.78rem; font-family:var(--font-mono);">--</div>
            </div>
          </div>
          <button class="btn-secondary" style="padding:0.2rem 0.6rem; font-size:0.8rem;" onclick="window.CredenceWS.closeWorkerDossier()">✕</button>
        </div>

        <div class="operator-modal-body" style="padding:1.25rem;">
          <!-- Pubkey Bar -->
          <div style="background:var(--bg-secondary); border:1px solid var(--border); padding:0.6rem 0.85rem; border-radius:var(--radius-sm); margin-bottom:1.25rem; display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
            <div style="min-width:0; flex:1;">
              <span style="font-size:0.72rem; text-transform:uppercase; color:var(--text-dim); font-weight:700;">Ed25519 Public Key:</span><br>
              <code id="wd-pubkey" style="font-family:var(--font-mono); font-size:0.78rem; color:#fff; word-break:break-all;">--</code>
            </div>
            <button class="btn-secondary" style="font-size:0.72rem; padding:0.3rem 0.6rem; white-space:nowrap;" onclick="window.CredenceWS.copyToClipboard(document.getElementById('wd-pubkey').textContent, 'Pubkey copied!')">📋 Copy</button>
          </div>

          <!-- 4-Metric Grid -->
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:0.75rem; margin-bottom:1.25rem;">
            <div class="metric-card" style="padding:0.85rem;" title="Worker Quality & Accuracy Score (Q_w). Scaled 0.0 to 10.0 based on volume, G=1.00 grounding, and longevity.">
              <div class="metric-label">Quality Score (Q_w)</div>
              <div class="metric-val" id="wd-qscore" style="color:var(--accent-green); font-size:1.35rem;">--</div>
              <div style="font-size:0.7rem; color:var(--text-dim); margin-top:2px;">Reliability (0-10)</div>
            </div>
            <div class="metric-card" style="padding:0.85rem;" title="Total mempool bounties claimed and verified with cryptographic attestation.">
              <div class="metric-label">Bounties Cleared</div>
              <div class="metric-val" id="wd-bounties" style="color:var(--accent-cyan); font-size:1.35rem;">--</div>
              <div style="font-size:0.7rem; color:var(--text-dim); margin-top:2px;">Verified Mempool Audits</div>
            </div>
            <div class="metric-card" style="padding:0.85rem;" title="Estimated total LLM tokens donated to open research.">
              <div class="metric-label">Tokens Donated</div>
              <div class="metric-val" id="wd-tokens" style="font-size:1.35rem;">--</div>
              <div style="font-size:0.7rem; color:var(--text-dim); margin-top:2px;">LLM Compute Volume</div>
            </div>
            <div class="metric-card" style="padding:0.85rem;" title="Estimated economic value contributed based on commercial API rates.">
              <div class="metric-label">Value Saved ($)</div>
              <div class="metric-val" id="wd-savings" style="color:var(--accent-amber); font-size:1.35rem;">--</div>
              <div style="font-size:0.7rem; color:var(--text-dim); margin-top:2px;">Public Benefit ($)</div>
            </div>
          </div>

          <!-- SVG Profile Badge & Embed Snippet -->
          <div style="background:var(--bg-secondary); border:1px solid var(--border); border-radius:6px; padding:1rem; margin-bottom:1.25rem;">
            <div style="font-size:0.85rem; font-weight:700; color:#fff; margin-bottom:0.5rem; display:flex; align-items:center; gap:0.4rem;">
              <span>🛡️</span> Live Achievement Profile Badge
            </div>
            <div style="display:flex; gap:1rem; align-items:center; flex-wrap:wrap; margin-bottom:0.75rem;">
              <img id="wd-badge-img" src="" alt="Worker Badge" style="height:32px; border-radius:4px; background:#111;">
              <div style="font-size:0.75rem; color:var(--text-dim); flex:1; min-width:200px;">
                Dynamic SVG badge updates automatically as bounties are fulfilled. Embed it on your GitHub README or personal portfolio.
              </div>
            </div>
            <div style="display:flex; gap:0.5rem;">
              <input type="text" id="wd-embed-snippet" readonly class="form-input" style="font-size:0.75rem; font-family:var(--font-mono); padding:0.35rem 0.6rem; background:var(--bg-card); color:#fff; flex:1;">
              <button class="btn-primary" style="font-size:0.75rem; padding:0.35rem 0.75rem; white-space:nowrap;" onclick="window.CredenceWS.copyToClipboard(document.getElementById('wd-embed-snippet').value, 'Markdown badge snippet copied!')">📋 Copy Markdown</button>
            </div>
          </div>

          <!-- Badges Gallery -->
          <div style="margin-bottom:1.25rem;">
            <div style="font-size:0.85rem; font-weight:700; color:#fff; margin-bottom:0.5rem;">🏆 Unlocked Achievement Badges</div>
            <div id="wd-badges-gallery" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:0.5rem;">
              <!-- Badges populated dynamically -->
            </div>
          </div>

          <!-- Key Custody Callout -->
          <div style="background:rgba(56,189,248,0.08); border:1px solid rgba(56,189,248,0.25); border-radius:6px; padding:0.75rem 1rem; margin-bottom:1.25rem; font-size:0.8rem; color:var(--text-muted); display:flex; gap:0.6rem; align-items:center;">
            <span style="font-size:1.2rem;">💡</span>
            <div>
              <b style="color:var(--accent-cyan);">Preserve Your Worker Identity:</b> Moving machines? Run <code>credence key export -o worker.pem</code> to keep your rank and badges intact on the leaderboard.
            </div>
          </div>

          <!-- Recent Audits Table -->
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.35rem;">
              <div style="font-size:0.85rem; font-weight:700; color:#fff;">📜 Fulfilled Bounties &amp; Signed Audits</div>
              <span id="wd-audits-count" style="font-size:0.75rem; color:var(--accent-cyan); font-family:var(--font-mono);">--</span>
            </div>
            <p style="font-size:0.75rem; color:var(--text-dim); margin:0 0 0.5rem;">Each cleared mempool bounty produces a character-grounded (G=1.00) cryptographic audit signed with this worker's Ed25519 key.</p>
            <div class="ws-table-container" style="max-height:220px; overflow-y:auto;">
              <table class="ws-table" style="font-size:0.78rem;">
                <thead>
                  <tr>
                    <th style="width:130px;">Audited At</th>
                    <th>Target Source URL</th>
                    <th style="width:70px;">Score</th>
                    <th style="width:90px;">Verdict</th>
                    <th style="width:110px;">Ed25519 Sig</th>
                  </tr>
                </thead>
                <tbody id="wd-audits-body">
                  <!-- Populated dynamically -->
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', html);
}

/**
 * Inject Worker Getting Started Modal HTML.
 */
function injectWorkerStartModal() {
  if (document.getElementById('worker-start-modal')) return;

  const html = `
    <div id="worker-start-modal" class="operator-modal-backdrop" style="display:none; z-index:10000;">
      <div class="operator-modal" style="max-width:680px; max-height:88vh; overflow-y:auto;">
        <div class="operator-modal-header">
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span style="font-size:1.3rem;">🚀</span>
            <b style="color:#fff; font-size:1.1rem;">Join the Volunteer Worker Fleet</b>
          </div>
          <button class="btn-secondary" style="padding:0.2rem 0.6rem; font-size:0.8rem;" onclick="window.CredenceWS.closeWorkerStartModal()">✕</button>
        </div>

        <div class="operator-modal-body" style="padding:1.25rem; font-size:0.85rem;">
          <p style="color:var(--text-muted); margin-bottom:1rem;">
            Contribute spare compute to the decentralized mempool. Fulfill peer audit requests, climb the contributor leaderboard, and earn cryptographic achievement badges.
            <br><b style="color:var(--accent-cyan);">Universal Model Support:</b> Run any cloud LLM or local open-weights engine (Gemini, Claude, GPT, DeepSeek, Llama, Mistral, Qwen, or custom fine-tunes via Ollama, vLLM, or LM Studio).
          </p>

          <h4 style="color:#fff; margin:1rem 0 0.5rem;">1. One-Command Quickstart (Universal Inference)</h4>
          <pre style="background:var(--bg-code); padding:0.75rem 1rem; border-radius:6px; font-family:var(--font-mono); font-size:0.8rem; overflow-x:auto; border:1px solid var(--border);"><code># Google Gemini (Default)
export GEMINI_API_KEY="AIzaSyYourGeminiApiKeyHere"
uvx credence worker --model google/gemini-3.8-flash

# Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-api03-YourAnthropicKeyHere"
uvx credence worker --model anthropic/claude-3-7-sonnet

# OpenAI GPT or DeepSeek
export OPENAI_API_KEY="sk-proj-YourOpenAiKeyHere"
uvx credence worker --model openai/gpt-4o-mini
# Or DeepSeek: uvx credence worker --model deepseek/deepseek-chat --api-base https://api.deepseek.com/v1

# Local Open-Weights (Ollama / vLLM / LM Studio — 100% Private &amp; Zero-Cost)
uvx credence worker --model deepseek-r1:70b --api-base http://localhost:11434/v1</code></pre>

          <h4 style="color:#fff; margin:1.25rem 0 0.5rem;">2. Key Custody: Maintain Your Rank Across Machines</h4>
          <p style="color:var(--text-muted); margin-bottom:0.5rem;">
            Your worker rank, badges, and reputation are permanently tied to your Ed25519 private key.
          </p>
          <pre style="background:var(--bg-code); padding:0.75rem 1rem; border-radius:6px; font-family:var(--font-mono); font-size:0.8rem; overflow-x:auto; border:1px solid var(--border);"><code># Export your key before moving to a new computer:
credence key export -o ~/my-credence-worker.pem

# Import and restore your identity on the new machine:
credence key import -i ~/my-credence-worker.pem</code></pre>

          <div style="margin-top:1.5rem; display:flex; justify-content:flex-end;">
            <button class="btn-primary" onclick="window.CredenceWS.closeWorkerStartModal()">Got It, Let's Compute!</button>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', html);
}

/**
 * Handle URL hash routing (#worker/{pubkey}).
 */
export function handleWorkerHashRoute() {
  const hash = window.location.hash || '';
  if (hash.startsWith('#worker/')) {
    const pubkey = hash.replace('#worker/', '').trim();
    if (pubkey) {
      if (window.CredenceWS && window.CredenceWS.switchTab) {
        window.CredenceWS.switchTab('leaderboard');
      }
      if (window.switchLeaderboardSubtab) {
        window.switchLeaderboardSubtab('workers');
      }
      openWorkerDossier(pubkey);
    }
  }
}
