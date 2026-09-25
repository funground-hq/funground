# Sprint 5 — Phase 2b: vocabulary, events, helpers (first half of release v0.7)

**Dates:** opens on the maintainer's word, after Sprint 4 sign-off.
**Release context (D-015):** Phase 2 ships as **v0.7** after Sprint 6. Its deliverables are the
code, **a User Guide**, and **an Examples Gallery that highlights every feature**. Both are built
*incrementally*: every feature story in Sprints 5–6 ships its gallery example and its guide
section in the same story (new Definition of Done rule), and Sprint 6 finishes and releases them.

**Goal:** the drawing vocabulary, colour, input events, helpers and loop control that a typical
p5/Processing 2D sketch uses — each with pinned semantics, tests, a gallery example and a guide
section — plus the gallery and guide foundations and the Sprint 4 follow-ups.

**Checkpoint:** all existing goldens and IR snapshots unchanged (everything is additive); every
new public name has a contract row, tests, a gallery example with golden + snapshot, and a guide
section; the guide and gallery build from the code (screenshots generated headless).

**Decisions:** none open at start. Sprint opened 25 Sept 2026; D-016 decided the same day.
**To be presented before the story that needs it:**
- ~~D-016 event-callback naming~~ — **decided 25 Sept 2026**: callbacks `mouse_pressed()` etc. (p5 names,
  snake_case); live booleans `is_mouse_pressed`, `is_key_pressed`. Approved contract change to v0.5.
- **D-018 curve naming** (before S-074): our Sprint-4 `curve_vertex` is a Bézier, but Processing/p5 use
  that name for Catmull-Rom curves through points.
- **D-017 colour-mode scope** (before S-044): whether `color_mode()` changes how *every* colour
  argument is read (p5/Processing behaviour) or only `p.color()`.

## Ordering

1. Foundations: S-040 (verify the Feature Map — may add or drop items below), S-068 (gallery),
   S-069 (guide skeleton), S-067 (Sprint 4 follow-ups), S-070 (version bump).
2. Features, in dependency order: S-041 → S-042 → S-043 → S-074 → S-046 → S-047 → S-048 → S-044 → S-045.
3. Close: S-058 (ADR-003), sprint review and reviewer's guide.

`text_align` and text metrics (formerly S-049) move to Sprint 6, where multi-line text layout
lives; alignment is designed once for both.

## Story set

### S-040 Verify the Feature Map against the live references — E-23 ✅
**Result (25 Sept 2026, p5.js 2.3.3 / Processing 4 / DrawBot 3.132):** one conflict (our `curve_vertex` is a Bézier; in Processing/p5 `curveVertex`/`splineVertex` is Catmull-Rom → **D-018**) and small gaps: `quadratic_vertex`, contours, `bezier()`/`curve()` shapes, `clear()`, `no_clip()`, `mouse_clicked()`, date/time helpers. Scope changes below: new story **S-074**; `clear`/`no_clip` added to S-041; `mouse_clicked` to S-045; date/time to S-048.
- [x] S-040.1 Check `docs/backlog/Feature_Map.md` against the current p5.js, Processing 4 and DrawBot 3.x references; mark corrections
- [x] S-040.2 Adjust Sprint 5–6 story scope if the check finds gaps; note changes in this file
*Acceptance:* Feature Map carries a "verified on <date> against <versions>" line; any scope change is listed here before feature work starts.

### S-067 Sprint 4 follow-ups — E-10 / E-11 / E-13 ✅
- [x] S-067.1 Contract F2 wording: only *pushed* state is unwound at frame end; a bare `p.fill()` in `draw()` carries to the next frame (as in p5). Update the row and its "Test coverage" paragraph
- [x] S-067.2 `p.clip()` with an empty path: warn (`PlaygroundWarning`) and ignore, instead of silently clipping everything; test
- [x] S-067.3 Linux window route: take the SDL high-DPI `pygame.Window` route only when it can matter (Wayland / an explicit opt-in), keep plain `set_mode` on X11; tests with simulated platforms
- [x] S-067.4 Minor verifier items: direct unit test for `StateStack.unwind()`; "lowercase colour names" wording in the reference relaxed; `delta_time` gets a full reference example
*Acceptance:* the Sprint 4 review's open verifier findings are closed or explicitly carried.

