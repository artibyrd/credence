/**
 * Credence Multi-Domain Zero-Build Edge Router
 * Handles all 4 domains: credence.run, mcp.credence.run, credence.nexus, credence.foundation, credence.report
 */

export default {
  async fetch(request, env, ctx) {
    try {
      const url = new URL(request.url);
      const host = url.hostname;

      // 1. FastMCP SSE & Tool Proxy for mcp.credence.run -> Google Cloud Run
      if (host === 'mcp.credence.run') {
        const backendUrl = new URL(url.pathname + url.search, 'https://credence-server-663899237633.us-central1.run.app');
        const newHeaders = new Headers(request.headers);
        newHeaders.set('Host', 'credence-server-663899237633.us-central1.run.app');
        
        const res = await fetch(backendUrl, {
          method: request.method,
          headers: newHeaders,
          body: ['GET', 'HEAD'].includes(request.method) ? null : request.body,
          redirect: 'follow',
        });

        // Preserve SSE streaming headers without buffering
        const resHeaders = new Headers(res.headers);
        resHeaders.set('Access-Control-Allow-Origin', '*');
        resHeaders.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
        resHeaders.set('Access-Control-Allow-Headers', '*');
        
        return new Response(res.body, {
          status: res.status,
          statusText: res.statusText,
          headers: resHeaders,
        });
      }

      // Handle CORS preflight
      if (request.method === 'OPTIONS') {
        return new Response(null, {
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': '*',
          }
        });
      }

      // 2. Normalize and Map Hostname to Static Asset Path
      let path = url.pathname;
      if (path === '/' || path === '') {
        path = '/index.html';
      }

      let prefix = '/credence.run';
      if (host.includes('nexus')) {
        prefix = '/credence.nexus';
      } else if (host.includes('foundation')) {
        if (host.startsWith('keys')) {
          prefix = '/credence.foundation/keys';
          if (path === '/index.html') path = '/root.pub';
        } else {
          prefix = '/credence.foundation';
        }
      } else if (host.includes('report')) {
        prefix = '/credence.report';
      }

      const assetUrl = new URL(prefix + path, request.url);
      let response;

      if (env && env.ASSETS) {
        response = await env.ASSETS.fetch(new Request(assetUrl, request));
      } else {
        response = await fetch(new Request(assetUrl, request));
      }

      // If exact file found, return with appropriate CORS
      const resHeaders = new Headers(response.headers);
      if (path.endsWith('.json') || path.endsWith('.pub') || path.endsWith('.yaml') || path.endsWith('.sh') || path.endsWith('.html') || path.endsWith('.css')) {
        resHeaders.set('Access-Control-Allow-Origin', '*');
        resHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
      }

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: resHeaders,
      });
    } catch (err) {
      return new Response(`Credence Edge Error: ${err.message}\n${err.stack}`, {
        status: 500,
        headers: { 'Content-Type': 'text/plain' },
      });
    }
  }
};
