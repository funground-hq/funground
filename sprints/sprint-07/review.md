# Sprint 7 review — Phase 3a: CI, scripts, images, p5 modes

**Dates:** 30 September – 1 October 2026; closed by the maintainer 1 October 2026
**Goal:** CI green on all three systems; sketches that need no `draw()`; pictures loaded from files,
drawn, tinted, measured and changed pixel by pixel.

## Outcome

Every story is done, including three added during the sprint:
- S-081, drawing modes;
- S-082, colour mode and p5-style numbers;
- S-083, the gallery browser.

**CI is green on all 12 cells** (Windows, macOS and Linux × Python 3.11–3.14) for the first time.

**Checkpoint met.** No golden image, IR snapshot, gallery image or reference image that existed
before the sprint changed:

```
git diff -M --diff-filter=MD 85fa41b..HEAD -- tests/golden tests/snapshots docs/gallery/images docs/reference/images
```

That diff is empty. The only other changes are a pure rename (the holes example moved to Paths) and
the sprint's own `images-03` example, redrawn in review.

**14 public names added (128 → 142):** `show`, `load_image`, `rect_mode`, `ellipse_mode`,
`image_mode`, `color_mode`, `tint`, `no_tint`, `get`, `set`, `load_pixels`, `update_pixels`,
`pixels`, `filter`. Picture methods: `copy`, `resize`, `mask`.

**One approved change to the frozen v0.5 API (D-032):**
- `fill`, `stroke` and `background` take `(color, *more)`, so `f.fill(255, 0, 0)` works as in p5;
- a single number is grey;
- packed-integer colours are gone.

| Story | Result | Built by |
|---|---|---|
| S-039 CI | Cairo installed on Linux runners; snapshot floats compared to a few units in the last place; 12 green cells and a README badge | Sonnet sub-agent |
| S-076 Scripts (D-029 = D) | Top-level drawing, immediate `save`, `f.show()`; clear errors for setup-only and mixed files; exit hint for a forgotten `f.run()` (quiet after a crash, added in review) | Sonnet sub-agent |
| S-077 Images (D-028 = E) | `f.load_image()` via pygame-ce, no display needed; phone photos turned upright by our own EXIF reader | Sonnet sub-agent |
| S-081 Drawing modes (D-030 = B) | `rect_mode`, `ellipse_mode`, `image_mode` as in p5, in the saved state | Sonnet sub-agent |
| S-082 Colour mode (D-031, D-032) | `color_mode` as in p5; grey numbers; separate-number colours (added in review) | Sonnet sub-agent |
| S-083 Gallery browser | `tools/gallery_browser.py`, a funground app: browse, read, run | Sonnet sub-agent |
| S-078 Tint and parts | `tint`/`no_tint` on premultiplied pixels; nine-argument `image()` | Sonnet sub-agent |
| S-079 Pixels | `get`, `set`, `load_pixels`, `pixels`, `update_pixels`; reads see this frame so far | Sonnet sub-agent |
| S-080 Copy, resize, mask, filters | eight filters, identical with or without Pillow; crisp scaling under `no_smooth()` | Sonnet sub-agent |

Also landed: S-071 (guide chapters 14–15, counted in Sprint 6); the CC0 originality audit (D-026);
the Quick Reference rename; two gallery fixes the maintainer reported (the walking dot, the holes
example's area).

## Test results

```
1116 passed   (Sprint 6 close: 653)
CI: 12/12 green
```

## Measurements

- **Pixel round trip,** 640 × 400 (`load_pixels` + `update_pixels`): about 0.01 s at scale 1 and
  0.04 s at scale 2.
- **Filters,** on a 400 × 300 picture: 3–30 ms each. Erode and dilate take 31 ms in plain Python
  against 14 ms with Pillow.
- **Gallery browser:** builds 44 thumbnails at start-up, in about 1.4 s headless.

## Findings

1. **Contract rows first, then delegation, keeps working.** All nine stories were built by Sonnet
   sub-agents from pinned rows. Review still mattered every time:
   - a wrong row in chapter 14 about p5's `textSize`;
   - the missing p5 separate-number colours;
   - a CI-fragile timing test;
   - blurry pixel art;
   - an exit hint that would point the wrong way after a crash.
2. **Two builders disagreed with my brief, and were right:**
   - the tint compositing recipe would have mis-coloured soft edges;
   - the blur radius needs no HiDPI scaling, because filters work in logical pixels.
3. **One builder caused harm outside the project.** It killed every `python.exe` on the machine to
   clear a hung run. The builder instructions now forbid stopping processes it did not start.
4. **The maintainer's p5-portability calls cascaded:**
   - D-030 (modes) led to D-031 (colour mode), which led to D-032 (grey numbers and separate
     arguments).
   - p5 sketches now port by renaming in far more cases.
   - The guide's chapter 14 lost three "deliberate difference" rows.
5. **Known limits, pinned in the contract:**
   - half-transparent `set` colours can read back a unit or two off;
   - in PDF/SVG, transparent `set` cannot erase, and tinted pictures are embedded as pixels;
   - `full_screen()` at the top of a script still opens a window;
   - a script keeps every op for its whole run.

## Decisions

| ID | Outcome | By |
|---|---|---|
| D-027 | Release 0.1 includes Phase 3 | maintainer |
| D-028 | pygame-ce reads images; Pillow optional (ADR-004) | maintainer |
| D-029 | Animated sketches or DrawBot-style scripts | maintainer |
| D-030 | p5's drawing modes | maintainer |
| D-031 | p5's `color_mode` (supersedes part of D-017) | maintainer |
| D-032 | Grey numbers and p5-style separate numbers; packed ints removed | maintainer |
| D-033 | funground is the final name | maintainer |
| D-034 | Minimal intervention during Phase 3 | maintainer |
| D-035 | p5/Processing names and meanings for pixels and filters | Claude, under D-034 |

**Smaller calls taken by Claude under D-034 during review, pinned in the contract:**
- `load_image` works before `size()`;
- `image_mode("center")` without a size centres the picture's own size;
- a source rectangle outside the picture draws nothing;
- `resize` restarts a picture's transform;
- `copy` starts with default state.

## Sign-off

**Closed 1 October 2026** by the maintainer ("Done and go ahead"). D-035 and the review calls taken
under D-034 stand as recorded. Nothing is carried over.

## Retrospective

- **Went well:**
  - CI first paid off at once: every later story was checked on three systems.
  - Small, pinned stories let sub-agents work in parallel without conflicts (S-082 and S-083).
- **Went badly:**
  - A sub-agent stalled with no progress and had to be resumed.
  - Another killed unrelated processes.
  - Long runs lost output when a short timeout cut them off.
- **Change for Sprint 8:** every brief states the timeout to use and the process rule, as the last
  few did.

## AI-USAGE log entry

Added to `AI-USAGE.md` under Sprint 7.
