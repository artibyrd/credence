/**
 * Credence Workstation: Volunteer Worker Fleet Leaderboard & Contributor Dossiers
 * Zero-npm native ES module. Uses safe DOM APIs (textContent + createElement) to
 * prevent Stored XSS across all dynamic worker and audit telemetry fields.
 *
 * Governed by Theme 1: Botanical Network & Lifecycle & Theme 4: Sovereign Governance.
 */

import { getApiBaseUrl } from './workstation-auth.js';
import { showToast } from './workstation-modals.js';
import { injectWorkerDossierModal, injectWorkerStartModal } from './workstation-workers-modals.js';

let cachedWorkers = [];
let currentFilterFamily = 'all';
let currentSearchQuery = '';

const UVX_WORKER_CMD = 'uvx --from git+https://github.com/artibyrd/credence credence worker';

/**
 * Escape HTML special characters for safe string serialization when needed.
 */
export function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Validate that a URL uses an explicit http:// or https:// protocol before rendering as a link.
 */
export function safeHttpUrl(rawUrl) {
  try {
    const parsed = new URL(String(rawUrl || '').trim());
    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
      return parsed.href;
    }
  } catch (_) {}
  return null;
}

function el(tag, attrs = {}, text = null) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined) continue;
    if (k === 'className') node.className = v;
    else if (k === 'style') node.setAttribute('style', v);
    else if (k.startsWith('data-')) node.setAttribute(k, String(v));
    else node.setAttribute(k, String(v));
  }
  if (text !== null && text !== undefined) {
    node.textContent = String(text);
  }
  return node;
}

function renderEmptyLeaderboardState(lBody, offlineMessage = null) {
  lBody.replaceChildren();
  const tr = el('tr');
  const td = el('td', { colspan: '9', style: 'padding:2rem; text-align:center;' });
  const card = el('div', {
    className: 'ws-empty-card',
    style:
      'max-width:560px; margin:0 auto; padding:1.25rem 1.5rem; border:1px solid var(--border); ' +
      'border-radius:8px; background:var(--bg-secondary); color:var(--text-muted);',
  });
  card.appendChild(
    el(
      'div',
      { style: 'font-weight:700; color:#fff; margin-bottom:0.45rem;' },
      offlineMessage || 'No Volunteer Workers Registered Yet'
    )
  );
  const sub = el('div', { style: 'font-size:0.82rem; line-height:1.5;' });
  sub.appendChild(document.createTextNode('Join the decentralized mempool by running '));
  sub.appendChild(el('code', { style: 'color:var(--accent-cyan);' }, UVX_WORKER_CMD));
  sub.appendChild(document.createTextNode(' to claim bounties and earn Ed25519 merit badges.'));
  card.appendChild(sub);
  td.appendChild(card);
  tr.appendChild(td);
  lBody.appendChild(tr);
}

/**
 * Fetch and render the volunteer worker leaderboard (fail-closed, zero mock fallback).
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

    const res = await fetch(`${base}/api/workers/leaderboard?${params.toString()}`);
    if (res.ok) {
      const data = await res.json();
      cachedWorkers = Array.isArray(data.workers) ? data.workers : [];
      if (countPill) {
        countPill.textContent = `${data.total_workers ?? cachedWorkers.length} Active Workers`;
      }
      renderWorkerLeaderboard(cachedWorkers);
      return;
    }
  } catch (e) {
    console.debug('Worker leaderboard live fetch unavailable:', e);
  }

  cachedWorkers = [];
  if (countPill) {
    countPill.textContent = '0 Active Workers';
  }
  if (lBody) {
    renderEmptyLeaderboardState(lBody, 'Volunteer Worker Telemetry Unavailable');
  }
}

/**
 * Filter cached workers locally on keystrokes.
 */
