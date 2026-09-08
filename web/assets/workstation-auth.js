/**
 * Credence Workstation Operator Authentication & Session Management
 * Zero-npm native ES module.
 */

import { showToast, openOperatorModal, closeOperatorModal } from './workstation-modals.js';

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

