# Test strategy

Implements §10 of the architecture document as it stands after Sprint 0. Run with
`.venv/Scripts/python -m pytest` (73 tests, ~15 s). Everything is headless.

## Layers

| Layer | Purpose | Where | Status |
|---|---|---|---|
| Public API contract | Names and signatures of the v0.5 surface never drift by accident | `tests/test_api_contract.py` | live |
| Semantic tests | One pixel-level test per pinned row of `docs/design/Semantic_Contract.md` | `tests/test_semantics.py` | live |
| Sample-suite smoke | Every `examples/session1/*.py` runs unchanged for 30 frames headless | `tests/test_examples_golden.py::test_sketch_runs_unchanged_headless` | live |
| Golden images | The sample suite renders exactly what it did before | `tests/test_examples_golden.py::test_sketch_matches_golden`, `tests/golden/*.png` | live |
| **IR snapshots** (primary cross-backend contract) | Learner code → expected draw-op list of the final frame, JSON, platform-independent | `tests/test_ops_snapshot.py`, `tests/snapshots/*.json` | live (Sprint 2) |
| Capability / error contract | Unsupported features fail at `f.size()`/`run()` with a learner-readable message | `tests/test_capabilities.py` | live (Sprint 2) |
| Examples Gallery | Every gallery example runs headless, matches its golden and IR snapshot; together the examples use every public name | `tests/test_gallery.py`, `tests/golden/gallery/`, `tests/snapshots/gallery/`, `tools/make_gallery.py` | live (Sprint 5) |
| Provider contract | Every renderer/platform obeys its protocol | planned, Sprint 3 |
| Cross-renderer conformance | Same ops → same semantics on pygame and Cairo (pixel tolerance) | planned, Sprint 3 |
| Export checks | PDF/SVG structure + rendered comparison | planned, Sprint 4 |
| Packaging CI | Windows/macOS/Linux × Python 3.11–3.14 | `.github/workflows/ci.yml` | written, not yet executed (no remote) |

## Headless execution

`tests/conftest.py` sets `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` before pygame is
imported. Under the dummy driver the mouse is at (0, 0) and no keys are pressed, which makes the
input-driven sketches deterministic.

`run_sketch(path, frames)` executes a learner file **unchanged**: it swaps `funground.run` for a
wrapper that forwards the sketch's own globals to `_core._run_namespace(..., max_frames=frames)`,
then returns the final frame's RGB bytes captured by the `max_frames` hook. Learner files never
contain test hooks.

## Test hierarchy (PROCESS)

1. Public API semantics (`test_api_contract`, `test_semantics`)
2. **IR snapshots** — what the learner's code asked for. Two correct renderers may differ in pixels;
   they may not differ in ops. Regenerate with `FUNGROUND_UPDATE_SNAPSHOTS=1`; a change here is
   a change in *behaviour requested*, never in rendering.
3. Per-backend semantic tests (pixel rows in `test_semantics`)
4. Per-backend golden images (below)

## Golden-image policy

- Goldens are produced on the Windows teaching machine (`GOLDEN_PLATFORM = "Windows"`); other
  platforms run every sketch but skip the pixel comparison, because font rasterisation differs.
- Comparison is **exact** while the only renderer is pygame. When Cairo lands (S-023) this becomes
  a per-channel tolerance, and the op-list snapshot layer becomes the primary regression guard.
- Regenerate only as a deliberate act tied to a contract change:
  `FUNGROUND_UPDATE_GOLDENS=1 pytest tests/test_examples_golden.py`. The diff of `tests/golden/`
  is reviewed like code.
- A failing comparison writes the actual frame to `tests/golden/_actual/` (git-ignored) for inspection.
- `11_delta_time.py` is time-dependent and smoke-tested only.

## Determinism

- `f.random_seed(0)` is applied by the autouse fixture before every test.
- Sketches run at `fps=1000` so 30 frames take ~30 ms of wall time; `delta_time` is not asserted
  beyond range checks.

## Adding a sketch to the suite

1. Write plain learner code in `examples/session1/NN_name.py` — it must call `f.run()` itself.
2. Run the suite once: the golden is written and the test skips with "golden written".
3. Run again: it compares. Commit the PNG with the sketch.

## Definition of green

All layers pass on the local machine and on every cell of the CI matrix. A skipped golden
comparison on macOS/Linux is expected; a skipped one on Windows is a bug.
