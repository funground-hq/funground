# Spike results — 24 September 2026

Machine: the Windows 11 teaching machine, CPython 3.14.7, pygame-ce 2.5.8, skia-python 144.0.post2,
pycairo 1.29.1 (cairo 1.18.4), numpy 2.5.3. Every spike has its own `.venv` (python `-m venv`),
its own `spike.py`, and a `results.json` with the raw numbers. Timings are per frame, 60–120 frames
averaged, on a hidden real window (`pygame.HIDDEN`) so blit + flip cost is real, not dummy-driver.

| # | Spike | Question | Answer |
|---|---|---|---|
| 01 | `01_pygame_rotated_rect` | Can `pygame.draw` alone implement transforms + stroked paths + clipping? | **No.** See §1. |
| 02 | `02_skia_pygame_present` | Is Skia → pygame presentation overhead negligible? | **Yes** (≤ 2 ms at 1080p). Skia's *CPU draw* is the cost. See §2. |
| 03 | `03_skia_install_cost` | What does skia-python cost a classroom install? | 17 s, 3 wheels (24 MB), **~80 MB on disk, of which 54 MB is numpy**. See §3. |
| 04 | `04_dependency_revalidation` | Do the document's dependency claims hold on cp314/Windows? | Mostly. ModernGL still capped at 3.13; **resvg-py** and **pycairo** have cp314 wheels. See §4. |
| 05 | `05_skia_vs_cairo` | Same mini-renderer on Cairo and Skia — which wins? | **Cairo is ~3× faster on CPU and 40× smaller; outputs are pixel-identical for this scene.** See §5. |

---

## 1. pygame.draw as a renderer for the core model — `01_pygame_rotated_rect/`

Each case is a PNG in the spike folder. `results.json` has the per-case verdict.

| Capability the Core model needs | pygame.draw alone | What it takes |
|---|---|---|
| Rotated filled rect | ✅ | Playground does the affine math and hands `polygon()` transformed corners. pygame contributes nothing to the transform. |
| Rotated **stroked** rect | ⚠️ | `polygon(width=12)` strokes each edge as a separate thick line — **notched/gapped joins** (`02b_join_zoom.png`), no join style, stroke not centred on the path. |
| Rotated ellipse | ⚠️ | `draw.ellipse` takes an axis-aligned Rect only. Only route is Playground polygonising the curve — the flattener §4.2 says not to write. |
| Anti-aliasing | ⚠️ | `aacircle`/`aaline`/`aalines` exist; **no `aapolygon`, no `aaellipse`, no anti-aliased thick stroke at all** in pygame-ce 2.5.8. |
| Clip to a rotated shape / any path | ❌ | `Surface.set_clip` is a Rect. Anything else = mask + per-pixel compositing in Playground. |
| Rotated text | ⚠️ | Render a bitmap, then `transform.rotate` it — resampled raster, no outlines, no hinting under transform. |
| Translucent fill | ⚠️ | `draw.polygon` **silently ignores alpha** on an opaque target; needs a temporary `SRCALPHA` surface per shape. |
| Bézier curves | ❌ | No curve primitive. |

Speed is not the problem — 50 rotated stroked rects cost **0.47 ms** at 640×400. Correctness is.

**Conclusion for Issue 1 of the review:** confirmed empirically. Making `PygameRenderer` satisfy
`draw_path(path, state)` means Playground writes the transform, the flattener, the stroker and the
clipper. pygame-ce is a platform/presentation provider, not a peer vector renderer.

## 2. Skia → pygame presentation cost — `02_skia_pygame_present/`

Scene: 50 rotated stroked AA rects, a translucent oval, a full-width cubic stroke, text.
Variant B draws with `Surface.MakeRasterDirect` straight into a numpy buffer that
`pygame.image.frombuffer` wraps (zero-copy); then blit + flip on a hidden real window.

