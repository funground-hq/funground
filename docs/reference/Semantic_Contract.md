# Playground Public Semantic Contract

**Status:** Phase 0 deliverable — every "v0.5 verified" cell was checked against `src_v0.5/playground/_core.py`
and by probe on the Windows teaching machine (24 Sept 2026). All rows are pinned; the ones that
change learner-visible output (C6, S2, S4) take effect together when Cairo becomes the renderer in
Sprint 3, with one deliberate golden regeneration. Decisions are indexed in `Decision_Log.md`
(`D-nnn`). Tests: `tests/test_semantics.py` pins the *v0.5 verified* column today and moves to the
*v0.6 rule* column in the same change that applies it.

The rule, from the architecture document: *Playground owns concepts and public semantics; libraries
provide capabilities.* This table is what "owns" means.

## Coordinates and units

| # | Semantic | v0.5 verified behaviour | v0.6 rule | Status |
|---|---|---|---|---|
| C1 | Origin / axes | (0, 0) top-left; +x right; +y down | Same | Pinned |
| C2 | Units | Logical pixels; `p.width`/`p.height` are exactly the values passed to `p.size()` | Same | Pinned |
| C3 | HiDPI | **Process is DPI-unaware.** On this 1920×1080 display at 125 % scaling Windows bitmap-stretches the 640×400 window (blurry); learners never see physical pixels | Logical coordinates unchanged; the renderer draws at physical resolution behind a scale transform, so shapes are crisp. `p.width` stays logical | Pinned intent; implement in Phase 1–2 |
| C4 | `rect(x, y, w, h)` | (x, y) is the top-left corner | Same | Pinned |
| C5 | `ellipse(x, y, w, h)` / `circle(x, y, d)` | (x, y) is the centre; circle takes a **diameter** | Same | Pinned |
| C6 | Sub-pixel positions | circle/ellipse/rect/point round every coordinate to the nearest integer; `line` passes floats through | Fractional coordinates honoured; edges anti-aliased. Visible change (edges soften); goldens regenerated once in Sprint 3 | Pinned (D-005) — applies when Cairo lands |

## Colour, fill and stroke

| # | Semantic | v0.5 verified behaviour | v0.6 rule | Status |
|---|---|---|---|---|
| S1 | Colour forms | Passed straight to pygame-ce: X11-style names, `(r,g,b)`, `(r,g,b,a)`, `[..]`, `"#RRGGBB"`, `"#RRGGBBAA"`, `"0xRRGGBB"`; components 0–255 | Same forms. Playground parses them into its own RGBA and **bundles the pygame-ce name table** so names render identically on every backend | Pinned |
| S2 | Alpha | **Silently dropped** — `(0,0,255,64)` draws opaque blue on the window | Alpha honoured: translucent fills and strokes, 0–255 | Pinned (D-003) — applies when Cairo lands |
| S3 | Default style | fill `"white"`, stroke `"black"`, `stroke_width` 1, `text_size` 20 | Same | Pinned |
| S4 | Stroke alignment | **Inside** the geometry: `rect(20,20,40,40)` with width 6 paints x = 20…25; nothing outside the edge | Stroke **centred** on the edge (half outside, half inside), as in p5, DrawBot, SVG, PDF. At the default width of 1 the difference is imperceptible | Pinned (D-004) — applies when Cairo lands |
| S5 | Draw order | Fill first, stroke on top | Same | Pinned |
| S6 | `stroke_width(n)` | Integer, minimum 1, `ValueError` below | Same validation; floats ≥ 1 accepted additively | Pinned |
| S7 | `point(x, y)` | A filled dot in the stroke colour, radius `max(1, stroke_width // 2)` | A dot of diameter ≈ `stroke_width` | Pinned |
| S8 | `no_fill()` / `no_stroke()` | Nothing drawn for that part; `line` and `point` use stroke only | Same | Pinned |
| S9 | `background(color)` | Fills the whole canvas, ignores stroke/fill | Same | Pinned |

## Text

