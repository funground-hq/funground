# ADR-001: Renderer topology and first rasteriser

**Status:** Accepted — option C, by the maintainer on 24 September 2026 (Decision Log D-001)
**Date:** proposed and accepted 24 September 2026
**Inputs:** architecture document §5–8, architecture review Issue 1, spikes 01/02/03/05 (`spikes/RESULTS.md`)

## Context

The architecture document keeps pygame-ce as a *peer renderer* next to Skia, with Playground Core
owning transforms, paths and clipping. Spike 01 showed `pygame.draw` cannot implement that model:
no transforms, no path fill, rect-only clipping, no anti-aliased thick strokes, notched joins,
alpha dropped. Making `PygameRenderer` satisfy `draw_path()` means writing a rasteriser in Playground.

Spike 02 showed that presenting a CPU-rendered buffer through pygame costs ≤ 2 ms per frame at
1080p, so a "one rasteriser + pygame presentation" topology is not limited by the hand-off.

Spike 05 rendered one draw-op list through Cairo and Skia adapters (~60 lines each) with
pixel-identical output:

| | Cairo (pycairo 1.29.1) | Skia (skia-python 144) |
|---|---|---|
| Draw ms @ 640×400 / 720p / 1080p | 3.5 / 6.4 / 11.2 | 6.9 / 17.6 / 34.6 |
| Installed footprint | 2 MB, no dependencies | ~81 MB (numpy is a hard dependency) |
| PNG / PDF / SVG | ✅ | ✅ |
| Built-in text shaping, GPU backends | ✗ | ✅ (Phase 3+/4 concerns) |

## Options

**A. Two peer renderers (document as written).** pygame 2D for teaching, Skia for design.
Rejected by spike 01: the capability cliff lands on `translate()`/`rotate()`, which are beginner topics.

**B. One rasteriser — Skia — in the base install; pygame is platform + presentation.**
Correct semantics everywhere; +81 MB and a numpy dependency in the classroom install; 25 fps at 1080p.

**C. One rasteriser — Cairo — in the base install; pygame is platform + presentation.** *(recommended)*
Correct semantics everywhere; +2 MB, no extra dependencies; 76 fps at 1080p; PDF/SVG for free.
Skia (or anything else) can be added later as a second consumer of the same draw-op IR when
typography or GPU work needs it.

**D. Keep pygame-only rendering for the v0.5 primitive set; everything else requires `[design]`.**
Preserves the smallest install but freezes the teaching tier at v0.5 features; transforms become
an "advanced" extra. Only justified if C's 2 MB is unacceptable.

## Decision

**Option C.** Playground owns the drawing semantics and the draw-op IR; **Cairo is the default 2D
renderer** (raster to the window, and PDF/SVG surfaces for export); **pygame-ce is the platform and
presentation provider** (window, events, input, timing, audio, blit of the finished frame). Skia,
OpenGL and any other renderer are optional future consumers of the same IR.

Sequenced as (D-007): Sprint 1 builds the `Sketch`/platform/state split under unchanged pygame
drawing; Sprint 2 adds the IR with a `LegacyPygameRenderer` consuming it (goldens byte-identical);
Sprint 3 adds `CairoRenderer`, applies the contract changes D-003/D-004/D-005 with one deliberate
golden regeneration, makes Cairo the default and deletes the legacy renderer (D-008).

## Consequences

- pygame-ce remains a hard dependency for window/events/input/timing/audio; pycairo becomes one for drawing.
- The IR becomes the only thing renderers see; `tests/` gains op-list snapshot tests.
- Default `p.size()` examples stay ≤ 1280×720 (CPU rasteriser headroom).
- Skia is not rejected — it is deferred to the epic that needs it (typography / GPU).
