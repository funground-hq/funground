# Playground Technology Architecture — Analysis, Critique and Revised Plan

| | |
|---|---|
| **Reviewed document** | `docs/Playground_Technology_Architecture.docx` — "Technology Architecture and Evolution Plan", baseline Playground v0.5.0, dated 24 September 2026 |
| **Review date** | 24 September 2026 |
| **Audience** | Maintainers, contributors and instructors |
| **Scope note** | This repository contains only `docs/`. No v0.5 source was available, so every statement about current behaviour in the reviewed document (§3, Appendix A) is taken on trust and was not verified against code. |

---

## Part 1 — Analysis

### 1.1 What the document proposes

Playground v0.5 is a small teaching wrapper over pygame-ce: `import playground as p`, optional
`setup()`, required `draw()`, `p.run()`, a handful of primitives, one module-level style object, live
values such as `p.width` and `p.frame_count`, and simple input helpers. Everything — lifecycle, state,
input and rendering — lives in one pygame-oriented `_core.py`.

The document proposes to evolve this into a multi-renderer creative-coding framework while keeping the
learner-facing API unchanged. Its core architectural statement is:

> Playground owns concepts and public semantics; underlying libraries provide replaceable capabilities.

Concretely:

- **Playground Core** owns the sketch lifecycle, a `GraphicsState` stack, a backend-neutral affine
  `Transform`, a `Path` model, `Image`/`Font`/`Sound`/`Canvas` resource handles, a Canvas/Page/Frame
  model and a capability registry.
- **pygame-ce** stays as the default *platform* provider (window, events, input, timing, audio,
  controllers, MIDI) and as a baseline *renderer* (`PygameRenderer`).
- **Skia** (via skia-python) is added as an optional high-quality 2D renderer (`SkiaRenderer`) for
  paths, transforms, gradients, clipping, typography and PDF/SVG export.
- **OpenGL** is designed for but deferred; ModernGL is not hard-wired because its wheels currently
  stop at CPython 3.13 while the teaching environment is 3.14.
- **Specialist providers** — Pillow/NumPy (raster), uharfbuzz/fontTools (text shaping), resvg (SVG
  import), ffmpeg (video export) — are adopted per capability, behind install extras and lazy imports.
- Provider boundaries are lightweight Python `Protocol`s (`Platform`, `Renderer`), not a plugin system.
- A five-phase roadmap: **0** stabilise v0.5 → **1** refactor core → **2** Skia renderer →
  **3** creative media → **4** optional GPU/3D. The v0.5 sample suite is the regression gate for every
  phase, and v0.6 is scoped as a pure internal refactor.

### 1.2 Overall verdict

**The thesis is right and the document is unusually well organised. Its weakness is that it commits
to a two-renderer topology before defining the semantics both renderers would have to share — and the
default renderer (pygame) cannot express the core model the document puts at the centre.** Fixing that
one decision, plus writing down the public semantics the document claims to own, would turn a good
direction paper into an executable architecture.

### 1.3 What is genuinely strong

- **The central framing** — concepts owned by Playground, capabilities delegated *per capability
  rather than per library* (§2.2, §6) — is the correct call and is applied consistently. Keeping
  pygame-ce for window/events/timing/audio while adding Skia only for rendering avoids the common
  mistake of a wholesale backend swap.
- **Refactor-before-breadth sequencing** (principle 7, Phases 0–1, §13 step 2) with *"existing learner
  code unchanged"* as the exit criterion. Phase 1's "no direct pygame draw/display calls outside
  providers" is a rare thing: an architectural goal that is mechanically testable (an AST/import lint
  in CI).
- **Treating the v0.5 sample suite as an executable compatibility contract** (§9.2) is the single best
  idea in the document.
- **Non-goals are real non-goals** (§4.2). Declining p5/DrawBot API compatibility and declining to
  reimplement SDL, shaping, SVG parsing, codecs or a 3D engine closes off the most expensive failure
  modes up front.
- **Capability flags over lowest-common-denominator** (principle 8, §11) is the right instinct.
- **drawbot-skia as precedent, not dependency** (§8.2) keeps the data model under Playground's control.
- Figures 3–6 carry real information rather than decorating; the "boundary rule" and "dependency
  rule" call-outs are the kind of thing contributors actually cite.

---

## Part 2 — Critique

### 2.1 Major issues

#### Issue 1 — Pygame cannot implement the `Renderer` protocol the document defines *(load-bearing)*