| # | Semantic | v0.5 verified behaviour | v0.6 rule | Status |
|---|---|---|---|---|
| T1 | Anchor | (x, y) is the **top-left** of the rendered glyph box | Same | Pinned |
| T2 | Font | pygame's bundled `freesansbold.ttf` via `Font(None, size)`; no way to choose a font | **DejaVu Sans** (Bitstream Vera licence, 757 KB) bundled with Playground. Mechanism: glyph outlines read by fontTools, positioned by uharfbuzz, emitted as path ops in the IR — deterministic on every platform and renderer. Known limitation, accepted: exported PDFs carry outlines, not searchable text, until fonts are embedded (S-032) | Pinned (D-006, D-009) |
| T3 | Size | pygame `Font(None, size)` semantics (size 20 → ~13 px glyph height) | Define `text_size` as font size in logical pixels; may shift metrics slightly | Pinned intent |
| T4 | Colour | explicit `color=` → current fill → current stroke → white | Same | Pinned |
| T5 | Message | Any object; `str()` is applied | Same | Pinned |

## Window, lifecycle and runtime

| # | Semantic | v0.5 verified behaviour | v0.6 rule | Status |
|---|---|---|---|---|
| R1 | Default window | 640×480, title `"playground"`, 60 fps, created by `run()` if `setup()` never called `size()` (Quick Reference examples use 640×400) | Same | Pinned |
| R2 | Callbacks | `setup()` optional, once; `draw()` required, repeated; found by name in the calling script's globals; non-callables raise `TypeError`, missing `draw` raises `RuntimeError` | Same | Pinned |
| R3 | `run()` | Keyword-only `fps=None`; **Phase 0 adds** keyword-only `max_frames=None` | Same | Pinned |
| R4 | Frame counting | `draw()` sees `frame_count == 0` on its first call; `frame_count` = completed frames; incremented after `draw()` | Same | Pinned |
| R5 | `delta_time` | Seconds taken by the previous frame; `0.0` during the first `draw()` | Same | Pinned |
| R6 | Stopping | Window close, Escape, or `p.stop()`; the loop ends after the current `draw()` | Same. Escape-quits stays (teaching convenience) | Pinned |
| R7 | Re-running | **v0.5 bug:** a second `p.run()` in one process crashed unless `setup()` called `size()` (dead display surface kept). Fixed in Phase 0 | Works | Pinned |
| R8 | Headless | Works with `SDL_VIDEODRIVER=dummy`; used by the test suite | A first-class headless/export mode later | Pinned |
| R9 | Errors | Drawing before `size()` → `RuntimeError` naming `p.size`; non-positive size/fps → `ValueError` | Same; unsupported-capability errors name the extra to install | Pinned |

## Input and helpers

| # | Semantic | v0.5 verified behaviour | v0.6 rule | Status |
|---|---|---|---|---|
| I1 | Mouse | `mouse_x`/`mouse_y` sampled once before each `draw()`; `mouse_pressed` = any of the first three buttons | Same | Pinned |
| I2 | Keyboard | `key_down(name)`: `left right up down space enter escape`, any single character, or a pygame key int; case-insensitive; unknown → `ValueError` | Same names; key names become Playground's, not pygame's | Pinned |
| H1 | `random(high)` / `random(low, high)` | Uniform float; **Phase 0:** uses Playground's own generator, `random_seed(seed)` makes it repeatable and never touches the learner's `import random` | Same | Pinned |
| H2 | `constrain`, `distance` | Clamp; Euclidean distance | Same | Pinned |

## Reserved for Phase 2 (not in v0.5)

| # | Semantic | Proposed rule | Status |
|---|---|---|---|
| F1 | Angle unit for `rotate()` | **Degrees**: `p.rotate(90)` is a quarter turn. `p.radians(deg)` and `p.degrees(rad)` helpers for trigonometry. No angle-mode switch | Pinned (D-002) |
| F2 | Transform state | `translate/rotate/scale` apply to all later geometry until restored; `push()`/`pop()` and `with p.state():` | Proposed |
| F3 | `rect`/`ellipse` mode switches | Not offered; anchoring is fixed as above (one rule, no `rectMode`) | Proposed |

## Test coverage

Every *Pinned* row above has at least one test in `tests/test_semantics.py` or `tests/test_api_contract.py`;
the Session-1 sample suite (`examples/session1/`, `tests/test_examples_golden.py`) guards the
combined behaviour with exact golden images. A row whose *v0.6 rule* differs from its *v0.5
verified* column (C6, S2, S4, T2) changes its test in the same commit that applies it (Sprint 3),
never before.
