# Sprint 1 — Phase 1a: Sketch, platform, state

**Dates:** to be set by the maintainer
**Goal:** Give Playground an explicit `Sketch`, move every pygame call behind `PygamePlatform`, and
introduce `GraphicsState` and `Color` — with **zero learner-visible change**: all 73 Sprint-0 tests
and all 11 goldens must pass unchanged at the end of the sprint.
**Blocked on:** S-012 (maintainer decisions) is the first story but does not block S-013…S-017,
which are pure refactors under the existing contract.

## Story set

### S-012 Decide the DECISION rows — E-03 ✅ (24 Sept 2026, before sprint start)
- [x] S-012.1 S2 alpha — honoured (D-003)
- [x] S-012.2 S4 stroke alignment — centred (D-004)
- [x] S-012.3 C6 sub-pixel — honoured + anti-aliased (D-005)
- [x] S-012.4 T2 default font — mechanism: outlines via fontTools + uharfbuzz in the IR (D-006); font *file* chosen by S-031
- [x] S-012.5 F1 angle unit — degrees (D-002)
- [x] S-012.6 ADR-001 — accepted, option C (D-001)
*Acceptance met:* no row in `Semantic_Contract.md` reads DECISION.

### S-031 Spike 06 — deterministic text from a bundled font — E-15
- [ ] S-031.1 `spikes/06_text_outlines/` with its own venv: pycairo, fontTools, uharfbuzz, pygame-ce
- [ ] S-031.2 Candidate OFL fonts downloaded with licence files (e.g. DejaVu Sans, Noto Sans); record sizes
- [ ] S-031.3 Shape with uharfbuzz → glyph ids/advances/offsets; outlines via fontTools glyph set + pen → path ops; render through Cairo; also render the same strings with Cairo's toy API and pygame for comparison
- [ ] S-031.4 Matrix: sizes 12/16/24/36/48 × strings `ABC xyz 123`, `Hello, Playground!`, `AVATAR`, `office`, one non-Latin sample
- [ ] S-031.5 Measure: per-frame cost with/without a glyph-outline cache; byte-identical output across two runs (and on Linux CI if available); baseline/anchor correctness; PDF/SVG output
- [ ] S-031.6 Write results into `spikes/RESULTS.md`; propose the font; close D-006 in `Decision_Log.md`
*Acceptance:* a recommendation with numbers and PNGs, narrow scope (single line, no layout).

### S-013 `Sketch` object and active-sketch facade — E-04
- [ ] S-013.1 `playground/sketch.py`: `Sketch` holds state, style, platform handle, frame counter
- [ ] S-013.2 `playground/api.py`: every public function delegates to `_active_sketch`
- [ ] S-013.3 `__init__.__getattr__` resolves live values from the active sketch
- [ ] S-013.4 Test: two `Sketch` instances in one process do not share state
*Acceptance:* existing suite green, no golden change.

### S-014 `PygamePlatform` behind a `Platform` protocol — E-05
- [ ] S-014.1 `playground/platform/base.py`: `Platform` protocol (`create_window`, `poll`, `input_state`, `tick`, `present`)
- [ ] S-014.2 `playground/platform/pygame_platform.py`
- [ ] S-014.3 `Sketch.run()` uses only the protocol
*Acceptance:* `grep pygame playground/sketch.py playground/api.py` is empty.

### S-015 `GraphicsState` with an internal stack — E-06
- [ ] S-015.1 `playground/state.py`: frozen-dataclass `GraphicsState` (fill, stroke, stroke_width, text_size); `save()`/`restore()`
- [ ] S-015.2 Unit tests for push/pop nesting and restore-on-error

### S-016 Playground `Color` — E-03
- [ ] S-016.1 `playground/color.py`: `Color(r, g, b, a)`; `Color.parse()` for every form in contract S1
- [ ] S-016.2 Bundle the pygame-ce colour-name table as data (verify licence/attribution)
- [ ] S-016.3 Tests: every Quick Reference colour example parses; unknown name raises a learner-readable error

### S-017 Provider-boundary lint — E-02
- [ ] S-017.1 `tests/test_boundaries.py`: AST walk; `import pygame` allowed only under `playground/platform/` and `playground/renderers/`
*Acceptance:* test fails on today's `_core.py` until S-014 lands; green after.

## Out of scope this sprint
The draw-op IR (Sprint 2) and any renderer other than pygame (Sprint 3).
