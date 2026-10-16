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
| S-060 | E-31 | Loop inversion: `Sketch.start()/step()/finish()`; desktop `run()` loops over `step()` | done (Sprint 19) |
| S-061 | E-31 | `BrowserPlatform`: rAF-driven, DOM input, `devicePixelRatio` scale | directional |
| S-062 | E-31 | `Canvas2DRenderer`: every IR op → Canvas 2D | directional |
| S-063 | E-31 | Browser text: uharfbuzz-for-Pyodide vs harfbuzzjs vs fontTools-only | directional |
| S-064 | E-31 | `playground.js` loader, `<playground-run>`, GitHub launcher URL | directional |
| S-065 | E-31 | Browser export: PNG download; IR→SVG writer | directional |
| S-066 | E-31 | Classroom page: editor + canvas + share-by-URL | directional |

### Release 0.2 — funground on the web (E-31 brought forward?) — candidates, no commitment

Options study: `docs/design/Web_Target_Options.md` (8 Oct 2026). Nothing below is scheduled. Whether E-31
moves into 0.2 at all supersedes D-014 and is the maintainer's decision (the note's Q1–Q10). The spikes
come first: S-133 to S-135 decide the renderer (Canvas 2D, Cairo in wasm, or both); S-136 to S-140 de-risk
the shared pieces. S-060 to S-066 above stay as the build stories, re-cut once the spikes report.

