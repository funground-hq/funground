# Story backlog

One row per story; tasks live in the sprint's `stories.md` once scheduled (and are mirrored
here for completed sprints so the backlog stays a full record). Status: `done` · `in progress` ·
`ready` · `blocked (reason)` · `later`.

## Sprint 0 — Phase 0: Stabilise v0.5 (done, 24 Sept 2026)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-001 | E-01 | As a maintainer I can run any learner sketch **unchanged**, headless, for N frames and capture its last frame | `tests/conftest.py::run_sketch`; `p.run(max_frames=)` | done |
| S-002 | E-01 | A Session-1 sample suite exists that covers every Quick Reference topic in plain learner code | 12 sketches in `examples/session1/` | done |
| S-003 | E-01 | Golden-image tests catch any rendering change to the sample suite | `tests/test_examples_golden.py`; 11 goldens; exact match | done |
| S-004 | E-01 | The v0.5 public API inventory and signatures are frozen as a test | `tests/test_api_contract.py` | done |
| S-005 | E-01 | Every learner-visible drawing/runtime rule is pinned by a pixel-level test | `tests/test_semantics.py` (42 tests) | done |
| S-006 | E-01 | As a learner I can make `p.random()` repeatable without affecting my own `import random` | `p.random_seed()`; own `Random` instance | done |
| S-007 | E-01 | A second `p.run()` in the same process works (v0.5 crashed when `setup()` did not call `size()`) | `test_a_second_run_in_the_same_process_works` | done |
| S-008 | E-02 | The package installs with `pip`, has a dev extra, and a CI matrix runs the suite headless on 3 OSes × Python 3.11–3.14 | `pyproject.toml`, `.github/workflows/ci.yml` | done (CI file written; not yet executed — no remote) |
| S-009 | E-03 | The public semantic contract is written from the verified source, with DECISION rows named | `docs/design/Semantic_Contract.md` | done |
| S-010 | E-08 | The renderer-topology question is answered with measurements and an ADR | spikes 01–05, `spikes/RESULTS.md`, `ADR-001` (proposed) | done |
| S-011 | E-23 | Work is organised as themes → epics → stories → tasks, in phases and sprints, with a written process | `docs/PROCESS.md`, this backlog, `sprints/` | done |

## Sprint 1 — Phase 1a: Sketch, platform, state (planned)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-012 | E-03 | The five DECISION rows in the contract are decided (S2 alpha, S4 stroke alignment, C6 sub-pixel, T2 default font, F1 angle unit) and ADR-001 is accepted | Contract rows pinned; `Decision_Log.md` D-001…D-008 | done 24 Sept 2026 (font *file* follows S-031) |
| S-031 | E-15 | **Spike 06 — deterministic text.** Can Playground render single-line text from a bundled OFL font through uharfbuzz shaping + fontTools outlines + IR path ops, at acceptable quality and speed? Narrow scope: no layout, no wrapping | Sizes 12/16/24/36/48; strings `ABC xyz 123`, `Hello, Playground!`, `AVATAR` (kerning), `office` (ligature), one non-Latin sample; measure visual quality vs pygame/Cairo toy text, baseline/anchor correctness, per-frame cost with and without an outline cache, byte-identical output across two runs and two platforms, PDF/SVG output. Result closes D-006 with a font choice | done (Sprint 1); font = DejaVu Sans (D-009) |
| S-013 | E-04 | Public functions delegate to an explicit `Sketch` instance (`_active_sketch`); live values resolve through `__getattr__` to it; two `Sketch`es can coexist in one process | New tests; all existing tests unchanged and green | done (Sprint 1) |
| S-014 | E-05 | Window, events, input sampling, clock and presentation live in `PygamePlatform` behind a `Platform` protocol | `_core.py` no longer calls `pygame.display`/`event`/`mouse`/`key`/`time` directly | done (Sprint 1) |
| S-015 | E-06 | Fill/stroke/width/text style is a Playground `GraphicsState` owned by the sketch, with `save()`/`restore()` (internal for now) | Unit tests on state stack | done (Sprint 1) |
| S-016 | E-03 | Colours are parsed once into a Playground `Color` (RGBA 0–255) using a bundled copy of the pygame-ce name table | `Color.parse("tomato") == Color(255, 99, 71, 255)`; all colour forms in contract S1 covered | done (Sprint 1) |
| S-017 | E-02 | CI fails if `pygame` is imported anywhere outside `playground/platform/` and `playground/renderers/` | AST lint test | done (Sprint 1) |

