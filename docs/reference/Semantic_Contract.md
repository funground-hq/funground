# Playground Public Semantic Contract

**Status:** Phase 0 deliverable — every "v0.5 verified" cell was checked against `src_v0.5/playground/_core.py`
and by probe on the Windows teaching machine (24 Sept 2026). All rows are pinned; the ones that
change learner-visible output (C6, S2, S4) took effect together when Cairo became the renderer in
Sprint 3, with one deliberate golden regeneration (commit noted in `sprints/sprint-03/review.md`). Decisions are indexed in `Decision_Log.md`
(`D-nnn`). Tests: `tests/test_semantics.py` pins the *v0.5 verified* column today and moves to the
*v0.6 rule* column in the same change that applies it.

The rule, from the architecture document: *Playground owns concepts and public semantics; libraries
provide capabilities.* This table is what "owns" means.

## Coordinates and units

| # | Semantic | v0.5 verified behaviour | v0.6 rule | Status |
|---|---|---|---|---|
| C1 | Origin / axes | (0, 0) top-left; +x right; +y down | Same | Pinned |
| C2 | Units | Logical pixels; `p.width`/`p.height` are exactly the values passed to `p.size()` | Same | Pinned |
| C3 | HiDPI | **Process is DPI-unaware.** On this 1920×1080 display at 125 % scaling Windows bitmap-stretches the 640×400 window (blurry); learners never see physical pixels | Logical coordinates unchanged; the renderer draws at physical resolution behind a scale transform, so shapes are crisp. `p.width` stays logical | Pinned — **Windows verified** (S-024, per-monitor DPI awareness, window at physical size). **macOS / Linux: code path only, unverified on real hardware** (S-038): on macOS, and on Linux only in a Wayland session (or with `PLAYGROUND_HIGHDPI=1`; plain X11 keeps `set_mode`, S-067), the window is opened with SDL's `ALLOW_HIGHDPI` flag (`pygame.Window(allow_high_dpi=True)`) and the scale is the drawable-surface / window-size ratio, mouse already in logical units; exercised only by simulated-2× unit tests until a maintainer with a Retina / Wayland machine confirms it. Dummy driver always 1.0; `PLAYGROUND_BACKING_SCALE` overrides everywhere |
| C4 | `rect(x, y, w, h)` | (x, y) is the top-left corner | Same | Pinned |
| C5 | `ellipse(x, y, w, h)` / `circle(x, y, d)` | (x, y) is the centre; circle takes a **diameter** | Same | Pinned |
| C6 | Sub-pixel positions | circle/ellipse/rect/point round every coordinate to the nearest integer; `line` passes floats through | Fractional coordinates honoured; edges anti-aliased. Visible change (edges soften); goldens regenerated once in Sprint 3 | Pinned (D-005) — in effect since Sprint 3 |

## Colour, fill and stroke

| # | Semantic | v0.5 verified behaviour | v0.6 rule | Status |
|---|---|---|---|---|
| S1 | Colour forms | Passed straight to pygame-ce: X11-style names, `(r,g,b)`, `(r,g,b,a)`, `[..]`, `"#RRGGBB"`, `"#RRGGBBAA"`, `"0xRRGGBB"`; components 0–255. Undocumented but working: `pygame.Color` objects and packed ints `0xRRGGBBAA` | Same forms, **including the undocumented ones** (frozen API): any object with `r/g/b[/a]` attributes is accepted by duck-typing, packed ints are decoded as pygame does — no pygame import needed. Playground parses everything into its own RGBA and **bundles the pygame-ce name table** so names render identically on every backend and cannot change under us | Pinned |
| S2 | Alpha | **Silently dropped** — `(0,0,255,64)` draws opaque blue on the window | Alpha honoured: translucent fills and strokes, 0–255 | Pinned (D-003) — in effect since Sprint 3 |
| S3 | Default style | fill `"white"`, stroke `"black"`, `stroke_width` 1, `text_size` 20 | Same | Pinned |
| S4 | Stroke alignment | **Inside** the geometry: `rect(20,20,40,40)` with width 6 paints x = 20…25; nothing outside the edge | Stroke **centred** on the edge (half outside, half inside), as in p5, DrawBot, SVG, PDF. At the default width of 1 the difference is imperceptible | Pinned (D-004) — in effect since Sprint 3 |
| S5 | Draw order | Fill first, stroke on top | Same | Pinned |
| S6 | `stroke_width(n)` | Integer, minimum 1, `ValueError` below | Same validation; floats ≥ 1 accepted additively | Pinned |
| S7 | `point(x, y)` | A filled dot in the stroke colour, radius `max(1, stroke_width // 2)` | A dot of diameter ≈ `stroke_width` | Pinned |
| S8 | `no_fill()` / `no_stroke()` | Nothing drawn for that part; `line` and `point` use stroke only | Same | Pinned |
| S9 | `background(color)` | Fills the whole canvas, ignores stroke/fill | Same | Pinned |