§5.2 puts **Transform**, **Path/Geometry** and **clipping** in Playground Core, and §5.3's protocol
makes `draw_path(path, state)` the primary rendering entry point. But `pygame.draw` has no affine
transform, no arbitrary path fill (no winding rules, no holes), no gradients, and `Surface.set_clip`
accepts a rectangle only. `PygameRenderer` therefore has exactly three options, and the document
chooses none of them:

1. Implement transform + curve flattening + scanline fill in Python — i.e. write a 2D rasteriser,
   which §4.2 explicitly lists as a non-goal.
2. Support only the v0.5 primitive set and fail on everything else — but then `p.translate()` and
   `p.rotate()`, *beginner-level* creative-coding topics that p5 teaches in its first lessons, are
   unavailable in the default teaching install.
3. Silently approximate by baking transforms into primitive coordinates — which works for
   translate/scale and breaks the moment rotation meets `rect()`, stroke width or text.

§11's "capability flags" mitigation does not resolve this, because the capability boundary lands in
the wrong place: transforms are not an advanced design feature.

**Recommendation.** Make this an explicit, named decision with the alternatives written down. The
strongest option is to stop treating pygame-ce as a *renderer* and treat it as a
*platform + presentation* provider only: one rasteriser (Skia) draws every frame into a buffer;
pygame-ce blits that buffer to the window and handles events, timing and audio. That yields one set
of drawing semantics, one golden-image target, no cross-renderer conformance layer (deleting a whole
row of §10) and no capability cliff mid-lesson. A per-frame `pygame.image.frombuffer` + blit is not a
meaningful cost at teaching resolutions.

The cost is that skia-python moves into the base install, which contradicts "base install stays
pygame-only" (§9.1, §11) — tens of MB of wheel and a second binary dependency for a classroom
`pip install`. **That trade-off is the real decision the document has to make, and it currently makes
it implicitly by assuming both can be true.** If the small base install wins, say plainly that the
base renderer is frozen at the v0.5 primitive set and that transforms/paths require
`playground[design]` — and accept what that means for teaching order.

#### Issue 2 — The public semantics Playground claims to own are never specified

The cover states *"Playground owns concepts and public semantics."* The document then never pins a
single one of them. All of the following are learner-visible and undecided:

| Undecided semantic | Why it must be decided in Phase 0/1 |
|---|---|
| Angle units | §7.2 shows `p.rotate(30)` — degrees. p5 defaults to radians, DrawBot to degrees. Unstated. |
| Coordinate origin / y direction | y-down (pygame and Skia native) vs y-up (design/DrawBot convention). Affects every example ever written. |
| Colour model | `"white"`, `"tomato"` imply CSS names; 0–255 vs 0–1, alpha channel, any `color_mode()` — all unstated. |
| `rect()` / `ellipse()` origin | Corner vs centre (p5's `rectMode`/`ellipseMode`). §3 lists `circle` and `ellipse` with no stated convention. |
| Text anchoring | Baseline vs top-left. `pygame.font` and Skia differ by default. |
| HiDPI / display scaling | **Completely absent.** Retina and Windows display scaling change what `p.width` means and whether golden images match across machines. |

HiDPI deserves a call-out: it is a breaking public semantic, cheap to decide now and expensive later,
and it is exactly the kind of thing that makes golden-image tests pass on one maintainer's machine and
fail on another's.

**Recommendation.** Add a "Public semantic contract" table to §5 fixing each row above, and change the
Phase 0 exit criterion from *"freeze the API"* to *"pin semantics, fix now-or-never defects, then
freeze."* v0.5 → v0.6 is the last cheap moment to change `rotate()` units or `rect()` origin; freezing
semantics that have never been written down freezes accidents.

#### Issue 3 — No neutral intermediate representation

§7.2 correctly says the most important long-term abstraction is a backend-neutral drawing model, but
§5.3 then defines an immediate-mode protocol that issues calls straight at a backend. The
Canvas/Page/Frame model (§5.2), PDF/SVG export (§6), off-screen rendering (§13 step 6) and video
export all want the same thing: a frame captured as **data** before it becomes pixels.

**Recommendation.** Define a small internal draw-op list (Skia's `SkPictureRecorder` is the model)
as the IR between Core and Renderer. It costs little and buys: replay of one frame to multiple
targets; export without re-running user code; and — most valuably — **cross-renderer conformance tests
that compare op lists instead of pixels**, which dissolves the "tolerate antialiasing differences"
problem §10 is left wrestling with.

#### Issue 4 — Scope realism is not addressed anywhere

Phases 0–2 are a focused, achievable refactor. Phase 3 (images, filters, HarfBuzz shaping, font
handling, SVG import, a document/page/frame model, UI controls, an expanded audio API) and Phase 4
(OpenGL renderer, shaders, textures, mesh/camera/light model, 3D primitives) are each larger than
everything before them combined; Phase 4 is a 3D engine in all but name.

The document never states who is doing the work or at what capacity. For what appears to be a small
or solo maintainer effort, that omission is what turns a good architecture into a stalled one.

**Recommendation.** Label Phases 3–4 explicitly as *directional, not committed* — they exist to prove
the Phase 1–2 boundaries do not foreclose them, not as a delivery promise. Add a one-line resourcing
assumption. Consider shipping the design tier as a **separate distribution** (`playground-design`)
rather than an extra of one package, so the teaching package keeps a slow, boring release cadence
independent of Skia/HarfBuzz churn.

#### Issue 5 — "Live values" as module-level rebinding will fight the refactor

§3 lists `p.width`, `p.frame_count` and `p.delta_time` as module-level live values and puts them under
"worth preserving". The *syntax* is worth preserving; the *mechanism* is not:

- `from playground import width` captures a stale value — a genuine beginner trap.
- Module-level rebinding forces exactly the global mutable state that §2.1 identifies as the problem.
- One global state means **one sketch per process**, which quietly forecloses the Canvas/Page model
  (§5.2), off-screen rendering (§13 step 6) and multi-page documents.

**Recommendation.** Keep the syntax exactly, change the mechanism: module `__getattr__` (PEP 562)
gives a dynamic `p.width` with no global rebinding, and the public facade in `api.py` becomes a thin
shim over an explicit `Sketch` / `_active_sketch` instance. Cheap, invisible to learners, and it
unblocks three later features. State it as a Phase 1 design decision.

### 2.2 Gaps worth closing

- **No "alternatives considered" section.** Appendix B summarises decisions but never records what was
  rejected or why. A reader will immediately ask about **cairo/pycairo** (mature, PDF/SVG/PNG
  backends, far smaller than Skia, excellent packaging) as the Skia alternative, and about
  **pyglet / arcade / moderngl-window** as pygame-ce alternatives. Not mentioning cairo at all is the
  most conspicuous omission in an otherwise well-researched document. A short rejected-alternatives
  table would strengthen the Skia recommendation, not weaken it.
- **No headless / non-interactive execution model.** DrawBot's whole model is "run script → produce
  file", and §6/§13 promise export, but there is no second lifecycle for a sketch that never opens a
  window. This also matters for CI (§10 packaging row): headless pygame needs
  `SDL_VIDEODRIVER=dummy`, which is worth naming.
- **Determinism for golden tests.** §10 wants deterministic golden images, but `p.random` is
  unseedable in the Appendix A baseline. Add `p.random_seed()` in Phase 0.
- **Default font.** v0.5 uses `pygame.font.Font(None, size)` — an unnamed platform default. Under Skia
  that becomes Playground's font-discovery problem and cross-renderer text comparison becomes
  impossible. **Bundle one OFL-licensed font as the guaranteed default** so `p.text()` is identical
  across renderers and platforms.
- **When capability checks fire.** §5.2's registry does not say whether an unsupported call raises at
  `p.size()`/`p.run()` or at the call site. Failing at frame 200 with
  `capability VECTOR_PATHS unsupported` is a bad classroom experience. Resolve at renderer selection
  where possible, and make the message name the extra to install (`pip install playground[design]`).
- **`draw()` as both simulation and render.** §7.1 defers `update()`, which is defensible, but the
  consequence is unexamined: exporting a frame range or replaying a frame re-runs user simulation, so
  static-document export from an interactive sketch has ambiguous semantics. Not an argument for
  `update()` — an argument for specifying what export does.
- **The renderer protocol under-specifies the parts that matter.** §5.3 has no `save`/`restore`/clip
  despite clipping being a Core concept; `begin_frame`/`end_frame` never say who owns presentation;
  and with a Skia renderer the buffer→window hand-off crosses the renderer/platform boundary that
  Figure 4 draws as clean. Figure 4 should show that hand-off.
- **Python version strategy is itself a risk.** §8.3 notes ModernGL wheels stop at 3.13 while the
  teaching environment is 3.14 — that *is* §11's dependency-fragility risk, already materialising.
  Supporting 3.11–3.14 with an explicit CI matrix turns "ModernGL churn" into a non-issue.
- **Licensing row is generic.** §11 says "maintain an inventory". Name the one that actually bites:
  ffmpeg redistribution (GPL vs LGPL builds) if binaries are ever shipped rather than found on PATH.

### 2.3 Smaller corrections

| Location | Problem | Fix |
|---|---|---|
| §9.1 vs Figure 6 | Text says extras are *independently* installable ("design without GPU, GPU without typography"); Figure 6 draws Core → Design → Media → GPU as a cumulative chain. | Keep the text; redraw the figure as independent tiers off a common core. |
| §6 vs Figure 6 | Pillow and NumPy are paired for raster processing in §6 but split into `design` and `media` extras in Figure 6. | Put them in the same extra. |
| §3 vs Appendix A | "No-argument `p.run()`" vs `p.run(fps=None)`. | Pick one signature. |
| §6, §8.4 | resvg is listed as a dependency with no access path named (CLI subprocess? third-party binding? Skia's own SVG module?). There is no first-party Python binding. | Name the binding and verify wheel availability before it enters the table. |
| §6 | `pygame.midi` is effectively legacy and inconsistent across platforms; listed beside solid choices. | Flag as at-risk/low-priority, as the camera row correctly is. |
| §2.3 vs §5.1 | p5 API compatibility is rejected, yet `p.translate`, `p.path`, `p.save` are p5/DrawBot names. | State a naming policy: borrow names where semantics genuinely match; never claim compatibility. |
| Contents | Heading drift ("Goals, non-goals and principles" vs "…and architectural principles"; "Technology choices" vs "…and rationale"); Appendix B missing. | Regenerate the table of contents. |
| §8.3 | Typo: "depending packaging". | "depending on packaging". |

---

## Part 3 — Revised plan

### 3.1 Document revisions, in priority order

1. **Add §5.x "Public semantic contract."** Angle units, origin/y-direction, colour model, shape
   origins, text anchoring, HiDPI policy. *Blocks Phase 0's API freeze.*
2. **Add §7.3 "Renderer topology decision."** Write out one-rasteriser-plus-presentation versus
   two-peer-renderers, with the packaging consequence of each, and decide. Everything in Phases 1–2
   depends on this.
3. **Add Appendix C "Alternatives considered."** cairo/pycairo, blend2d, pyglet/arcade,
   moderngl-window — and why Skia + pygame-ce wins.
4. **Rewrite the Phase 0 exit criterion.** "Semantics pinned, now-or-never defects fixed, sample suite
   green, *then* API frozen" — not "API frozen".
5. **Add a draw-op IR** to §5.3 and §7.2; retarget §10's cross-renderer conformance row from pixel
   comparison to op-list comparison.
6. **Mark Phases 3–4 as directional**, add a resourcing assumption, and evaluate a separate
   `playground-design` distribution.
7. **Fix the §9.1/Figure 6 contradiction and the smaller corrections** in §2.3 above.
8. **Extend the Renderer protocol** with `save`/`restore`/`clip` and an explicit presentation
   hand-off; update Figure 4 to match.

### 3.2 Revised Phase 0 and Phase 1 scope

The original roadmap's phases remain; this sharpens the first two so the later ones are buildable.

**Phase 0 — Pin and stabilise v0.5**

| Work | Exit criterion |
|---|---|
| Write the public semantic contract (§3.1 item 1) and check each row against the v0.5 source. | Every row is either "matches v0.5" or "deliberate pre-freeze change, listed in the v0.6 changelog". |
| Fix now-or-never defects: angle units, shape origins, anything the contract changes. | Applied before the freeze, not after. |
| Add `p.random_seed()`; bundle a default OFL font. | Golden tests are deterministic on every machine in the CI matrix. |
| Freeze the public API in a sample suite; run it headless (`SDL_VIDEODRIVER=dummy`) in CI. | Session 1 sketches and the reference guide match tested behaviour. |
| Declare the supported Python matrix (3.11–3.14) in CI. | Packaging CI green on Windows/macOS/Linux across the matrix. |

**Phase 1 — Refactor core (no learner-visible change)**

| Work | Exit criterion |
|---|---|
| Decide renderer topology (§3.1 item 2) and record it as an ADR. | Decision, alternatives and packaging consequence written down. |
| Split `_core.py` into runtime, `PygamePlatform` and renderer/presentation. | No direct pygame draw/display calls outside providers — enforced by a lint in CI. |
| Replace module-level live values with PEP 562 `__getattr__` over a `Sketch` instance. | `p.width` etc. behave identically; two `Sketch` instances can coexist in one process. |
| Introduce Playground-owned `GraphicsState`, affine `Transform` and a minimal draw-op IR. | Current primitives route through the IR; op-list snapshot tests exist for each. |
| Capability registry with checks at renderer selection and messages naming the missing extra. | An unsupported feature fails at `p.size()`/`p.run()`, not mid-loop. |
| Compatibility gate. | The Phase 0 sample suite runs unchanged. |

Phase 2 (Skia) then starts from a single, specified drawing semantics and an IR to render from —
which is what makes "the same deterministic examples render through both targets" (original §13 step 5)
actually verifiable.

### 3.3 Spikes that settle open questions cheaply

- **Rotated stroked rectangle via `pygame.draw` only** (~20 lines). If it cannot be done without
  writing a rasteriser, §7.3 writes itself.
- **Skia → pygame presentation loop** at 640×400 and 1920×1080: render a frame with skia-python,
  `pygame.image.frombuffer`, blit, flip. Measure per-frame cost. This is the number the base-install
  decision turns on.
- **skia-python wheel size and install time** on a clean Windows Python 3.14 — the classroom cost of
  Issue 1's recommended option, measured rather than guessed.
- **Dependency revalidation**: skia-python cp314 wheels, ModernGL's 3.13 cap, PyOpenGL, resvg
  bindings — before any version is pinned. The reviewed document's own closing line asks for this.

### 3.4 What this review did not do

- It did not verify §3 or Appendix A against the v0.5 source, which is not in this repository.
- It did not re-check the time-sensitive dependency claims dated 24 September 2026.
- It did not produce a rewritten architecture document; §3.1 is the change list for one.

---

## Addendum — verified against the v0.5 source (24 September 2026, later the same day)

The v0.5 package (`src_v0.5/`) and the Quick Reference arrived after the review above was written.
Source and tests are authoritative; these are the corrections and confirmations.

| Review claim | Verdict | Detail |
|---|---|---|
| Issue 5: live values are module-level rebinding | **Wrong** | `__init__.py` already uses PEP 562 `__getattr__` → `_core.live_value()`. No stale-copy problem exists. The surviving point is the single global `_state/_style/_screen` (one sketch per process) — now story S-013. |
| §3 vs Appendix A `p.run()` signature | Appendix A right | `run(*, fps: int \| None = None)`, keyword-only. |
| Default canvas | New finding | 640×**480**, not the 640×400 the Quick Reference uses throughout. |
| Angle units, colour model, anchoring, HiDPI unspecified | Confirmed, now specified | See `Semantic_Contract.md`. Anchoring: rect top-left, ellipse/circle centre, text top-left. Colours pass straight to pygame. |
| HiDPI | New finding | Process is DPI-unaware; Windows bitmap-stretches at 125 % scaling. |
| Stroke alignment | New finding | v0.5 strokes are drawn **inside** the geometry (pygame `width`); vector renderers centre them. DECISION row S4. |
| Alpha | New finding | RGBA alpha is silently dropped on the window. DECISION row S2. |
| Determinism (`p.random` unseedable) | Confirmed, fixed | `p.random_seed()` added with a private generator. |
| Headless execution | Confirmed feasible | Works with `SDL_VIDEODRIVER=dummy`; harness in `tests/conftest.py`. |
| Second `p.run()` in one process | New defect found | Crashed unless `setup()` called `size()`; fixed in Phase 0. |
| "No tests, no packaging" assumption | Confirmed | v0.5 shipped as a bare folder with one example; Phase 0 added `pyproject`, 73 tests, 12 sample sketches, CI matrix. |
| Issue 1 (pygame cannot implement the core model) | Confirmed by spike 01 | See `spikes/RESULTS.md`. |
| Skia as the design renderer | **Reversed by measurement** | Spike 05: Cairo is ~3× faster on CPU, 2 MB vs 81 MB, no numpy, pixel-identical output. `ADR-001` recommends Cairo first, Skia deferred to typography/GPU epics. |