## Sprint 2 — Phase 1b: draw-op IR (planned)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-018 | E-06 | Every current primitive (`background circle ellipse rect line point text`) records a backend-neutral op instead of drawing; the IR also carries `Transform`, `Path`, clip and state ops **internally** (no public API yet — see PROCESS "internal first") | `Frame` op list; op dataclasses; `Transform`, `Path` types | ready |
| S-019 | E-06 | `LegacyPygameRenderer` consumes the op list and produces **byte-identical** goldens; it is named legacy because it is deleted in S-026 (D-008) | Sample suite green with unchanged goldens | ready |
| S-020 | E-06 | Op-list snapshot tests exist for the sample suite | `tests/test_ops_snapshot.py` | ready |
| S-021 | E-07 | Asking for an unsupported capability fails at `p.size()`/`p.run()` with a message naming the extra to install | Tests for message text | ready |
| S-022 | E-08 | ADR-001 is accepted or amended | ADR status ≠ Proposed | done 24 Sept 2026 (D-001, accepted early) |

## Sprint 3 — Phase 1c: Cairo via the IR (D-011 = D), semantic migration (done, 25 Sept 2026)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-023 | E-09 | The D-011 engine's renderer consumes the same op list and presents through `PygamePlatform`; Cairo remains the export path for PDF/SVG regardless | Spike 05/07 adapter productionised; sample suite renders | done (Sprint 3) |
| S-024 | E-13 | Rendering happens at physical resolution behind a scale; `p.width` stays logical | Crisp output at 125 % scaling on the teaching machine | done (Sprint 3) |
| S-025 | E-03 | Contract decisions D-003/D-004/D-005 (alpha, centred strokes, fractional + AA) are applied and goldens regenerated once, deliberately, with each visual change listed in the sprint review | Contract + tests + goldens in one change | done (Sprint 3) |
| S-026 | E-09 | The D-011 engine is the default interactive renderer; `LegacyPygameRenderer` and all `pygame.draw` usage are deleted (D-008) | No `pygame.draw` in the package; boundary lint updated | done (Sprint 3) |
| S-034 | E-12 | Headless run and `p.save()` to PNG/PDF/SVG through Cairo surfaces (moved forward from Sprint 4 per D-007) | Export files checked structurally + rendered | done (Sprint 3) |

## Sprint 2 — additional (planned)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-033 | E-23 | Architecture document v2 reflecting ADR-001/D-007 (and ADR-002 if D-010 = B): IR, pygame platform + presentation, interactive renderer marked OPEN with Cairo as reference implementation, export via Cairo, three-checkpoint Phase 1, text-as-outlines with `TextRun` reserved | `docs/design/Playground_Technology_Architecture_v2.md` (Markdown; the .docx stays as the v1 record) | done (Sprint 2) |
| S-035 | E-08 | **Spike 07 — renderer bake-off** (D-010 = B). Same IR stream to Cairo, Skia and Blend2D (the last only if its binding passes a coverage gate: clip, scale, fill rule, stroke join/cap). Scenes: primitive-heavy animation (500 circles + 500 rects, alpha, rotation); complex paths (100 Béziers, joins/caps, clip, nested transforms); translucency/compositing; gradients incl. conic; text via outlines route + Blend2D native font load; export replay through Cairo PDF/SVG; install size, cold import, first frame; binding-risk score | Numbers + PNGs in `spikes/RESULTS.md` §7; D-011 presented per PROCESS before Sprint 3 | done (Sprint 2); D-011 pending |

