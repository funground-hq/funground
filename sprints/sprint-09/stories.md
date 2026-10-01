# Sprint 9 — Phase 3c: path depth

**Dates:** opened 1 Oct 2026 under D-034 (minimal intervention); **closed by the maintainer 1 Oct 2026** (`review.md`).
**Release context (D-027):** part of release 0.1, after Phase 3.

**Goal:** DrawBot's path tools on funground's path builder: shapes combined with booleans,
overlaps removed, strokes turned into outlines, paths measured, tested and moved, and letters
turned into paths.

**Checkpoint:** every existing golden and snapshot unchanged; every new public name has a contract
row, tests, a gallery example (with golden, snapshot and originality check), a guide section and a
Quick Reference entry; CI green on 12 cells; the boundary test keeps `pathops` inside one module.

**Decisions:** D-037 = A (skia-pathops, the maintainer); D-038 (API, decided by Claude under D-034).

## Story set

### S-086 Path shapes and booleans — E-11 *(contract F11, ADR-005)*
- [x] S-086.1 `funground/pathops.py` (the only importer of `pathops`): Path ↔ Skia conversion; union, intersection, difference, xor, remove_overlap
- [x] S-086.2 Builder helpers `rect`, `ellipse`, `circle`, `polygon`; boolean methods and operators
- [x] S-086.3 Tests; gallery `paths/` (shapes cut and joined); guide chapter 9; chapter 15 (DrawBot `BezierPath` table); Quick Reference; changelog

### S-087 Stroke outlines, queries, transforms — E-11 *(contract F12)*
- [x] S-087.1 `expand_stroke`, `bounds`, `contains`, `translate`, `scale`, `rotate`, `copy`
- [x] S-087.2 Tests; gallery example; guide; Quick Reference; changelog

### S-088 Text as a path — E-15 *(contract F13)*
- [x] S-088.1 `f.text_path(message, x, y)` from the same layout as `f.text`
- [x] S-088.2 Tests; gallery example (letters cut out of a shape); guide chapter 6; Quick Reference; changelog

## Out of scope this sprint
Rich typography and SVG import (Sprint 10); sound, video, controls and the release (Sprint 11).