| ID | Epic | Story | Status |
|---|---|---|---|
| S-133 | E-31 | Spike: uharfbuzz as a Pyodide (`pyemscripten`) wheel; text outlines identical to native (fallback: a harfbuzzjs shim) | done (Sprint 17) |
| S-134 | E-31 | Spike: pycairo (cairo, pixman) for Pyodide; goldens byte-identical; frame time at DPR 2; wheel sizes | done (Sprint 17) |
| S-135 | E-31 | Spike: Canvas 2D renderer over all 20 IR op types; goldens within tolerance in Chrome, Firefox, Safari | done (Sprint 17) |
| S-136 | E-31 | Spike: inverted loop (`start/step/finish`) with Python in a module worker, rAF-driven, Stop by `terminate()`, no COOP/COEP | done (Sprint 17) |
| S-137 | E-31 | Spike: made sounds via Web Audio and the microphone via AudioWorklet, from a worker | Sprint 20 (as a story) |
| S-138 | E-31 | Spike: PNG/PDF/SVG/GIF from Pyodide equal to desktop files; MP4 via WebCodecs | candidate |
| S-139 | E-31 | Spike: first-load time and download budget on a real page | candidate |
| S-140 | E-31 | Spike: gallery examples as share links (compressed code in the URL fragment) | candidate |
| S-141 | E-22 | The gallery online as static pages (architecture A): picture, code, explanation per example, on GitHub Pages | done (Sprint 19) |
| S-142 | E-31 | Spike: Cairo-in-wasm and Canvas 2D timed in Chrome on the same cases (draw, frame copy, end to end, 1x and 2x) | done (Sprint 18) |
| S-143 | E-31 | Spike: profile heavy frames (Python, IR, shaping, encoding, transfer, drawing) native and in Pyodide; prototype fixes | done (Sprint 18, native half) |
| S-144 | E-31 | Style calls without copying the whole graphics state via `dataclasses.replace` | done (Sprint 19) |
| S-145 | E-31 | Colour strings parsed once (named, bounded cache) | done (Sprint 19) |
| S-146 | E-31 | Plain int/float accepted without the `numbers.Real` ABC check (Vector and peers) | done (Sprint 19) |
| S-147 | E-31 | Text outlines scaled once per glyph and size, then placed | done (Sprint 19) |
| S-148 | E-31 | Re-measure both web routes in Chrome after S-144–S-147; redo the D-075 matrix | done (Sprint 19) |
| S-149 | E-31 | Public `Path.translated(dx, dy)` (D-076) | done (Sprint 19) |
| S-150 | E-22 | The website: MkDocs Material site at funground-hq.github.io (home, guide, reference) built in Actions from `funground` (D-077) | done (Sprint 19) |
| S-151 | E-31 | The site's Play page: the browser editor (H1) once D-075 and the runner are ready | Sprint 20 (parts 1 and 2) |
| S-152 | E-31 | Browser entry point: `BrowserPlatform`, `funground.web.Session`, `f.run`/`f.show` under a host, contract row W1 | Sprint 20 |
| S-153 | E-31 | Loading Pyodide, the wheels and fonts; first-load budget | Sprint 20 |
| S-154 | E-31 | Numeric colours parsed once | Sprint 20 |
| S-155 | E-31 | The sketchbook: template repo `funground-hq/sketchbook`; learners edit and save in github.dev and see the sketch render on the same page (D-079 = C; how: S-156); desktop use from the same repo (Editor_Note.md) | Sprint 20 |
| S-156 | E-31 | Spike: funground preview beside github.dev: framing check, and a VS Code web extension whose webview runs the runner with live update, data files, sound (Editor_Note.md Q1-Q6) | Sprint 20 (done) |
| S-157 | E-31 | A second `Session` in the same Python draws exactly what a fresh one draws; say what is not reset (the test D-083 asks for before the runner reuses its Python) | Sprint 20 |
| S-158 | E-31 | The funground extension for github.dev from the S-156 spike: runner reuse (D-083, after S-157), runtime from the site in versioned folders (D-081), `'unsafe-eval'` in the panel only (D-080), a microphone message that fits a panel | Sprint 20 |

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
| S-110 | E-17 | Tones, notes, pan, create_sound, save WAV (D-055, ADR-006) | 13 |
| S-111 | E-17 | Seeing sound: wave, spectrum, pitch line, spectrogram (D-056) | 14 |
| S-112 | E-17 | Onsets and tempo (D-056) | 14 |
| S-113 | E-17 | Chroma, key and chords (D-056) | 14 |
| S-114 | E-22 | Music teaching scenarios and ragas (D-056) | 14 |
| S-115 | E-17 | Ragas for learners: synthesis and analysis, basic to intermediate (D-057) | 14 |
| S-116 | E-15 | `save(..., text="shapes")` for handoff files (D-060) | 13 |
| S-117 | E-22 | Project capstones: raga explorer, poster series, voice game, rangoli (D-063) | 14 |
| S-118 | E-17 | Sound quality across the board (D-064) | 14 |
| S-120 | E-22 | Every example explains itself: what you see, how it works, make it yours (D-065) | 15 |
| S-121 | E-22 | Four more projects with their own guide pages (D-065) | 15 |
| S-122 | E-22 | User guide solidified: read-through, exercises, errors page, glossary, learning path (D-065) | 15 |
| S-123 | E-23 | Developer docs refreshed for Sprints 11-14 (D-065) | 15 |
| S-124 | E-22 | Poster designer: a visible way to edit the headline (an on-screen "type to edit" hint or a text field control); a multi-page PDF from an animated sketch (library: pages outside scripts) | later |
| S-130 | E-23 | Typing for editors and AI tools: a `py.typed` marker; the live values (`width`, `mouse_x`, …) declared with their types under `if TYPE_CHECKING:` in `__init__.py`; a test that every public function is fully and correctly annotated (e.g. `stroke_width` takes fractions). No separate `.pyi` (from an outside AI review, 6 Oct) | moved to E-35 (14 Oct) |
| S-131 | E-21 | `f.describe()`: the canvas described in words for learners debugging, screen-reader users and AI assistants (like p5's `describe()`/`textOutput()`): a short summary by default, the full op list as JSON on request via the IR. New public API: needs a contract row and the maintainer's decision (from an outside AI review, 6 Oct) | later |

## E-32 Typographic, print-ready posters (11 October 2026) — Sprint 21

From the review of poster support: funground's typography, shapes, layout and vector export are strong; the
gaps are line breaking (justification, hyphenation), type on a path, fitting a headline, and print handoff
(resolution, bleed and marks, CMYK). Plan: `sprints/sprint-21/stories.md`.

| Story | Epic | Value · tasks · acceptance | Sprint |
|---|---|---|---|
| S-159 | E-32 | Justified text. Tasks: `"justify"` in `text_align` for `text_box` (strings, FormattedStrings), word spaces stretched, last line and lines ending a paragraph left-aligned; contract row; golden. Acceptance: a justified box's lines (but the last) end exactly at the box's right edge | 21 |
| S-160 | E-32 | Hyphenation by soft hyphens (D-085 = a). Tasks: soft hyphens (U+00AD) as break points in `text_box`, a hyphen drawn only where a line breaks there, invisible elsewhere (also in `text_width`, PDF and SVG text); works with justify and FormattedStrings; contract row; golden. Acceptance: a narrow box of long words with soft hyphens breaks at them and shows hyphens only at line ends | 21 |
| S-161 | E-32 | Type on a path. Tasks: `f.text_on_path(message, path, offset=0)` places shaped glyphs along a `Path` by arc length, each rotated to the tangent; alignment along the path; overflow beyond the path's end dropped and returned; live text in PDF/SVG; contract row; golden. Acceptance: text around a circle reads correctly and its PDF text is selectable | 21 |
| S-162 | E-32 | Fitted headline. Tasks: `f.fit_text_size(message, width, height=None)` with the current font, features, variations and tracking; contract row; tests. Acceptance: text set at the returned size measures the width within 0.5 pt | 21 |
| S-163 | E-32 | Print resolution. Tasks: `dpi=` on `f.save(".png")` (scripts, pages, animated sketches), memory check for A2 at 300 dpi; desktop and browser; contract row. Acceptance: an A3 page saves as a 3508 x 4961 PNG matching the vector drawing | 21 |
| S-164 | E-32 | Print-ready PDF. Tasks: `bleed=` and `marks=` on `f.save(".pdf")`; MediaBox grown by bleed and slug, TrimBox and BleedBox set, crop marks in registration black outside the bleed; `f.mm()`, `f.inch()`; contract row; tests read the boxes back with pypdf. Acceptance: an A4 PDF with 3 mm bleed has TrimBox 595 x 842 pt and crop marks at the trim corners | 21 |
| S-165 | E-32 | Spike: CMYK / PDF/X. Question: can funground produce a file a print shop accepts as CMYK (or PDF/X) without a heavy dependency, on Windows, macOS, Linux and in the browser? Criteria before work; options measured (e.g. a converter tool, colour-managed export); recommendation. No product code | 21 |
| S-166 | E-32 | Teaching. Tasks: guide sections (justified columns, hyphenation, type on a path, fitted headlines, preparing a file for print), four gallery examples, "Event poster series" project print-ready; Quick Reference rows. Acceptance: examples run on the desktop and in the browser editor; links checked | 21 |
| S-167 | E-32 | Later: baseline grid (text boxes snapping lines to a grid's baseline), optical margin alignment and hanging punctuation | backlog |
| S-170 | E-32 | CMYK colour model (D-087). Tasks: `f.cmyk()` colour objects (0-100; no `color_mode`, D-017); the IR keeps CMYK; Cairo draws a stand-in RGB unique in the document and the PDF step rewrites it to exact `k`/`K` operators, CMYK gradient stops and transparency groups; RGB colours tagged sRGB (ICCBased) with an sRGB output intent; marks in registration (100/100/100/100); screen/PNG/SVG approximation by formula; a leftover-RGB scan in tests; design note; contract rows. Acceptance: a PDF of CMYK fills, text and a gradient holds exactly the CMYK values written (read back), and no unintended RGB | 21 |
| S-171 | E-32 | Fractional text sizes (maintainer, 11 Oct 2026). Tasks: `text_size()` and the size in `text_font()` keep fractions (remove the pygame-era `int()`; a size of 0.5 is valid, 0 or less an error); contract T3 states it; the scaled-outline cache (S-147) reworked so continuously varying sizes stay fast (e.g. cache outlines unscaled and scale when drawing), timed before and after on a varying-size sketch; goldens and snapshots of examples with fractional sizes regenerated deliberately and listed; the typographic portrait project checked. Acceptance: `fit_text_size` then `text_size` gives text within 0.5 pt of the width; the varying-size benchmark is no slower than today | 21 |
| S-169 | E-32 | Later: dictionary hyphenation (`f.hyphenation(True, language=...)`), e.g. with `pyphen`; deferred by D-085 | backlog |
| S-168 | E-22 | Later: the browser editor's polish (toolbar buttons sized for the page; Reset shown only when the code differs), found in the live check of S-151 part 2 | backlog |

## Option constants (D-090, 11 October 2026)

| Story | Epic | Value · tasks · acceptance | Sprint |
|---|---|---|---|
| S-174 | E-23 | Named constants for every option word (D-090): flat capitals holding the words (`CENTER`, `BASELINE`, `BOLD`, `MULTIPLY`, `LEFT`, key names, cap/join, blend modes, text modes, page sizes...), exported and documented; `Literal[...]` types on every function that takes an option word (with S-130's `py.typed`); `f.colors` with the named colours as constants; contract rows; Quick Reference and guide use the constants; a test that every option word has its constant and every constant is accepted. Acceptance: `f.text_align(f.CENTRE)` is a NameError an editor underlines; `f.text_align("centre")` is underlined by a type-checking editor; all existing sketches unchanged | 25 (with E-35: `f.colors` and the option words complete in editors) |
| S-175 | E-23 | Spike for D-088 (less verbose sketches), per `Sketch_Style_Note.md`: ten gallery examples rewritten in the proposed style, prototypes of the safe `*` and the live-value refresh on a branch, `run()` behaviour in IDLE, Thonny, VS Code, the terminal, the website editor and github.dev; criteria set first; recommendation. No product code on the release branch | done 11 Oct (`spikes/12_sketch_style/RESULTS.md` on `spike/s175-sketch-style`); D-088 accepted 12 Oct |
| S-176 | E-23 | The global style and `run()` as a safety net (D-088): `from funground import *` without `set`, `filter`, `exit`, `random` (new names `set_pixel`, `apply_filter`, `random_number`; `stop`); live values refreshed in a global-style sketch's globals (callbacks, `size()`, `load_pixels()`, scripts); the friendly note for a variable that hides a funground function; a sketch that never calls `run()` starts when the file ends (terminal, VS Code, `funground.web.Session`), the hint kept for notebooks; contract R13, R19; guide chapter 2 "Writing without `f.`", errors page, chapter 14. Acceptance: `tests/test_global_style.py`; `import funground as f` sketches unchanged (full suite) | 22 |
| S-179 | E-23 | Every option word explained in the API reference (maintainer, 12 Oct, converting a DrawBot poster: `blend_mode` named its 17 modes but never said what they do). Tasks: audit all option arguments; word -> meaning tables in the code for blend modes, stroke caps and joins, text alignment, text styles, filter kinds, cursors, key names, waves, mark anchors (D-092); the reference prints them under each function; a test that every word has a sentence; DrawBot's mode names in `blend_mode` and guide chapter 15. Acceptance: `tests/test_api_docs.py::test_every_option_word_is_explained`; API.md regenerated | 23 |
| S-180 | E-21 | A script that never shows its drawing says so (found porting a DrawBot poster: blank Play page, no message). Tasks: on the Play page and in the VS Code panel, a script's drawing is presented when the file ends if it never called `f.show()`; on the desktop, a script that drew but never called `f.show()` or `f.save()` prints one line at exit ("Your script drew something but never showed it. Add f.show() as the last line."), not in interactive sessions, notebooks or `python -m`, nor after an error; contract R13/R14 updated. Acceptance: tests for the web Session, the desktop hint (subprocess) and its quiet cases | 23 |
| S-181 | E-32 | Leading-based line fitting in `text_box()` (D-093): a line fits while its top + leading ≤ the box height, as in DrawBot and InDesign, so `lineHeight(100)` with three lines fits a 300-high box. Tasks: contract T10 rewritten; `text_box` and the overflow it returns follow it (strings, FormattedStrings with mixed sizes: a line's leading is its largest run's); goldens and snapshots that change regenerated deliberately and listed; the DrawBot chapter says the boxes port unchanged. Acceptance: the poster case (size 90, leading 100, three lines, height 300) shows three lines; a test per rule edge | 23 |
| S-182 | E-32 | Teaching: a guide project on generative posters (maintainer, 12 Oct, after porting a DrawBot poster): the design principles that stay when shapes, grids and colours change (format and margin in real units, the grid, repetition with variation and seeds, a limited palette in hsb, hierarchy, space, alignment, type), four tested stages on an A3 page ending in a four-page series PDF, challenge cards for exploration. Acceptance: its code blocks run in `tests/test_guide.py`; listed in chapter 18 | 23 |
| S-129 | E-23 | Documentation for AI assistants and agents: `llms.txt` and `llms-full.txt` (generated from `docs/reference/llms_rules.md` and the API reference, at the root and in the package) and `AGENTS.md`, so an assistant writes funground code that runs and an agent changes funground by its rules | done (Sprint 23) |
| S-183 | E-32 | Right-to-left text that every PDF reader copies in the right order (found 13 Oct: pypdfium2 5.14 reads funground's Hebrew and Arabic in visual order, 5.13 in logical order; the PDF is the same, the readers guess). Mark each right-to-left run with its logical text (`/ActualText`) so copying, search and screen readers get it right whatever the reader; test with pypdf, pdfium 5.13 and 5.14 and one more reader; then lift the pypdfium2 pin in `tests/constraints.txt` | backlog |

## E-33 Camera input (11 October 2026)

| Story | Epic | Value · tasks · acceptance | Sprint |
|---|---|---|---|
| S-172 | E-33 | Camera input, `f.camera()`, desktop and browser, still image and short clips. Tasks per `docs/design/Camera_Note.md` (draft, decisions D-089): `camera_input.py` with a replaceable device (as the microphone), pygame-ce capture on Windows and Linux, `Session.push_camera` and the runner's getUserMedia frames, Play page `allow="camera"`, the github.dev panel's one-line refusal, `picture()`, `save()`, `record()` clips to GIF (and MP4 with the `video` extra), contract rows, Quick Reference, a guide section, two gallery examples with a fallback picture. Acceptance: a fake camera's frames are drawn, saved and recorded on the desktop and in headless Chrome; refusal leaves a black picture and one line of output | 28 |
| S-173 | E-22 | Gallery example and project "Blow the letters away": rings of letters around the mouth on the live camera picture, scattered by breath (`mic.level()`), faded, re-formed; saved as a GIF. **Depends on S-172 (camera)**; until then the idea is parked (11 Oct 2026, from an animated GIF the maintainer shared) | parked |

## E-34 Site identity and the Play editor (13 October 2026)

A visitor sees in ten seconds what funground is for, tries it in the browser without reading instructions, and the editor uses the whole screen. The design was made in claude.ai and handed over as files on branch `design/site-identity` of funground-hq.github.io (`design/` there: DESIGN.md, PLAY_EDITOR.md, BACKLOG.md, tokens, mockups). Candidate ids SITE-C-nn are kept in each row.

| Story | Epic | Value · tasks · acceptance | Sprint |
|---|---|---|---|
| S-184 | E-34 | (SITE-C-01) Fix the Play page's duplicate id: `# Play` gets `id="play"`, the editor's container had the same id, so `play.js` built the editor inside the heading (toolbar at twice its size, instructions below the fold). Container renamed `funground-play`; `test_editor.mjs` now has the heading and checks the editor is not inside it. Acceptance: toolbar one row under 48px at 1366 x 768; the h1 reads Play | 24 |
| S-185 | E-34 | (SITE-C-02) The stylesheet, fonts and logo: `funground.css` (tokens, Material mapping, components), three OFL font families hosted on the site, the logo mark; every page, the guide and reference included, gets the paper look and night mode with no markdown change. Acceptance: strict build, guide chapter matches `design/mockups/guide-chapter.png`, no font from another site, contrast check passes in both schemes. Needs D-096, D-097, D-098 | 24 |
| S-186 | E-34 | (SITE-C-03) The home page: `overrides/home.html`, the first sketch beside its picture, three reasons (browser, Windows, ragas and talas), Try it in your browser first. Acceptance: matches the home mockups at 1366 and 390, no horizontal scroll, accessibility at least 95, a colour chip changes code and circle | 24 |
| S-187 | E-34 | (SITE-C-04) The Play layout: the editor fills the window, split with a drag handle, the picture at 1:1, console drawer, help popover, status chip, keyboard (`design/PLAY_EDITOR.md` section 3); protocol, share link and `test_editor.mjs` stay green; a design note for the layout | 24 |
| S-188 | E-34 | (SITE-C-05) The example picker with thumbnails, search and groups, usable by keyboard; `assemble.py` adds each example's picture to `examples.json` | later |
| S-189 | E-34 | (SITE-C-06) Play layouts (remembered) and phones: sticky picture and floating Run under 900px | later |
| S-190 | E-34 | (SITE-C-07) The gallery index: Showcase strip, topic chips that filter, tiles with Run; changes `tools/assemble.py` | later (carried from Sprint 24) |
| S-191 | E-34 | (SITE-C-08) Sketch panels on the gallery's example pages: code beside picture, Copy and Run it here; changes `tools/assemble.py` | later (carried from Sprint 24) |
| S-192 | E-34 | (SITE-C-09) In funground: a square 600 x 600 thumbnail for every example, and a short WebM loop and poster frame for animated ones, used by the gallery index when present (candidate) | - |
| S-193 | E-34 | (SITE-C-10) In funground: the guide's "change X to Y" experiments as `!!! tip "Try this"` notes, one in each of the first five chapters at least (candidate) | - |
| S-194 | E-23 | The course **Creative practice with funground** (the maintainer's, written with another agent, PR #1, 13 Oct): an overview, eleven lessons from composition to a capstone and an epilogue, 37 downloadable sketches, rendered pictures, two zip downloads, an originality check; `tests/test_course.py`. On the website under Learn. Follow-ups from the review: a `--check` mode so the pictures stay true to their code, and a link between lesson 8 and the guide's project 9 | done (Sprint 24) |

## E-35 A smooth start (0.2) (14 October 2026)

A newcomer installs funground or opens Play, and within minutes knows where things go on the canvas and lets the
editor suggest what to type: `f.` lists every function with its arguments and a sentence, `f.fill("` offers the
colour names. Maintainer, 14 Oct: "the focus should be smooth getting started experience. Editor, gentle intro ...
auto complete is not working ... Ideally I would love to have this capability even in the Play editor."

Evidence (14 Oct, Pyright 1.1.390, the engine of VS Code's Pylance, on a probe sketch): with the 0.1.0 wheel
installed, `f.circle` completes with its signature, but `f.width` and `f.mouse_x` are `object` (they come from
the module `__getattr__`), and `from funground import *` is flagged "Wildcard import from a library not allowed".
Adding only `py.typed` makes it worse: `"circle" is not exported from module "funground"`, because `__all__` is
computed at run time. A static `__all__` with typed live values fixes both types (`float`). With the repository's
editable install (setuptools' import-hook finder) Pyright cannot find funground at all: no completion for anyone
working in the repository. `f.colors` does not exist yet (S-174). No Python language server runs in github.dev or
in Play, so completion there must come from funground's own data.

| Story | Epic | Value · tasks · acceptance | Sprint |
|---|---|---|---|
| S-130 | E-35 | (moved from E-23) Typing that editors read: `py.typed`; every public name re-exported as `name as name`; `__all__` a literal list (a test keeps it equal to the star rule of D-088); live values declared with their types under `if TYPE_CHECKING:`; option words as `Literal[...]` with S-174. Acceptance: a Pyright probe of `f.`, `f.width` and the star style reports the right types and no export errors (test, skipped where Pyright is absent) | 25 |
| S-195 | E-35 | Completion data: `tools/make_api_reference.py` also writes `completions.json` (every public name: kind, signature, the summary sentence, the reference link; the option words of each parameter, the colour names with their values), shipped in the package and in the site's runtime. Acceptance: generated, never hand-edited, a test that it matches `_PUBLIC_NAMES` | 25 |
| S-196 | E-35 | Completion in Play: after `f.` (and for bare names in the star style) CodeMirror lists functions and live values with their signatures and summary; inside the quotes of `fill(`, `stroke(`, `background(`, `text_align(` and the like it offers the option words, colours with a swatch; a hint shows the arguments while typing a call. Acceptance: headless checks in `test_editor.mjs`; works offline with the runtime | 25 |
| S-197 | E-35 | Spike: completion in github.dev and vscode.dev. Does the browser's Pylance read stubs carried by the sketchbook (`typings/funground/`)? Otherwise the funground extension supplies completion from `completions.json`. Criteria before the work: `f.` lists functions with signatures in real github.dev | 25 |
| S-198 | E-35 | Quiet, complete VS Code on the desktop: the sketchbook's and the guide's recommended `.vscode/settings.json` silence the wildcard-import warning for the star style; the developer set-up (`AGENTS.md`, Contributing) installs editable in a mode Pylance can follow (`editable_mode=strict`); chapter 1 says how to choose the interpreter. Acceptance: in this repository and in a fresh learner folder, `f.` completes (Pyright probe) | 25 |
| S-199 | E-35 | A gentle first chapter: "Where things are" becomes a section with a labelled picture (the grid, the origin, x to the right and y down, `f.width` and `f.height`, the centre), a live sketch that shows the mouse's x and y, what is drawn outside the window, sizes in pixels and why a high-resolution screen still shows the same picture; a gallery example `basics-00_where_things_are` with its golden; the same steps as the first page under Learn on the site. Acceptance: guide tests run the new code; the example runs in Play | 25 |
| S-200 | E-35 | Play's first visit: opens on a short starter sketch with three comments that say what to change, a "New to funground? First steps" link, and errors that point at the line with a sentence from the errors page. Acceptance: `test_editor.mjs` covers the first visit | 26 |
| S-201 | E-35 | Play: the arguments while typing and help on hover (roadmap 8, SITE-C-18). Inside `f.circle(` a hint shows `circle(x, y, diameter)` with the current argument in bold; hovering a funground name shows its signature, sentence and a Reference link; both from `completions.json`. Acceptance: `test_editor.mjs`: after `f.circle(10, ` the hint shows `y` in bold; hovering `circle` shows its box | 26 |
| S-202 | E-35 | Play: where the mouse is (roadmap 5, SITE-C-15). A "Guides" switch in the toolbar: over the picture, the mouse's x and y in the sketch's own pixels, and a grid every 50 pixels with the numbers on the edges; drawn by the preview over its canvas (new editor-to-preview message `{type: "guides", coords, grid}`, ignored by older previews, documented in both READMEs), remembered in localStorage, off by default. Ties Play to chapter 1 "Where things are". Acceptance: `test_editor.mjs`: with Guides on, moving the mouse to the canvas's (100, 50) shows "x 100, y 50" at zoom 1:1 and at Fit; the sketch still gets the mouse | 26 |
| S-203 | E-35 | Play: errors where they happen (roadmap 9, SITE-C-19). The error's line is marked in the code (the tomato wash and bar of PLAY_EDITOR.md, until the code is changed); a wavy underline under the name a `NameError` or `AttributeError` names; under the one-line message a link to the matching section of the guide's errors page when there is one. Acceptance: `test_editor.mjs`: `f.circl(...)` marks the line, underlines `circl`, links the errors page | 26 |
| S-204 | E-35 | Play at night: the editor's colours come from the site's code tokens in both schemes, not One Dark (roadmap; S-187 limit); the suggestion popup and hints follow. Acceptance: contrast check passes for the code colours in both schemes; `design_shots.mjs` night shot | 26 |
| S-205 | E-35 | Suggestions in github.dev and VS Code from the funground extension (S-197 route B): completion after `f.` and in the star style, inside `f.COLORS.`/`f.CONSTANTS.`, colour names and option words inside quotes, hover and signature help, from `completions.json` bundled in the `.vsix` by `build.py`; the extension's version and `CHANGELOG` bumped; the Marketplace publish is the maintainer's. Acceptance: a test with a stand-in VS Code API (from spike 13), the `.vsix` builds; the maintainer's github.dev check P1 | 26 |
| S-206 | E-34 | Gallery example pages you can walk through (maintainer, 15 Oct): a breadcrumb at the top (Gallery › Topic › Example, each a link), Previous and Next at the top and the bottom with the examples' titles, in the gallery's order across topics, and "Back to the gallery" to the topic's place in the index; generated by `tools/assemble.py`, usable by keyboard and on a phone. Acceptance: on the assembled site every example page has the breadcrumb and both links (the first and last only one), `check_links.py` passes, strict MkDocs build | 26 |
| S-207 | E-34 | Play: Previous and Next beside the example picker (maintainer, 15 Oct): ‹ and › step through the examples in the gallery's order, their tooltips name the example, each example's draft is kept as today; hidden for a blank or shared sketch. Acceptance: `test_editor.mjs`: › opens the next example and its code, ‹ goes back, a draft survives the round trip | 26 |
| S-208 | E-35 | Play: change a number from the keyboard or by dragging (Play roadmap item 6, pulled forward: maintainer, 15 Oct, asked when editing numbers with arrow keys is scheduled). With the cursor on a number, Alt+Up and Alt+Down change it by one step, the step following the number's last digit (120 by 1, 0.5 by 0.1, 0.25 by 0.01); with Shift, ten steps; Alt+drag on a number scrubs it with the mouse; with Auto-run on, the picture follows. Agreed with the maintainer (15 Oct): Shift for the bigger step, not Alt+Left/Right (Back in the browser on Windows and Linux, word jumps on a Mac). Off a number, Alt+Up/Down keep CodeMirror's move-line. **Alt shows what it will move** (maintainer, 15 Oct: "what is shifted is decided by context: number or line"): while Alt is held, the number under the cursor is highlighted, or the whole line when the cursor is not on a number; with the mouse, the number under the pointer (the Alt+drag target); the highlight goes on Alt's release and when the window loses focus (Alt+Tab sends no key-up). Check that tapping Alt alone on Windows does not leave the editor (Chrome may move focus to its menu): if it cannot be prevented, the highlight still clears and typing goes on. Typing and plain arrow keys are never affected. Acceptance: `test_editor.mjs`: Alt+Up on 120 gives 121, Alt+Shift+Up 131, Alt+Down on 0.5 gives 0.4, on 0.25 gives 0.24, a negative number crosses zero, Alt+Up off a number still moves the line, Alt+drag right increases, Auto-run reruns; holding Alt highlights the number (cursor on it) or the line (cursor elsewhere), releasing Alt or blurring the window clears it | 26 |
| S-209 | E-35 | Play shows the picture before Python is ready (roadmap 1, SITE-C-11): an example opens with its gallery picture in the frame and the loading progress over it; the first Run replaces it; a blank or shared sketch shows the loading message as today. Acceptance: `test_editor.mjs`: with the runner held back, the example's picture is shown and replaced after Run | 27 |
| S-210 | E-35 | Play keeps its runtime on the device (roadmap 2, SITE-C-12; maintainer, 14 Oct: yes, with the update rule in `design/Play_Roadmap.md`): a service worker caches Pyodide and the wheels in a cache named after the manifest's hash; the manifest is always asked for first; a new version downloads in the background, starts on the next Run, and the old cache is deleted when the new one is complete; unchanged files are copied, not downloaded; "Remove Play from this browser" in the help. Acceptance: a repeat visit starts with no runtime download (measured, against the 3 s budget); a test build with a changed manifest replaces the cache; offline Play runs a sketch | carried over from 27 (rolled back: a first visit hung on GitHub Pages; next, find the cause with logging from the live preview) |
| S-211 | E-31 | Fonts on demand in the browser (roadmap 3, SITE-C-13): the bundled fonts (2.4 of 12.4 MB) are fetched the first time a sketch draws text, as pygame-ce and Pillow already are, with the same care for a complete on-demand list. Acceptance: a sketch with no text fetches no font file; text, `text_box` and SVG/PDF text still match their goldens in the browser (funground-web's tests) | carried over from 27 (built; GitHub Pages compresses fonts, so Play loads them at start-up; option B, a font fetched when first opened, awaits the maintainer) |
| S-212 | E-35 | Saving from Play (roadmap 12, SITE-C-21): `f.save("poster.png")` (and PDF, SVG, GIF, MP4 where the browser can make it) offers the file as a download: the preview sends the saved file to the editor (`{type: "file", name, bytes}`, documented), the editor saves it; plus a "Save picture" button that saves the current frame as PNG. Acceptance: `test_editor.mjs`: a sketch that saves `out.png` and `out.pdf` gives two downloads with the right bytes; Save picture gives a PNG of the frame | 27 |
| S-213 | E-35 | My sketches (roadmap 13, SITE-C-22): a list of the sketches kept in this browser, with names; New, Rename, Duplicate, Delete; Download `.py`; Open a `.py` from the computer; the work stays on the device (no account, no server: maintainer, 14 Oct). Acceptance: `test_editor.mjs`: create, rename, reload, open, download, delete | 27 |
