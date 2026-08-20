/**
 * Credence Multi-Domain Zero-Build Edge Router
 * Supports Canonical (credence.run, credence.nexus, credence.foundation, credence.report)
 * and Dev Subdomains (dev.credence.run, dev.credence.nexus, dev.credence.foundation, dev.credence.report)
 */

export default {
  async fetch(request, env, ctx) {
    try {
      const url = new URL(request.url);
      const host = url.hostname;
      const isDev = host.startsWith('dev.') || host.startsWith('mcp.dev.');

      // 1. Resolve Target Cloud Run Compute Backend
      const devBackend = (env && env.DEV_BACKEND_URL) || 'https://credence-dev-wukzqiyqbq-uc.a.run.app';
      const prodBackend = (env && (env.PROD_BACKEND_URL || env.BACKEND_URL)) || 'https://credence-server-psgqr4nwoq-uc.a.run.app';
      const targetBackend = isDev ? devBackend : prodBackend;
      const targetBackendHost = new URL(targetBackend).hostname;

      // 2. FastMCP SSE & Tool Proxy (mcp.credence.run & mcp.dev.credence.run)
      if (host === 'mcp.credence.run' || host === 'mcp.dev.credence.run') {
        const backendUrl = new URL(url.pathname + url.search, targetBackend);
        const newHeaders = new Headers(request.headers);
        newHeaders.set('Host', targetBackendHost);
        
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

      // 3. REST API Gateway & Health Check Proxy -> Target Compute Backend
      if (url.pathname.startsWith('/api/') || url.pathname === '/health') {
        const backendUrl = new URL(url.pathname + url.search, targetBackend);
        const newHeaders = new Headers(request.headers);
        newHeaders.set('Host', targetBackendHost);

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

        // Environment-aware cache headers for audit reports
        if (url.pathname.startsWith('/api/reports/')) {
          if (isDev) {
            resHeaders.set('Cache-Control', 'private, max-age=60');
          } else {
            resHeaders.set('Cache-Control', 'public, max-age=2592000, immutable');
          }
        }

        return new Response(res.body, {
          status: res.status,
          statusText: res.statusText,
          headers: resHeaders,
        });
      }

      // 4. Canonical URL redirect: if browser visits with subdirectory prefix, 301 redirect to clean root
      const dirPrefixes = ['/credence.run', '/credence.nexus', '/credence.foundation', '/credence.report'];
      for (const dp of dirPrefixes) {
        if (url.pathname === dp || url.pathname.startsWith(dp + '/')) {
          const cleanPath = url.pathname.slice(dp.length) || '/';
          return Response.redirect(new URL(cleanPath + url.search, request.url), 301);
        }
      }

      // 5. Resolve Domain-Specific Asset Prefix (stripping dev. prefix for asset mapping)
      const cleanHost = host.replace(/^dev\./, '');
      let prefix = 'credence.run';
      if (cleanHost.includes('nexus')) {
        prefix = 'credence.nexus';
      } else if (cleanHost.includes('foundation')) {
        prefix = cleanHost.startsWith('keys') ? 'credence.foundation/keys' : 'credence.foundation';
      } else if (cleanHost.includes('report')) {
        prefix = 'credence.report';
      }

      let reqPath = url.pathname;
      if (reqPath === '' || reqPath === '/') {
        reqPath = '/';
      }

      // If keys.credence.foundation root requested, serve root.pub
      if (cleanHost.startsWith('keys') && (reqPath === '/' || reqPath === '/index.html')) {
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
