# Sprint 10 — Phase 3d: typography and SVG

**Dates:** opened 1 Oct 2026 under D-034. Sprint 9 closed by the maintainer the same day.
**Release context (D-027):** part of release 0.1, after Phase 3.

**Goal:** richer text (tracking, OpenType features, variable fonts, mixed styles in one text),
rounded corners, and SVG files loaded as vector drawings; a spike on searchable PDF text.

**Checkpoint:** existing goldens and snapshots unchanged; each new public name has a contract row,
tests, a gallery example (golden, snapshot, originality check), a guide section and a Quick
Reference entry; CI green on 12 cells. Other tools' API names are cited with where they were checked.

**Decisions:** D-040 rounded corners (maintainer); D-042 typography names (Claude, D-034);
**D-041 SVG library: pending, the maintainer's call (a new dependency)**.

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

### S-092 SVG import — E-16 *(needs D-041)*
- [ ] S-092.1 `f.load_svg(path)` returns a picture drawn from the SVG's shapes (vector in PDF/SVG); paths available for booleans

### S-093 Spike: searchable PDF text — E-15 ✅
*Result:* `spikes/09_pdf_text/README.md`.
- Cairo cannot embed our TTFs: pycairo has no FreeType.
- An invisible text layer added after Cairo writes the PDF works: pixel-identical drawing; ligatures and Hebrew/Arabic copy and search in 3 of 4 engines; +6% file size.
- It needs `pypdf` (BSD, 0.4 MB).
- Raised as D-043 for the maintainer.
- [x] S-093.1 Can funground embed its fonts in PDFs so text is selectable and searchable (lifting D-006's limit) with pycairo, without new dependencies? Report options, effort and a recommendation; build nothing beyond the spike

## Out of scope this sprint
Sound, GIF/MP4, controls and the release (Sprint 11).
