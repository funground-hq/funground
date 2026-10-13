# Design note: the editor and the learner's sketchbook (0.2)

**Status:** draft, 9 October 2026. **Update (D-079 accepted as C):** learners edit and save in **github.dev**, GitHub's own web editor, and the sketch renders on the same page; spike S-156 finds out how (see the last section). Elaborates S-151 part 2 (the editor) and S-155 (the
sketchbook on GitHub). Builds on D-074 (H1 editor), D-077 (website), D-078 (preview origin) and
`Web_Runner_Note.md`. One decision is open: **D-079**, how the editor gets permission to save to a learner's
repository.

## The experience (p5.js editor style, one page)

```
┌ funground-hq.github.io/play/ ───────────────────────────────────────────────────────────┐
│ [sketchbook: anna/sketchbook ▾]  [▶ Run] [■ Stop] [☐ Auto-run]  [Save] [New] [Share]  │
├──────────────┬────────────────────────────────────┬──────────────────────────────────────┤
│ sketches/    │ import funground as f              │                                      │
│  bounce.py ● │                                    │      (the running sketch:            │
│  poster.py   │ def setup():                       │       an iframe on                   │
│  tune.py     │     f.size(640, 400)               │       funground-run.github.io)       │
│ data/        │ ...                                │                                      │
│  photo.png   ├────────────────────────────────────┴──────────────────────────────────────┤
│              │ output: print() and errors, with the line to look at                       │
└──────────────┴───────────────────────────────────────────────────────────────────────────┘
```

- **Edit, run and see on one page.** Code on the left (CodeMirror 6, Python highlighting), the running
  sketch on the right, output below. Run restarts the sketch; Auto-run restarts it a moment after typing
  stops, as p5's editor does. Errors point at the line.
- **The files are the learner's GitHub repository**, made from our template
  `funground-hq/sketchbook` ("Use this template"). The left panel lists its `sketches/` and `data/`
  folders; a sketch's pictures, sounds and fonts load from `data/` into the runner.
- **Save** commits the open file to the learner's repository, with a message they can edit ("Save" in
  the editor = a commit on GitHub). **New** adds a sketch from a starter. Unsaved edits are kept in the
  browser as a draft, so closing the tab loses nothing.
- **Share** gives a link that opens a sketch read-only: `…/play/?gh=anna/sketchbook/sketches/bounce.py`.
  Anyone can open it and run it; to change it they use their own sketchbook (Save a copy).
- **Without GitHub** the editor still works: the gallery examples and a scratch sketch, drafts in the
  browser, Share by link with the code in the URL fragment (H1 as planned).
- **The same files run on the desktop:** `git clone`, `pip install funground`, `python sketches/bounce.py`.
  The template's README says so, and its GitHub Pages workflow publishes the sketchbook as a small site
  of runnable sketches at `anna.github.io/sketchbook/`.

## Security

- The editor page (`funground-hq.github.io`) holds the learner's GitHub permission. **It never runs
  sketch code.** Sketches run only in the sandboxed iframe on `funground-run.github.io` (D-078), which
  receives the code by `postMessage` and has no access to the editor's storage or the permission.
- The permission is limited to the learner's sketchbook repository, contents only (read and write).

## How Save gets permission (D-079, open)

Reading public repositories needs no login (GitHub's API allows it from the browser, 60 requests an hour
without one). Writing needs a token, and GitHub's sign-in endpoints cannot be called from a web page
directly (no CORS), so a full "Sign in with GitHub" needs a small server.

| Option | How | Learner effort | We run | Notes |
|---|---|---|---|---|
| A. A personal token the learner pastes | GitHub fine-grained token, limited to the sketchbook repo, contents read/write; kept in the browser (session or local storage, the learner chooses) | Once: a guided page with screenshots, about 2 minutes | Nothing | No backend, no secret; tokens expire (the learner picks up to a year); fine for teachers and older learners, fiddly for young ones |
| B. "Sign in with GitHub" via a GitHub App | A GitHub App installed on the sketchbook repo; a tiny token-exchange service (e.g. one Cloudflare Worker, free tier) holds the app's secret | One click, then approve | A small service with one secret | Best experience; a service and a secret to look after; privacy page needed |
| C. No saving from the editor | Download / copy the file; edit in github.dev for saving | Each save is manual | Nothing | Not the p5 experience asked for |

**Recommendation:** A for 0.2, designed so B can replace it without changing the editor (one "get a token"
function). A needs no server and keeps learners' work in their own repositories; B follows when the
editor has users who find the token step hard.

## Stories

- **S-151 part 2, the editor:** the page above with GitHub-free use (examples, scratch, drafts, Share in the
  fragment), the sandboxed preview on `funground-run.github.io`, Run/Stop/Auto-run, output with line
  numbers.
- **S-155, the sketchbook:** the template repository `funground-hq/sketchbook` (starter sketches, `data/`,
  README for desktop use, Pages workflow); the editor's GitHub panel: open a sketchbook (public, no login),
  list and open files, load `data/`, Save (commit) and New with the D-079 permission, Share links
  `?gh=owner/repo/path`; a guide page "Keep your sketches on GitHub".

