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
| S-012 | E-03 | The five DECISION rows in the contract are decided (S2 alpha, S4 stroke alignment, C6 sub-pixel, T2 default font, F1 angle unit) | Contract rows changed from DECISION to Pinned; ADR or note per decision | ready — maintainer decision |
| S-013 | E-04 | Public functions delegate to an explicit `Sketch` instance (`_active_sketch`); live values resolve through `__getattr__` to it; two `Sketch`es can coexist in one process | New tests; all existing tests unchanged and green | ready |
| S-014 | E-05 | Window, events, input sampling, clock and presentation live in `PygamePlatform` behind a `Platform` protocol | `_core.py` no longer calls `pygame.display`/`event`/`mouse`/`key`/`time` directly | ready |
| S-015 | E-06 | Fill/stroke/width/text style is a Playground `GraphicsState` owned by the sketch, with `save()`/`restore()` (internal for now) | Unit tests on state stack | ready |
| S-016 | E-03 | Colours are parsed once into a Playground `Color` (RGBA 0–255) using a bundled copy of the pygame-ce name table | `Color.parse("tomato") == Color(255, 99, 71, 255)`; all colour forms in contract S1 covered | ready |
| S-017 | E-02 | CI fails if `pygame` is imported anywhere outside `playground/platform/` and `playground/renderers/` | AST lint test | ready |

## Sprint 2 — Phase 1b: draw-op IR (planned)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-018 | E-06 | Every current primitive (`background circle ellipse rect line point text`) records a backend-neutral op instead of drawing | `Frame` op list; op dataclasses | ready |
| S-019 | E-06 | `PygameRenderer` consumes the op list and produces **identical** goldens | Sample suite green with unchanged goldens | ready |
| S-020 | E-06 | Op-list snapshot tests exist for the sample suite | `tests/test_ops_snapshot.py` | ready |
| S-021 | E-07 | Asking for an unsupported capability fails at `p.size()`/`p.run()` with a message naming the extra to install | Tests for message text | ready |
| S-022 | E-08 | ADR-001 is accepted or amended | ADR status ≠ Proposed | ready — maintainer decision |

## Sprint 3 — Phase 2a: Cairo via the IR (planned)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-023 | E-09 | `CairoRenderer` consumes the same op list and presents through `PygamePlatform` | Spike 05 adapter productionised; sample suite renders | ready (after S-022) |
| S-024 | E-13 | Rendering happens at physical resolution behind a scale; `p.width` stays logical | Crisp output at 125 % scaling on the teaching machine | ready |
| S-025 | E-03 | Contract decisions S2/S4/C6 are applied and goldens regenerated once, deliberately | Contract + tests + goldens in one change | ready (after S-012) |
| S-026 | E-09 | Cairo is the default renderer; pygame drawing remains selectable as a fallback | `PLAYGROUND_RENDERER` env / `p.size(renderer=)` | ready |

## Sprint 4 — Phase 2b: transforms, paths, export (planned)

| ID | Epic | Story | Acceptance | Status |
|---|---|---|---|---|
| S-027 | E-10 | `p.translate/rotate/scale`, `p.push/pop`, `with p.state():` | Semantic tests; contract F1/F2 pinned | ready |
| S-028 | E-11 | `p.path()` with `move_to/line_to/curve_to/close`, fill/stroke/clip | Tests; golden sketch | ready |
| S-029 | E-12 | `p.save("x.png|pdf|svg")` and a headless run that never opens a window | Export files checked structurally + rendered | ready |
| S-030 | E-22 | Quick Reference v0.6 documents every additive API | PDF/MD regenerated | ready |

## Later (Phases 3–4, directional)

Stories are cut from epics E-14 … E-21 when their phase is scheduled. Nothing here is committed.