## Sprint 4 — Phase 2: public API on the vector model (planned)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-027 | E-10 | `p.translate/rotate/scale` (degrees, D-002), `p.radians/degrees`, `p.push/pop`, `with p.saved_state():` | Semantic tests; contract F2 pinned | done (Sprint 4) |
| S-028 | E-11 | `p.path()` with `move_to/line_to/curve_to/close`, fill/stroke/clip | Tests; golden sketch | done (Sprint 4) |
| S-029 | E-15 | **Done in Sprint 3** (moved forward for the S-026 ordering constraint) — text subsystem v1 (font: DejaVu Sans, D-009): `FontResource` (HarfBuzz face + fontTools glyph set + glyph-outline cache), `TextRun` (semantic text + shaped glyphs, outlines materialised for the IR) — `p.text()` unchanged for learners | Deterministic text goldens on two platforms | ready (after S-031) |
| S-030 | E-22 | Quick Reference v0.6 documents every additive API | PDF/MD regenerated | done (Sprint 4) — markdown + headless-generated images; no PDF render |

## Later (Phases 3–4, directional)

| ID | Epic | Story | Note |
|---|---|---|---|
| S-032 | E-12 | PDF exporter consumes `TextRun` and embeds/subsets the font so exported text is searchable and selectable | Accepted limitation from D-006 until then |

Other stories are cut from epics E-14 … E-21 when their phase is scheduled. Nothing here is committed.

## Tracking (engine watch)

| ID | Epic | Story | Trigger | Status |
|---|---|---|---|---|
| S-036 | E-08 | Blend2D as a gated optional renderer (`playground[fast]`): re-run Spike 07, then productionise the adapter as a second IR consumer | `blend2d-py` exposes clip + matrix + fill rule and ships macOS x86_64 wheels | tracking (D-011) |

## Sprint 4 — additional stories (planned 25 Sept 2026)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-037 | E-15 | Text polish: LRU-capped `TextRun` cache; `p.text_width()` | 10k-frame headless run keeps the cache bounded | done (Sprint 4) |
| S-038 | E-13 | macOS / Linux HiDPI via SDL high-DPI flag (unverifiable on the teaching machine) | forced-scale unit tests; documented as unverified on real hardware | done (Sprint 4) — code path only, real-hardware verification pending |
| S-039 | E-02 | First CI run on a remote; 12-cell matrix green | green badge | 7 — done (12 cells green, 30 Sept 2026) |

## Phase 2 story cuts from the Feature Map (25 Sept 2026) — Sprints 5–6, not yet scheduled

| ID | Epic | Story | Sprint |
|---|---|---|---|
| S-040 | E-23 | Verify `Feature_Map.md` against the live p5.js 2.x, Processing 4 and DrawBot 3.x references; correct the inventory | 5 — done |
| S-041 | E-24 | `square`, `triangle`, `quad`, `arc` (open/chord/pie), `polygon(points)` | 5 — done |
| S-042 | E-24 | `stroke_cap`, `stroke_join`, `stroke_dash`, miter limit; `no_smooth()` opt-out | 5 — done |
| S-043 | E-10 | `shear_x/shear_y`, `apply_matrix`, `reset_matrix` | 5 — done |
| S-044 | E-25 | `color_mode(RGB|HSB|HSL, max…)`, `color()` objects with component getters, `lerp_color` | 5 — done |
| S-045 | E-26 | `pmouse_x/y`, `mouse_button`, wheel, drag; `mouse_pressed()/mouse_released()/mouse_moved()/key_pressed()/key_released()` callbacks; `key`, `key_code` | 5 — done |
| S-046 | E-27 | `map_range`, `lerp`, `norm`, `mag`, `random_gaussian`, `random_choice` | 5 — done |
| S-047 | E-27 | `noise(x[, y[, z]])`, `noise_seed`, `noise_detail` — deterministic, seeded | 5 — done |
| S-048 | E-29 | `no_loop`, `loop`, `redraw`, `millis`, `frame_rate()` query, `exit()` | 5 — done |
| S-049 | E-15 | `text_align(h, v)`, `text_ascent/descent`, cap height; `text_width` already in S-037 | 6 — done |
| S-050 | E-25 | Linear and radial gradients for fill and stroke (IR op + Cairo + export) | 6 — done |
| S-051 | E-25 | `blend_mode`, global `opacity`, `shadow` | 6 — done |
| S-052 | E-28 | Off-screen graphics: `g = f.create_graphics(w, h)`, one picture type with images (D-021 = A); draw with the same verbs on `g`; `f.image(g, x, y)` | 6 — done |
| S-053 | E-15 | Multi-line text, `text_leading`, word-wrap in a box with alignment and overflow | 6 — done |
| S-054 | E-15 | `load_font`, `text_font`, `text_style` (bundled DejaVu family, D-022) | 6 — done |
| S-055 | E-27 | `Vector` (add, sub, mult, mag, normalize, heading, rotate, dist, lerp) | 6 — done |
| S-056 | E-19 | `save_frames(pattern, count)` sequence export (headless-friendly) | 6 — done |
| S-057 | E-29 | `cursor`/`no_cursor`, `full_screen`, `resize_canvas` | 6 — done |
| S-058 | E-23 | ADR-003 "Deliberately out of scope": CMYK/print, sound synthesis, Core-Image-scale filters, data loaders | 5 — done |