## Text

| # | Semantic | v0.5 verified behaviour | v0.6 rule | Status |
|---|---|---|---|---|
| T1 | Anchor | (x, y) is the **top-left** of the rendered glyph box | Same | Pinned |
| T2 | Font | pygame's bundled `freesansbold.ttf` via `Font(None, size)`; no way to choose a font | **DejaVu Sans** (Bitstream Vera licence, 757 KB) bundled with Playground. Mechanism: glyph outlines read by fontTools, positioned by uharfbuzz, emitted as path ops in the IR — deterministic on every platform and renderer. Known limitation, accepted: exported PDFs carry outlines, not searchable text, until fonts are embedded (S-032) | Pinned (D-006, D-009) — in effect since Sprint 3 |
| T3 | Size | pygame `Font(None, size)` semantics (size 20 → ~13 px glyph height) | **`text_size(n)` is an n-pixel em** in logical pixels — the CSS/p5/DrawBot convention. Text therefore renders ~1.4× larger than v0.5 at the same number; a deliberate, one-time change | Pinned (D-012) — in effect since Sprint 3 |
| T4 | Colour | explicit `color=` → current fill → current stroke → white | Same | Pinned |
| T5 | Message | Any object; `str()` is applied | Same | Pinned |
| T6 | Measurement | — (v0.5 had no way to measure text) | `text_width(message)` returns the **advance width** of `str(message)` in logical pixels at the current `text_size`: the shaped run's kerned advance (T2), exactly the distance `text()` moves its pen, so `text(msg, (width - text_width(msg)) / 2, y)` centres it. Independent of the transform stack (`scale(2)` doubles the drawing, not the number); `""` → `0.0` | Pinned (S-037, Sprint 4) |

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
| F2 | Transform state | `translate(dx, dy)` / `rotate(degrees)` / `scale(s)` / `scale(sx, sy)` are **cumulative**: each multiplies the current transform (local geometry first, so `translate` then `rotate` turns about the new origin, and the reverse order rotates the translation too) and applies to **all later geometry and text** (images when they arrive) until restored. `push()` saves the transform **and** the style (fill, stroke, stroke width, text size) on one stack; `pop()` restores both — restore restores everything. `with p.saved_state():` is push on entry, pop on exit, exception-safe. **Transforms reset at the start of every `draw()`** (as in p5/Processing): a `translate`/`rotate`/`scale` never carries into the next frame, pushed or not. **Style does not reset**: a `fill()`/`stroke()`/`text_size()` set inside `draw()` *without* a push stays current for the next frame, exactly as in p5/Processing (S3); only state saved by an open `push()` is unwound. Safety: pushes left open at the end of `draw()` are popped by Playground with a `PlaygroundWarning` naming the count; a `pop()` without a `push()` warns and is ignored; `scale(0)` is a `ValueError` at the call site. `background()` ignores the transform (S9) | Pinned (S-027, Sprint 4) |
| F3 | Shapes, paths and clipping | `begin_shape()` / `vertex(x, y)` / `curve_vertex(cx1, cy1, cx2, cy2, x, y)` / `end_shape(close=False)` build a shape from its corners; `p.path()` returns a reusable builder (`move_to`, `line_to`, `curve_to`, `quad_to`, `close`, each returning the builder) drawn with `draw_path(path)`. Both use the **current fill and stroke** (S3, S8) at the moment they are drawn, fill first then stroke (S5), stroke centred (S4). **Fill rule is non-zero (winding)**: a self-crossing outline such as a pentagram is filled right through its centre. **Open shapes are stroked, never filled**: a shape or path is filled only when it is closed (`end_shape(close=True)`, or every sub-path of a `p.path()` ends with `close()`); a fill that is set but unused is not an error. `quad_to` is stored as its exact cubic equivalent, so every backend needs one curve kind. `clip(path)` limits all later drawing to the inside of the path (implicitly closed, same fill rule) and follows the current transform; it is **lifted by the `pop()` of the enclosing `push()`** / end of the `with p.saved_state():` block, and, like transforms, never survives into the next `draw()` (F2). `background()` ignores the clip (S9). A shape left open at the end of `draw()` is dropped with a `PlaygroundWarning`; `vertex()`/`end_shape()` outside `begin_shape()`, `begin_shape()` twice, or `curve_vertex()` before the first `vertex()` are `RuntimeError`s at the call site | Pinned (S-028, Sprint 4) |
| F4 | `rect`/`ellipse` mode switches | Not offered; anchoring is fixed as above (one rule, no `rectMode`). *(Was F3 until Sprint 4 gave F3 to paths, as the sprint plan numbered it.)* | Proposed |
| S11 | Stroke styles (S-042) | `stroke_cap("round"\|"square"\|"butt")` — `square` extends half the stroke width past the end, `butt` stops flat (DrawBot/SVG names; Processing's `SQUARE` is our `"butt"`, its `PROJECT` our `"square"`). `stroke_join("round"\|"miter"\|"bevel")`; `miter_limit(n)`, n ≥ 1, default 10. `stroke_dash(pattern, offset=0)` with one length or a list, `no_dash()`. All are **style**: saved by `push`/`saved_state`, carried across frames like `fill`. Defaults round/round, no dash (D-004 look). Unknown names → `ValueError` listing the choices | Pinned (Sprint 5) |
| C6a | `no_smooth()` / `smooth()` (S-042) | Exception to C6: after `no_smooth()` edges are hard (no anti-aliasing) for fills, strokes and text, from that point in the frame and in every later frame until `smooth()`. A **sketch setting**, not style: `pop()` does not undo it, as in p5 | Pinned (Sprint 5) |
| F5 | More shapes (S-041) | `square(x, y, size)` is placed by its **top-left** corner like `rect`. `triangle`, `quad` (corners in order) and `polygon(points)` (a list of `(x, y)`, at least two) are **closed** shapes: filled, then stroked. Errors at the call site for malformed points | Pinned (Sprint 5) |
| F6 | `arc(x, y, w, h, start, stop, mode="open")` | Centred like `ellipse`. Angles in **degrees**, measured from +x and turning **clockwise on screen** (90 = straight down, F1). If `stop < start`, 360 is added until it is not; a sweep over 360 is clamped to a full turn. Modes: `"open"` fills the chord area but strokes only the curve (as in p5); `"chord"` closes with a straight line; `"pie"` closes through the centre. Unknown mode → `ValueError` | Pinned (Sprint 5) |
| F7 | `clear()` and `no_clip()` | `clear()` sets every pixel to fully transparent, ignoring transforms and clips like `background`; the window shows transparency as black, a saved PNG keeps it. `no_clip()` removes all clipping until the enclosing `pop()` / end of the `saved_state` block, which brings the previous clip back | Pinned (Sprint 5) |

## Test coverage

Every *Pinned* row above has at least one test: v0.5 rows in `tests/test_semantics.py` / `tests/test_api_contract.py`, F2 in `tests/test_transforms.py`, F3 in `tests/test_paths.py`, F5–F7 in `tests/test_shapes.py`, S11/C6a in `tests/test_strokes.py`, T6 in `tests/test_text.py`, C3 in `tests/test_hidpi.py`;
the Session-1 sample suite (`examples/session1/`, `tests/test_examples_golden.py`) guards the
combined behaviour with exact golden images. A row whose *v0.6 rule* differs from its *v0.5
verified* column (C6, S2, S4, T2) changes its test in the same commit that applies it (Sprint 3).
