# Sprint 10 — Phase 3d: typography and SVG

**Dates:** opened 1 Oct 2026 under D-034. Sprint 9 closed by the maintainer the same day.
**Release context (D-027):** part of release 0.1, after Phase 3.

**Goal:** richer text (tracking, OpenType features, variable fonts, mixed styles in one text),
rounded corners, and SVG files loaded as vector drawings; a spike on searchable PDF text.

**Checkpoint:** existing goldens and snapshots unchanged; each new public name has a contract row,
tests, a gallery example (golden, snapshot, originality check), a guide section and a Quick
Reference entry; CI green on 12 cells. Other tools' API names are cited with where they were checked.

**Decisions:** D-040 rounded corners (maintainer); D-042 typography names (Claude, D-034);
D-041 SVG library: svgelements (maintainer).

## Story set

### S-089 Rounded corners — E-24 *(D-040; contract F14)*
- [x] S-089.1 `rect`/`square` with 0, 1 or 4 radii (p5 order); path builder `rect` too; IR field omitted when sharp
- [x] S-089.2 Tests; gallery `shapes/`; guide chapter 3; chapter 14 (p5 row); Quick Reference; changelog

### S-090 Tracking, OpenType features, variable fonts — E-15 *(D-042; contract T13)*
- [x] S-090.1 `text_tracking`, `text_features`, `font_variations`: shaping and outlines at the same variation location
- [x] S-090.2 A small variable test font generated in the tests (fontTools), never downloaded; gallery `text/` using DejaVu features where possible
- [x] S-090.3 Tests; guide chapter 6; chapter 15 (DrawBot rows, checked in DrawBot's source); Quick Reference; changelog

### S-091 Mixed styles in one text — E-15 *(contract row to pin after S-090)*
- [x] S-091.1 A formatted-text object (DrawBot `FormattedString`): runs with their own font, size, colour, tracking and features, drawn with `text` and `text_box`

### S-092 SVG import — E-16 *(D-041 = A; contract P11)*
- [x] S-092.1 `funground/svg.py` (only importer of svgelements); `f.load_svg(path)` → vector picture; `f.svg_paths(path)` → path builders
- [x] S-092.2 Tests with SVG files written by the tests; gallery `images/` (an original SVG drawn for the example); guide chapter 9; chapters 14/15 (`loadShape`); Quick Reference; changelog; THIRD_PARTY_LICENSES

### S-093 Spike: searchable PDF text — E-15 ✅
*Result:* `spikes/09_pdf_text/README.md`.
- Cairo cannot embed our TTFs: pycairo has no FreeType.
- An invisible text layer added after Cairo writes the PDF works: pixel-identical drawing; ligatures and Hebrew/Arabic copy and search in 3 of 4 engines; +6% file size.
- It needs `pypdf` (BSD, 0.4 MB).
- Raised as D-043 for the maintainer.
- [x] S-093.1 Can funground embed its fonts in PDFs so text is selectable and searchable (lifting D-006's limit) with pycairo, without new dependencies? Report options, effort and a recommendation; build nothing beyond the spike
### S-094 Real text in PDFs — E-15 *(D-043 = D; contract T15)*
- [ ] S-094.1 Spike-check, then build: Cairo draws each text run as a marker group; a pypdf post-step swaps each marker for real text with an embedded font subset
- [ ] S-094.2 Every PDF route (frame, document, picture save, pictures and SVGs drawn into a PDF); fallbacks (`fsType`, unsupported fonts); variable fonts as instances
- [ ] S-094.3 Tests: text extraction (pypdf, pdfium), rendering compared with the outline version, file size; guide chapters 6 and 10; changelog; THIRD_PARTY_LICENSES

## Out of scope this sprint
Sound, GIF/MP4, controls and the release (Sprint 11).

## Findings collected for the review (from S-092 and the documentation pass)
- `stroke_width()` truncates floats (`int(pixels)`), against S6; `svg.py` works around it via the state.
- Picture names clash: the counter resets at `size()`/`run()`, so a picture loaded before it and the first `create_graphics` after it are both `graphics-1` (P3/P4 say creation order within a run). Snapshots only.
- `svg_paths` returns even-odd shapes as their original sub-paths, so `draw_path` fills the hole; P11 is silent.
- `Frame.ops` copies the op list on every call; scripts calling `get()` in a loop slow down as they grow (unmeasured).
- R16 does not say what `new_page` inside an open `push()` does (`unwind()` restores the outer style).
- Variable fonts: `text_ascent`/`text_descent` use default-instance metrics.
- No test saves a shadow or a blend mode to PDF.
- Stale: `docs/qa/Test_Strategy.md`, the `capabilities.py` comment, unused renderer libraries in `tests/test_boundaries.py`.