## Directional — after 1.0 (D-014)

### E-31 Playground in the browser — see `docs/design/Browser_Mode_Note.md`

| ID | Epic | Story | Status |
|---|---|---|---|
| S-059 | E-31 | Spike 08 — Pyodide feasibility (core in wasm, IR frame timings, Canvas 2D page over IR snapshots) | done (Sprint 4 lane; results in `spikes/RESULTS.md` §8) |
| S-060 | E-31 | Loop inversion: `Sketch.start()/step()/finish()`; desktop `run()` loops over `step()` | directional |
| S-061 | E-31 | `BrowserPlatform`: rAF-driven, DOM input, `devicePixelRatio` scale | directional |
| S-062 | E-31 | `Canvas2DRenderer`: every IR op → Canvas 2D | directional |
| S-063 | E-31 | Browser text: uharfbuzz-for-Pyodide vs harfbuzzjs vs fontTools-only | directional |
| S-064 | E-31 | `playground.js` loader, `<playground-run>`, GitHub launcher URL | directional |
| S-065 | E-31 | Browser export: PNG download; IR→SVG writer | directional |
| S-066 | E-31 | Classroom page: editor + canvas + share-by-URL | directional |

## Release v0.7 deliverables and Sprint 5 additions (D-015, 25 Sept 2026)

| ID | Epic | Story | Sprint |
|---|---|---|---|
| S-067 | E-10/E-11/E-13 | Sprint 4 follow-ups: F2 wording, empty-path clip warns, Linux window route narrowed, minor verifier items | 5 — done |
| S-068 | E-22 | Examples Gallery foundation: `examples/gallery/`, golden + snapshot per example, `tools/make_gallery.py`, rendered index, API-coverage test | 5 — done |
| S-069 | E-22 | User Guide skeleton and first chapters (`docs/guide/`), runnable-snippet test | 5 — done |
| S-070 | E-02 | Version `0.7.0.dev0` | 5 — done |
| S-071 | E-22 | User Guide completed for every 0.1 feature; "Coming from p5/Processing" and "Coming from DrawBot" chapters | 6 — done |
| S-072 | E-22 | Examples Gallery completed: coverage test green for all of `__all__`; curated showcase page | 11 |
| S-073 | E-02 | Release 0.1 on PyPI (D-019, moved to Sprint 11 by D-027): distribution name (D-020), packaging metadata and wheel, changelog, Quick Reference for 0.1, version `0.1.0`, tagged, CI green (needs S-039) | 6 |
| S-074 | E-11 | Curve vocabulary aligned with Processing/p5 (D-018): Bézier / quadratic / Catmull-Rom vertices, contours, `bezier()`/`curve()` shapes, `bezier_point`/`tangent` | 5 — done |
| S-075 | E-02 | Rename to `funground` (D-020): package, `pyproject`, examples, guide, reference, tests; `import funground as f`; history not rewritten | 6 — done |

