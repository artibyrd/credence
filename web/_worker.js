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

      // 2. REST API Gateway & Health Check Proxy -> Google Cloud Run
      if (url.pathname.startsWith('/api/') || url.pathname === '/health') {
        const backendUrl = new URL(url.pathname + url.search, 'https://credence-server-663899237633.us-central1.run.app');
        const newHeaders = new Headers(request.headers);
        newHeaders.set('Host', 'credence-server-663899237633.us-central1.run.app');

        const res = await fetch(backendUrl, {
          method: request.method,
          headers: newHeaders,
          body: ['GET', 'HEAD'].includes(request.method) ? null : request.body,
          redirect: 'follow',
        });

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

      // 3. Canonical URL redirect: if browser visits with subdirectory prefix, 301 redirect to clean root
      const dirPrefixes = ['/credence.run', '/credence.nexus', '/credence.foundation', '/credence.report'];
      for (const dp of dirPrefixes) {
        if (url.pathname === dp || url.pathname.startsWith(dp + '/')) {
          const cleanPath = url.pathname.slice(dp.length) || '/';
          return Response.redirect(new URL(cleanPath + url.search, request.url), 301);
        }
      }

      // 3. Resolve Domain-Specific Asset Prefix
      let prefix = 'credence.run';
      if (host.includes('nexus')) {
        prefix = 'credence.nexus';
      } else if (host.includes('foundation')) {
        prefix = host.startsWith('keys') ? 'credence.foundation/keys' : 'credence.foundation';
      } else if (host.includes('report')) {
        prefix = 'credence.report';
      }

      let reqPath = url.pathname;
      if (reqPath === '' || reqPath === '/') {
        reqPath = '/';
      }

      // If keys.credence.foundation root requested, serve root.pub
      if (host.startsWith('keys') && (reqPath === '/' || reqPath === '/index.html')) {
        reqPath = '/root.pub';
      }

      // Build target asset path
      let finalPath;
      if (reqPath === '/') {
        finalPath = `/${prefix}/`;
      } else {
        finalPath = `/${prefix}${reqPath}`;
      }

      const assetUrl = new URL(finalPath, request.url);
      let response;

      if (env && env.ASSETS) {
        response = await env.ASSETS.fetch(new Request(assetUrl, request));
        // If Cloudflare returns a redirect for internal folder, follow it internally to hide redirect from browser
        if (response.status >= 300 && response.status < 400 && response.headers.has('Location')) {
          const loc = response.headers.get('Location');
          const targetUrl = new URL(loc, request.url);
          response = await env.ASSETS.fetch(new Request(targetUrl, request));
        }
        // Clean URL fallback: try .html if extensionless path returns 404
        if (response.status === 404 && !reqPath.includes('.')) {
          const htmlAssetUrl = new URL(finalPath + '.html', request.url);
          const htmlResponse = await env.ASSETS.fetch(new Request(htmlAssetUrl, request));
          if (htmlResponse.status < 400) {
            response = htmlResponse;
          }
        }
      } else {
        response = await fetch(new Request(assetUrl, request));
      }

      // If exact file found, return with appropriate CORS
      const resHeaders = new Headers(response.headers);
      if (url.pathname.endsWith('.json') || url.pathname.endsWith('.pub') || url.pathname.endsWith('.yaml') || url.pathname.endsWith('.sh') || url.pathname.endsWith('.html') || url.pathname.endsWith('.css')) {
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