| Size | Skia CPU draw | buffer → Surface | blit + flip | **Total** | ≈ fps | pygame-only same scene (wrong output) |
|---|---|---|---|---|---|---|
| 640×400 | 6.8 ms | 0.007 ms | 0.14 ms | **6.9 ms** | 145 | 0.46 ms |
| 1280×720 | 18.9 ms | 0.012 ms | 0.78 ms | **19.7 ms** | 51 | 0.86 ms |
| 1920×1080 | 38.8 ms | 0.014 ms | 1.93 ms | **40.7 ms** | 25 | 1.40 ms |

Variant A (snapshot → `tobytes()` → `frombuffer`) adds 0.3 / 1.9 / 3.6 ms per frame — avoid it.

**Findings**
- The topology the review recommended is cheap to *present*: **≤ 2 ms at 1080p**, ~2 % of the
  frame. The other agent's "if copy/presentation overhead is negligible" condition is met.
- The real cost is **Skia's single-threaded CPU rasteriser**, scaling with pixel area: 60 fps holds
  comfortably at 640×400, exactly at 720p, and not at 1080p for a fill-heavy scene. That is an
  argument for keeping the teaching canvas ≤ 720p or for the GPU path later — not against the topology.

## 3. skia-python install cost — `03_skia_install_cost/`

Fresh venv, `--no-cache-dir`, on this machine's connection:

| | |
|---|---|
| Install time | **17.4 s** |
| Wheels downloaded | skia_python 11.3 MB + **numpy 12.7 MB** + pybind11 0.3 MB (pygame-ce for comparison: 9.8 MB) |
| Installed footprint | skia 15.2 MB + icudtl.dat 10.5 MB + **numpy 54.2 MB** + pybind11 1.2 MB ≈ **81 MB** |

**Finding the document and the other agent both missed:** `skia-python` has a hard dependency on
**numpy**. "Skia in the base install" is really "Skia + numpy in the base install" — roughly 8× the
on-disk footprint of pygame-ce alone. The other agent's table entry "Skia: 11 MB, larger" understates
this by a factor of ~7.

## 4. Dependency revalidation — `04_dependency_revalidation/pypi_snapshot.json`

Live PyPI metadata, queried today. "cp314 win" = a CPython 3.14 win_amd64 wheel (or abi3/pure-Python) exists.

| Package | Latest | Released | cp314 win | Note |
|---|---|---|---|---|
| pygame-ce | 2.5.8 | 2026-08-09 | ✅ | cp310–cp315 |
| skia-python | 144.0.post2 | 2026-03-19 | ✅ | cp38–cp314; **requires numpy** |
| pycairo | 1.29.1 | 2026-08-07 | ✅ | 0.9 MB wheel, bundles cairo 1.18.4 — no external DLL |
| moderngl | 5.12.0 | 2024-10-17 | ❌ | **still cp313 max**, no release in ~2 years — document's §8.3 claim confirmed |
| PyOpenGL | 3.1.10 | 2025-08-18 | ✅ | pure Python |
| resvg-py | 0.5.0 | 2026-08-24 | ✅ | **a maintained resvg binding with cp314 wheels exists** — resolves the review's "name the binding" item |
| resvg-python | 0.1.0 | 2024-06-09 | ❌ | stale, cp312 max — do not use |
| uharfbuzz | 0.56.2 | 2026-09-21 | ✅ | abi3 |
| fonttools | 4.66.0 | 2026-09-23 | ✅ | |
| pillow | 12.3.0 | 2026-07-01 | ✅ | 7.2 MB |
| numpy | 2.5.3 | 2026-09-06 | ✅ | 12.7 MB wheel, 54 MB installed |
| pyglet / arcade / moderngl-window | 2.1.16 / 3.3.3 / 3.1.1 | — | ✅ (pure) | alternatives for Appendix C |
| drawbot-skia | 0.5.1 | 2024-07-21 | ✅ (pure) | precedent only; last release 2 years ago |

## 5. Skia vs Cairo bake-off — `05_skia_vs_cairo/`

One scene expressed as a **list of backend-neutral ops** (`scene_ops()` — a 20-line version of the
draw-op IR the review proposed), consumed by a `CairoRenderer` and a `SkiaRenderer` of ~60 lines
each. Both implement: rect, circle, cubic Bézier, fill, stroke (round join), translate, rotate,
scale, save/restore, path clip, linear gradient, text (top-left anchored), PNG, PDF, SVG, and
zero-copy pygame presentation.

