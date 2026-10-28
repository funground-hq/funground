# Spike S-238: signing in to GitHub from Play

Desk research and prototype code for D-118. Done 28 Oct 2026. Nothing was created at GitHub or any host, and
nothing was run against a real App. What was measured is marked **measured**. Everything else is read from the
sources named.

## Answer in brief

1. **PKCE does not remove the exchange service.** GitHub added PKCE in July 2025, but it still requires the client
   secret, and the token endpoint still has no CORS. A GitHub staff member said so in July and October 2025, and
   nothing newer has come from GitHub (checked to August 2026).
   Sources: <https://github.blog/changelog/2025-07-14-pkce-support-for-oauth-and-github-app-authentication/>,
   <https://github.com/orgs/community/discussions/15752>, roadmap item <https://github.com/github/roadmap/issues/1153>
   (reported "paused" by a commenter; not confirmed by GitHub).
2. **Recommended: option c.** A GitHub App with a tiny Cloudflare Worker for the exchange, and the pasted
   fine-grained token kept as a second way in, and the existing fallback (Download, Open `.py`, github.dev) kept.
   Cost: **0 pounds a month** on Cloudflare's free plan. The maintainer creates two things: the App and a free
   Cloudflare account with one Worker.
3. If the maintainer will not own a service, option a (paste a token) works today with no server, but it is a
   hard task for a novice (about eight steps). See section 3.
4. The learner must also install the App on their sketchbook repository (one extra screen). See section 2.

## 1. CORS and PKCE, as of 2026

**Measured (28 Oct 2026, from this machine, with `Origin: https://funground-hq.github.io`):**

| Request | Result |
|---|---|
| `OPTIONS https://github.com/login/oauth/access_token` (preflight) | 404, no `Access-Control-*` header |
| `OPTIONS https://github.com/login/device/code` | 404, no `Access-Control-*` header |
| `POST https://github.com/login/oauth/access_token` | no `Access-Control-Allow-Origin` header |
| `OPTIONS https://api.github.com/repos/.../contents/...` | 204, `Access-Control-Allow-Origin: *`, methods `GET, POST, PATCH, PUT, DELETE`, headers include `Authorization`, `Content-Type`, `If-Match`, `X-GitHub-Api-Version` |
| `GET https://api.github.com/repos/funground-hq/sketchbook/contents/sketches` | 200, `Access-Control-Allow-Origin: *` |

So a browser cannot call `github.com/login/oauth/access_token` or the device-flow endpoints, and it can call
`api.github.com`. This agrees with GitHub's own page, which says CORS preflight (`OPTIONS`) is not supported
for the device flow
(<https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps>) and with GitHub staff in
<https://github.com/orgs/community/discussions/15752>: "CORS on the token endpoint still has to be added" (15 Jul 2025).

