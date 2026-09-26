# Playground roadmap to 1.0

**Status:** agreed direction, 25 September 2026 (D-014); release numbering changed 26 September 2026 (D-019). Sprint numbers show sequence, not
dates; sprint length is the maintainer's call. The backlog (`docs/backlog/`) holds the stories;
`docs/backlog/Feature_Map.md` holds the feature-by-feature comparison this roadmap is built from.

> **1.0 is desktop, Cairo, 2D — with as much of DrawBot's and Processing's 2D functionality as we
> can provide.** Browser rendering, GPU and 3D are directional: the architecture keeps them
> possible (the IR is backend-neutral, proven by Spikes 07 and 08) but none is on the path to 1.0.

## Done

| Phase | Sprints | Outcome |
|---|---|---|
| 0 Stabilise v0.5 | 0 | v0.5 frozen as executable tests: API, semantics, Session-1 sketches, goldens |
| 1 Architecture | 1–3 | `Sketch`, platform split, draw-op IR, Cairo renderer, text as outlines (DejaVu Sans), HiDPI (Windows), headless, PNG/PDF/SVG export |
| 2a Public vocabulary | 4 | transforms, `push/pop`, `with p.saved_state():`, paths and clipping, `text_width`, Quick Reference v0.6 *(awaiting sign-off)* |

## Phase 2 — the p5/Processing core (Sprints 5–6) → release **0.1**, the first PyPI release (D-019)

**Exit:** a typical p5/Processing 2D sketch and a typical DrawBot single-page composition port
with only naming changes.

**0.1 deliverables:** the code; a **User Guide** (`docs/guide/`, chapters from getting started to
"coming from p5/DrawBot"); an **Examples Gallery** (`examples/gallery/`, rendered index in
`docs/gallery/`) with at least one example for every public name — enforced by a coverage test.
Both grow story by story from Sprint 5 and are finished in Sprint 6.

| Sprint | Content |
|---|---|
| 5 — vocabulary, events, helpers | Feature Map verified (S-040); gallery and guide foundations (S-068, S-069); `square/triangle/quad/arc/polygon`; stroke cap/join/dash/miter, `no_smooth`; shear/`apply_matrix`/`reset_matrix`; `color_mode` HSB/HSL, `color()`, `lerp_color`; input events and callbacks, `pmouse`, buttons, wheel; `map_range/lerp/norm/random_gaussian/random_choice`; `noise`; `no_loop/loop/redraw/millis/frame_rate/exit`; ADR-003; Sprint 4 follow-ups |
| 6 — compositing, canvases, text layout, release | `text_align` and text metrics; linear/radial gradients; blend modes, opacity, shadow; off-screen canvas (Processing `PGraphics`); multi-line text, leading, word-wrap in a box; `load_font`, bold/italic; `Vector`; frame-sequence export; cursor, full screen, resize; User Guide and Gallery completed; Quick Reference for 0.1; PyPI packaging; release 0.1 |

**Release 0.1** after Sprint 6: the first release published on PyPI (D-019). v0.5 was a
teaching zip, never published, so public numbering starts again at 0.1. Prerequisites: git remote,
CI green on the 12-cell matrix (S-039). The package is published as **funground**
(D-020, renamed in S-075): `pip install funground`, then `import funground as f`.

## Phase 3 — DrawBot and Processing depth (Sprints 7–11) → releases **0.2, 0.3, …**

**Exit:** DrawBot-style document work and Processing-style media sketches are both at home.

| Area | Content | Parity with |
|---|---|---|
| Images (E-14) | `load_image`, `image()` with transform, tint/alpha, `image_mode`; pixel access (`get/set`, `pixels`), `copy`, `resize`, `mask`; a handful of filters via Pillow (blur, invert, threshold, grey) | Processing `PImage`, DrawBot `image` |
| Documents (E-18) | pages and page sizes (A4, Letter…), `new_page`, multi-page PDF; a first-class script mode (no `draw()` needed: draw once, save) | DrawBot's core model |
| Path depth (E-11) | boolean operations (union, intersect, difference, xor), `point_inside`, bounds, `expand_stroke`, text to path, reusable shapes (Processing `PShape`) | DrawBot `BezierPath`, Processing `PShape` |
| Rich typography (E-15) | mixed-style text runs (DrawBot `FormattedString`), tracking, OpenType features, variable fonts, per-script font fallback; **searchable PDF text with embedded fonts** (S-032, lifts D-006's limitation) | DrawBot text |
| SVG import (E-16) | `load_svg` via resvg-py, as image or as paths | Processing `loadShape`, DrawBot |
| Sound (E-17) | load/play/loop/volume; amplitude and FFT for visualisers; no synthesis | Processing Sound (basic) |
| Motion export (E-19) | GIF and MP4 via ffmpeg | DrawBot `saveImage("x.mp4")`, p5 `saveGif` |
| Controls (E-30) | sliders/toggles bound to sketch variables | DrawBot `Variable` |

Engine watch continues (S-036): if the Blend2D binding matures, re-run the Spike 07 bake-off.

## Toward 1.0 (Sprints 12–14) → release **v1.0**

**Exit:** stable, documented, teachable; no known contract gaps.

- API review and freeze for 1.0; any deprecations resolved.
- macOS/Linux HiDPI verified on real hardware (S-038 follow-up).
- Documentation: complete reference, tutorials, a curriculum sequence built from the Session
  sketches, migration notes from v0.5.
- Performance pass driven by profiling (e.g. moving hot IR walks into the renderer).
- Error messages reviewed for learners; localisation optional.

## Directional — after 1.0 (D-014)

| Track | Epic | State |
|---|---|---|
| Playground in the browser | E-31 | Feasible (Spike 08: 0.8 ms frames in wasm, Canvas 2D page over the IR verified); plan in `docs/design/Browser_Mode_Note.md` |
| GPU renderer | E-20 | IR consumer; Skia or a GPU engine re-evaluated when needed |
| 3D (Processing P3D) | E-21 | Not in 1.0; 1.0 means the 2D surface |

## Deliberately out of scope — [ADR-003](design/ADR-003-out-of-scope.md)

CMYK/print colour spaces; sound synthesis; DrawBot's large Core Image filter library (a handful
via Pillow instead); Processing's data, serial, network and video/camera libraries (plain Python
covers most of these).

## Milestones

```
Sprint 5 ── Sprint 6 ── 0.1 on PyPI ── Sprints 7–11 ── 0.2, 0.3 … ── Sprints 12–14 ── 1.0 ─ ─ directional: web, GPU, 3D
```

## Decisions ahead

| When | Decision |
|---|---|
| Before 0.1 | Release cadence; git remote and CI host (the name is decided: funground, D-020) |
| Sprint 5 | `rect_mode`-style switches (postponed so far); D-016, D-017, D-018 decided 25 Sept 2026 |
| Sprint 6 | Whether off-screen canvases and images share one type |
| Phase 3 | Page/document model shape (DrawBot-like vs Processing-like); sound backend scope |
| v1.0 | What "1.0 stable" guarantees: API freeze scope, supported Python versions |

## Risks

- **Scope:** Phase 3 is as large as everything so far; holding "Phase 2 portability first" keeps the arc honest.
- **Review bandwidth:** the sign-off gate is the bottleneck by design; larger sprints need more maintainer time.
- **Dependencies:** pycairo, uharfbuzz and fontTools versions; CI is the early warning and is not running yet.
