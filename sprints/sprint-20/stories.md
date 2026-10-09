# Sprint 20 — 0.2: the browser runner, on Cairo, and the editor

**Dates:** from 9 October 2026, on `release-0.2-web` (with `funground-web`, `funground-hq.github.io` and
`funground-run.github.io`). **Goal:** a learner opens the website, runs any gallery example in the
browser, and edits and shares sketches in a sandboxed editor. Design: `docs/design/Web_Runner_Note.md`.

| Story | Value | Status |
|---|---|---|
| S-152 | funground's own browser entry point: `BrowserPlatform` and the `funground.web.Session` host API; `f.run()`/`f.show()` under a host; web contract row W1 | done |
| S-153 | Loading: Pyodide, the funground wheel, the three C-extension wheels from a release, fonts; first-load budget (S-139) | done (`funground-web` `feature/runner` 6f70ecd): 14/15 goldens exact, JPEG decoding differs (decision), first-load budget not met yet |
| S-137 | Sound through Web Audio and the microphone through an AudioWorklet, from the worker | planned |
| S-154 | Numeric colours (`fill(r, g, b)`, greys, tuples) parsed once: the largest clean hotspot left (S-148) | done |
| S-151 | The Play page: part 1 runs gallery examples on the site; part 2 the editor (H1: CodeMirror, Run/Stop, output, share by link in the URL fragment) with previews on `funground-run.github.io` (D-078) | planned |

Acceptance: full suite green; no golden or snapshot changes; the runner passes the S-148 pixel checks
(Cairo byte-identical in Chrome); the Play page works on the live site; the editor's previews run on the
second origin.

- [x] S-152
- [x] S-153
- [ ] S-137
- [x] S-154
- [ ] S-151 part 1
- [ ] S-151 part 2
