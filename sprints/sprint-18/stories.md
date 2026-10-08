# Sprint 18 — 0.2 web: measure in the browser, then make it fast

**Dates:** from 8 October 2026, on branch `release-0.2-web`.
**Goal:** replace Node timings with browser timings, find where the time goes, and try the obvious
optimisations, so D-075 (how the browser draws) is decided on browser numbers.

**Framing (maintainer, 8 Oct):** the original architecture (ADR-001, D-010) already expects several
renderers behind one IR (Cairo, Canvas/web, Skia). More than one renderer is not a cost in itself if
they are managed well: one IR, one contract, conformance tests against the goldens.

| Story | Question | Built by | Status |
|---|---|---|---|
| S-142 | Cairo-in-wasm in Chrome vs Canvas 2D in Chrome, same cases, same harness: draw time, frame copy, end-to-end frame time at 1× and 2× | Sonnet subagent | done |
| S-143 | Where does a heavy frame's time go (Python `draw()`, IR building, shaping, encoding, transfer, drawing), native and in Pyodide; prototype the fixes | Sonnet subagent | native half done; Pyodide half moved to Sprint 19 (S-148) |

S-143 candidate optimisations: compact frame hand-off (typed arrays instead of JSON), a shaped-line
cache, bounded shadow layers, cheaper op construction in the IR, OffscreenCanvas in the worker for
heavy frames, and anything the profile shows.

- [x] S-142 harness, Cairo wheel from the CI artifact, both renderers measured in Chrome
- [x] S-142 results file and comparison table
- [x] S-143 profile (native; Pyodide phase split via S-142) of the 10 heaviest examples
- [x] S-143 prototypes and before/after numbers
- [x] Decision matrix for D-075 redone on browser numbers (review.md); decision deferred to after Sprint 19