## Phase 3 — part of release 0.1 (D-027, 30 Sept 2026)

| ID | Epic | Story | Sprint |
|---|---|---|---|
| S-076 | E-18 | Script mode: sketches without `draw()` (D-029) | 7 — done |
| S-077 | E-14 | `load_image` and `image()` for loaded pictures (D-028) | 7 — done |
| S-078 | E-14 | `tint` / `no_tint`; drawing part of a picture | 7 — done |
| S-079 | E-14 | Pixel access: get/set, whole-picture access | 7 — done |
| S-080 | E-14 | `copy`, `resize`, `mask`, a few filters | 7 — done |
| S-081 | E-24 | `rect_mode` / `ellipse_mode` / `image_mode` (D-030 = B) | 7 — done |
| S-082 | E-25 | `color_mode()` as in p5 (D-031 = B) and grey numbers (D-032 = B) | 7 — done |
| S-083 | E-22 | Gallery browser: a funground app to browse, read and run the examples | 7 — done |
| S-084 | E-18 | Pages and page sizes: `new_page`, `page_count`, `page_size`; multi-page PDF; `show()` flips pages | 8 — done |
| S-085 | E-18 | Script follow-ups: top-level `full_screen()`, memory note | 8 — done |
| S-086 | E-11 | Path shapes and booleans (`union`, `intersection`, `difference`, `xor`, `remove_overlap`; skia-pathops, D-037) | 9 — done |
| S-087 | E-11 | Path `expand_stroke`, `bounds`, `contains`, `translate`/`scale`/`rotate`, `copy` | 9 — done |
| S-088 | E-15 | `f.text_path()`: letters as a path | 9 — done |
| S-089 | E-24 | Rounded corners for `rect`/`square` (D-040) | 10 — done |
| S-090 | E-15 | `text_tracking`, `text_features`, `font_variations` | 10 — done |
| S-091 | E-15 | Mixed styles in one text (formatted text runs) | 10 — done |
| S-092 | E-16 | `load_svg` (D-041) | 10 — done |
| S-093 | E-15 | Spike: searchable PDF text | 10 — done (D-043 raised) |
| S-094 | E-15 | Real text in PDFs (D-043) | 10 — done |
| S-095 | E-18 | Named layers: `with f.layer("sky"):` built on pictures, stacked in order; shown/hidden by name | 12 (D-053) |
| S-096 | E-18 | PDF layers (optional content groups) that can be switched on and off in Acrobat/Illustrator; builds on S-094's PDF rewrite and on S-095 | 12 (D-053) |
| S-097 | E-15 | Real text in SVG output (`<text>` with the font embedded), as T15 does for PDF | 13 (D-049) |
| S-098 | E-17 | Sound playback: `load_sound`, play/loop/stop/pause/volume (D-046) | 11 | done
| S-099 | E-17 | Sound analysis: `level()`, `spectrum()` (D-046) | 11 | done
| S-100 | E-19 | GIF and MP4 export (D-045 for MP4) | 11 | done (ffmpeg extra waits for D-045)
| S-101 | E-30 | Controls: slider, checkbox, button (D-047) | 11 | done
| S-102 | E-15 | Font fallback (missing characters from a fallback chain) | 12 |
| S-103 | E-22 | Examples and gallery browser in the package (`python -m funground.gallery`) | 12 |
| S-104 | E-15 | `text_to_points` (p5 `textToPoints`) | 12 |
| S-105 | E-15 | `text_box` returns its overflow (DrawBot) | 12 — already done (S-053, T10) |
| S-106 | E-15 | Font information (axes, names, has characters) | 12 |
| S-107 | E-25 | `erase()` / `no_erase()` (p5) | 12 |
| S-108 | E-17 | Microphone input (pygame-ce capture) | 13 |
| S-109 | E-15 | PDF text: fill mode for solid colours | 13 |
