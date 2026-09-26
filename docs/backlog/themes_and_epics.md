# Themes and epics

Status: `done` · `in progress` · `ready` · `directional` (architecture placeholder, not committed).
Phase exit criteria come from the architecture document, sharpened by the review.

## TH-1 Teaching Core Stability
*The Session-1 experience keeps working, provably, on every supported platform.*

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-01 Freeze and test the v0.5 contract | API inventory, semantics and Session-1 sketches are executable tests | 0 | done (Sprint 0) |
| E-02 Packaging, install and CI | `pip install` works; CI matrix Windows/macOS/Linux × 3.11–3.14; import-lint guards provider boundaries | 0–1 | in progress |

| E-26 Input events | previous mouse, buttons, wheel, drag; `mouse_pressed()`/`key_pressed()` callbacks; last key; cursor; touch/gamepad later | 2 | ready (Feature_Map §7) |
| E-27 Creative-coding helpers | `map`, `lerp`, `norm`, `random_gaussian`, `random_choice`; `noise`; `Vector` | 2 | ready (Feature_Map §8) |
| E-29 Runtime controls | `no_loop`/`loop`/`redraw`, `millis`, `frame_rate` query, `exit`, full screen, resize, script mode | 2 | ready (Feature_Map §1) |

**Phase 0 exit criterion:** semantics pinned, now-or-never defects fixed, sample suite green, API frozen. *Met in Sprint 0 except the DECISION rows, which are Sprint 1's first task.*

## TH-2 Architecture Foundation
*Playground owns its concepts; providers are replaceable; no learner-visible change.*

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-03 Public semantic contract | Every learner-visible rule written, decided and tested | 0–1 | done (D-012 pending on text size) |
| E-04 Sketch object and runtime split | `Sketch` + `_active_sketch`; facade in `api.py`; live values via `__getattr__` over the active sketch; two sketches per process possible | 1 | ready |
| E-05 Platform provider | `PygamePlatform` behind a `Platform` protocol: window, events, input, clock, presentation | 1 | ready |
| E-06 Draw-op IR and GraphicsState | Public calls record backend-neutral ops; `GraphicsState` owned by Playground; pygame drawing consumes the IR; op-list snapshot tests | 1 | ready |
| E-07 Capability registry and errors | Unsupported features fail at renderer selection with a message naming the extra to install | 1 | ready |

**Phase 1 exit criterion (D-007, three sprints):** Sprint 1 — refactor under pygame drawing, goldens byte-identical. Sprint 2 — IR + `LegacyPygameRenderer`, goldens byte-identical, IR snapshots established. Sprint 3 — Cairo default renderer, contract changes D-003/4/5 applied with one golden regeneration, HiDPI, headless, PNG/PDF/SVG, legacy renderer deleted. Learner code unchanged throughout; no `pygame` outside `platform/` (lint).

## TH-3 Design-Quality Rendering
*Correct vector semantics — transforms, paths, clipping, anti-aliasing, export — in the base install.*

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-08 Rasteriser decision | ADR-001 accepted: Cairo default 2D renderer, pygame platform + presentation, Skia/GPU future IR consumers | 1 | done (D-001) |
| E-09 Cairo renderer via IR | `CairoRenderer` consumes the IR, presents through pygame; passes the sample suite under the pinned contract; the only renderer after Sprint 3 | 1 | done (Sprint 3) |
| E-13 HiDPI-correct rendering | Logical coordinates, physical-resolution rendering; crisp on scaled displays (Windows verified; macOS/Linux follow-up) | 1 | done (Sprint 3) |
| E-12 Export and headless mode | `p.save()` PNG/PDF/SVG through Cairo surfaces; run a sketch to files without a window; later: embedded-font PDF text (S-032) | 1 (basic) / 3 (embedded fonts) | basic done (Sprint 3) |
| E-10 Transforms and state stack | Internal `Transform` + state ops in the IR (Phase 1); public `translate/rotate/scale`, `push/pop`, `with p.saved_state()` (Phase 2) | 1 → 2 | ready |
| E-11 Path API | Internal `Path` in the IR (Phase 1); public `p.path()` and clip (Phase 2) | 1 → 2 | ready |

| E-24 Drawing vocabulary completeness | `square`, `triangle`, `quad`, `arc`, `polygon`; stroke cap/join/dash/miter; anti-alias opt-out; revisit rect/ellipse modes | 2 | ready (Feature_Map §2) |
| E-25 Colour, gradients and compositing | `color_mode` HSB/HSL, colour objects, `lerp_color`; linear/radial gradients; blend modes; opacity; shadow | 2 | ready (Feature_Map §3) |
| E-28 Off-screen canvas | `create_canvas()` buffers drawn with the same API and used like images | 2 | ready (Feature_Map §1) |

**Phase 2 exit criterion (revised 25 Sept 2026, see `Feature_Map.md`):** a learner can port a typical p5 "core" sketch (shapes, transforms, colour modes, events, noise, text) and a typical DrawBot single-page composition (paths, gradients, text box, PDF) with only naming changes; the Quick Reference documents it; published on PyPI as 0.1 (D-019); default examples ≤ 720p hold 60 fps on the teaching machine.

## TH-4 Creative Media *(directional)*

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-14 Images | `load_image`, draw with transform, Pillow adapter | 3 | directional |
| E-15 Typography | v1 (Phase 2): bundled OFL font, uharfbuzz shaping + fontTools outlines as IR paths, `FontResource`/`TextRun` (S-031, S-029). Later: font choice, multiline layout, embedded-font export | 2 (v1) / 3 | ready (v1) |
| E-16 SVG import | via `resvg-py` | 3 | directional |
| E-17 Sound API | Simple `p.sound()` over pygame mixer | 3 | directional |
| E-18 Document / page / frame model | Multi-page documents, frame sequences | 3 | directional |
| E-19 Video export | frame sequences (Phase 2), GIF and mp4 via ffmpeg (Phase 3) | 2–3 | directional |
| E-30 Controls | sliders/toggles bound to sketch variables (DrawBot `Variable`) | 3 | directional |

## TH-5 Beyond 1.0: GPU, 3D and the web *(directional, D-014)*

1.0 is desktop, Cairo, 2D. These epics are kept so the architecture does not foreclose them; none is scheduled.

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-20 OpenGL feasibility | Context-creation spike through `PygamePlatform`; provider interface only | 4 | directional |
| E-21 3D primitives, shaders, camera | | 4 | directional |
| E-31 Playground in the browser | Pyodide + `BrowserPlatform` + `Canvas2DRenderer` consuming the same IR; loader, `<playground-run>`, launcher URL, classroom page. Feasibility proven by Spike 08 (S-059, done); see `docs/design/Browser_Mode_Note.md` | post-1.0 | directional (D-014) |

## TH-6 Documentation and Process

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-22 Teaching material: Quick Reference, User Guide, Examples Gallery | Learner docs updated for every additive API; release 0.1 ships a User Guide and a Gallery covering every feature (D-015, D-019) | 2 | in progress |
| E-23 SDLC process, ADRs, contributor docs | This backlog, `docs/PROCESS.md`, ADR series, sprint records | 0 | done (Sprint 0) |