export function filterWorkerLeaderboard() {
  const sInput = document.getElementById('worker-search-input');
  const fSelect = document.getElementById('worker-family-select');
  const q = (sInput ? sInput.value : currentSearchQuery).trim().toLowerCase();
  const fam = fSelect ? fSelect.value : currentFilterFamily;

  const filtered = cachedWorkers.filter((w) => {
    const alias = String(w.worker_alias || '').toLowerCase();
    const pub = String(w.worker_pubkey || '').toLowerCase();
    const modelFam = String(w.model_family || '').toLowerCase();
    const matchSearch = !q || alias.includes(q) || pub.includes(q);
    const matchFam = fam === 'all' || modelFam.includes(fam);
    return matchSearch && matchFam;
  });
  renderWorkerLeaderboard(filtered);
}

/**
 * Render worker leaderboard rows using safe DOM nodes and delegated click handlers.
 */
export function renderWorkerLeaderboard(workers) {
  const lBody = document.getElementById('worker-leaderboard-body');
  if (!lBody) return;

  if (!lBody.dataset.workerDelegated) {
    lBody.dataset.workerDelegated = '1';
    lBody.addEventListener('click', (event) => {
      const target = event.target.closest('[data-worker-pubkey]');
      if (!target) return;
      const pubkey = target.dataset.workerPubkey;
      if (pubkey) {
        event.stopPropagation();
        openWorkerDossier(pubkey);
      }
    });
  }

  if (!workers || workers.length === 0) {
    renderEmptyLeaderboardState(lBody);
    return;
  }

  const fragment = document.createDocumentFragment();
  workers.forEach((w, idx) => {
    const pubkey = String(w.worker_pubkey || '');
    const tr = el('tr', {
      style: 'cursor:pointer;',
      title: 'Click to inspect contributor dossier',
      'data-worker-pubkey': pubkey,
    });

    const rankTd = el('td', { style: 'text-align:center;' });
    rankTd.appendChild(el('b', { style: 'color:var(--accent-amber);' }, `#${idx + 1}`));
    tr.appendChild(rankTd);

    const idTd = el('td');
    idTd.appendChild(el('b', { style: 'color:#fff;' }, w.worker_alias || 'volunteer'));
    idTd.appendChild(document.createElement('br'));
    idTd.appendChild(
      el(
        'span',
        { style: 'font-family:var(--font-mono); font-size:0.75rem; color:var(--text-dim); word-break:break-all;' },
        pubkey.slice(0, 16)
      )
    );
    tr.appendChild(idTd);

    const famTd = el('td');
    famTd.appendChild(el('span', { className: 'ribbon-pill ready', style: 'font-size:0.72rem;' }, w.model_family || 'general'));
    famTd.appendChild(document.createElement('br'));
    famTd.appendChild(
      el(
        'span',
        {
          style: 'font-family:var(--font-mono); font-size:0.72rem; color:var(--text-muted); word-break:break-all;',
          title: w.model_slug || '',
        },
        w.model_slug || ''
      )
    );
    tr.appendChild(famTd);

    const qTd = el('td');
    const qVal = Number(w.quality_score || 0);
    qTd.appendChild(
      el('b', { style: 'color:var(--accent-green); font-family:var(--font-mono);' }, `${(qVal * 10).toFixed(1)} / 10`)
    );
    tr.appendChild(qTd);

    const bTd = el('td');
    bTd.appendChild(
      el('b', { style: 'color:var(--accent-cyan); font-family:var(--font-mono);' }, String(w.bounties_cleared ?? 0))
    );
    tr.appendChild(bTd);

    tr.appendChild(el('td', { style: 'font-family:var(--font-mono);' }, Number(w.tokens_donated || 0).toLocaleString()));
    tr.appendChild(
      el(
        'td',
        { style: 'font-family:var(--font-mono); color:var(--accent-green);' },
        `$${Number(w.tokens_saved_usd || 0).toFixed(4)}`
      )
    );

    const badgesTd = el('td');
    const badges = Array.isArray(w.badges) ? w.badges : [];
    if (badges.length === 0) {
      badgesTd.appendChild(el('span', { style: 'color:var(--text-dim); font-size:0.75rem;' }, 'None yet'));
    } else {
      badges.forEach((b) => {
        badgesTd.appendChild(
          el(
            'span',
            {
              title: `${b.name || 'Badge'}: ${b.description || ''}`,
              style: 'cursor:help; font-size:1.1rem; margin-right:2px;',
            },
            b.icon || '🏅'
          )
        );
      });
    }
    tr.appendChild(badgesTd);

    const actionTd = el('td', { style: 'text-align:center;' });
    actionTd.appendChild(
      el(
        'button',
        {
          type: 'button',
          className: 'btn-secondary',
          style: 'font-size:0.72rem; padding:0.2rem 0.5rem; color:var(--accent-cyan);',
          'data-worker-pubkey': pubkey,
        },
        'Dossier ↗'
      )
    );
    tr.appendChild(actionTd);
    fragment.appendChild(tr);
  });

  lBody.replaceChildren(fragment);
}

