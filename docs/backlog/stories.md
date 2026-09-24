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

## Sprint 3 — Phase 1c: vector renderer via the IR (engine per D-011; reference: Cairo), semantic migration (planned)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-023 | E-09 | The D-011 engine's renderer consumes the same op list and presents through `PygamePlatform`; Cairo remains the export path for PDF/SVG regardless | Spike 05/07 adapter productionised; sample suite renders | ready (after D-011) |
| S-024 | E-13 | Rendering happens at physical resolution behind a scale; `p.width` stays logical | Crisp output at 125 % scaling on the teaching machine | ready |
| S-025 | E-03 | Contract decisions D-003/D-004/D-005 (alpha, centred strokes, fractional + AA) are applied and goldens regenerated once, deliberately, with each visual change listed in the sprint review | Contract + tests + goldens in one change | ready |
| S-026 | E-09 | The D-011 engine is the default interactive renderer; `LegacyPygameRenderer` and all `pygame.draw` usage are deleted (D-008) | No `pygame.draw` in the package; boundary lint updated | ready |
| S-034 | E-12 | Headless run and `p.save()` to PNG/PDF/SVG through Cairo surfaces (moved forward from Sprint 4 per D-007) | Export files checked structurally + rendered | ready |

## Sprint 2 — additional (planned)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-033 | E-23 | Architecture document v2 reflecting ADR-001/D-007 (and ADR-002 if D-010 = B): IR, pygame platform + presentation, interactive renderer marked OPEN with Cairo as reference implementation, export via Cairo, three-checkpoint Phase 1, text-as-outlines with `TextRun` reserved | `docs/design/Playground_Technology_Architecture_v2.md` (Markdown; the .docx stays as the v1 record) | ready |
| S-035 | E-08 | **Spike 07 — renderer bake-off** (D-010 = B). Same IR stream to Cairo, Skia and Blend2D (the last only if its binding passes a coverage gate: clip, scale, fill rule, stroke join/cap). Scenes: primitive-heavy animation (500 circles + 500 rects, alpha, rotation); complex paths (100 Béziers, joins/caps, clip, nested transforms); translucency/compositing; gradients incl. conic; text via outlines route + Blend2D native font load; export replay through Cairo PDF/SVG; install size, cold import, first frame; binding-risk score | Numbers + PNGs in `spikes/RESULTS.md` §7; D-011 presented per PROCESS before Sprint 3 | done (Sprint 2); D-011 pending |

## Sprint 4 — Phase 2: public API on the vector model (planned)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-027 | E-10 | `p.translate/rotate/scale` (degrees, D-002), `p.radians/degrees`, `p.push/pop`, `with p.state():` | Semantic tests; contract F2 pinned | ready |
| S-028 | E-11 | `p.path()` with `move_to/line_to/curve_to/close`, fill/stroke/clip | Tests; golden sketch | ready |
| S-029 | E-15 | Text subsystem v1 from Spike 06 (font: DejaVu Sans, D-009): `FontResource` (HarfBuzz face + fontTools glyph set + glyph-outline cache), `TextRun` (semantic text + shaped glyphs, outlines materialised for the IR) — `p.text()` unchanged for learners | Deterministic text goldens on two platforms | ready (after S-031) |
| S-030 | E-22 | Quick Reference v0.6 documents every additive API | PDF/MD regenerated | ready |

## Later (Phases 3–4, directional)

| ID | Epic | Story | Note |
|---|---|---|---|
| S-032 | E-12 | PDF exporter consumes `TextRun` and embeds/subsets the font so exported text is searchable and selectable | Accepted limitation from D-006 until then |

Other stories are cut from epics E-14 … E-21 when their phase is scheduled. Nothing here is committed.
