# Sprint 0 review — Phase 0: Stabilise v0.5

**Date:** 24 September 2026

## Outcome

11 of 11 stories done; one task (S-008.3, first remote CI run) open because no repository remote exists.
Phase 0 exit criterion — *semantics pinned, now-or-never defects fixed, sample suite green, API frozen* —
is met except that five semantic rows are still marked DECISION (see below). Those are Sprint 1's first story.

## Test results

```
73 passed in 14.3 s   (tests/test_api_contract.py 7 · tests/test_semantics.py 42 · tests/test_examples_golden.py 24 incl. 11 goldens)
```

Second consecutive run compared all 11 goldens exactly. Windows 11, Python 3.14.7, pygame-ce 2.5.8.

## Code changes to `playground/` (all additive or defect fixes)

| Change | Kind | Learner-visible? |
|---|---|---|
| `p.random_seed(seed)`; `p.random()` uses a private generator | additive | New function only |
| `p.run(max_frames=None)` | additive | New keyword only |
| `_core.run()` → `run()` + `_run_namespace()` | internal | No |
| `_screen`/`_clock` cleared after `pygame.quit()` | defect fix | Second `p.run()` no longer crashes |
| `__version__` → `0.6.0.dev0` | metadata | Yes (was `0.5.0`) |

`src_v0.5/` is untouched and remains the baseline.

## Findings that change the plan

1. **The review's Issue 5 was partly wrong.** v0.5 already exposes live values through module
   `__getattr__` (PEP 562); there is no stale-copy problem. What stands is the single global
   `_state/_style/_screen`, which still limits the process to one sketch. Story S-013 is scoped to that.
2. **v0.5 is DPI-unaware.** On the teaching machine (1920×1080 at 125 %) Windows bitmap-stretches
   the window. New epic E-13; contract row C3.
3. **Strokes are inside the geometry; alpha is dropped; coordinates are rounded** — all verified
   and pinned as v0.5 behaviour, all things a vector renderer does differently. Contract rows S4, S2, C6
   are DECISION rows for that reason.
4. **The default window is 640×480**, not the 640×400 every Quick Reference example uses. Pinned as is.
5. **No tests, no `pyproject`, one example** existed. Phase 0 was larger than the architecture
   document assumed and is now done.
6. **Cairo beat Skia on every Phase-1/2 axis** (3× faster CPU raster, 2 MB vs 81 MB, no numpy,
   pixel-identical output). ADR-001 recommends Cairo as the first rasteriser with Skia deferred to
   the typography/GPU epics. Skia → pygame presentation overhead itself is ≤ 2 ms at 1080p.
7. **Dependency corrections for the architecture document:** skia-python hard-depends on numpy;
   use `resvg-py` (cp314 wheels) not `resvg-python`; ModernGL is still cp313-max; pycairo bundles cairo.

## Decisions taken

- Phase 0 is closed; DECISION rows move to Sprint 1 rather than blocking it.
- Extras (`playground[design]`) before any separate distribution (other agent's amendment accepted).
- Goldens are produced on Windows only; other platforms smoke-test.

## Decisions requested (Sprint 1, S-012) — *all accepted as recommended on 24 Sept 2026; see `docs/design/Decision_Log.md` D-001…D-008*

| Row | Question | Recommendation |
|---|---|---|
| S2 | Honour RGBA alpha? | Yes |
| S4 | Stroke alignment: inside (v0.5) or centred (vector norm)? | Centred |
| C6 | Honour sub-pixel coordinates with AA? | Yes |
| T2 | Which bundled default font? | An OFL font, chosen in Sprint 1 |
| F1 | Angle unit for `rotate()` | Degrees, with `p.radians()`/`p.degrees()` |
| ADR-001 | First rasteriser | Cairo (option C) |

## Retrospective

- *Went well:* measuring before deciding — two spikes reversed a prior the review and the other agent shared.
- *Went badly:* the review made a claim about live values without the source; the source arrived later and corrected it. Process rule added: source and tests outrank documents.
- *Change for next sprint:* stories are planned before the work, not recorded after it.
