# Sprint 17 — 0.2 web spikes (renderer, loop, text)

**Dates:** 8 October 2026, on branch `release-0.2-web` (in parallel with Sprint 16 / release 0.1 on `main`).
**Goal:** answer the questions that choose the 0.2 web architecture (`docs/design/Web_Target_Options.md`
section 6, D-074): can the browser draw funground's IR, can Cairo run in the browser, does the inverted
loop work in a worker, and can text be shaped identically in Pyodide.

Spikes produce evidence, not product code. Work lives in the sibling repositories
`funground-hq/funground-web` and `funground-hq/funground-cairo-wasm`, plus a loop prototype on
`spike/s136-loop` here.

| Story | Where | Built by | Status |
|---|---|---|---|
| S-135 Canvas 2D renderer over all 20 IR op types | `funground-web` `spike/s135-canvas-renderer` | Sonnet subagent | done |
| S-134 pycairo, uharfbuzz, skia-pathops for Pyodide | `funground-cairo-wasm` PR #1 | Claude cloud session | done |
| S-136 inverted loop, Python in a module worker | `spike/s136-loop` here; `funground-web` `spike/s136-worker-loop` | Sonnet subagent | done |
| S-133 text shaping in Pyodide | `funground-web` `spike/s133-text-shim` | Sonnet subagent | done |

Tasks for each spike: pass/fail criteria fixed in the options note before the work; build; measure;
write the results file; main session reviews, commits and pushes.

- [x] S-135
- [x] S-134
- [x] S-136
- [x] S-133

Decision needed: **D-075** — how the browser draws (B, C or D), from these results.
