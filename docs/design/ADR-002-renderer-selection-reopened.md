# ADR-002: Renderer selection reopened — Cairo as reference implementation pending a bake-off

**Status:** Accepted — option B on 24 September 2026 (D-010); **open clause closed by D-011 on 25 September 2026: Cairo is the Sprint 3 interactive renderer and the exporter; Blend2D is a gated optional renderer (S-036).** Bake-off evidence: `spikes/RESULTS.md` §7.
Supersedes the *engine* clause of ADR-001. The *topology* clause of ADR-001 (Playground owns
semantics + IR; pygame-ce is platform + presentation; renderers are IR consumers) is unchanged.
**Date:** proposed and accepted 24 September 2026

## Context

ADR-001 chose Cairo as the default 2D renderer on the strength of spike 05 (Cairo vs Skia: faster on
CPU, 40× smaller, pixel-identical output). The maintainer then asked whether committing to Cairo is
wise when large projects (WebKitGTK, Firefox's GPU path) have moved to Skia/GPU engines.

The advising agent's reassessment, which this ADR adopts in substance: spike 05 established that
*Cairo is a very good implementation of the Phase 1–2 contract on the teaching machine*, not that
*Cairo is the best foundation for a long-lived framework*. The migrations away from Cairo elsewhere
are workload-driven (GPU-accelerated browser canvases), not evidence of obsolescence — cairo 1.18.x
is maintained and pycairo ships cp314 wheels. The candidates that are the right *kind* of component
for Playground are Cairo, Skia and Blend2D; Vello is a watch item; WebRender, GSK, Moz2D and
WebKitGTK are architecture inspiration or the wrong kind of component.

New evidence gathered for this ADR (24 Sept 2026):

| | Cairo (pycairo 1.29.1) | Skia (skia-python 144) | Blend2D (blend2d-py 2025.5.0) |
|---|---|---|---|
| cp314 Windows wheel | 0.87 MB | 11.3 MB + numpy 12.7 MB | 0.94 MB |
| Platforms | win / manylinux / macOS x86_64 + arm64 | win / manylinux / macOS x86_64 + arm64 | win / manylinux / **macOS arm64 only** |
| Binding ownership | pygobject project (long-lived) | kyamagu (third-party, long-lived) | Shiguredo (third-party, first release 2025) |
| Binding covers the IR ops? | ✅ paths, fill rule, stroke join/cap, clip, transforms, gradients | ✅ | **✗ today**: no clip, no scale, no fill rule / stroke options exposed (14 names in total); `FontFace.create_from_file` ✅ |
| Native PDF / SVG | ✅ | ✅ | ✗ |
| Measured (spike 05) | 3.5 / 6.4 / 11.2 ms @ 640×400 / 720p / 1080p | 6.9 / 17.6 / 34.6 ms | not yet measurable through the binding |

## Options

**A. Keep ADR-001 as written.** Cairo is the default; Sprint 3 proceeds. Cheapest; ignores the
concern; the IR still lets us swap later, but at Sprint-3-plus cost.

**B. Reopen the engine choice; Cairo becomes the *reference implementation* of the IR; run a
bake-off (Spike 07) during Sprint 2; decide (D-011) before Sprint 3.** *(recommended)*
Sprint 2 (IR + legacy renderer) does not depend on the engine, so no schedule cost. The bake-off
gives the IR a third consumer, which is the best possible test of backend-neutrality. Blend2D
enters the bake-off only after a *binding-coverage gate*: either the binding gains clip/scale/fill
rule, or we accept writing and owning a nanobind binding (a new story with real cost).

**C. As B, but bake-off Cairo vs Skia only; Blend2D on the watch list with Vello.** Honest about
today's binding, but it forfeits the strongest CPU contender without measuring it.

## Decision

**Option B.** The interactive 2D engine is **open**; Cairo is the *reference implementation* of the
IR until Spike 07 (S-035) reports and D-011 is decided before Sprint 3. Principle adopted in
`PROCESS.md`: **providers are selected per capability and workload, not per framework** —
interactive raster, vector export, shaping and font model may be different providers behind one
IR, as long as learners never see the seam.

## Consequences

- Architecture document v2 (S-033) says "interactive 2D renderer: OPEN — reference implementation
  Cairo"; export through Cairo PDF/SVG surfaces is retained regardless of the interactive winner.
- Spike 07 (S-035) is scoped to what decides Sprint 3: primitive-heavy animation, complex paths with
  joins/caps/clip/nested transforms, translucency/compositing, gradients (incl. conic where
  available), text via the outlines route (renderer-independent) plus Blend2D native font loading,
  export replay through Cairo, install/cold-import/first-frame cost, and a **binding-risk score**
  (ownership, wheel coverage, release cadence, API coverage). Images and multi-OS reliability are
  deferred: no image API exists yet, and multi-OS needs the CI remote.
- D-011 (engine choice) is presented at the end of Sprint 2 with the numbers.
- ADR-001 is not edited; its status line gains "engine clause superseded by ADR-002" if B is accepted.
