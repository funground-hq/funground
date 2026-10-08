# Sprint 18 review — 0.2 web: browser timings and where the time goes

**Dates:** 8 October 2026, on `release-0.2-web`. **Signed off 8 October 2026** (maintainer: "close 18
and start 19").

## Outcome

| Story | Result | Where |
|---|---|---|
| S-142 Cairo-in-wasm vs Canvas 2D in Chrome | done | `funground-web` `spike/s142-browser-bench`, `spikes/S-142_RESULTS.md` |
| S-143 where a heavy frame's time goes (native half) | done; the Pyodide phase split came from S-142 | same branch, `spikes/S-143_native_RESULTS.md` |

**S-142** (Chrome 154 headless, 13 cases, 1× and 2×, three repeats, medians; differences under ~25 %
are noise):

| ms per frame | native Cairo | Chrome Cairo | Chrome Canvas |
|---|---|---|---|
| 10 heavy examples, 1× | 21.7 | 59–64 | 71–89 |
| 10 heavy examples, 2× | 27.9 | 67–75 | 72–74 |
| Session-1, 1× | 1.7 | 7.0 | 6.0 |
| Session-1, 2× | 3.3 | 14.1 | 6.0 |

- Cairo in Chrome: 12/12 goldens byte-identical. Canvas: 12/12 within the S-135 tolerance.
- Python `draw()` is the largest cost on both routes (~3× native). The Canvas route adds 25–34 ms of
  JSON encoding per heavy frame; the Cairo route adds render (14–18 ms) and a pixel copy that grows with
  size (1.4 ms at 1×, 4.5 ms at 2×).
- Marks and Grid call `CairoRenderer.ink_bounds`, so the Canvas route needs pycairo anyway.
- First load, cold: ~9 s either way; the Cairo route downloads 0.5 MB more.

**S-143** (native): user code is 1–7 % of `draw()`. The rest is funground: `dataclasses.replace` on
every style call, colours re-parsed on every call, `Vector` validating through the `numbers.Real` ABC,
4–5 wrapper layers per shape; glyph outlines re-transformed every frame in the renderer; per-op dict
building in `op_to_jsonable`. Prototypes (monkeypatches, measurement only) took 25–40 % off `draw()` and
halved poster_series's Cairo time, with identical ops and pixels.

## D-075 matrix, redone on browser numbers

| | B Canvas | C Cairo | D hybrid |
|---|---|---|---|
| Heavy frames in Chrome | 71–89 ms | 59–75 ms | as B |
| Light sketches at 2× | 6 ms | 14 ms | as B |
| Fidelity | tolerance | byte-identical | screen tolerance, files exact |
| Second implementation | yes | no | yes, plus switching |
| Needs pycairo anyway | yes (marks, Grid) | yes | yes |

Leaning **C** by default, with the Canvas renderer kept as a proven second IR consumer for when a compact
hand-over exists and high-density screens make the pixel copy the bottleneck. **Decision deferred** by
the maintainer until the Sprint 19 performance work is measured.

## Findings

1. Clean performance work in funground's core helps both routes and the desktop; it comes first.
2. The compact IR hand-over only matters for the Canvas route; it waits for D-075.
3. Shortening the per-shape wrapper chain touches the API plumbing: a design decision, later.
4. Maintainer (8 Oct): fixes must be clean, not hackish; added to the `funground-sdlc` skill.

## Built by

S-142 and S-143 by Sonnet subagents; both were interrupted by a network outage and resumed. The S-143
subagent could not write its report file; the main session wrote it from the report.

## Retrospective

- Measuring in the real browser reversed the Node-based expectation: the Canvas route's cost was in
  Python, not in drawing. Measure in the target environment before deciding.
- Running a light native job beside a Chrome job worked on this machine, at the cost of noisy numbers.
