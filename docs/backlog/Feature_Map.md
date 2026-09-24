# Feature map — Playground against p5.js / Processing and DrawBot

**Purpose.** Our stated goal is "functionality similar to Processing/p5 and DrawBot". This document
lists what those tools offer, area by area; what Playground has today (end of Phase 1); which epic
owns the gap; and which sprint it is planned for. It is the source for the Phase 2–3 story cuts
below and for `themes_and_epics.md`. Status: `have` · `planned (sprint)` · `epic, no stories` ·
`no epic` · `out of scope`.

Inventory taken from p5.js 1.x/2.0 and Processing 4 references and the DrawBot 3.x reference,
from memory on 25 Sept 2026 — story S-040 verifies it against the live docs before Sprint 5.

## 1. Sketch lifecycle and runtime

| Feature | p5 / Processing | DrawBot | Playground today | Owner | Plan |
|---|---|---|---|---|---|
| `setup()` / `draw()` loop, frame count, delta time, fps | ✅ | – (script model) | **have** | E-01 | — |
| Script (non-loop) execution: draw once, save | – | ✅ `newDrawing()`… | **have** via headless + `save()`; no "no draw() needed" form | E-12 | Sprint 5 |
| `no_loop()` / `loop()` / `redraw()` | ✅ | – | no epic | **E-29 Runtime controls** | Sprint 5 |
| `millis()`, `frame_rate()` query, `exit()` | ✅ | – | `stop()` only | E-29 | Sprint 5 |
| `full_screen()`, window resize, `resize_canvas()` | ✅ | – | no epic | E-29 | Sprint 6 |
| Pixel density / HiDPI | ✅ `pixelDensity()` | implicit | **have** (Windows); macOS/Linux S-038 | E-13 | Sprint 4 |
| Off-screen buffers (`createGraphics`) | ✅ | – (pages instead) | no epic | **E-28 Off-screen canvas** | Sprint 6 |
| Pages / multi-page documents, page sizes (A4…) | – | ✅ `newPage`, `size("A4")` | epic, no stories | E-18 | Phase 3 |

## 2. Shapes and drawing attributes

| Feature | p5 | DrawBot | Today | Owner | Plan |
|---|---|---|---|---|---|
| point, line, rect, ellipse, circle | ✅ | ✅ | **have** | — | — |
| `square`, `triangle`, `quad`, `arc`, `polygon` | ✅ (arc modes) | `polygon`, `arc`, `arcTo` | no epic | **E-24 Drawing vocabulary** | Sprint 5 |
| Stroke cap / join / miter / **dash** | ✅ cap, join | ✅ incl. `lineDash` | fixed round cap+join in renderer | E-24 | Sprint 5 |
| `rect_mode` / `ellipse_mode` (corner/center/radius) | ✅ | – | postponed by decision (contract F3) | E-24 | revisit Phase 3 |
| Anti-aliasing toggle (`noSmooth`) | ✅ | – | always on | E-24 | Sprint 5 (opt-out) |
| Vertex shapes: `beginShape/vertex/endShape`, contours (holes) | ✅ incl. TRIANGLES/QUADS modes | via BezierPath | **planned (Sprint 4)** basic; holes/modes later | E-11 | Sprint 4 / 5 |
| Bézier & quadratic curves, `curve()` (Catmull-Rom) | ✅ | ✅ | **planned (Sprint 4)** bezier; Catmull-Rom no | E-11 | Sprint 5 |
| Reusable path object (`BezierPath`), `drawPath`, `clipPath` | Processing `PShape` | ✅ | **planned (Sprint 4)** | E-11 | Sprint 4 |
| Path geometry: bounds, `pointInside`, boolean ops (union/intersect/difference), `expandStroke`, `optimizePath` | – | ✅ | no stories | E-11 | Phase 3 |
| Path from text (`BezierPath.text()`), trace image | – | ✅ | text→outlines exists internally | E-11/E-15 | Phase 3 |

## 3. Colour and compositing

| Feature | p5 | DrawBot | Today | Owner | Plan |
|---|---|---|---|---|---|
| RGB(A) 0–255, names, hex | ✅ | 0–1 floats | **have** | — | — |
| `color_mode(HSB/HSL)`, `color()` objects, `lerp_color`, component getters | ✅ | – | no epic | **E-25 Colour, gradients, compositing** | Sprint 5 |
| Linear / radial gradients (fill and stroke) | – (canvas API) | ✅ with stops | no epic (IR has none; Cairo supports) | E-25 | Sprint 6 |
| `blend_mode()` (multiply, screen, add …) | ✅ | ✅ | no epic | E-25 | Sprint 6 |
| Global opacity, shadow | – | ✅ `opacity`, `shadow` | no epic | E-25 | Sprint 6 |
| CMYK / colour spaces for print | – | ✅ | — | **out of scope** (document why in ADR) | — |