**Outputs `cairo_640x400.png` and `skia_640x400.png` are visually identical** — same geometry,
same gradient, same clip, same stroke joins, same text. That also demonstrates the IR idea works:
neither renderer ever saw a public API call.

| Size | Cairo draw | Skia draw | present (both) | Cairo ≈ fps | Skia ≈ fps |
|---|---|---|---|---|---|
| 640×400 | **3.5 ms** | 6.9 ms | 0.14 ms | 272 | 141 |
| 1280×720 | **6.4 ms** | 17.6 ms | 0.75 ms | 140 | 55 |
| 1920×1080 | **11.2 ms** | 34.6 ms | 1.9 ms | 76 | 27 |

| | Cairo (pycairo) | Skia (skia-python) |
|---|---|---|
| Wheel | 0.9 MB | 11.3 MB + numpy 12.7 MB |
| Installed | **2.0 MB** | ~81 MB |
| Extra deps | none | numpy, pybind11 |
| PDF export | ✅ 14 KB | ✅ 18 KB |
| SVG export | ✅ 29 KB | ✅ 22 KB |
| CPU raster speed (this scene) | **~3× faster** | slower; single-threaded |
| API shape for an IR consumer | Stateful context — maps 1:1 onto a state-stack IR | Paint objects per op — equally easy |
| Text | "toy" API only; real shaping needs HarfBuzz + manual glyph placement (pycairo has no pango wheel) | Built-in shaping via `skia.textlayout`, font manager, variable fonts |
| GPU future | none | Ganesh/Graphite backends (not exposed usefully in skia-python today) |
| 60 fps at 1080p on this machine | ✅ | ❌ |

**Finding:** for everything Phases 1–2 actually need (paths, transforms, clipping, gradients, AA,
PNG/PDF/SVG), Cairo is empirically **faster, 40× smaller, dependency-free, and equally correct**.
Skia's advantages are real but all live in Phase 3+ (typography stack) and Phase 4 (GPU) — the
phases the review and the other agent both agreed to mark *directional*.

That reverses the other agent's prior ("Skia is probably stronger, Cairo deserves an empirical
rejection"): the empirical result is that **Cairo, not Skia, is the natural first rasteriser**, and
it is small enough to go in the base install without the trade-off Issue 1 worried about — which
would make `IR → Cairo → pygame presentation` viable as the *default* teaching renderer, not just the
design tier. Skia can still be added later as a second IR consumer when typography or GPU demand it;
the IR is what makes that swap cheap.

---

## What this changes in the plan

1. **Issue 1's trade-off dissolves.** The base install can have one real vector rasteriser (Cairo,
   +2 MB) *and* stay small. pygame-ce becomes platform + presentation only.
2. **The renderer bake-off the other agent proposed is done**, at all three resolutions, on the
   teaching machine: `IR → Cairo → pygame` wins Phase 1–2 on every measured axis.
3. **The IR is validated** at toy scale: one op list, two renderers, identical output, and the
   adapters are ~60 lines each.
4. **Dependency table corrections for the document:** skia-python requires numpy; use `resvg-py`
   (not `resvg-python`); ModernGL is still 3.13-only; pycairo bundles cairo (no system DLL).
5. **Resolution guidance:** with any CPU rasteriser, 1080p at 60 fps is Cairo-only headroom; the
   default `p.size()` examples should stay ≤ 720p.

## Still blocked on

- **The Playground v0.5 source, Session-1 sketches and Quick Reference** are not in this repository.
  Phase 0/1 (regression suite, semantic contract check, `Sketch`/`__getattr__`, `PygamePlatform`
  extraction, IR routing) cannot start without them. A repo URL or a local path is all that's needed.

## Reference clone

`spikes/reference/drawbot-skia/` — shallow clone of justvanrossum/drawbot-skia (precedent for the
Skia adapter, `gstate.py`, `path.py`, `document.py`). Study only; not a dependency.
