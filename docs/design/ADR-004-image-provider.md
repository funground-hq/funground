# ADR-004: Image files are read by pygame-ce; Pillow is an optional extra

**Status:** Accepted 1 October 2026 (D-028 = E). Refines the image line of ADR-003 ("a handful via
Pillow") and the Images row of the Roadmap.
**Date:** 1 October 2026

## Context

Phase 3 brings images to funground (Sprint 7, stories S-077 to S-080):
- loading the files learners bring, mostly PNG and JPEG photos;
- drawing, tinting and changing their pixels;
- resizing and a few filters.

Cairo, the renderer, reads only PNG. So a second library must read image files, and possibly do
the filters. The roadmap had assumed Pillow, which would add about 6 MB to every install.

pygame-ce is already a dependency (the window and input, ADR-001). Checked on 1 October 2026
with pygame-ce 2.5.8 and no display:
- it reads and writes PNG, JPEG, BMP and TGA, keeping transparency where the format has it;
- it reads animated GIFs (`load_animation`) and renders SVG files to images (`load_sized_svg`);
- its `transform` module has smooth resizing, Gaussian and box blur, grey, invert and threshold;
- it cannot write WebP or animated GIFs;
- it ignores the orientation tag in phone photos;
- its fast whole-image pixel arrays need numpy, which funground does not install.

## Options

- **A. pygame-ce only.**
- **B. Pillow in the base install.**
- **C. Pillow as an optional extra, PNG only without it.**
- **D. PNG only, through Cairo.**
- **E. pygame-ce in the base install with funground's own orientation fix; Pillow as an optional
  extra for what pygame-ce cannot do.**

The trade-offs are in the decision log, D-028.

## Decision

**E.**

- **pygame-ce decodes every image file** in the base install. All decoding goes through one module,
  `funground/imaging.py`. It is the only place outside `platform/` allowed to import pygame (the
  provider boundary, tests/test_boundaries.py).
- **funground reads the JPEG orientation tag itself** (EXIF, plain Python) and turns phone photos
  the right way up.
- **Resizing and the blur, grey, invert and threshold filters use pygame-ce.**
- **Pillow is an optional extra:** `pip install funground[extras]`. It is used only for what
  pygame-ce cannot do:
  - writing animated GIFs (Sprint 11);
  - the rarer filters (posterise, erode, dilate) at full speed.

  Without it, those features either work slowly in plain Python on small pictures, or give an
  error saying which extra to install. Each story pins which.
- **Files are decoded one way only**, by pygame-ce, so the same file gives the same pixels on every
  install, with or without Pillow.

## Consequences

- **The base install does not grow.**
- **pygame-ce gains a second role,** reading image files, besides window and input. It stays behind
  one module, so it can be replaced later without touching the rest.
- **Video export (MP4) still needs ffmpeg** whatever this decision says. That is a Sprint 11
  decision.
- **Pixel access without numpy is per-pixel and slower.** Stories that need speed say how they
  achieve it.