### S-068 Examples Gallery foundation — E-22
- [ ] S-068.1 `examples/gallery/<area>/NN_name.py` — plain, deterministic learner sketches (no mouse/keyboard dependence unless the example is about input, in which case it must still render a sensible frame headless)
- [ ] S-068.2 Tests discover the gallery as well as `examples/session1`: every gallery sketch runs headless, has a golden and an IR snapshot (extend `tests/conftest.py`, `test_examples_golden.py`, `test_ops_snapshot.py`)
- [ ] S-068.3 `tools/make_gallery.py`: renders every gallery sketch headless with `p.save()` to `docs/gallery/images/`, and writes `docs/gallery/README.md` — an index grouped by area with image, one-line description and a link to the source
- [ ] S-068.4 Seed the gallery with the features that already exist (shapes, colour, fill/stroke, text, animation, transforms, `saved_state`, paths, clipping, `text_width`, `save`), re-using the Session-1 and reference sketches where they fit
- [ ] S-068.5 A test that every public name in `playground.__all__` is used by at least one gallery example — fails until the gallery covers the API; the list of uncovered names is the gallery backlog
*Acceptance:* `python tools/make_gallery.py` regenerates the gallery index and images unchanged; the coverage test passes for every name that exists at sprint end.

### S-069 User Guide skeleton and first chapters — E-22
- [ ] S-069.1 `docs/guide/` in Markdown, one file per chapter, `docs/guide/README.md` as the table of contents. Planned chapters: 1 Getting started · 2 The sketch: `setup`, `draw`, `run` · 3 Shapes · 4 Colour · 5 Fill, stroke and lines · 6 Text · 7 Animation and time · 8 Transforms and `saved_state` · 9 Paths and clipping · 10 Interaction: mouse and keyboard · 11 Randomness and noise · 12 Useful maths · 13 Saving your work · 14 Coming from p5/Processing · 15 Coming from DrawBot
- [ ] S-069.2 Write chapters for features that exist now (1, 2, 3 partial, 5 partial, 6, 7, 8, 9, 13), each with runnable snippets and images generated from gallery sketches
- [ ] S-069.3 Guide ↔ reference ↔ gallery cross-links: the guide teaches, the Quick Reference is for lookup, the gallery shows
- [ ] S-069.4 A test that every code snippet in the guide marked as runnable executes headless without error
*Acceptance:* a newcomer can go from install to a saved PNG using chapters 1–2 alone; snippet test green.

### S-070 Version bump for the v0.7 cycle — E-02 ✅ (8a47e88)
- [x] S-070.1 `__version__` and `pyproject.toml` → `0.7.0.dev0`; Quick Reference title follows the release (renamed at release in Sprint 6)
*Acceptance:* one commit, suite green.

### S-041 Remaining basic shapes — E-24
- [ ] S-041.1 `square(x, y, size)` (top-left, like `rect`), `triangle(x1, y1, x2, y2, x3, y3)`, `quad(...)` (4 points), `polygon(points)` (list of `(x, y)`, closed)
- [ ] S-041.2 `arc(x, y, w, h, start, stop, mode="open")` — centre-anchored like `ellipse`, angles in **degrees** (D-002), clockwise on screen; modes `open` / `chord` / `pie`
- [ ] S-041.4 `clear()` (transparent background — keeps alpha in PNG export) and `no_clip()` (from S-040)
- [ ] S-041.3 All emit existing IR ops (paths); contract rows added; tests; gallery example `shapes/`; guide chapter 3 completed
*Acceptance:* each shape matches its contract row pixel-for-pixel in tests; exports to PDF.

### S-042 Stroke styles and smoothing — E-24
- [ ] S-042.1 `stroke_cap("round"|"square"|"butt")`, `stroke_join("round"|"miter"|"bevel")`, `miter_limit(n)`, `stroke_dash(pattern, offset=0)` / `no_dash()` — part of `GraphicsState`, so `push/pop` and `saved_state` restore them
- [ ] S-042.2 `no_smooth()` / `smooth()` — anti-aliasing opt-out for pixel-art sketches (contract C6 gets an exception clause)
- [ ] S-042.3 IR: stroke style carried in the op's style; Cairo renderer honours it; defaults stay round/round (D-004) so no existing golden moves
- [ ] S-042.4 Tests; gallery `lines/`; guide chapter 5 completed
*Acceptance:* existing goldens byte-identical; each style visibly and testably distinct.

### S-043 Shear and matrices — E-10
- [ ] S-043.1 `shear_x(degrees)`, `shear_y(degrees)`, `apply_matrix(a, b, c, d, e, f)`, `reset_matrix()` — all through `ir.Concat` / a reset op
- [ ] S-043.2 Contract F2 extended; tests; gallery `transforms/`; guide chapter 8 addendum
*Acceptance:* `apply_matrix` with a rotation matrix equals `rotate` pixel-for-pixel.