/**
 * Open Worker Dossier modal using strictly safe DOM rendering.
 */
export async function openWorkerDossier(pubkey) {
  const cleanPubkey = String(pubkey || '').trim();
  let modal = document.getElementById('worker-dossier-modal');
  if (!modal) {
    injectWorkerDossierModal(closeWorkerDossier, copyToClipboard);
    modal = document.getElementById('worker-dossier-modal');
  }

  modal.style.display = 'flex';
  const base = getApiBaseUrl();

  document.getElementById('wd-pubkey').textContent = cleanPubkey;
  document.getElementById('wd-alias').textContent = 'Loading';
  document.getElementById('wd-family').textContent = 'Loading';
  document.getElementById('wd-qscore').textContent = '--';
  document.getElementById('wd-bounties').textContent = '--';
  document.getElementById('wd-tokens').textContent = '--';
  document.getElementById('wd-savings').textContent = '--';

  const gallery = document.getElementById('wd-badges-gallery');
  if (gallery) {
    gallery.replaceChildren(el('p', { style: 'color:var(--text-dim);' }, 'Loading badges'));
  }
  const aCountInit = document.getElementById('wd-audits-count');
  if (aCountInit) aCountInit.textContent = 'Loading';

  const aBody = document.getElementById('wd-audits-body');
  if (aBody) {
    const tr = el('tr');
    tr.appendChild(el('td', { colspan: '5', style: 'text-align:center; color:var(--text-dim);' }, 'Loading audit history'));
    aBody.replaceChildren(tr);
  }

  const encodedPub = encodeURIComponent(cleanPubkey);
  const badgeOrigin = base || window.location.origin;
  const badgeUrl = `${badgeOrigin}/api/badge/worker/${encodedPub}.svg`;
  const badgeImg = document.getElementById('wd-badge-img');
  if (badgeImg) badgeImg.src = badgeUrl;

  const mdSnippet = `[![Credence Worker](${badgeUrl})](https://credence.nexus/#worker/${encodedPub})`;
  const snippetInput = document.getElementById('wd-embed-snippet');
  if (snippetInput) snippetInput.value = mdSnippet;

  try {
    const res = await fetch(`${base}/api/worker/${encodedPub}`);
    if (!res.ok) {
      document.getElementById('wd-alias').textContent = 'Worker Not Found';
      return;
    }
    const data = await res.json();
    document.getElementById('wd-alias').textContent = data.worker_alias || 'Volunteer Contributor';
    document.getElementById('wd-family').textContent = `${data.model_family || 'general'} (${data.model_slug || ''})`;
    document.getElementById('wd-qscore').textContent = `${(Number(data.quality_score || 0) * 10).toFixed(1)} / 10`;
    document.getElementById('wd-bounties').textContent = String(data.bounties_cleared ?? 0);
    document.getElementById('wd-tokens').textContent = Number(data.tokens_donated || 0).toLocaleString();
    document.getElementById('wd-savings').textContent = `$${Number(data.tokens_saved_usd || 0).toFixed(4)}`;

    if (gallery) {
      const badges = Array.isArray(data.badges) ? data.badges : [];
      if (badges.length === 0) {
        gallery.replaceChildren(
          el('p', { style: 'color:var(--text-dim); font-size:0.85rem;' }, 'No achievement badges unlocked yet. Keep fulfilling bounties!')
        );
      } else {
        const frag = document.createDocumentFragment();
        badges.forEach((b) => {
          const card = el('div', {
            style:
              'background:var(--bg-card); border:1px solid var(--border); border-radius:6px; ' +
              'padding:0.65rem 0.85rem; display:flex; align-items:center; gap:0.6rem;',
          });
          card.appendChild(el('span', { style: 'font-size:1.6rem;' }, b.icon || '🏅'));
          const info = el('div');
          info.appendChild(el('b', { style: 'color:#fff; font-size:0.85rem;' }, b.name || 'Badge'));
          info.appendChild(el('p', { style: 'color:var(--text-dim); font-size:0.75rem; margin:0;' }, b.description || ''));
          card.appendChild(info);
          frag.appendChild(card);
        });
        gallery.replaceChildren(frag);
      }
    }

    const audits = Array.isArray(data.recent_audits) ? data.recent_audits : [];
    const aCount = document.getElementById('wd-audits-count');
    if (aCount) {
      aCount.textContent = `Showing ${audits.length} of ${data.bounties_cleared || audits.length} completed bounties`;
    }
    if (aBody) {
      if (audits.length === 0) {
        const tr = el('tr');
        tr.appendChild(
          el('td', { colspan: '5', style: 'text-align:center; color:var(--text-dim); padding:1rem;' }, 'No verified mempool audits recorded yet.')
        );
        aBody.replaceChildren(tr);
      } else {
        const frag = document.createDocumentFragment();
        audits.forEach((a) => {
          const tr = el('tr');
          const ts = String(a.audited_at || '').slice(0, 19).replace('T', ' ');
          tr.appendChild(el('td', { style: 'font-size:0.78rem; font-family:var(--font-mono);' }, ts));

          const urlTd = el('td', { style: 'max-width:240px; word-break:break-all;' });
          const safeHref = safeHttpUrl(a.url);
          if (safeHref) {
            urlTd.appendChild(
              el(
                'a',
                { href: safeHref, target: '_blank', rel: 'noopener noreferrer', style: 'color:var(--accent-cyan); text-decoration:none;' },
                a.url
              )
            );
          } else {
            urlTd.appendChild(el('span', { style: 'color:var(--text-muted);' }, String(a.url || 'unknown')));
          }
          tr.appendChild(urlTd);

          const score = Number(a.suspicion_score || 0);
          const scoreTd = el('td');
          scoreTd.appendChild(
            el(
              'b',
              { style: `font-family:var(--font-mono); color:${score > 50 ? 'var(--accent-red)' : 'var(--accent-green)'};` },
              score.toFixed(1)
            )
          );
          tr.appendChild(scoreTd);

          const verdictTd = el('td');
          verdictTd.appendChild(el('span', { className: 'ribbon-pill ready', style: 'font-size:0.7rem;' }, a.classification || 'CLEAN'));
          tr.appendChild(verdictTd);

          const sigText = a.node_signature ? String(a.node_signature).slice(0, 16) : '--';
          tr.appendChild(el('td', { style: 'font-family:var(--font-mono); font-size:0.72rem; color:var(--text-dim);' }, sigText));
          frag.appendChild(tr);
        });
        aBody.replaceChildren(frag);
      }
    }
  } catch (err) {
    console.debug('Worker dossier fetch failed:', err);
  }
}

export function closeWorkerDossier() {
  const modal = document.getElementById('worker-dossier-modal');
  if (modal) modal.style.display = 'none';
}

export function openWorkerStartModal() {
  let modal = document.getElementById('worker-start-modal');
  if (!modal) {
    injectWorkerStartModal(closeWorkerStartModal);
    modal = document.getElementById('worker-start-modal');
  }
  modal.style.display = 'flex';
}

export function closeWorkerStartModal() {
  const modal = document.getElementById('worker-start-modal');
  if (modal) modal.style.display = 'none';
}

export function copyToClipboard(text, label = 'Copied to clipboard!') {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => showToast(label, 'success'));
  }
}

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
