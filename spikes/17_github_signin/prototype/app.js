// Sketchbook sign-in spike (S-238). Plain JavaScript, no libraries.
// Option a: a pasted fine-grained token.   Option b: GitHub App sign-in through the exchange service.
// Serve this folder from a local static server, for example: python -m http.server 8080  (from the prototype folder),
// then open http://localhost:8080/ . The App's callback URL must be exactly that address (see research.md).

const CONFIG = {
  // Fill these in after the maintainer has made the App and the Worker. Empty values switch option b off.
  CLIENT_ID: "",                                   // the GitHub App's client ID (public)
  APP_SLUG: "",                                    // the App's URL name: github.com/apps/<slug>
  EXCHANGE_URL: "",                                // e.g. "https://funground-token.<account>.workers.dev"
  SKETCH_DIR: "sketches",                          // the sketchbook template's folder
};

const API = "https://api.github.com";
const KEY = "fg-spike-auth";                       // sessionStorage: { token, refresh, expires, kind }
const PENDING = "fg-spike-pending";                // sessionStorage: { state, verifier } during the redirect

const $ = (id) => document.getElementById(id);
let auth = null;                                   // { token, refresh, expires, kind: "pat" | "app" }
let current = null;                                // { path, sha, text } as opened (text = what we loaded)

// ---- small helpers -------------------------------------------------------------------------------------------

function say(text, bad = false) {
  const p = $("status");
  p.textContent = text;
  p.className = bad ? "bad" : "ok";
}

// The log shows every request: where it went. The token itself is never printed.
function log(line) {
  const box = $("log");
  box.textContent += line + "\n";
  box.scrollTop = box.scrollHeight;
}

const toBase64 = (text) => {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
};
const fromBase64 = (b64) => {
  const binary = atob(b64.replace(/\n/g, ""));
  return new TextDecoder().decode(Uint8Array.from(binary, (c) => c.charCodeAt(0)));
};
const b64url = (bytes) =>
  btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const randomString = () => b64url(crypto.getRandomValues(new Uint8Array(32)));

// ---- keeping the token ---------------------------------------------------------------------------------------
// sessionStorage: this tab only, gone when the tab closes, and it survives the redirect to GitHub and back.
// Memory alone would lose the token on that redirect. Nothing goes in localStorage.

function keep() {
  try { sessionStorage.setItem(KEY, JSON.stringify(auth)); } catch { /* private window: memory only */ }
}
function forget() {
  auth = null;
  current = null;
  try { sessionStorage.removeItem(KEY); sessionStorage.removeItem(PENDING); } catch { /* nothing to remove */ }
}
function restore() {
  try { auth = JSON.parse(sessionStorage.getItem(KEY)); } catch { auth = null; }
}

// ---- talking to GitHub ---------------------------------------------------------------------------------------

async function github(method, path, body) {
  await refreshIfDue();
  const response = await send(method, path, body);
  if (response.status === 401 && auth?.refresh && (await refresh())) return send(method, path, body);
  return response;
}

