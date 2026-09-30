# Sprint 7 — Phase 3a: CI, script mode, images

**Dates:** opened 30 Sept 2026 on the maintainer's word ("Begin phase 3").
**Release context (D-027):** release 0.1 now includes Phase 3. It is published on PyPI when
Phase 3 is complete, after Sprint 11. Nothing is published before then.

**Goal:** CI green on all three systems; sketches that need no `draw()`; pictures loaded from
files, drawn, tinted, measured and changed pixel by pixel.

**Checkpoint:** every existing golden and IR snapshot is unchanged; every new public name has a
contract row, tests, a gallery example with golden and snapshot, a guide section and a Quick
Reference entry; every new example passes `tools/check_originality.py` (D-026).

**Who builds:** stories with a pinned contract row go to the Sonnet `story-builder`; mechanical
edits to the Haiku `mechanical-editor`; design, decisions, review, commits and pushes stay with
the main session (PROCESS.md, "Who does what").

## Ordering

1. S-039 (CI): no decision needed; first.
2. S-076 (script mode) after D-029.
3. S-077 → S-078 → S-079 → S-080 (images) after D-028.
4. S-081 (modes) only if D-030 says so.

## Decisions to take, one per turn

- **D-028 Image files: which library reads and processes them.** Cairo reads PNG only. JPEG and
  the other formats, resizing and filters need a library such as Pillow, which would be a new
  dependency in the base install. Needed before S-077.
- **D-029 Sketches without `draw()`.** Today `f.run()` needs a `draw()` function (a v0.5 rule).
  p5 allows a sketch with only `setup()`, and DrawBot needs no functions at all. Needed before
  S-076.
- **D-030 `rect_mode`, `ellipse_mode`, `image_mode`.** Postponed since Sprint 4 (contract F4).
  Images make the question come up again. Needed before S-081.

## Story set

### S-039 CI green on Windows, macOS and Linux — E-02 *(carried from Sprints 4–6)*
First run, 26 Sept 2026: the four Windows cells pass; Linux and macOS fail.
- [ ] S-039.1 Linux: install the Cairo development files in the workflow so `pycairo` builds;
  add the same line to the guide's install page and the README
- [ ] S-039.2 macOS: IR snapshots differ in the last digit of some numbers (the maths library
  rounds `sin`/`cos` differently). Compare snapshot numbers with a tolerance of a few units in
  the last place; structure, names and strings stay exact. No snapshot file is regenerated
- [ ] S-039.3 All 12 cells green; a CI badge in the README
*Acceptance:* a push to `main` shows 12 green cells.

### S-076 Script mode: sketches without `draw()` — E-18 *(needs D-029)*
- [ ] S-076.1 Per D-029
- [ ] S-076.2 Contract row; tests; gallery example; guide chapter 2; Quick Reference
*Acceptance:* a DrawBot-style static page runs and saves with no `draw()` function.

### S-077 Load and draw images — E-14 *(needs D-028)*
- [ ] S-077.1 `f.load_image(path)` returns a picture (the same type as `create_graphics`,
  D-021): found next to the sketch file first, like `load_font`; clear errors for a missing file
  and for a file that is not an image
- [ ] S-077.2 `f.image(pic, x, y, w=None, h=None)` draws it under transform, clip, blend and
  opacity (contract P3 already says so); PDF/SVG embed its pixels
- [ ] S-077.3 Contract rows; tests; gallery `images/`; a new guide chapter "Pictures and images";
  Quick Reference
*Acceptance:* a Processing `loadImage`/`image` sketch ports by renaming only.

### S-078 Tint and parts of images — E-14
- [ ] S-078.1 `f.tint(colour)` / `f.no_tint()`: colour and transparency applied to images
- [ ] S-078.2 Drawing part of a picture: a source rectangle, as p5's nine-argument `image()` and
  Processing's `copy()` do
- [ ] S-078.3 Contract rows; tests; gallery; guide; Quick Reference

### S-079 Pixels — E-14
- [ ] S-079.1 `pic.get(x, y)` returns a colour; `pic.set(x, y, colour)`; the same on the canvas
  with `f.get_pixel` / `f.set_pixel` (names to be pinned in the contract row)
- [ ] S-079.2 Whole-picture access for speed: load, change, update
- [ ] S-079.3 Contract rows; tests; gallery (a picture made pixel by pixel); guide; Quick Reference
*Acceptance:* reading a pixel returns what was drawn there, on HiDPI screens too.

### S-080 Resize, copy, mask and a few filters — E-14 *(scope depends on D-028)*
- [ ] S-080.1 `pic.copy()`, `pic.resize(w, h)`, `pic.mask(other)`
- [ ] S-080.2 `pic.filter(kind)`: blur, grey, invert, threshold. ADR-003 limits this to a handful
- [ ] S-080.3 Contract rows; tests; gallery; guide; Quick Reference

### S-081 Drawing modes — E-24 *(only if D-030 says so)*
- [ ] S-081.1 Per D-030

## Out of scope this sprint
Pages and multi-page documents (Sprint 8); path booleans (Sprint 9); rich typography and SVG
import (Sprint 10); sound, GIF and video export, controls, and the release (Sprint 11).
