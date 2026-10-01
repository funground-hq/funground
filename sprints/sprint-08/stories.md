# Sprint 8 — Phase 3b: documents and pages

**Dates:** opened 1 Oct 2026 under D-034 (minimal intervention); **closed by the maintainer 1 Oct 2026** (`review.md`).
**Release context (D-027):** part of release 0.1, after Phase 3.

**Goal:** DrawBot-style documents. A script draws pages of any size and saves them as one
multi-page PDF; `show()` flips through them. Plus the script follow-ups from Sprint 7.

**Checkpoint:** every existing golden and snapshot is unchanged; every new public name has a
contract row, tests, a gallery example with golden, snapshot and originality check, a guide
section and a Quick Reference entry. CI is green on 12 cells.

**Who builds:** Sonnet `story-builder` sub-agents from pinned contract rows; review, commits,
pushes and CI stay with the main session.

## Decisions
- D-036 (decided by Claude under D-034): the page API shape. Contract R16, R17, D1.

## Story set

### S-084 Pages and page sizes — E-18 *(contract R16, R17, D1)*
- [x] S-084.1 `new_page`, `page_count`, `page_size`; per-page state rules; the current page for drawing and pixels
- [x] S-084.2 Multi-page PDF; numbered PNG/SVG; `show()` flipping pages with the arrow keys
- [x] S-084.3 Tests; gallery `documents/` (a short multi-page booklet); a new guide section in chapter 2 or 13; Quick Reference; changelog
*Acceptance:* a DrawBot script with `newPage("A4")` and `saveImage("x.pdf")` ports by renaming, with the y-flip and colours handled as chapter 15 shows.

### S-085 Script follow-ups — E-18
- [x] S-085.1 `full_screen()` at the top level of a script: makes the canvas the screen size without opening a window (it opens with `show()`), headless 1920 × 1080 as R12
- [x] S-085.2 Pin and test the memory behaviour: a script keeps every op; document a rough size limit in the guide

## Out of scope this sprint
Path booleans (Sprint 9), typography and SVG (Sprint 10), sound, video, controls, release (Sprint 11).