async function send(method, path, body) {
  log(`${method} ${API}${path}  (token sent to api.github.com only)`);
  return fetch(API + path, {
    method,
    cache: "no-store",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${auth.token}`,
      "X-GitHub-Api-Version": "2022-11-28",
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}

// ---- option b: sign in through the exchange service ----------------------------------------------------------

const redirectUri = () => location.origin + location.pathname;
const optionBReady = () => CONFIG.CLIENT_ID && CONFIG.EXCHANGE_URL;

async function startSignIn() {
  if (!optionBReady()) return say("Option b is not set up: fill in CONFIG in app.js.", true);
  const state = randomString();
  const verifier = randomString();
  const challenge = b64url(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier))));
  sessionStorage.setItem(PENDING, JSON.stringify({ state, verifier }));
  const url = new URL("https://github.com/login/oauth/authorize");
  url.search = new URLSearchParams({
    client_id: CONFIG.CLIENT_ID,
    redirect_uri: redirectUri(),
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });
  location.assign(url);
}

// Installing the App on a repository (the learner picks which). GitHub then returns here with a code too,
// when "Request user authorization (OAuth) during installation" is on. That return carries no state, so
// it is accepted only if we started the install from this tab.
function startInstall() {
  sessionStorage.setItem(PENDING, JSON.stringify({ state: null, verifier: null }));
  if (!CONFIG.APP_SLUG) return say("Option b is not set up: fill in CONFIG in app.js.", true);
  location.assign(`https://github.com/apps/${CONFIG.APP_SLUG}/installations/new`);
}

// Called on load: if the address carries ?code=..., trade it for a token through the exchange service.
async function finishSignIn() {
  const params = new URLSearchParams(location.search);
  const code = params.get("code");
  if (!code) return;
  history.replaceState(null, "", location.pathname);       // take the code out of the address bar at once
  let pending = null;
  try { pending = JSON.parse(sessionStorage.getItem(PENDING)); } catch { /* none */ }
  sessionStorage.removeItem(PENDING);
  // Sign-in from the authorize link must return our random state. A return from the install page has none.
  if (pending?.state && params.get("state") !== pending.state) {
    return say("Sign-in was refused: the answer did not match the request.", true);
  }
  if (!pending) return say("Start the sign-in from this page, then try again.", true);
  log(`POST ${CONFIG.EXCHANGE_URL}/token  (the code and PKCE verifier go to the exchange service)`);
  const response = await fetch(CONFIG.EXCHANGE_URL + "/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, redirect_uri: redirectUri(), ...(pending.verifier ? { code_verifier: pending.verifier } : {}) }),
  });
  const data = await response.json().catch(() => ({}));
  if (!data.access_token) return say("GitHub did not give a token: " + (data.error || response.status), true);
  setAuth(data);
}

function setAuth(data) {
  auth = {
    kind: "app",
    token: data.access_token,
    refresh: data.refresh_token || null,
    expires: data.expires_in ? Date.now() + (data.expires_in - 60) * 1000 : null,
  };
  keep();
}

async function refreshIfDue() {
  if (auth?.kind === "app" && auth.expires && Date.now() > auth.expires) await refresh();
}

// A refresh token works once: the answer replaces both tokens.
async function refresh() {
  if (!auth?.refresh || !CONFIG.EXCHANGE_URL) return false;
  log(`POST ${CONFIG.EXCHANGE_URL}/refresh  (the refresh token goes to the exchange service)`);
  const response = await fetch(CONFIG.EXCHANGE_URL + "/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: auth.refresh }),
  });
  const data = await response.json().catch(() => ({}));
  if (!data.access_token) { forget(); showSignedOut(); say("Please sign in again.", true); return false; }
  setAuth(data);
  return true;
}

// ---- option a: a pasted token --------------------------------------------------------------------------------

function usePat() {
  const token = $("pat").value.trim();
  $("pat").value = "";
  if (!token) return say("Paste a token first.", true);
  auth = { kind: "pat", token, refresh: null, expires: null };
  keep();
  enter();
}

// ---- the sketchbook ------------------------------------------------------------------------------------------

async function enter() {
  const me = await github("GET", "/user");
  if (!me.ok) { forget(); showSignedOut(); return say("GitHub did not accept the token (" + me.status + ").", true); }
  $("who").textContent = (await me.json()).login;
  $("signedOut").classList.add("hidden");
  $("signedIn").classList.remove("hidden");
  say("Signed in.");
  if (auth.kind === "app") await listInstalledRepos();
}

function showSignedOut() {
  $("signedOut").classList.remove("hidden");
  $("signedIn").classList.add("hidden");
  $("editor").value = "";
  $("files").replaceChildren();
  $("conflict").classList.add("hidden");
}

// The repositories the learner gave the App. (A fine-grained token has no such list: type the name.)
async function listInstalledRepos() {
  const installs = await github("GET", "/user/installations");
  if (!installs.ok) return;
  const list = $("repos");
  list.replaceChildren();
  for (const install of (await installs.json()).installations) {
    const repos = await github("GET", `/user/installations/${install.id}/repositories`);
    if (!repos.ok) continue;
    for (const repo of (await repos.json()).repositories) {
      const option = document.createElement("option");
      option.value = repo.full_name;
      list.append(option);
    }
  }
  if (list.firstChild && !$("repo").value) $("repo").value = list.firstChild.value;
}

const repoPath = () => {
  const name = $("repo").value.trim();
  if (!/^[\w.-]+\/[\w.-]+$/.test(name)) { say("Write the repository as owner/name.", true); return null; }
  return `/repos/${name}/contents`;
};
// Encode each part of a path but keep the slashes.
const encodePath = (path) => path.split("/").map(encodeURIComponent).join("/");

async function listSketches() {
  const base = repoPath();
  if (!base) return;
  const response = await github("GET", `${base}/${CONFIG.SKETCH_DIR}`);
  if (!response.ok) return say(`Could not list ${CONFIG.SKETCH_DIR}/ (${response.status}). Is the App installed on this repository?`, true);
  const select = $("files");
  select.replaceChildren();
  for (const item of await response.json()) {
    if (item.type !== "file" || !item.name.endsWith(".py")) continue;
    const option = document.createElement("option");
    option.value = item.path;
    option.textContent = item.name;
    select.append(option);
  }
  say(`${select.options.length} sketches.`);
}

