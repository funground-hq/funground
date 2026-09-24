# Sprint 2 — Phase 1b: draw-op IR

**Dates:** to be set by the maintainer (opens after Sprint 1 sign-off)
**Goal:** every public drawing call records a backend-neutral op; a `LegacyPygameRenderer` consumes
the op list and reproduces today's pixels; IR snapshots become the cross-backend contract. In
parallel, the renderer bake-off (Spike 07) produces the numbers for D-011.
**Checkpoint (D-007 #2):** all 11 goldens byte-identical at sprint end; IR snapshot files committed.
**Decisions open at start:** none. **Decision expected at end:** D-011 (interactive 2D engine).

## Story set

### S-018 Draw-op IR — E-06
- [ ] S-018.1 `playground/ir.py`: frozen op dataclasses for the current primitives — `Clear`, `Circle`, `Ellipse`, `Rect`, `Line`, `Point`, `Text` — each carrying the `GraphicsState` snapshot it was issued under
- [ ] S-018.2 Internal-only ops the vector renderer will need: `Save`, `Restore`, `Transform` (affine 2×3), `ClipPath`, `Path` (`move/line/cubic/close`) — no public API (PROCESS "internal first")
- [ ] S-018.3 `playground/geometry.py`: `Transform` (compose, apply, invert, from translate/rotate(deg)/scale) and `Path` builder; unit tests
- [ ] S-018.4 `Frame`: an ordered op list with `append()`, `__iter__`, `clear()`; `Sketch` owns one per frame
- [ ] S-018.5 `Sketch` drawing methods append ops instead of calling the renderer; renderer is invoked once per frame with the whole list
*Acceptance:* `Sketch` has no per-primitive renderer calls; ops are plain data (hashable, reprable).

### S-019 `LegacyPygameRenderer` consumes the IR — E-06
- [ ] S-019.1 Rename `renderers/pygame2d.py` → `renderers/legacy_pygame.py`, class `LegacyPygameRenderer`; single entry `render(frame, target)`
- [ ] S-019.2 Per-op dispatch reproducing today's `pygame.draw` calls exactly (rounding, inside strokes, alpha dropped, font cache)
- [ ] S-019.3 Renderer protocol in `renderers/__init__.py` becomes `render(ops)` + `capabilities`
- [ ] S-019.4 Delete the per-primitive protocol methods
*Acceptance:* goldens byte-identical; `test_semantics.py` unchanged.

### S-020 IR snapshot tests — E-06
- [ ] S-020.1 `tests/test_ops_snapshot.py`: run each Session-1 sketch for 30 frames, serialise the last frame's op list to `tests/snapshots/<sketch>.json`
- [ ] S-020.2 Exact comparison; `PLAYGROUND_UPDATE_SNAPSHOTS=1` to regenerate; failure writes `_actual/`
- [ ] S-020.3 `docs/qa/Test_Strategy.md`: IR snapshots become the primary cross-backend layer; goldens per backend
*Acceptance:* 11 snapshot files committed; suite green on Windows and (when CI exists) Linux — snapshots are platform-independent by construction.

### S-021 Capability registry and learner-facing errors — E-07
- [ ] S-021.1 `playground/capabilities.py`: `Capability` enum (`RASTER_2D`, `VECTOR_PATHS`, `CLIP_PATH`, `TRANSFORMS`, `ALPHA`, `PDF_EXPORT`, `SVG_EXPORT`, …); each renderer declares a frozenset
- [ ] S-021.2 Renderer selection at `p.size()`/`run()`; a missing capability raises `PlaygroundError` naming the feature and the extra to install
- [ ] S-021.3 Tests for message text
*Acceptance:* no capability check happens inside the frame loop.

### S-035 Spike 07 — renderer bake-off — E-08 *(parallel; feeds D-011)*
- [ ] S-035.1 `spikes/07_renderer_bakeoff/` with one venv per engine (pycairo; skia-python; blend2d-py) and a shared scene generator that emits the **Sprint 2 IR** (so the spike also tests the IR)
- [ ] S-035.2 Binding-coverage gate for Blend2D: clip path, scale, fill rule, stroke join/cap, gradient types — pass/fail table; if fail, Blend2D is measured only on what it can do and scored on binding risk
- [ ] S-035.3 Scenes: A primitive-heavy animation (500 circles + 500 rects, alpha, rotation) · B complex paths (100 Béziers, joins/caps, clip, nested transforms) · C translucency/compositing (multiply/add/screen where supported) · D gradients (linear, radial, conic where available) · E text via the outlines route with DejaVu Sans (+ Blend2D native font load for comparison)
- [ ] S-035.4 Export replay: the same IR through Cairo PDF/SVG surfaces regardless of interactive engine
- [ ] S-035.5 Classroom cost: `pip install` time, download size, installed footprint, cold import, first frame — each in a fresh venv
- [ ] S-035.6 Binding-risk score per engine: core project stability, binding ownership, wheel coverage (incl. macOS x86_64), release cadence, API coverage, licence
- [ ] S-035.7 Results in `spikes/RESULTS.md` §7; **D-011** presented per PROCESS (context / options / trade-offs / recommendation / why)
*Acceptance:* the maintainer can decide the engine from the document alone.

### S-033 Architecture document v2 — E-23
- [ ] S-033.1 `docs/design/Playground_Technology_Architecture_v2.md`: headline "Playground owns the programming model and drawing semantics; the IR is the contract; pygame-ce runs the interactive environment; providers are selected per capability and workload"; interactive renderer **OPEN (reference implementation: Cairo)**; export via Cairo; text as outlines with `TextRun` reserved; three-checkpoint Phase 1; Phases 3–4 directional; alternatives-considered appendix (Skia, Blend2D, Vello, WebRender, GSK, Moz2D — from the D-010 discussion)
- [ ] S-033.2 The .docx stays as the v1 record; v2 links the ADRs and decision log
*Acceptance:* a new contributor can read v2 alone and know what is decided, what is open, and why.

## Out of scope this sprint
Any vector renderer in the package (Sprint 3, after D-011); public transform/path API (Phase 2).
