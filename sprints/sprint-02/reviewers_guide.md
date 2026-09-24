# Sprint 2 — Reviewer's guide

For the maintainer reviewing Sprint 2 before closing it. Budget: about an hour. The sprint's
claim: **drawing now goes through a backend-neutral IR, and no learner-visible pixel changed.**

Diff under review: `git diff 07c9faa..HEAD -- playground tests` — 23 files, +2298 / −100.

## 1. Verify the claim first (10 minutes)

```powershell
.venv\Scripts\python -m pytest                       # expect: 153 passed
git diff --stat 18a5d21..HEAD -- tests/golden        # expect: no output - goldens untouched since Sprint 0
git status --short                                   # expect: empty
dir tests\snapshots                                  # expect: 11 JSON files
.venv\Scripts\python examples\session1\04_fill_stroke.py   # a real window; Escape closes
```

Then open one snapshot, e.g. `tests/snapshots/02_shapes.json`: it should read as exactly what the
sketch asked for — a `Clear`, then shapes with their style — with no pygame anywhere in it.

## 2. Commits in reading order

| Commit | Story | Read | Why |
|---|---|---|---|
| `73e26fa` | S-018.3 | `playground/geometry.py`, `tests/test_geometry.py` | Leaf types. Check the conventions: degrees, y-down, `then()` vs `concat()`. |
| `f3be412` | S-018 | `playground/ir.py`, `tests/test_ir.py` | The contract. 13 ops, `Frame`, JSON round-trip. |
| `a3ab4a5` | S-018.5 / S-019 | `playground/sketch.py` (diff), `renderers/legacy_pygame.py`, `renderers/__init__.py`, `capabilities.py`, `tests/conftest.py` (diff) | The wiring. This is the commit that could have moved a pixel; it didn't. |
| `e090148` | S-020 | `tests/test_ops_snapshot.py`, `tests/snapshots/`, `docs/qa/Test_Strategy.md` | The new primary regression layer. |
| `4291a1d` | S-021 | `tests/test_capabilities.py` | Error UX. |
| `60c3f41` | S-035 | `spikes/07_renderer_bakeoff/{scenes,adapter_*,bench}.py`, `spikes/RESULTS.md` §7 | Evidence for D-011. Not production code. |
| this commit | S-033 | `docs/design/Playground_Technology_Architecture_v2.md` | The document a new contributor reads first. |

## 3. What to scrutinise

### `sketch.py` — the loop
- `run_namespace`: order is now `poll → input → draw() → [capture ops] → _render() → present → frame_count++ → [capture pixels] → tick`. The only insertion relative to Sprint 1 is `_render()` between `draw()` and `present()`. Confirm nothing else moved.
- `_emit()` keeps the v0.5 "no window yet" error at *call* time (contract R9), not at render time.
- `_render()` clears the frame after drawing; `finally` clears it again and detaches the renderer. *Question:* are you happy that ops recorded in `setup()` are drawn on frame 0 (as v0.5 did)?
- `_check_capabilities()` runs in `size()`, which `run_namespace()` calls if `setup()` didn't — so both entry points are covered (`test_run_without_size_also_checks_capabilities`).

### `ir.py`
- Ops carry a `GraphicsState` *snapshot*. Because the state is frozen, this is a reference, not a copy — verify you're comfortable that a later `p.fill()` cannot mutate an already-recorded op (it can't; `StateStack.update` replaces the object).
- `to_jsonable` emits colours as `[r,g,b,a]`, transforms as 6 floats, paths as nested lists. Floats are written by `json.dumps` — deterministic for identical inputs, which is all snapshots need.
- Internal ops (`Save … StrokePath`) have no emitter in `api.py`. That's deliberate (PROCESS "internal first"). `test_renderer_refuses_unknown_ops_loudly` proves the legacy renderer raises rather than skips if one leaks.

### `renderers/legacy_pygame.py`
- Every `_handler` is the Sprint-1 method body with `op.` in front. Diff against `git show fa5c66e:playground/renderers/pygame2d.py` to confirm nothing changed inside the drawing calls.
- `_HANDLERS` maps op type → method. An op type missing from it raises `NotImplementedError` naming the op.

### `geometry.py`
- `Transform.rotation(90).apply(1, 0) == (0, 1)`: with y-down this is *visually clockwise*, matching p5/DrawBot/Cairo. Say so if you'd rather the contract stated it explicitly (it will, in F2, Phase 2).
- `Path` segments are tuples, not objects — on purpose, for hashing and JSON. `quad_to` stores a cubic so renderers need one curve kind.

### `tests/conftest.py`
- `LiveCanvas.get_at` calls `_render()` first. This is the only change that touched the 42 semantic tests, and it touched their *fixture*, not their assertions (`git diff 07c9faa..HEAD -- tests/test_semantics.py` is empty).

### Spike 07 (evidence, not code)
- All three adapters consume `playground.ir` directly (`scenes.py` puts the repo root on `sys.path`). Compare `cairo_A_primitives_640x400.png` with `blend2d_…` and `skia_…`: identical.
- The Blend2D adapter keeps a CTM in Python and transforms paths itself; it *ignores* `ClipPath` and counts it (`unsupported_ops`). Scene B's Blend2D number is therefore marked † in the tables.
- `results_skia.json → sanity_C_scene_variants_ms` is the check that Skia's slowness isn't the adapter.

## 4. Things I would flag

1. **Every Spike 07 draw time includes Python walking the IR.** It is equal across engines and a few ms at teaching scale, but if someone reads "Cairo 70 ms for 2500 ops" as the engine's cost alone, that's ~2× too pessimistic.
2. **`ir.Text` is a temporary op.** The vector adapters raise on it by design; the text subsystem (S-029, Phase 2) turns it into `FillPath` ops. Until then only the legacy renderer draws text — which is fine because it is the only renderer until Sprint 3, when S-029's outline route must land alongside the vector renderer or text disappears. This is the one Sprint 3 ordering constraint worth writing down.
3. **Snapshots are exact JSON.** A refactor that changes float formatting (e.g. `640/2` → `320` int) would fail them without any behaviour change. Acceptable — a snapshot failure should be looked at, and regeneration is one env var — but be aware.
4. **Scene E used DejaVu Sans for Devanagari** and rendered boxes: scene bug, not an engine or font-route defect (Spike 06 covered Devanagari with the right font).

## 5. Open decision

**D-011 — interactive 2D engine.** Presented in full in `Decision_Log.md` § Open (context, four
options, trade-off table, recommendation D and what would change it). It blocks Sprint 3.

## 6. Sign-off checklist

- [ ] 153 tests pass; goldens unchanged since `18a5d21`; 11 snapshots present
- [ ] One sketch run in a real window behaves as before
- [ ] `sketch.py::run_namespace` differs from Sprint 1 only by `_render()` before `present()`
- [ ] Legacy renderer handlers are verbatim Sprint-1 drawing code
- [ ] `test_semantics.py` assertions unchanged (fixture-only change)
- [ ] Architecture v2 reads as the current truth (decided vs open is clear)
- [ ] D-011 decided, or explicitly deferred with Sprint 3 blocked
