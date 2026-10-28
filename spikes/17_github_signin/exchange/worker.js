// Token exchange for "Sign in with GitHub" on funground Play (spike S-238, option b of D-118).
//
// A Cloudflare Worker. It does three jobs and nothing else:
//   POST /token    { code, redirect_uri, code_verifier }  ->  GitHub: code for a user token
//   POST /refresh  { refresh_token }                      ->  GitHub: a new user token (the old pair stops working)
//   POST /revoke   { access_token }                       ->  GitHub: delete the token (sign out for real)
//
// Why it exists: GitHub's token endpoints do not answer browsers (no CORS), and GitHub still wants the app's
// client secret for the exchange and for refreshing, even with PKCE. A web page cannot hold a secret.
//
// Settings (Cloudflare dashboard > Worker > Settings > Variables and Secrets):
//   CLIENT_ID      plain variable   the GitHub App's client ID (not secret)
//   CLIENT_SECRET  SECRET           the GitHub App's client secret (use "Encrypt"; or `wrangler secret put CLIENT_SECRET`)
//
// The worker keeps nothing: no storage, no logs of requests, no copy of any token. It never calls
// console.log. Turn "Workers Logs" off for this Worker so that nothing is kept by the platform either.

const GITHUB = "https://github.com";
const API = "https://api.github.com";

// Only these pages may call the worker. Add the exact origin of your test server when testing.
const ALLOWED_ORIGINS = new Set([
  "https://funground-hq.github.io",
  "http://localhost:8000",
  "http://localhost:8080",
  "http://127.0.0.1:8000",
  "http://127.0.0.1:8080",
]);

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin");
    // A browser always sends Origin on a cross-origin POST. No Origin, or a stranger's: refuse.
    if (!origin || !ALLOWED_ORIGINS.has(origin)) return new Response("Forbidden", { status: 403 });

    const cors = {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Max-Age": "86400",
      "Vary": "Origin",
    };
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method !== "POST") return reply({ error: "POST only" }, 405, cors);

    let body;
    try {
      body = await request.json();
    } catch {
      return reply({ error: "bad request" }, 400, cors);
    }

    const path = new URL(request.url).pathname;
    if (path === "/token") {
      if (!body.code || !body.redirect_uri) return reply({ error: "bad request" }, 400, cors);
      return viaGithub(env, cors, {
        code: body.code,
        redirect_uri: body.redirect_uri,
        ...(body.code_verifier ? { code_verifier: body.code_verifier } : {}),   // absent after "install + authorize"
      });
    }
    if (path === "/refresh") {
      if (!body.refresh_token) return reply({ error: "bad request" }, 400, cors);
      return viaGithub(env, cors, { grant_type: "refresh_token", refresh_token: body.refresh_token });
    }
    if (path === "/revoke") {
      if (!body.access_token) return reply({ error: "bad request" }, 400, cors);
      const basic = btoa(`${env.CLIENT_ID}:${env.CLIENT_SECRET}`);
      const gone = await fetch(`${API}/applications/${env.CLIENT_ID}/token`, {
        method: "DELETE",
        headers: {
          Authorization: `Basic ${basic}`,
          Accept: "application/vnd.github+json",
          "Content-Type": "application/json",
          "User-Agent": "funground-token-exchange",
        },
        body: JSON.stringify({ access_token: body.access_token }),
      });
      return reply({ revoked: gone.status === 204 }, gone.status === 204 ? 200 : 502, cors);
    }
    return reply({ error: "not found" }, 404, cors);
  },
};

// Adds the app's id and secret, asks GitHub, and hands back only the fields the page needs.
async function viaGithub(env, cors, fields) {
  const response = await fetch(`${GITHUB}/login/oauth/access_token`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json", "User-Agent": "funground-token-exchange" },
    body: JSON.stringify({ client_id: env.CLIENT_ID, client_secret: env.CLIENT_SECRET, ...fields }),
  });
  const data = await response.json().catch(() => ({}));
  if (!data.access_token) {
    // GitHub answers 200 with { error, error_description } for a bad code. Pass the reason on, nothing else.
    return reply({ error: data.error || "exchange failed" }, 400, cors);
  }
  return reply(
    {
      access_token: data.access_token,
      expires_in: data.expires_in,
      refresh_token: data.refresh_token,
      refresh_token_expires_in: data.refresh_token_expires_in,
    },
    200,
    cors,
  );
}

function reply(object, status, cors) {
  return new Response(JSON.stringify(object), {
    status,
    headers: { ...cors, "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
