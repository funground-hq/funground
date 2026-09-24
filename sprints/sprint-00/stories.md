# Sprint 0 — Phase 0: Stabilise v0.5

**Dates:** 24 September 2026 (single day, retrospectively recorded — the work preceded the SDLC structure)
**Goal:** Turn the v0.5 package into an executable compatibility contract before any refactor, and
answer the renderer-topology question with measurements instead of opinion.
**Inputs:** `src_v0.5/` (v0.5.0 package), Quick Reference PDF, architecture document, architecture review.

## Story set

### S-001 Headless regression harness — E-01 ✅
- [x] S-001.1 `p.run(max_frames=None)` keyword-only hook; captures the final frame as RGB bytes (`_core._last_frame`)
- [x] S-001.2 `_core.run()` split into frame discovery + `_run_namespace(namespace, fps, max_frames)`
- [x] S-001.3 `tests/conftest.py::run_sketch` executes a learner file unchanged with the wrapper
- [x] S-001.4 Dummy SDL video/audio drivers selected before pygame import

### S-002 Session-1 sample suite — E-01 ✅
- [x] S-002.1 12 sketches in `examples/session1/` mirroring every Quick Reference topic (first sketch, shapes, colours, fill/stroke, text, animation, bounce, mouse, keyboard, helpers, delta_time, default window)
- [x] S-002.2 Plain learner code only — no test hooks

### S-003 Golden-image tests — E-01 ✅
- [x] S-003.1 `tests/test_examples_golden.py`; exact match; Windows as golden platform; update flag; `_actual/` dump on failure
- [x] S-003.2 11 goldens generated and verified on a second run

### S-004 API inventory frozen — E-01 ✅
- [x] S-004.1 `tests/test_api_contract.py`: v0.5 signatures, additive signatures listed separately, `__all__` exact, live values dynamic

### S-005 Semantic tests — E-01 ✅
- [x] S-005.1 42 pixel/behaviour tests covering every pinned contract row (origin, anchoring, rounding, stroke inside, alpha dropped, text anchor/colour fallback, key names, random, lifecycle, frame_count, delta_time, second run, max_frames)

### S-006 `random_seed()` — E-01 ✅
- [x] S-006.1 Private `random.Random()` instance; `p.random()` uses it; `p.random_seed(seed)` exported

### S-007 Second-run crash fix — E-01 ✅
- [x] S-007.1 `_screen`/`_clock` reset after `pygame.quit()` so a later `run()` recreates the window

### S-008 Packaging and CI — E-02 ✅ (CI unexecuted)
- [x] S-008.1 `pyproject.toml` (setuptools, `pygame-ce>=2.5`, `[dev]` extra, pytest config); version `0.6.0.dev0`
- [x] S-008.2 `.github/workflows/ci.yml`: 3 OS × 4 Python, headless
- [ ] S-008.3 First CI run on a remote — *no repository remote exists yet*

### S-009 Semantic contract — E-03 ✅
- [x] S-009.1 `docs/design/Semantic_Contract.md` from source + probes; 5 DECISION rows named

### S-010 Renderer topology answered — E-08 ✅
- [x] S-010.1 Spike 01 pygame-only capability audit
- [x] S-010.2 Spike 02 Skia → pygame presentation cost at 3 resolutions
- [x] S-010.3 Spike 03 skia-python install cost
- [x] S-010.4 Spike 04 PyPI revalidation
- [x] S-010.5 Spike 05 Skia vs Cairo behind one op list
- [x] S-010.6 `ADR-001` drafted (Proposed)

### S-011 SDLC structure — E-23 ✅
- [x] S-011.1 `docs/PROCESS.md`, backlog, QA strategy, `sprints/` layout