## 4. Transforms and state

| Feature | p5 | DrawBot | Today | Owner | Plan |
|---|---|---|---|---|---|
| translate / rotate / scale, push / pop, `with state()` | ✅ | ✅ `savedState()` | **planned (Sprint 4)** | E-10 | Sprint 4 |
| `shear` / `skew`, `apply_matrix`, `reset_matrix` | ✅ | ✅ `skew`, `transform` | IR supports; no story | E-10 | Sprint 5 |

## 5. Text and typography

| Feature | p5 | DrawBot | Today | Owner | Plan |
|---|---|---|---|---|---|
| `text`, `text_size`, deterministic default font | ✅ | ✅ | **have** (outlines, DejaVu) | E-15 | — |
| `text_width`, ascent/descent/cap-height metrics | ✅ | ✅ | **planned (Sprint 4)** width only | E-15 | Sprint 4 / 5 |
| `text_align` (left/center/right × top/baseline/bottom) | ✅ | in `textBox` | no story | E-15 | Sprint 5 |
| Multi-line text, `text_leading`, word-wrap in a box (`textBox`, overflow) | ✅ box form | ✅ | no story | E-15 | Sprint 6 |
| `font()` / `load_font()` from file, bold/italic style | ✅ | ✅ | no story (mechanism ready) | E-15 | Sprint 6 |
| Rich text runs (`FormattedString`: mixed fonts/sizes/colours, tracking, OpenType features, variable fonts) | – | ✅ | `TextRun` reserved | E-15 | Phase 3 |
| Hyphenation, language, glyph lists, installed-font enumeration | – | ✅ | — | E-15 | Phase 3 (partial) / out of scope |
| Searchable text in PDF (embedded fonts) | ✅ | ✅ | outlines only (accepted, D-006) | E-12 | Phase 3 (S-032) |

## 6. Images and pixels

| Feature | p5 | DrawBot | Today | Owner | Plan |
|---|---|---|---|---|---|
| `load_image`, `image(img, x, y, w, h)`, `image_mode` | ✅ | ✅ `image(path, (x,y), alpha)` | none | E-14 | Phase 3, Sprint 7 |
| `tint`, image alpha | ✅ | ✅ | none | E-14 | Sprint 7 |
| Pixel access (`get`/`set`, `pixels[]`), `copy`, `resize`, `mask` | ✅ | `imagePixelColor` | none | E-14 | Sprint 8 |
| Filters (blur, invert, threshold …), image filters library | ✅ (few) | ✅ (~100 Core Image) | none | E-14 | Sprint 8 (few); rest out of scope |
| SVG import | (as image) | ✅ | epic, no stories | E-16 | Phase 3 |
| Save canvas as image / frames sequence / **GIF** / video | ✅ `saveCanvas`, `saveFrames`, `saveGif` | ✅ mp4/gif via `frameDuration` | PNG/PDF/SVG **have** | E-12 / E-19 | Sprint 6 (frames), Phase 3 (gif/mp4) |

## 7. Input and events

| Feature | p5 | DrawBot | Today | Owner | Plan |
|---|---|---|---|---|---|
| Mouse position & pressed (polled) | ✅ | – | **have** | — | — |
| Previous mouse (`pmouseX`), `mouse_button`, wheel, drag | ✅ | – | no epic | **E-26 Input events** | Sprint 5 |
| Event callbacks: `mouse_pressed()`, `mouse_released()`, `mouse_moved()`, `key_pressed()`, `key_released()`, `key` / `key_code` last-key values | ✅ | – | no epic | E-26 | Sprint 5 |
| Touch, gamepad | ✅ touch | – | none (pygame has both) | E-26 | Phase 3 |
| Cursor control (`cursor()`, `noCursor()`) | ✅ | – | no epic | E-26 | Sprint 6 |

## 8. Math, randomness, helpers

