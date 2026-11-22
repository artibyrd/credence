/**
 * Credence Workstation: Volunteer Worker Modal Shells
 * Extracted from workstation-workers.js to uphold the 500 LOC Ceiling Law.
 * Zero-npm native ES module. Contains strictly static modal shell templates.
 */

const UVX_CMD = 'uvx --from git+https://github.com/artibyrd/credence credence';

/**
 * Inject the static Worker Dossier Modal shell and bind event listeners.
 */
export function injectWorkerDossierModal(onClose, onCopy) {
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
          <button id="wd-close-btn" type="button" class="btn-secondary" style="padding:0.2rem 0.6rem; font-size:0.8rem;">✕</button>
        </div>

        <div class="operator-modal-body" style="padding:1.25rem;">
          <div style="background:var(--bg-secondary); border:1px solid var(--border); padding:0.6rem 0.85rem; border-radius:var(--radius-sm); margin-bottom:1.25rem; display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
            <div style="min-width:0; flex:1;">
              <span style="font-size:0.72rem; text-transform:uppercase; color:var(--text-dim); font-weight:700;">Ed25519 Public Key:</span><br>
              <code id="wd-pubkey" style="font-family:var(--font-mono); font-size:0.78rem; color:#fff; word-break:break-all;">--</code>
            </div>
            <button id="wd-copy-pubkey-btn" type="button" class="btn-secondary" style="font-size:0.72rem; padding:0.3rem 0.6rem; white-space:nowrap;">📋 Copy</button>
          </div>

          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:0.75rem; margin-bottom:1.25rem;">
            <div class="metric-card" style="padding:0.85rem;" title="Worker Quality & Accuracy Score (Q_w). Scaled 0.0 to 10.0 from backend 0.0-1.0 telemetry.">
              <div class="metric-label">Quality Score (Q_w)</div>
              <div class="metric-val" id="wd-qscore" style="color:var(--accent-green); font-size:1.35rem;">--</div>
              <div style="font-size:0.7rem; color:var(--text-dim); margin-top:2px;">Reliability (0-10)</div>
            </div>
            <div class="metric-card" style="padding:0.85rem;" title="Total mempool bounties claimed and verified with cryptographic attestation.">
              <div class="metric-label">Bounties Cleared</div>
              <div class="metric-val" id="wd-bounties" style="color:var(--accent-cyan); font-size:1.35rem;">--</div>
              <div style="font-size:0.7rem; color:var(--text-dim); margin-top:2px;">Verified Mempool Audits</div>
            </div>
            <div class="metric-card" style="padding:0.85rem;" title="Total LLM tokens donated to open research.">
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
              <button id="wd-copy-snippet-btn" type="button" class="btn-primary" style="font-size:0.75rem; padding:0.35rem 0.75rem; white-space:nowrap;">📋 Copy Markdown</button>
            </div>
          </div>

          <div style="margin-bottom:1.25rem;">
            <div style="font-size:0.85rem; font-weight:700; color:#fff; margin-bottom:0.5rem;">🏆 Unlocked Achievement Badges</div>
            <div id="wd-badges-gallery" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:0.5rem;"></div>
          </div>

          <div style="background:rgba(56,189,248,0.08); border:1px solid rgba(56,189,248,0.25); border-radius:6px; padding:0.75rem 1rem; margin-bottom:1.25rem; font-size:0.8rem; color:var(--text-muted); display:flex; gap:0.6rem; align-items:center;">
            <span style="font-size:1.2rem;">💡</span>
            <div>
              <b style="color:var(--accent-cyan);">Preserve Your Worker Identity:</b> Moving machines? Run <code>credence key export -o worker.pem</code> to keep your rank and badges intact on the leaderboard.
            </div>
          </div>

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
                <tbody id="wd-audits-body"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', html);

  document.getElementById('wd-close-btn')?.addEventListener('click', onClose);
  document.getElementById('wd-copy-pubkey-btn')?.addEventListener('click', () => {
    const pk = document.getElementById('wd-pubkey')?.textContent || '';
    onCopy(pk, 'Pubkey copied!');
  });
  document.getElementById('wd-copy-snippet-btn')?.addEventListener('click', () => {
    const snippet = document.getElementById('wd-embed-snippet')?.value || '';
    onCopy(snippet, 'Markdown badge snippet copied!');
  });
}

