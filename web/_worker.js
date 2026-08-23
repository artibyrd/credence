/**
 * Credence Multi-Domain Zero-Build Edge Router
 * Supports Canonical (credence.run, admin.credence.run, credence.nexus, credence.foundation, credence.report)
 * and Dev Subdomains (dev.credence.run, dev.admin.credence.run, dev.credence.nexus, dev.credence.foundation, dev.credence.report)
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

      // 2. Dynamic Zero-Cache Docs & Blog Proxy (docs.credence.run, blog.credence.run, or /docs & /blog on dev)
      const isDocsOrBlogDomain =
        host === 'docs.credence.run' ||
        host === 'dev.docs.credence.run' ||
        host === 'blog.credence.run' ||
        host === 'dev.blog.credence.run';

      if (
        isDocsOrBlogDomain ||
        (isDev && (url.pathname === '/docs' || url.pathname.startsWith('/docs/') || url.pathname === '/blog' || url.pathname.startsWith('/blog/')))
      ) {
        let subPath = url.pathname;
        if (!isDocsOrBlogDomain) {
          if (subPath === '/docs' || subPath === '/blog') {
            return Response.redirect(`${url.origin}${subPath}/`, 301);
          }
          if (subPath === '/docs/' || subPath === '/blog/') {
            subPath = '/';
          } else if (subPath.startsWith('/docs/')) {
            subPath = subPath.substring(5);
          } else if (subPath.startsWith('/blog/')) {
            subPath = subPath.substring(5);
          }
        }
        if (!subPath || subPath === '') {
          subPath = '/';
        }
        const targetPagesDomain = isDev ? 'dev.credence-docs.pages.dev' : 'credence-docs.pages.dev';
        const pagesUrl = new URL(subPath + url.search, `https://${targetPagesDomain}`);
        const reqHeaders = new Headers(request.headers);
        reqHeaders.set('Host', targetPagesDomain);
        
        const res = await fetch(pagesUrl, {
          method: request.method,
          headers: reqHeaders,
          body: ['GET', 'HEAD'].includes(request.method) ? null : request.body,
        });

        const resHeaders = new Headers(res.headers);
        resHeaders.set('Cache-Control', 'no-cache, no-store, must-revalidate');
        resHeaders.set('Access-Control-Allow-Origin', '*');
        
        return new Response(res.body, {
          status: res.status,
          statusText: res.statusText,
          headers: resHeaders,
        });
      }

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

      // 4. Resolve Domain-Specific Asset Prefix (stripping dev. prefix for asset mapping)
      const cleanHost = host.replace(/^dev\./, '');
      let prefix = 'credence.run';
      if (cleanHost.startsWith('admin')) {
        prefix = 'admin.credence.run';
      } else if (cleanHost.includes('nexus')) {
        prefix = 'credence.nexus';
      } else if (cleanHost.includes('foundation')) {
        prefix = cleanHost.startsWith('keys') ? 'credence.foundation/keys' : 'credence.foundation';
      } else if (cleanHost.includes('report')) {
        prefix = 'credence.report';
      }

      let reqPath = url.pathname;
      if (reqPath === '' || reqPath === '/') {
        reqPath = '/index.html';
      }

      // If keys.credence.foundation root requested, serve root.pub
      if (cleanHost.startsWith('keys') && (reqPath === '/' || reqPath === '/index.html')) {
        reqPath = '/root.pub';
      }

      // If seeds.credence.nexus root requested, serve peers.json
      if (cleanHost.startsWith('seeds') && (reqPath === '/' || reqPath === '/index.html')) {
        reqPath = '/peers.json';
      }

      // Build target asset path
      let finalPath;
      if (reqPath.startsWith('/assets/')) {
        finalPath = reqPath;
      } else if (reqPath === '/' || reqPath === '' || reqPath === '/index.html') {
        finalPath = `/${prefix}/index.html`;
      } else if (reqPath.endsWith('/')) {
        finalPath = `/${prefix}${reqPath}index.html`;
      } else {
        finalPath = `/${prefix}${reqPath}`;
      }

      const assetUrl = new URL(finalPath, request.url);
      let response;

      if (env && env.ASSETS) {
        response = await env.ASSETS.fetch(new Request(assetUrl));
        // Fallback 1: try root path if domain-prefixed path returned 404
        if (response.status === 404 && finalPath !== reqPath) {
          const rootAssetUrl = new URL(reqPath, request.url);
          const rootResponse = await env.ASSETS.fetch(new Request(rootAssetUrl));
          if (rootResponse.status < 400) {
            response = rootResponse;
          }
        }
        // Fallback 2: try .html if extensionless path returns 404
        if (response.status === 404 && !reqPath.includes('.')) {
          const htmlAssetUrl = new URL(finalPath + '.html', request.url);
          const htmlResponse = await env.ASSETS.fetch(new Request(htmlAssetUrl));
          if (htmlResponse.status < 400) {
            response = htmlResponse;
          }
        }
      } else {
        response = await fetch(new Request(new URL(finalPath, request.url)));
      }

      // If exact file found, return with appropriate CORS & Zero-Cache Policy
      const resHeaders = new Headers(response.headers);
      if (url.pathname.endsWith('.json') || url.pathname.endsWith('.pub') || url.pathname.endsWith('.yaml') || url.pathname.endsWith('.sh') || url.pathname.endsWith('.html') || url.pathname.endsWith('.css') || url.pathname.endsWith('.js') || reqPath === '/index.html') {
        resHeaders.set('Access-Control-Allow-Origin', '*');
        resHeaders.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
        resHeaders.set('Cache-Control', 'public, max-age=0, must-revalidate');
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
