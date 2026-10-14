# Sprint 20 review — 0.2: the browser runner, on Cairo, and the editor

**Dates:** 9–13 October 2026, on `release-0.2-web` (merged to `main` with S-177), with `funground-web`,
`funground-hq.github.io`, `funground-run.github.io` and `funground-hq/sketchbook`. **Signed off 14 October 2026.**

## Outcome

Goal met: a learner opens the website, runs any gallery example in the browser, and edits and shares sketches in
an editor whose previews run on a second origin. Live at https://funground-hq.github.io/play/.

| Story | Result | Commit |
|---|---|---|
| S-152 BrowserPlatform and `funground.web.Session` | `f.run()`/`f.show()` under a host; contract W1 proposed | `ac120f2` |
| S-153 The browser runner (Pyodide, wheels, fonts) | 14 of 15 golden cases byte-identical in Chrome; the JPEG case differs (finding 1); pygame-ce and Pillow loaded on demand | `funground-web` `6f70ecd` |
| S-137 Sound and microphone in the browser | Web Audio from the worker, microphone through an AudioWorklet; the maintainer listened | `7961044`, `funground-web` `794b604` |
| S-154 Numeric colours made once | `fill(200, 100, 50)` 7.2 → 4.7 µs, `fill(128)` 4.6 → 3.0 µs; kinetic_type about −7 %, others within noise | `deca92a` |
| S-151 The Play page (part 1) and the editor (part 2) | part 1: site PR #2; part 2: CodeMirror 6, Run/Stop/Auto-run, error line, Share in `#code=`, drafts, previews on funground-run.github.io; 10 headless checks | site PRs #2, #5; `funground-run` PR #1 |
| S-156 Spike: a panel beside github.dev | a web extension's panel runs the runner, frames byte-identical, re-run about 0.4 s after typing stops; framing ruled out (`frame-ancestors 'none'`) | `funground-web` `f2412e2` (cloud session) |
| S-157 A second Session draws what a fresh one draws | the golden examples in order and reversed in one interpreter, byte-identical; fonts and sketch modules forgotten between runs | `17a5e51` |
| S-158 The funground extension | runner `reuse`, versioned runtime at `/runtime/0.2-dev/` with CORS, `'unsafe-eval'` in the panel only; on the Visual Studio Marketplace | `funground-web` PRs #2–#5, site PRs #3, #4 |
| S-155 The sketchbook template | `funground-hq/sketchbook` is a template (six starter sketches, data folder, helper, learner README) and recommends the Marketplace extension | sketchbook `c5b9133` |

**Tests:** full suite 3667 (S-152) → 3684 (S-154) → 3711 (S-137) → 3717 passed (S-157); no golden or snapshot
changed. Runner: `tests/out/report.json` in funground-web (15 golden cases, stop, errors, syntax error, input).

## Decisions

- **D-079 = C** (github.dev as the editor, with a funground panel).
- **D-080 = b** (`'unsafe-eval'` in the extension panel only), **D-081 = b** (runtime from the site, versioned),
  **D-082** template-carried extension first (outcome: it does not load in the browser, so the Marketplace),
  **D-083** runner reuse after a test (S-157).
- **D-084:** LGPL-2.1-only.
- **D-101 raised by this review** (pending): JPEG decoding in the browser (finding 1).

## Findings that change later work

1. **JPEG decodes differently in Pyodide.** images-01 differs in 50,454 of 256,000 pixels (largest channel
   difference 87): Pyodide's libjpeg build, not the runner, Cairo or the renderer (the same picture as PNG is
   identical). Proposed in `funground-web/runner/RESULTS.md` but never logged; now D-101.
2. **The first-load budget (S-139) is not met.** A plain sketch fetches 12.4 MB (Pyodide 6.2 MB, funground wheel
   2.7 MB of which fonts 2.4 MB): about 10 to 14 s on 10 Mb/s against a 10 s budget; repeat visit 3.3 to 5.5 s
   against 3 s on this machine. Loading pygame-ce and Pillow on demand saved 2.56 MB. Biggest lever left: the
   bundled fonts. S-139 stays a candidate.
3. **On-demand loading needs its list kept complete.** The first user-reported bug (14 Oct) was `apply_filter`
   missing from the ON_DEMAND list; `tools/check_on_demand.py` now follows api.py wrappers too
   (funground-web PR #7, live since the 14 Oct build).
4. A browser can install an extension only from the Marketplace or localhost; a repository-carried extension
   does not load in vscode.dev.

## Built by

Not recorded at the time; the commits are the main session's. S-156 ran in a Claude cloud session.

## Not done

- **The maintainer's run-through of the sketchbook in real github.dev** (S-155's last check) is not recorded.
  The story is ticked because the template and the Marketplace extension are live; the check is asked for at
  sign-off.

## Retrospective

- Spiking the riskiest question in a cloud session (S-156) while the runner was built here worked: the answer
  arrived with byte-identical frames and four decisions ready to put to the maintainer.
- A list kept by hand in one repository (ON_DEMAND) and checked against another only by a tool someone has to
  run let a bug through. The check should run in funground-web's CI against funground `main`.
- Who built what was not written down; from Sprint 25 each review lists it as the stories land.

## Sign-off

**Signed off by the maintainer, 14 October 2026** ("Sign off pending sprints"). Sprint closed.

Open after sign-off: the maintainer's run-through of the sketchbook in real github.dev (S-155) and D-101 (JPEG decoding) stay open; neither blocks the close.