### S-046 Mapping and interpolation helpers — E-27
- [ ] S-046.1 `map_range(value, start1, stop1, start2, stop2, clamp=False)` (named to avoid shadowing Python's `map` in `from playground import *`), `lerp`, `norm`, `mag`, `random_gaussian(mean=0, sd=1)`, `random_choice(seq)`
- [ ] S-046.2 All deterministic under `random_seed`; tests; gallery `maths/`; guide chapter 12
*Acceptance:* same seed, same sequence, across `random`, `random_gaussian` and `random_choice`.

### S-047 Noise — E-27
- [ ] S-047.1 `noise(x, y=0, z=0)` returning 0–1, `noise_seed(n)`, `noise_detail(octaves, falloff)` — p5-compatible octave behaviour, pure Python, deterministic
- [ ] S-047.2 Performance: 10 000 samples per frame within a few ms, or a note and a cached/vectorised path
- [ ] S-047.3 Tests (determinism, range, continuity); gallery `noise/` (landscape line, flow field, texture); guide chapter 11
*Acceptance:* same seed gives the same field on every platform.

### S-048 Loop control and time — E-29
- [ ] S-048.1 `no_loop()`, `loop()`, `redraw()` — the window stays open and responsive when not looping; `is_looping()`
- [ ] S-048.2 `millis()` (since `run()` started), `frame_rate()` (measured fps, live), `exit()` (alias semantics of `stop()` documented); `second()`, `minute()`, `hour()`, `day()`, `month()`, `year()` (from S-040)
- [ ] S-048.3 Tests with the headless platform; gallery `animation/`; guide chapter 7 completed
*Acceptance:* a `no_loop()` sketch draws exactly once and still responds to `redraw()`.

### S-044 Colour modes and colour objects — E-25 *(needs D-017)*
- [ ] S-044.1 `color(...)` returns a Playground colour object with `red/green/blue/alpha/hue/saturation/brightness/lightness` getters; accepted everywhere a colour is
- [ ] S-044.2 `color_mode("rgb"|"hsb"|"hsl", max1=255, max2=..., max3=..., max_a=...)` with the scope decided by D-017
- [ ] S-044.3 `lerp_color(c1, c2, t)`
- [ ] S-044.4 Contract S1 extended; tests; gallery `colour/`; guide chapter 4
*Acceptance:* every v0.5 colour form still parses unchanged (frozen API).

### S-045 Input events — E-26 *(D-016 decided)*
- [ ] S-045.0 Contract change (D-016): live value `mouse_pressed` → `is_mouse_pressed`; `p.mouse_pressed` raises an AttributeError naming the new name; update `08_mouse.py`, contract I1, API contract test, Quick Reference, snapshots if their serialised names change
- [ ] S-045.1 Live values: `pmouse_x`, `pmouse_y`, `mouse_button` (`"left"|"right"|"center"|None`), `key` (last character), `key_code`, `is_key_pressed`
- [ ] S-045.2 Callbacks discovered by name like `setup`/`draw`: `mouse_pressed`, `mouse_released`, `mouse_moved`, `mouse_dragged`, `mouse_clicked`, `mouse_wheel(delta)`, `key_pressed`, `key_released`, `key_typed`
- [ ] S-045.3 Platform: events from pygame queued per frame and dispatched after input sampling, before `draw()`; headless platform supports scripted events for tests
- [ ] S-045.4 Tests with scripted events; gallery `interaction/` (paint program, keyboard mover); guide chapter 10
*Acceptance:* callbacks fire once per event in order; polling via `is_mouse_pressed` and `key_down` works; the old name fails with a helpful message.

### S-074 Curve vocabulary aligned with Processing/p5 — E-11 *(needs D-018)*
- [ ] S-074.1 Apply D-018 to the existing `curve_vertex` (Sprint 4): rename or change meaning; update contract F3, tests, `14_paths.py`, reference and guide
- [ ] S-074.2 `bezier_vertex(cx1, cy1, cx2, cy2, x, y)`, `quadratic_vertex(cx, cy, x, y)`, Catmull-Rom `curve_vertex(x, y)` / `spline_vertex(x, y)` per D-018, `curve_tightness(t)`
- [ ] S-074.3 `begin_contour()` / `end_contour()` for holes (non-zero fill with reversed winding, contract F3 extended)
- [ ] S-074.4 One-call shapes `bezier(x1, y1, cx1, cy1, cx2, cy2, x2, y2)` and `curve(...)`; `bezier_point(a, b, c, d, t)`, `bezier_tangent(...)`
- [ ] S-074.5 Tests; gallery `curves/`; guide chapter 9
*Acceptance:* a Processing curve sketch ports with only snake_case renames.

### S-058 ADR-003: deliberately out of scope — E-23
- [ ] S-058.1 `docs/design/ADR-003-out-of-scope.md`: CMYK/print colour; sound synthesis; large filter libraries; Processing data/serial/network/video libraries; 3D before 1.0; browser before 1.0 (D-014) — each with the reason and what a learner uses instead
*Acceptance:* referenced from the Roadmap and the guide's "Coming from…" chapters.

### S-039 CI first run — E-02 *(carried; blocked until a git remote exists)*

## Out of scope this sprint
Gradients, blend modes, off-screen canvas, multi-line text and `text_align` (Sprint 6); images and documents (Phase 3).