Acceptance for both: a learner with a fresh GitHub account makes a sketchbook from the template, opens it
in the editor, edits and runs a sketch, saves it (a commit appears in their repository), shares a link that
runs for someone else, and runs the same file on the desktop. The editor origin never executes sketch
code (checked by a test that a sketch cannot read the editor's storage).

## Design of the web editor (S-151 part 2, 11 October 2026)

With D-079 = C, saving to GitHub belongs to github.dev and the funground extension (`Extension_Note.md`).
The web editor is for learners **without GitHub**: open the website, write, run, share a link. No account,
no token, no server of ours.

**One page.** The Play page (`funground-hq.github.io/play/`) becomes the editor: an example list, a code
editor (CodeMirror 6, Python colours), Run / Stop / Auto-run (re-run 400 ms after typing stops, as the
extension), output under the picture, Share. `?example=<id>` opens an example (the gallery's "Run it here"
links keep working). The page that only ran our examples (part 1) is replaced, not kept beside it.

**Every run in the preview origin (D-078).** The editor never runs Python. It sends the code (and an
example's data files) by `postMessage` to an iframe from `funground-run.github.io/preview.html`, sandboxed
(`allow-scripts allow-same-origin`: the tests showed the runner's worker does not start without
`allow-same-origin`; the frame then has its own origin, separate from the editor's) with `allow="autoplay; microphone"`. The preview answers with `ready`, `output`,
`error` (the traceback), `started`, `finished` and its canvas size. Both sides check the other's origin;
the preview accepts runs only from the editor's origin.

**The preview holds no build.** `preview.html` loads the runner, Pyodide and the wheels from the website
(`funground-hq.github.io/play/runner/`, served with CORS; the runner starts its worker from a `blob:` URL
when its files are on another origin), so the editor and the preview always run the same funground. The
`funground-run.github.io` repository is a few static files.

**Share.** A link carries the code in the URL fragment, compressed (`#code=` + base64url of deflate-raw):
never sent to a server, works for anyone. Opening it shows the code and waits for Run (a shared sketch is
someone else's code: the learner chooses to run it, and it runs in the preview origin anyway).

**Drafts.** Unsaved changes are kept in the browser (`localStorage` on the website's origin, per example or
scratch sketch), offered back on return; "Reset" restores the example.

**Errors.** The traceback's line in the sketch is highlighted in the editor, as the extension underlines it.

**Not in part 2:** saving to GitHub (github.dev's job), uploading the learner's own pictures (later: a file
picker that sends files with the run), several files per sketch.

## github.dev as the editor (D-079 = C): what spike S-156 must find out

The maintainer prefers GitHub's own editor to ours: editing and saving (committing) are then GitHub's, with
no token and no server of ours, and the sketch renders beside the code on the same page. Two ways, in order:

1. **A funground extension for github.dev / vscode.dev (VS Code for the web).** A *web extension* adds a
   "funground: Run" command and a preview panel (a webview) beside the editor. The panel runs the S-153
   runner (Pyodide, Cairo, sound) and re-runs the sketch as the learner types or saves; `data/` files come
   from the repository through the extension's file-system API. Saving is GitHub's commit button. The
   sketchbook template recommends the extension (`.vscode/extensions.json`), so github.dev offers it on
   opening. The webview has its own sandboxed origin, so the sketch never runs with the editor's rights.
2. **github.dev framed inside our page** (our page = github.dev on the left, our runner on the right).
   Likely refused: GitHub's pages usually forbid being framed. The spike checks it in minutes; if it is
   refused, option 1 is the way.

Questions and pass criteria for S-156 (time-boxed, about 3 days):
- Q1: can github.dev or vscode.dev be framed by another site? (Pass: yes, or a clear no with the header that
  forbids it.)
- Q2: can a VS Code web extension's webview run the funground runner: Pyodide in a worker, the Cairo/
  uharfbuzz/skia-pathops wheels, a canvas, Web Audio and the microphone, under the webview's Content
  Security Policy? (Pass: a Session-1 sketch and a sound example run in the panel in vscode.dev with
  github.dev parity; frames byte-identical to the goldens as in S-153.)
- Q3: live update: the panel re-runs on edit (debounced) and on save, using the active file's text, and
  shows output and errors with line numbers. (Pass: under 1 s from a pause in typing to a new run, after
  the first load.)
- Q4: data files: a sketch loading `data/photo.png` and a WAV works from the repository. (Pass: yes.)
- Q5: install path: sideload for testing ("Install Extension from Location"), and what publishing needs
  for learners (Visual Studio Marketplace and/or Open VSX publisher accounts; the maintainer's act). How
  the template's recommendation appears to a learner opening their sketchbook in github.dev.
- Q6: size and load: the extension's own size, whether the runtime loads from our site (CORS) or ships in
  the extension, first-run time.

Where to run it: github.dev, vscode.dev and Open VSX are unreachable from the maintainer's machine on its
current network (the same block as GitHub). The spike suits a Claude cloud session: it can install
`@vscode/test-web` and Chromium there and drive vscode.dev-like hosting headlessly; the final check in
real github.dev is the maintainer's, on a network that reaches GitHub.

**Outcome (S-156, 10 October 2026).** Way 1 works: a VS Code web extension's panel runs the unchanged runner
beside the editor (VS Code for the web 1.141 and 1.91, headless Chromium), frames byte-identical to the goldens,
a re-run about 0.4 s after typing stops (the 400 ms pause included) and within 0.1 s of a save, errors underlined
at their line, sound playing, `data/` WAV files read from the workspace. Way 2 is out: github.dev redirects to
`vscode.dev/github/`, which sends `frame-ancestors 'none'` (checked by the maintainer's machine, 10 October).
Limits: no microphone (VS Code does not let a panel ask for it; listening sketches stay on the website and the
desktop), and pictures wait for D-080. Not yet tried in real github.dev. Decisions D-080 to D-083. Results:
`funground-web` branch `claude/spike-s156-github-dev-x5szgv`, `spikes/S-156_RESULTS.md`.

**How the extension is designed and built:** `Extension_Note.md`.

If both ways fail, the fallback is the one-page editor of S-151 part 2 with "Open in github.dev" for
saving (two tabs) and Share links.
