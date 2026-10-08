# Sprint 19 — 0.2: a faster core, measured in the browser

**Dates:** from 8 October 2026, on `release-0.2-web`.
**Goal:** make funground's own per-call work cheaper, cleanly, so heavy sketches run faster on the
desktop and in the browser; then re-measure both web routes for D-075.

**Rule for this sprint (maintainer, 8 Oct):** fixes are designed, not patched in. S-143's monkeypatches
measured what each change is worth; the product versions are clear, idiomatic changes with tests that
prove the output is unchanged (IR snapshots and goldens untouched), and a short design note where a
design changes. No tricks only a profiler could justify.

| Story | Value | Status |
|---|---|---|
| S-060 | Run loop as start/step/finish (L1, D-074). Merged from the S-136 spike after review; full suite was green (3620) | done |
| S-144 | Style calls stop copying the whole graphics state through `dataclasses.replace` | done |
| S-145 | A colour string is parsed once, through a named, bounded cache | done |
| S-146 | `Vector` (and the same number checks elsewhere) accept plain int and float without the ABC check | done |
| S-147 | Text outlines are scaled once per glyph and size, then only placed | done |
| S-149 | Public `Path.translated(dx, dy)` (D-076); `PathBuilder.translate` and text outlines use it | done |
| S-148 | Re-run the S-142 cases in Chrome on both routes with S-144–S-147; profile Pyodide phases; redo the D-075 matrix | planned |

Acceptance for S-144–S-147: the full suite green; no golden or snapshot changes; a before/after timing
on the S-143 examples it targets; the code reads as plainly as what it replaces.

- [x] S-060
- [x] S-144
- [x] S-145
- [x] S-146
- [x] S-147
- [x] S-149
- [ ] S-148
