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

      // 2. Map Hostname to Static Web Directory
      let assetPath = url.pathname;
      if (host.includes('nexus')) {
        assetPath = `/credence.nexus${url.pathname === '/' ? '/index.html' : url.pathname}`;
      } else if (host.includes('foundation')) {
        if (host.startsWith('keys')) {
          assetPath = `/credence.foundation/keys${url.pathname === '/' ? '/root.pub' : url.pathname}`;
        } else {
          assetPath = `/credence.foundation${url.pathname === '/' ? '/index.html' : url.pathname}`;
        }
      } else if (host.includes('report')) {
        assetPath = `/credence.report${url.pathname === '/' ? '/index.html' : url.pathname}`;
      } else {
        // credence.run
        assetPath = `/credence.run${url.pathname === '/' ? '/index.html' : url.pathname}`;
      }

      const assetUrl = new URL(assetPath, request.url);
      let response;

      if (env && env.ASSETS) {
        response = await env.ASSETS.fetch(new Request(assetUrl, request));
      } else {
        response = await fetch(new Request(assetUrl, request));
      }

      // Attach CORS headers for JSON seed files, taxonomy definitions, and public keys
      if (url.pathname.endsWith('.json') || url.pathname.endsWith('.pub') || url.pathname.endsWith('.yaml') || url.pathname.endsWith('.sh')) {
        const corsHeaders = new Headers(response.headers);
        corsHeaders.set('Access-Control-Allow-Origin', '*');
        corsHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
        return new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: corsHeaders,
        });
      }

      return response;
    } catch (err) {
      return new Response(`Credence Edge Error: ${err.message}\n${err.stack}`, {
        status: 500,
        headers: { 'Content-Type': 'text/plain' },
      });
    }
  }
};