async function openSketch() {
  const base = repoPath();
  const path = $("files").value;
  if (!base || !path) return say("Choose a sketch first.", true);
  const response = await github("GET", `${base}/${encodePath(path)}`);
  if (!response.ok) return say("Could not open it (" + response.status + ").", true);
  const file = await response.json();
  const text = fromBase64(file.content);
  current = { path, sha: file.sha, text };
  $("editor").value = text;
  $("conflict").classList.add("hidden");
  say("Opened " + path);
}

// Save. First look at the file as it is on GitHub now. If its sha is not the one we opened, show their version
// and write nothing. If GitHub itself says 409 or 422 (changed between our look and our write), do the same.
async function save(overwrite = false) {
  const base = repoPath();
  if (!base || !current) return say("Open or create a sketch first.", true);
  const url = `${base}/${encodePath(current.path)}`;
  const now = await github("GET", url);
  let sha = current.sha;
  if (now.ok) {
    const remote = await now.json();
    if (remote.sha !== current.sha && !overwrite) return showConflict(fromBase64(remote.content), remote.sha);
    sha = remote.sha;
  } else if (now.status !== 404) {
    return say("Could not check the file (" + now.status + ").", true);
  }
  const put = await github("PUT", url, {
    message: $("message").value || "Update from Play (spike)",
    content: toBase64($("editor").value),
    ...(now.ok ? { sha } : {}),
  });
  if (put.status === 409 || put.status === 422) {
    const again = await github("GET", url);
    if (again.ok) { const remote = await again.json(); return showConflict(fromBase64(remote.content), remote.sha); }
  }
  if (!put.ok) return say("Save failed (" + put.status + ").", true);
  const result = await put.json();
  current = { path: current.path, sha: result.content.sha, text: $("editor").value };
  $("conflict").classList.add("hidden");
  say("Saved as commit " + result.commit.sha.slice(0, 7));
}

function showConflict(theirText, theirSha) {
  $("theirs").value = theirText;
  $("conflict").dataset.sha = theirSha;
  $("conflict").classList.remove("hidden");
  say("Not saved: the file changed on GitHub.", true);
}

async function newSketch() {
  const base = repoPath();
  if (!base) return;
  let name = prompt("Name of the new sketch (letters, numbers and _):");
  if (!name) return;
  name = name.replace(/\.py$/, "");
  if (!/^[A-Za-z0-9_]+$/.test(name)) return say("Use letters, numbers and _ only.", true);
  const path = `${CONFIG.SKETCH_DIR}/${name}.py`;
  const text = "import funground as f\n\n\ndef draw():\n    f.circle(200, 200, 100)\n\n\nf.run()\n";
  const put = await github("PUT", `${base}/${encodePath(path)}`, {   // no sha: GitHub refuses if it already exists
    message: `New sketch ${name}`,
    content: toBase64(text),
  });
  if (put.status === 422) return say(`${name}.py already exists. Open it instead.`, true);
  if (!put.ok) return say("Could not create it (" + put.status + ").", true);
  const result = await put.json();
  current = { path, sha: result.content.sha, text };
  $("editor").value = text;
  await listSketches();
  $("files").value = path;
  say("Created " + path);
}

// Sign out: delete the token from this browser, and for option b ask the service to revoke it at GitHub.
async function signOut() {
  const old = auth;
  forget();
  showSignedOut();
  if (old?.kind === "app" && CONFIG.EXCHANGE_URL) {
    log(`POST ${CONFIG.EXCHANGE_URL}/revoke  (asks GitHub to delete the token)`);
    try {
      await fetch(CONFIG.EXCHANGE_URL + "/revoke", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_token: old.token }),
      });
    } catch { /* the token still expires in 8 hours */ }
  }
  say(old?.kind === "pat"
    ? "Signed out here. The token still works until it expires: delete it at GitHub, Settings, Developer settings."
    : "Signed out. The token is gone from this browser.");
}

// ---- wire up -------------------------------------------------------------------------------------------------

$("usePat").onclick = usePat;
$("signIn").onclick = startSignIn;
$("install").onclick = startInstall;
$("signOut").onclick = signOut;
$("load").onclick = listSketches;
$("open").onclick = openSketch;
$("newSketch").onclick = newSketch;
$("save").onclick = () => save(false);
$("keepMine").onclick = () => save(true);
$("takeTheirs").onclick = async () => { await openSketch(); };
$("files").ondblclick = openSketch;

(async function start() {
  restore();
  await finishSignIn();
  if (auth) await enter(); else showSignedOut();
})();
