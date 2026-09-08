/**
 * Credence Workstation Navigation & TUI Helpers
 * Zero-npm native ES module.
 */

// TUI HUD MODE TOGGLE
// -----------------------------------------------------------------------------

export function toggleTuiMode() {
  // Theme toggle removed by design
}

export function initTuiMode() {
  document.body.classList.remove('tui-mode');
  localStorage.removeItem('credence_tui_mode');
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
      'https://admin.credence.run': 'https://dev.credence.run/admin/',
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
      'https://dev.credence.run/admin': '/admin.credence.run/',
      'https://dev.credence.run/admin/': '/admin.credence.run/',
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