| Feature | p5 | DrawBot | Today | Owner | Plan |
|---|---|---|---|---|---|
| `random`, `random_seed`, `constrain`, `distance` | ✅ | ✅ | **have** | — | — |
| `map`, `lerp`, `norm`, `mag`, `random_gaussian`, `random_choice` | ✅ | – | no epic | **E-27 Creative-coding helpers** | Sprint 5 |
| `noise()` (Perlin/simplex) + `noise_seed` | ✅ | – | no epic | E-27 | Sprint 5 |
| `Vector` (add, mult, mag, normalize, heading, rotate, dist) | ✅ `p5.Vector` | – | no epic | E-27 | Sprint 6 |
| Time helpers (`millis`, `second`, `minute`, `hour`) | ✅ | – | no epic | E-29 | Sprint 5 |
| Data loading (JSON/CSV/strings) | ✅ | – | plain Python suffices | out of scope (document) | — |

## 9. Sound

| Feature | p5.sound | DrawBot | Today | Owner | Plan |
|---|---|---|---|---|---|
| Load & play sound, volume, loop | ✅ | – | none | E-17 | Phase 3 |
| Amplitude / FFT analysis, oscillators | ✅ | – | none | E-17 | Phase 3 (analysis) / out of scope (synthesis) |

## 10. UI controls, 3D, misc

| Feature | p5 | DrawBot | Today | Owner | Plan |
|---|---|---|---|---|---|
| Sliders / variables UI (`Variable()`) | (p5.dom) | ✅ | none | **E-30 Controls** (arch doc Phase 3 "controls") | Phase 3 |
| 3D primitives, camera, lights, shaders | ✅ WEBGL | – | none | E-20/E-21 | Phase 4, directional |
| Print / `printImage` | – | ✅ | — | out of scope | — |

## Summary of gaps that had no epic

New epics proposed (added to `themes_and_epics.md`):

| Epic | Theme | Covers |
|---|---|---|
| **E-24 Drawing vocabulary completeness** | TH-3 | square, triangle, quad, arc, polygon; stroke cap/join/dash/miter; AA opt-out; modes revisit |
| **E-25 Colour, gradients and compositing** | TH-3 | HSB/HSL colour mode, colour objects, lerp; linear/radial gradients; blend modes; opacity; shadow |
| **E-26 Input events** | TH-1/TH-4 | previous mouse, buttons, wheel, drag; event callbacks; last key; cursor; touch/gamepad later |
| **E-27 Creative-coding helpers** | TH-1 | map, lerp, norm, gaussian, choice; noise; Vector |
| **E-28 Off-screen canvas** | TH-3 | `create_canvas()` buffers drawn with the same API, used as images |
| **E-29 Runtime controls** | TH-1 | no_loop/loop/redraw, millis, frame_rate query, exit, full screen, resize, script mode |
| **E-30 Controls** | TH-4 | sliders/toggles bound to variables (DrawBot `Variable`) |

Explicitly **out of scope**, to be recorded in ADR-003: CMYK/print colour spaces; sound synthesis;
DrawBot's ~100 Core Image filters (a handful via Pillow instead); data-loading helpers (Python has them).

## Proposed Phase 2 sequence (Sprints 4–6): "the p5 core"

| Sprint | Theme | Stories |
|---|---|---|
| 4 (planned) | transforms, state, paths, text width, Quick Reference v0.6 | S-027, S-028, S-037, S-038, S-030, S-039 |
| 5 | **vocabulary + events + helpers** | S-041 shapes (square/triangle/quad/arc/polygon) · S-042 stroke cap/join/dash · S-043 shear/apply_matrix · S-044 colour mode HSB/HSL + `color()`/`lerp_color` · S-045 input events & callbacks · S-046 helpers (map/lerp/norm/gaussian/choice) · S-047 noise · S-048 runtime controls (no_loop/redraw/millis) · S-049 text_align + metrics |
| 6 | **compositing + canvases + text layout** | S-050 gradients · S-051 blend modes/opacity/shadow · S-052 off-screen canvas · S-053 multi-line text/word-wrap/leading · S-054 load_font + styles · S-055 Vector · S-056 save_frames sequence · S-057 cursor/full_screen/resize · Quick Reference v0.7 |

**Phase 2 exit:** a learner can port a typical p5 "core" sketch (shapes, transforms, colour modes,
events, noise, text) and a typical DrawBot single-page composition (paths, gradients, text box,
PDF) with only naming changes. Phase 3 then adds images, pages, rich typography, SVG import,
sound, GIF/video, controls.
