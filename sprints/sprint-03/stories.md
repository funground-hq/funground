# Sprint 3 — Phase 1c: Cairo via the IR, semantic migration

**Dates:** opened 25 September 2026
**Goal:** Cairo consumes the IR and presents through pygame; the pinned v0.6 semantics (alpha,
centred strokes, fractional + AA) take effect with **one deliberate golden regeneration**; text
moves to the outline route so nothing is lost when the legacy renderer is deleted; HiDPI, headless
and PNG/PDF/SVG export land. **Checkpoint (D-007 #3):** IR snapshots unchanged (learner code asks
for the same ops); goldens regenerated once with every visual change listed in the review; no
`pygame.draw` left in the package.
**Decisions:** D-011 = D (Cairo). None open.

## Ordering constraint (from the Sprint 2 guide)
`ir.Text` is drawn only by the legacy renderer. S-029 (outline text) must land before S-026
deletes it. Order below respects that.

## Story set

### S-023 `CairoRenderer` consumes the IR — E-09
- [ ] S-023.1 `pycairo` becomes a base dependency (`pyproject.toml`)
- [ ] S-023.2 `renderers/cairo2d.py`: `CairoRenderer` — every IR op incl. `Save/Restore/Concat/ClipPath/FillPath/StrokePath`; v0.6 semantics (alpha, centred round-join strokes, AA, fractional coords); `capabilities` = RASTER_2D, ALPHA, ANTIALIAS, TRANSFORMS, VECTOR_PATHS, CLIP_PATH
- [ ] S-023.3 Presentation: Cairo `ImageSurface` → `pygame.image.frombuffer(..., "BGRA")` → blit, zero-copy; `attach(target)` receives the platform surface
- [ ] S-023.4 Renderer selection: `PLAYGROUND_RENDERER=legacy|cairo` env (default `cairo` once S-025 lands); `Sketch(renderer=...)` unchanged
- [ ] S-023.5 Unit tests: each op renders; alpha honoured; centred stroke geometry; sub-pixel AA present
*Acceptance:* sample suite renders through Cairo (goldens differ as expected, not yet regenerated).

### S-029 Text subsystem v1 (outline route) — E-15
- [ ] S-029.1 `fontTools` + `uharfbuzz` base dependencies; `playground/fonts/DejaVuSans.ttf` + `DejaVu-LICENSE.txt` bundled (D-009); package data in `pyproject`
- [ ] S-029.2 `playground/text.py`: `FontResource` (HarfBuzz font, fontTools glyph set, glyph-outline cache), `TextRun` (text, size, shaped glyphs, `outline_ops()` → `FillPath`s), top-left anchor (contract T1)
- [ ] S-029.3 `CairoRenderer` handles `ir.Text` by materialising a `TextRun` (cached per (text, size)) — `ir.Text` stays in the IR (reserved for embedded-font export, S-032)
- [ ] S-029.4 Tests: deterministic bytes across two runs; kerning/ligature; anchor; `p.text()` unchanged for learners
*Acceptance:* `05_text.py` renders through Cairo with DejaVu Sans; no pygame font code on the Cairo path.

### S-025 Semantic migration and golden regeneration — E-03
- [ ] S-025.1 `test_semantics.py` rows S2/S4/C6/T2 rewritten to the v0.6 rule (alpha honoured, stroke centred, fractional + AA, DejaVu text)
- [ ] S-025.2 Default renderer → Cairo; `PLAYGROUND_UPDATE_GOLDENS=1` once; each visual change listed in `review.md` with before/after PNGs
- [ ] S-025.3 IR snapshots must be byte-identical before and after (proof the learner-facing request did not change)
- [ ] S-025.4 `Semantic_Contract.md` status column: "applies when Cairo lands" → "in effect since Sprint 3"
*Acceptance:* suite green; snapshot diff empty; golden diff reviewed.

### S-026 Delete the legacy renderer — E-09 (D-008)
- [ ] S-026.1 Remove `renderers/legacy_pygame.py`, the `legacy` selection value, and all `pygame.draw`/`pygame.font` usage
- [ ] S-026.2 Boundary lint: `pygame` allowed only under `platform/`; `cairo` only under `renderers/` and `export/`
*Acceptance:* `grep -r "pygame.draw" playground` empty.

### S-024 HiDPI-correct rendering — E-13
- [ ] S-024.1 `PygamePlatform`: declare per-monitor DPI awareness on Windows before the window opens; report `backing_scale`
- [ ] S-024.2 Window opened at physical pixels; Cairo surface at physical size with a `scale(backing_scale)` base transform; `p.width`/`p.height` stay logical; mouse coordinates divided back to logical
- [ ] S-024.3 Test with a forced `backing_scale=2` on the dummy driver: surface is 2× and a `rect(0,0,10,10)` covers 20 physical px
*Acceptance:* crisp output at 125 % on the teaching machine (screenshot in review).

### S-034 Headless run and export — E-12
- [ ] S-034.1 `Platform` gets a `HeadlessPlatform` (no window; capture only) selected by `PLAYGROUND_HEADLESS=1` or `p.run(headless=True)`? — **decide: keep to env + `max_frames`** to avoid new public API this sprint
- [ ] S-034.2 `playground/export.py`: replay a `Frame` to Cairo PNG / PDF / SVG surfaces; `p.save(path)` records the *current* frame's ops and writes at end of frame
- [ ] S-034.3 Tests: PNG bytes match the on-screen frame; PDF/SVG structurally valid (magic bytes, page count); export of a frame with text and clip
*Acceptance:* `p.save("frame.pdf")` from a Session-1 sketch works headless in CI.

### S-036 Blend2D as a gated optional renderer — E-08 *(tracking; not this sprint)*
Re-run Spike 07 when `blend2d-py` exposes clip + matrix + fill rule and ships macOS x86_64 wheels; then `playground[fast]`.

## Out of scope
Public transform/path/state API (Sprint 4); font choice API; searchable-PDF text (S-032).