**PKCE.** Supported for OAuth apps and GitHub Apps since 14 Jul 2025, S256 only, recommended, not required. Send
`code_challenge` and `code_challenge_method=S256` to authorize, then `code_verifier` with the code. "GitHub does not
distinguish between public and confidential clients", and the device flow does not use PKCE
(<https://github.blog/changelog/2025-07-14-pkce-support-for-oauth-and-github-app-authentication/>). GitHub's page for
user tokens still marks `client_secret` as required for the code exchange
(<https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app>).
GitHub staff, 15 Jul 2025: GitHub always requires the secret; single-page apps must include it; no date to change
(<https://github.com/orgs/community/discussions/15752>). Unconfirmed: I did not try an exchange without a secret,
because that needs a real App. The prototype's Worker still sends PKCE, so it will keep working if GitHub drops the secret.

**If GitHub ever ships secret-free PKCE with CORS** (watch roadmap issue 1153), the Worker can be deleted and
`app.js` can post to GitHub directly. The page code changes by one URL.

## 2. GitHub App or OAuth App

Use a **GitHub App**. Sources: <https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app>,
<https://docs.github.com/en/apps/using-github-apps/authorizing-github-apps>.

- **Permissions are narrow.** The App asks for "Contents: Read and write" and nothing else (Metadata: read is
  added automatically). An OAuth app can only ask for the `repo` scope: all code in all the learner's repositories,
  public and private (<https://docs.github.com/en/rest/repos/contents>). That is too much to ask of a child or a parent.
- **Repository choice.** A GitHub App is installed on the repositories the learner picks. A user token reaches only
  what both the user and the App can reach: "The GitHub App can only do things that both you and the app have
  permission to do" (authorizing-github-apps page). The page does not say outright that installation is needed,
  but the intersection rule implies it. **Expect one extra screen: the learner installs the App on their sketchbook
  repository** ("Only select repositories"). The prototype has a "Choose repositories" button that goes to
  `https://github.com/apps/<slug>/installations/new`. With "Request user authorization during installation" on,
  GitHub then returns to the callback with a code, so install and sign-in are one trip.
- **Token life.** User tokens expire after **8 hours** (`expires_in` is always 28800); refresh tokens after **6 months**
  (`refresh_token_expires_in` 15897600). Keep "Expire user authorization tokens" ticked
  (generating-a-user-access-token page above).
- **Refreshing needs the secret.** "client_secret: Required unless the user access token was generated using the
  device flow." A refresh token works once: using it kills the old pair and returns a new one
  (<https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/refreshing-user-access-tokens>).
  The device flow would avoid the secret, but its endpoints have no CORS, so a browser cannot use it. So the
  Worker also does `/refresh`. A learner who works for more than 8 hours is refreshed silently; one who
  returns after 6 months signs in again.
- **Rate limits.** User-to-server tokens use the user's 5,000 requests an hour; secondary limit for writes is about
  80 a minute and 500 an hour (<https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api>).
  Play will not get near them.
- **Commits show the learner** as author with the App's badge
  (authorizing-github-apps page).

## 3. Option a: fine-grained personal access token

Source: <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens>.

Steps the learner takes: open Settings, Developer settings, Personal access tokens, Fine-grained tokens, Generate
new token; name it; choose an expiry; choose the resource owner; under Repository access pick "Only select
repositories" and the sketchbook; under Permissions set Contents to Read and write; Generate; copy it; paste it
into Play. About eight steps over three pages, and the token is shown once.

- **Can be limited to one repository:** yes.
- **Expiry:** default 30 days; custom 1 to 366 days; no expiry allowed unless an organisation forbids it.
- **From a browser:** works. `api.github.com` answers with `Access-Control-Allow-Origin: *` (measured, section 1).
  Contents endpoints need only the Contents permission.
- **Limits:** cannot act in a repository the user is only a collaborator on, or in several organisations
  (same page). Fine for a learner's own sketchbook.
- **Risk:** the learner holds a secret with write access to their repository, may paste it elsewhere, and a
  "no expiry" token stays alive after they leave Play. No revoke call from Play (the learner must delete it at GitHub).
- It is a good option for adults, for tests, and as a fallback if the Worker is down.

## 4. The REST calls Play needs

All answer browsers (measured, section 1). Header on each: `Authorization: Bearer <token>`,
`Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`.
Source: <https://docs.github.com/en/rest/repos/contents>.

| Job | Call | Notes |
|---|---|---|
| Who am I | `GET /user` | Check the token. |
| Repositories the App has | `GET /user/installations`, then `GET /user/installations/{id}/repositories` | For the picker. Not for a fine-grained token. |
| List a folder | `GET /repos/{o}/{r}/contents/sketches` | Array of `{name, path, sha, type}`. Up to 1,000 files in a folder; use the Git Trees API beyond that. |
| Read a file | `GET /repos/{o}/{r}/contents/{path}` | `content` is base64 (decode as UTF-8). Up to 1 MB with all features; 1 to 100 MB only with the raw media type. Pictures and sounds in `data/` can be larger: use `Accept: application/vnd.github.raw+json`. |
| Save (a commit) | `PUT /repos/{o}/{r}/contents/{path}` `{message, content, sha}` | `sha` is required when the file exists. One commit per file. |
| New file | same `PUT`, no `sha` | 422 if the file already exists. |
| Several files in one commit | Git Data API (blobs, tree, commit, ref) | Later; not needed for the spike. |

**Conflict detection.** The `sha` of the file as opened is the version. Sending a stale `sha` gives **409** or
**422** and writes nothing (the page lists both as outcomes but does not say what causes 409). The prototype
does not rely on that alone: before each save it reads the file again with `cache: "no-store"` and compares the `sha`. If
it differs it shows their version and asks. The `PUT` error is a second net for a change that lands in between.
Do not send two writes at once: "the concurrent requests will conflict" (contents page), so Play must queue saves.
`PUT` needs both `name` and `email` if you set author or committer; the prototype sets neither, and GitHub uses the learner's.

## 5. Free hosts for the exchange

The service holds the client secret and does about three calls per learner per 8 hours. Even 1,000 active
learners is a few thousand requests a day.

| Host | Free plan | Source |
|---|---|---|
| **Cloudflare Workers** | 100,000 requests a day, 10 ms CPU per request, 50 subrequests. Paid plan 5 USD a month, not needed | <https://developers.cloudflare.com/workers/platform/limits/> (the 5 USD price is from third-party pages and not checked on Cloudflare's own) |
| Deno Deploy | 1 million requests a month, 0 USD | <https://deno.com/deploy/pricing> |
| Netlify | Credit-based: 300 free credits; 2 credits per 10,000 web requests. Function pricing not stated on the page I read | <https://www.netlify.com/pricing/> |
| Vercel | Hobby plan with a monthly allotment; Hobby cannot connect repositories owned by a Git organisation. Hobby is described elsewhere as non-commercial; I did not confirm that | <https://vercel.com/docs/limits> |

**Choice: Cloudflare Workers.** The code is a plain `fetch` handler with no dependencies; a Worker can be pasted
into the dashboard editor (no installs, no Wrangler needed); the free limits are far above the need.
Where the secret lives: a Worker **secret** (encrypted variable) named `CLIENT_SECRET`, set in the dashboard. It is
never in the repository and never sent to the browser. The `CLIENT_ID` is public. Cost in a quiet month: 0.
If the free plan is exceeded Cloudflare returns an error (Error 1027) rather than billing.

Risks to name for the maintainer: (1) the Worker holds the secret, so a bad edit to it could leak the secret
(rotate the secret at GitHub if so); (2) it can see the code and tokens in transit, which is why it keeps nothing and
logs nothing; (3) if it is down, new sign-ins fail but signed-in learners keep working until their 8-hour token runs out,
and option a and the fallback still work.

## 6. Keeping the token in the browser

| Place | Survives | Risk |
|---|---|---|
| Memory only (a variable) | Until reload; lost on the redirect to GitHub | Smallest window; any script already on the page can still read it. Annoying: a reload signs you out. |
| `sessionStorage` | This tab, until it closes; survives the redirect and reload | Readable by any script on the same origin (cross-site scripting would steal it). Gone when the tab closes. **Used by the prototype.** |
| `localStorage` / IndexedDB | Until cleared | Same exposure, for months. Needed only to stay signed in across days. Play already uses IndexedDB for My files (S-221). |

No browser store is safe against a script injected into the page. What reduces the risk: no third-party scripts on
the Play page; a Content-Security-Policy (GitHub Pages cannot set headers, but a `<meta>` CSP works, as in the prototype);
the sketches run in an iframe on another origin (`funground-run.github.io`, D-078), so learner code cannot read
the token; keep the token out of URLs and logs. The refresh token (6 months) is the more valuable one: if Play wants
"stay signed in", keep the refresh token in IndexedDB and the 8-hour token in memory, and say so to the learner.
Recommendation for S-239: 8-hour token in memory plus `sessionStorage`; refresh token in `sessionStorage`; offer "Keep me signed in on this device" as an opt-in that uses IndexedDB.

**Signing out.** Delete the stored values and clear the editor. For an App token also call the Worker's `/revoke`, which
sends `DELETE /applications/{client_id}/token` (needs the secret, so the browser cannot do it; endpoint described at
<https://docs.github.com/en/rest/apps/oauth-applications>, not fetched in this spike). A pasted token cannot be revoked
from Play; the learner deletes it at GitHub. The prototype says so.

## 7. A learner with no GitHub account

Play must work exactly as now: sketches in the browser, Download, Open `.py`, "Open in github.dev" (D-079). The
"Sign in with GitHub" button is an extra. A learner without an account sees the button and a plain line: "Not
needed. You can keep working here and download your sketches." Plus a link "Make a free GitHub account" for those
who want to. GitHub's terms set a minimum age (13 in most countries: <https://docs.github.com/en/site-policy/github-terms/github-terms-of-service>,
not fetched in this spike), so younger learners and school machines with GitHub blocked must never need it. Say that in
the guide. This is a question for the maintainer, because the audience is learners.

## What the maintainer must do

Everything below is done by you, under your own account. Nothing was created by this spike.

1. **Decide the owner.** Create the App under the `funground-hq` organisation (preferred, so it outlives one person),
   or under your own account.
2. **Create the GitHub App.** GitHub, Settings (of the org), Developer settings, GitHub Apps, New GitHub App.
   - GitHub App name: `funground Play` (must be unique; the URL name becomes the slug, e.g. `funground-play`).
   - Homepage URL: `https://funground-hq.github.io/play/`
   - Callback URL (add each; the page's address must match exactly, up to 10 allowed):
     `https://funground-hq.github.io/play/` and, for testing, `http://localhost:8080/`
   - Expire user authorization tokens: **ticked**.
   - Request user authorization (OAuth) during installation: **ticked** (the Setup URL then goes unavailable; that is fine).
   - Enable Device Flow: **off**.
   - Webhook: untick **Active**.
   - Permissions, Repository permissions: **Contents: Read and write**. Leave Metadata (read, automatic). All others "No access".
     No account or organisation permissions.
   - Where can this GitHub App be installed: **Any account**.
   - Create. Then on the App's page: copy the **Client ID**; **Generate a new client secret** and copy it once.
     Do not generate a private key (not needed).
   - Optionally set a logo and the description "Lets Play save your sketches to your own sketchbook."
3. **Create the host account.** A free Cloudflare account (no card needed for Workers Free). Workers & Pages,
   Create, "Hello World" Worker, name it `funground-token`. Edit code, paste `exchange/worker.js`, Deploy.
4. **Set the secret.** Worker, Settings, Variables and Secrets: add `CLIENT_ID` (type Text) and `CLIENT_SECRET`
   (type **Secret**). Under Observability, turn **Workers Logs off** (so nothing is kept). Note the Worker's URL
   (`https://funground-token.<account>.workers.dev`).
5. **Tell the build** the three public values: Client ID, App slug, Worker URL (they go in `CONFIG` in `app.js`; none
   is secret).
6. Keep the secret in your password manager. To rotate: generate a new secret at GitHub, replace it in the Worker, delete the old one.

Cost: 0 per month. Ongoing: you own the secret and the Worker; check them if sign-in breaks.

## How to test

Fill in `CONFIG` in `prototype/app.js` (Client ID, slug, Worker URL). Serve the `prototype` folder with the venv's
Python: `C:\Projects\playground\.venv\Scripts\python.exe -m http.server 8080 --directory C:\Projects\playground\spikes\17_github_signin\prototype`.
The Worker also allows `http://localhost:8080`. Make a test sketchbook from the template `funground-hq/sketchbook`
under a test account.

**Laptop**

1. Open `http://localhost:8080/`. Press "Choose repositories", install the App on the test sketchbook only, authorise. You return to the page signed in.
2. The repository box is filled. Press "List sketches": the `.py` files in `sketches/` appear.
3. Open one, change a line, Save. Check on GitHub that a commit by the test account appeared.
4. Change the same file on github.com, then Save in the page without reopening: expect "Not saved: the file changed" and their version. Try both buttons.
5. New sketch with a name that exists (expect "already exists") and one that does not.
6. Open the browser's Network tab. Confirm the token (`Authorization`) appears only on `api.github.com`, and the code and refresh token only go to the Worker. Look at the page's log too.
7. Sign out. In Application, Session storage: `fg-spike-auth` is gone. Reload: still signed out. On GitHub, Settings, Applications, Authorized GitHub Apps: the App's access token is revoked (a request with the old token gives 401).
8. Option a: make a fine-grained token (one repository, Contents read and write, 1 day), paste it, repeat steps 2 to 5. Sign out; then delete the token at GitHub.
9. Wait 8 hours (or set `expires` to now in session storage) and press List: expect a silent refresh through `/refresh`.

**Phone** (same Wi-Fi; or use a test page on a real host)

GitHub requires the callback to match exactly, and `localhost` on a phone is the phone. Easiest: publish the
prototype on a throwaway path of the site, or add a second callback URL using the laptop's address, e.g.
`http://192.168.x.x:8080/`, and add that origin to `ALLOWED_ORIGINS` in the Worker. Then repeat steps 1 to 7 in the phone's browser,
including the return from GitHub (the GitHub app may offer to open the link in its own app: choose the browser).
Note the number of taps, whether the install screen is understandable to a novice, and typing the repository name
(the picker should avoid it).

**Pass criteria (from S-238):** sign in, list, open, save, new and sign out all work on both; the Network tab shows the
token only at GitHub, and the Worker sees only codes and refresh tokens; signed-out storage is empty; the Worker
costs nothing. Then answer: can a novice finish the install screen unaided?

## Open points the desk work could not settle

- Whether installing the App is strictly needed for a user token to reach a repository (very likely; test step 1).
- Whether `http://localhost` is accepted as a GitHub App callback (commonly done; test).
- Whether the install-then-authorise return carries a `state` (the prototype accepts it without one if the install began in the same tab).
- Whether GitHub will drop the secret requirement (watch roadmap 1153).
- The 5 USD price of Workers Paid and Vercel's Hobby terms were not checked on the vendors' own pages.
