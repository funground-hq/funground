# Sprint 20 — 0.2: the browser runner, on Cairo, and the editor

**Dates:** from 9 October 2026, on `release-0.2-web` (with `funground-web`, `funground-hq.github.io` and
`funground-run.github.io`). **Goal:** a learner opens the website, runs any gallery example in the
browser, and edits and shares sketches in a sandboxed editor. Design: `docs/design/Web_Runner_Note.md`.

| Story | Value | Status |
|---|---|---|
| S-152 | funground's own browser entry point: `BrowserPlatform` and the `funground.web.Session` host API; `f.run()`/`f.show()` under a host; web contract row W1 | done |
| S-153 | Loading: Pyodide, the funground wheel, the three C-extension wheels from a release, fonts; first-load budget (S-139) | done (`funground-web` `feature/runner` 6f70ecd): 14/15 goldens exact, JPEG decoding differs (decision), first-load budget not met yet |
| S-137 | Sound through Web Audio and the microphone through an AudioWorklet, from the worker | done (sound and mic in the runner; listening check by the maintainer) |
| S-154 | Numeric colours (`fill(r, g, b)`, greys, tuples) parsed once: the largest clean hotspot left (S-148) | done |
| S-151 | The Play page: part 1 runs gallery examples on the site; part 2 the editor (H1: CodeMirror, Run/Stop, output, share by link in the URL fragment) with previews on `funground-run.github.io` (D-078) | part 1 done and live at https://funground-hq.github.io/play/ (site PR #2; the runner merged to funground-web main, PR #1; checked in headless Chrome); part 2 planned |
| S-156 | Spike: the sketch rendered beside github.dev (a VS Code web extension, or framing); `Editor_Note.md` Q1-Q6 | done (cloud session; `funground-web` branch `claude/spike-s156-github-dev-x5szgv`, `spikes/S-156_RESULTS.md`): a web extension's panel runs the runner beside the editor, frames byte-identical, re-run about 0.4 s after typing stops. No microphone in a panel; pictures need D-080. Q1: github.dev redirects to vscode.dev, which sends `frame-ancestors 'none'`, so framing is out. Decisions D-080 to D-083 proposed |
| S-157 | funground: a second `Session` in the same Python draws what a fresh one draws (the test D-083 asks for); say what is not reset | done: the 13 golden examples in order and reversed in one interpreter, byte-identical to the desktop; a run now forgets the fonts it loaded from files and the modules it imported from the sketch's folder (`tests/test_web_reuse.py`, contract W1, `web.py`) |
| S-158 | The funground extension for github.dev, from the S-156 spike: runner `reuse` (D-083, after S-157), runtime from the site in versioned folders (D-081), `'unsafe-eval'` in the panel only (D-080), a microphone message that fits a panel; from S-157: the worker puts the sketch's folder on `sys.path` (as `python sketch.py` does) and sets `sys.dont_write_bytecode` (an edit of the same size within a second could otherwise run stale bytecode) | planned |
| S-155 | The sketchbook: template repo carrying the extension in `.vscode/extensions/` (D-082: try this first; Marketplace later); edit and save in github.dev, render on the same page (D-079 = C) | planned (after S-158) |

Acceptance: full suite green; no golden or snapshot changes; the runner passes the S-148 pixel checks
(Cairo byte-identical in Chrome); the Play page works on the live site; the editor's previews run on the
second origin.

- [x] S-152
- [x] S-153
- [x] S-137
- [x] S-154
- [x] S-151 part 1
- [ ] S-151 part 2
- [x] S-156
- [x] S-157
- [ ] S-158
- [ ] S-155
