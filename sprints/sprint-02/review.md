# Sprint 2 review — Phase 1b: draw-op IR

**Dates:** 24–25 September 2026
**Goal:** every public drawing call records a backend-neutral op; `LegacyPygameRenderer` consumes
the op list and reproduces today's pixels; IR snapshots become the cross-backend contract; the
renderer bake-off produces the numbers for D-011.

## Outcome

All six stories done. **Phase 1 checkpoint 2 (D-007) met: all 11 goldens byte-identical; 11 IR
snapshots committed.** One decision raised and pending: D-011 (interactive engine).

| Story | Result | Commit |
|---|---|---|
| S-018 Draw-op IR | `geometry.py` (`Transform`, `Path`), `ir.py` (13 op types, `Frame`, JSON round-trip); `Sketch` emits ops, renders once per loop | 73e26fa, f3be412, a3ab4a5 |
| S-019 `LegacyPygameRenderer` | `render(frame)` dispatch, v0.5 drawing verbatim, `capabilities` | a3ab4a5 |
| S-020 IR snapshots | `tests/test_ops_snapshot.py`, 11 JSON files, test hierarchy in `Test_Strategy.md` | e090148 |
| S-021 Capability registry | `Capability`, `PlaygroundError`, check at `size()`/`run()`, extra-naming message | 4291a1d |
| S-035 Spike 07 bake-off | Cairo / Skia / Blend2D on the real IR; D-011 presented | 60c3f41 |
| S-033 Architecture v2 | `docs/design/Playground_Technology_Architecture_v2.md` | this commit |

## Test results

```
153 passed
  test_api_contract 7 · test_semantics 42 · test_examples_golden 24 (11 goldens, exact)
  test_color 33 · test_state 4 · test_sketch 5 · test_boundaries 2
  test_geometry 13 · test_ir 4 · test_ops_snapshot 13 · test_capabilities 6
```

Windows 11, Python 3.14.7, pygame-ce 2.5.8. Goldens unchanged since Sprint 0 (`18a5d21`).
Code diff for the sprint: 23 files, +2298 / −100.

## Findings

1. **The IR is backend-neutral in practice, not just in design.** Spike 07 rendered the same
   `Frame` objects through Cairo, Skia and Blend2D with pixel-identical results; each adapter is
   ~100 lines. This is the strongest evidence the architecture has produced so far.
2. **Engine numbers (draw ms, scene A / C at 640×400):** Blend2D 24 / 5.5 · Cairo 70 / 21 · Skia
   206 / 506. Skia's slowness is the binding's CPU rasteriser (`drawOval` no faster). Presentation
   0.1–1.5 ms for all. Full tables in `spikes/RESULTS.md` §7.
3. **`blend2d-py` cannot run the IR today**: no clip, no matrix, no fill rule; scale was emulated
   by transforming paths in Python and it was *still* fastest. Native font-from-file works
   (0.03 ms/line). No macOS x86_64 wheel; single-company binding since 2025.
4. **Deferred drawing changed one test mechanism only.** Pixels now exist after `Sketch._render()`,
   so the `canvas` fixture became `LiveCanvas` (renders on `get_at`). No assertion changed.
5. **Ops recorded in `setup()` render on the first frame**, exactly as v0.5 drew them immediately
   to the persistent surface — the goldens confirm it.
6. **The Python cost of walking the IR is inside every Spike 07 number** and is the same for all
   engines; at teaching scale (hundreds of ops) it is a few ms.
7. **Text stays an op**: `ir.Text` is drawn by the legacy renderer; the vector adapters raise on it
   because the text subsystem (S-029) will materialise it into `FillPath` ops. The scene-E timings
   used that route already.

## Decisions

- **Pending: D-011 — the interactive 2D engine.** Presented per PROCESS in `Decision_Log.md`.
  Recommendation D: Cairo for Sprint 3 and export; Blend2D as a gated optional renderer later.
- Taken during the sprint: none beyond D-010's application.

## Retrospective

- *Went well:* every story landed as one commit with a byte-identical golden run; the bake-off
  reused the production IR instead of a spike-local scene format, so it tested the real thing.
- *Went badly:* the Blend2D adapter needed two fix-and-rerun cycles for binding signatures
  (rgba ints, `create_from_file` as an instance method) — an introspection pass *before* writing
  the adapter would have avoided both.
- *Carry-over:* none. Sprint 3 opens on D-011.
