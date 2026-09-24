# Themes and epics

Status: `done` · `in progress` · `ready` · `directional` (architecture placeholder, not committed).
Phase exit criteria come from the architecture document, sharpened by the review.

## TH-1 Teaching Core Stability
*The Session-1 experience keeps working, provably, on every supported platform.*

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-01 Freeze and test the v0.5 contract | API inventory, semantics and Session-1 sketches are executable tests | 0 | done (Sprint 0) |
| E-02 Packaging, install and CI | `pip install` works; CI matrix Windows/macOS/Linux × 3.11–3.14; import-lint guards provider boundaries | 0–1 | in progress |

**Phase 0 exit criterion:** semantics pinned, now-or-never defects fixed, sample suite green, API frozen. *Met in Sprint 0 except the DECISION rows, which are Sprint 1's first task.*

## TH-2 Architecture Foundation
*Playground owns its concepts; providers are replaceable; no learner-visible change.*

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-03 Public semantic contract | Every learner-visible rule written, decided and tested | 0–1 | in progress (DECISION rows open) |
| E-04 Sketch object and runtime split | `Sketch` + `_active_sketch`; facade in `api.py`; live values via `__getattr__` over the active sketch; two sketches per process possible | 1 | ready |
| E-05 Platform provider | `PygamePlatform` behind a `Platform` protocol: window, events, input, clock, presentation | 1 | ready |
| E-06 Draw-op IR and GraphicsState | Public calls record backend-neutral ops; `GraphicsState` owned by Playground; pygame drawing consumes the IR; op-list snapshot tests | 1 | ready |
| E-07 Capability registry and errors | Unsupported features fail at renderer selection with a message naming the extra to install | 1 | ready |

**Phase 1 exit criterion:** existing learner code unchanged; goldens identical; no pygame draw/display calls outside providers (enforced by lint).

## TH-3 Design-Quality Rendering
*Correct vector semantics — transforms, paths, clipping, anti-aliasing, export — in the base install.*

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-08 Rasteriser decision | ADR-001 accepted (recommendation: Cairo first, Skia deferred) | 1–2 | ready (ADR proposed) |
| E-09 Cairo renderer via IR | `CairoRenderer` consumes the IR, presents through pygame; passes the sample suite under the agreed contract; becomes default | 2 | ready |
| E-10 Transforms and state stack | `translate/rotate/scale`, `push/pop`, `with p.state()` | 2 | ready |
| E-11 Path API | Reusable `Path` with lines, curves, close; fill/stroke; clip | 2 | ready |
| E-12 Export and headless mode | `p.save()` PNG/PDF/SVG; run a sketch to files without a window | 2 | ready |
| E-13 HiDPI-correct rendering | Logical coordinates, physical-resolution rendering; crisp on scaled displays | 2 | ready |

**Phase 2 exit criterion:** a representative 2D sketch renders through the IR to window, PNG and PDF; exports stable; default examples ≤ 720p hold 60 fps on the teaching machine.

## TH-4 Creative Media *(directional)*

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-14 Images | `load_image`, draw with transform, Pillow adapter | 3 | directional |
| E-15 Typography | Font choice, shaping (uharfbuzz/fontTools), multiline layout | 3 | directional |
| E-16 SVG import | via `resvg-py` | 3 | directional |
| E-17 Sound API | Simple `p.sound()` over pygame mixer | 3 | directional |
| E-18 Document / page / frame model | Multi-page documents, frame sequences | 3 | directional |
| E-19 Video export | ffmpeg subprocess | 3 | directional |

## TH-5 GPU and 3D *(directional)*

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-20 OpenGL feasibility | Context-creation spike through `PygamePlatform`; provider interface only | 4 | directional |
| E-21 3D primitives, shaders, camera | | 4 | directional |

## TH-6 Documentation and Process

| Epic | Outcome | Phase | Status |
|---|---|---|---|
| E-22 Quick Reference v0.6 and teaching docs | Learner docs updated for every additive API | 2 | ready |
| E-23 SDLC process, ADRs, contributor docs | This backlog, `docs/PROCESS.md`, ADR series, sprint records | 0 | done (Sprint 0) |