/**
 * Inject the static Worker Getting Started Modal shell and bind event listeners.
 */
export function injectWorkerStartModal(onClose) {
  if (document.getElementById('worker-start-modal')) return;

  const html = `
    <div id="worker-start-modal" class="operator-modal-backdrop" style="display:none; z-index:10000;">
      <div class="operator-modal" style="max-width:680px; max-height:88vh; overflow-y:auto;">
        <div class="operator-modal-header">
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span style="font-size:1.3rem;">🚀</span>
            <b style="color:#fff; font-size:1.1rem;">Join the Volunteer Worker Fleet</b>
          </div>
          <button id="ws-modal-close-x" type="button" class="btn-secondary" style="padding:0.2rem 0.6rem; font-size:0.8rem;">✕</button>
        </div>

        <div class="operator-modal-body" style="padding:1.25rem; font-size:0.85rem;">
          <p style="color:var(--text-muted); margin-bottom:1rem;">
            Contribute spare compute to the decentralized mempool. Fulfill peer audit requests, climb the contributor leaderboard, and earn cryptographic achievement badges.
            <br><b style="color:var(--accent-cyan);">Universal Model Support:</b> Run any cloud LLM or local open-weights engine (Gemini, Claude, GPT, DeepSeek, Llama, Mistral, Qwen, or custom fine-tunes via Ollama, vLLM, or LM Studio).
          </p>

          <h4 style="color:#fff; margin:1rem 0 0.5rem;">1. One-Command Quickstart (Universal Inference)</h4>
          <pre style="background:var(--bg-code); padding:0.75rem 1rem; border-radius:6px; font-family:var(--font-mono); font-size:0.78rem; overflow-x:auto; border:1px solid var(--border);"><code># Google Gemini (Default)
export GEMINI_API_KEY="AIzaSyYourGeminiApiKeyHere"
${UVX_CMD} worker --model google/gemini-3.8-flash

# Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-api03-YourAnthropicKeyHere"
${UVX_CMD} worker --model anthropic/claude-3-7-sonnet

# OpenAI GPT or DeepSeek
export OPENAI_API_KEY="sk-proj-YourOpenAiKeyHere"
${UVX_CMD} worker --model openai/gpt-4o-mini

export DEEPSEEK_API_KEY="sk-YourDeepSeekKeyHere"
${UVX_CMD} worker --model deepseek/deepseek-chat

# Local Open-Weights (Ollama / vLLM / LM Studio — 100% Private &amp; Zero-Cost)
export OLLAMA_HOST="http://localhost:11434"
${UVX_CMD} worker --model ollama/llama3.3:70b</code></pre>

          <h4 style="color:#fff; margin:1.25rem 0 0.5rem;">2. Key Custody: Maintain Your Rank Across Machines</h4>
          <p style="color:var(--text-muted); margin-bottom:0.5rem;">
            Your worker rank, badges, and reputation are permanently tied to your Ed25519 private key.
          </p>
          <pre style="background:var(--bg-code); padding:0.75rem 1rem; border-radius:6px; font-family:var(--font-mono); font-size:0.78rem; overflow-x:auto; border:1px solid var(--border);"><code># Export your key before moving to a new computer:
credence key export -o ~/my-credence-worker.pem

# Import and restore your identity on the new machine:
credence key import ~/my-credence-worker.pem</code></pre>

          <div style="margin-top:1.5rem; display:flex; justify-content:flex-end;">
            <button id="ws-modal-close-cta" type="button" class="btn-primary">Got It, Let's Compute!</button>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', html);

  document.getElementById('ws-modal-close-x')?.addEventListener('click', onClose);
  document.getElementById('ws-modal-close-cta')?.addEventListener('click', onClose);
}
