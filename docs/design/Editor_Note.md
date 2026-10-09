# Design note: the editor and the learner's sketchbook (0.2)

**Status:** draft for the maintainer, 9 October 2026. Elaborates S-151 part 2 (the editor) and S-155 (the
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
