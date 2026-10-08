# Playground — Technology Architecture v2

| | |
|---|---|
| **Status** | The Sprint 2 architecture record (as built through Sprint 2, decided through D-010). Superseded for current code by [`docs/developer/Architecture.md`](../developer/Architecture.md); the rest of this page is kept as history |
| **Supersedes** | `Playground_Technology_Architecture.docx` (v1, 24 Sept 2026) — kept as the historical record |
| **Baseline** | Playground v0.5.0 (`src_v0.5/`, never edited) → working package `playground/` at `0.6.0.dev0` |
| **Audience** | Maintainers, contributors, instructors |
| **Date** | 25 September 2026 |
| **Authority** | The source and the test suite outrank this document (`docs/PROCESS.md`). Decisions are indexed in `Decision_Log.md`; long-lived ones have an ADR |

> **Playground owns the programming model and the drawing semantics. The draw-op IR is the
> contract. pygame-ce runs the interactive environment. Providers are selected per capability and
> workload, not per framework — and learners never see the seam.**

---

## 1. What changed since v1, and why

v1 proposed a multi-renderer framework with pygame drawing as the teaching renderer and Skia as
the design renderer. Three things overturned that:

1. **pygame cannot implement the model** (Spike 01). `pygame.draw` has no transforms, no path fill,
   rect-only clipping and no anti-aliased thick strokes. Making it a peer renderer meant writing a
   rasteriser inside Playground — a stated non-goal — or putting the feature cliff on `rotate()`.
2. **Presentation is cheap, rasterisation is not** (Spike 02). Handing a CPU-rendered frame to
   pygame costs ≤ 2 ms at 1080p. So pygame's job is the window, input, timing, audio and the blit;
   something else draws.
3. **Measured, the engines rank differently from their reputations** (Spikes 05, 07). Through the
   Python bindings we can actually ship, Skia is 81 MB and 3–25× slower than Cairo on CPU; Cairo is
   2 MB, complete and exports PDF/SVG natively; Blend2D is 3–10× faster than Cairo at 2 MB but its
   binding cannot yet run our IR (no clip, no matrix).

The response was not to pick a different winner but to change what is fixed: **the IR is frozen,
the engine is not.** ADR-001 settled the topology; ADR-002 reopened the engine clause and made
Cairo the reference implementation pending the bake-off; D-011 chooses the Sprint 3 engine.

## 2. Architecture

```
                 learner program            import playground as p
                        │
                        ▼
              ┌───────────────────┐   api.py — one function per public name,
              │   Playground API  │   frozen signatures (tests/test_api_contract.py)
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐   sketch.py — lifecycle, live values, RNG,
              │   Active Sketch   │   helpers; owns GraphicsState + Color
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐   ir.py — Frame of frozen op dataclasses:
              │    Draw-op IR     │   Clear Circle Ellipse Rect Line Point Text
              │  (the contract)   │   Save Restore Concat ClipPath FillPath StrokePath
              └───┬─────────┬─────┘
                  │         │
        ┌─────────▼──┐  ┌───▼──────────┐
        │  Renderer  │  │   Exporter   │   both are IR consumers; ~100 lines each
        │ (interactive)│ │ PNG/PDF/SVG  │   (Spike 07 proved three engines pixel-identical)
        └─────┬──────┘  └──────────────┘
              ▼
        raster buffer ──► pygame Surface ──► window        (≤ 2 ms per frame)

   pygame-ce / SDL supplies, independently of drawing:
   window · events · keyboard/mouse · clock · audio · controllers · presentation
   (platform/pygame_platform.py — the only window/input code in the package)
```

**Boundary rule.** Backend libraries are imported only under `playground/platform/` and
`playground/renderers/` (enforced by `tests/test_boundaries.py`). `api.py`, `sketch.py`,
`state.py`, `color.py`, `geometry.py`, `ir.py` import no backend.

## 3. Components (as built)

| Module | Responsibility | Sprint |
|---|---|---|
| `__init__.py` | Public names, `__all__`, `__getattr__` for live values (`p.width` …) | 1 |
| `api.py` | Learner-facing functions → active `Sketch`; `use_sketch()` for tests/multi-sketch | 1 |
| `sketch.py` | `Sketch`: `run_namespace()` loop, live values, `GraphicsState` stack, RNG, helpers, `frame` of ops, capability check at `size()` | 1–2 |
| `state.py` | `GraphicsState` (frozen: fill, stroke, stroke_width, text_size), `StateStack` save/restore | 1 |
| `color.py`, `_colornames.py` | `Color` RGBA 0–255; `Color.parse()` for every documented *and* v0.5-working form; 665 bundled X11 names | 1 |
| `geometry.py` | `Transform` (affine, degrees, y-down), `Path` (move/line/cubic/close, rect/ellipse helpers) — internal | 2 |
| `ir.py` | Op dataclasses, `Frame`, JSON round-trip (`to_jsonable`/`from_jsonable`) | 2 |
| `capabilities.py` | `Capability` enum, `PlaygroundError`, extra-naming errors | 2 |
| `platform/base.py`, `platform/pygame_platform.py` | `Platform` protocol; pygame implementation (window, poll, input, key map, tick, present, capture, close) | 1 |
| `renderers/__init__.py` | `Renderer` protocol: `attach(target)`, `render(frame)`, `capabilities` | 2 |
| `renderers/legacy_pygame.py` | `LegacyPygameRenderer`: v0.5's `pygame.draw` calls driven by the IR — **deleted in Sprint 3** (D-008) | 2 |

Call path: `p.circle(x, y, d)` → `api.circle` → `Sketch.circle` → `frame.append(ir.Circle(..., style))`;
once per loop iteration, after `draw()` and before `present()`: `renderer.render(frame)`.

## 4. The IR

- **Ops are plain data**: frozen dataclasses, hashable, serialisable. Ops that draw carry the
  `GraphicsState` snapshot they were issued under (free, because state is immutable).
- **Style calls copy cheaply** (S-144). `GraphicsState` has about thirty fields and every
  `fill`/`stroke`/`stroke_width` call makes a new one through `with_`. `with_` returns the same
  object when every given value is already current (equal and of the same type; safe because the
  state is immutable), and otherwise builds the copy positionally from field names computed once,
  rather than through `dataclasses.replace`, which re-inspects the fields on every call. An unknown
  field still raises `TypeError`. Draw time in the heaviest sketches fell by 16-29 %.
- **A colour string is parsed once** (S-145). `Color` is frozen and hashable, so
  `Color._parse_str` hands the work to `_parse_color_string`, an `lru_cache(maxsize=512)` function
  keyed on the string as given; every later `fill("tomato")` reuses the same `Color`. The bound is
  far above the distinct colour strings a sketch uses. A bad string raises and is never cached, so
  the error and its message are unchanged. `Color.parse("tomato")` 1.3 to 0.29 us, `"#336699"`
  2.6 to 0.29 us; `fill()` 4.7 to 3.2 us; whole `draw()` is 13 % faster on gaussian_and_choice
  and unchanged where the sketch parses few colour strings (noise, text_dots).
- **Plain numbers skip the ABC check** (S-146). `Vector` validates every number it is given, and
  `isinstance(v, numbers.Real)` goes through the ABC machinery. `vector._is_number` now tests the
  exact types `int` and `float` first and only then falls back to the `Real` check, so a `bool`
  is still refused and Fractions behave as before; the same helper serves `*` and `/`. Messages
  are unchanged. `Vector(1.5, 2.5)` 1.2 to 0.29 us; whole `draw()` 25 % faster on kinetic_type and
  15 % on flow_field_print.
- **Text outlines are scaled once per glyph and size** (S-147). `TextRun.outline_ops` used to scale,
  flip and place every glyph's outline on every frame, point by point in Python. `FontResource.scaled_outline`
  now keeps the scaled, y-down outline per `(glyph, variation, size)` in a per-font LRU of at most 2048
  entries (a sketch that changes its text size every frame cannot grow it), and `outline_ops` only adds the
  pen position to each point, with the public `Path.translated` (S-149, D-076). A `Path` cannot be changed, so the cached outline is shared safely. The ops are
  equal, float for float, to the old ones: no snapshot or golden changed. Cairo time per frame, min of 5
  rounds: poster_series 10.6 to 8.2 ms, paths-06 outlines 4.2 to 3.3, text_dots 5.4 to 4.6, Session 1
  05_text 1.7 to 1.1; `draw()` unchanged.
- **Internal capability first, public API later** (`PROCESS.md`). `Save/Restore/Concat/ClipPath/
  FillPath/StrokePath` exist in the IR now so the vector renderer and the text subsystem can use
  them; `p.translate()`, `p.path()`, `with p.saved_state()` arrive in Phase 2 as thin emitters.
- **Snapshots are the cross-backend contract** (`tests/test_ops_snapshot.py`): the final frame's
  op list for each Session-1 sketch, as JSON. Two correct renderers may differ in pixels; they may
  not differ in ops.
- **Export is replay**: the same frame goes to a Cairo PDF/SVG surface whoever drew the window.
- **`Text` is reserved**: today the legacy renderer draws it; from Sprint 3 the text subsystem
  materialises it into `FillPath` ops (glyph outlines), and a later PDF exporter may consume the
  richer `TextRun` to embed fonts (S-032).

## 5. Providers, per capability

| Capability | Provider | Status |
|---|---|---|
| Window, events, input, clock, audio, controllers, presentation | **pygame-ce** | decided (ADR-001) |
| Interactive 2D rendering | **OPEN — reference implementation Cairo**; D-011 pending (recommendation: Cairo for Sprint 3, Blend2D as a gated optional fast renderer later) | ADR-002 |
| PNG / PDF / SVG export | **Cairo** surfaces, replaying the IR | ADR-002 |
| Text shaping | **uharfbuzz** | D-006 |
| Font model / glyph outlines | **fontTools**; bundled **DejaVu Sans** | D-006, D-009 |
| SVG import | resvg-py (Phase 3) | backlog |
| Raster images | Pillow (Phase 3) | backlog |
| Video | ffmpeg subprocess (Phase 3) | backlog |
| GPU / 3D | none; Vello and Skia GPU on the watch list (Phase 4) | directional |

## 6. Public semantics

Pinned in `Semantic_Contract.md` and tested pixel by pixel. Highlights: origin top-left, y down,
logical pixels, HiDPI hidden (physical-resolution rendering from Sprint 3); `rect` top-left,
`ellipse`/`circle` centre, circle by diameter; colours 0–255 in every v0.5 form; **degrees**;
text anchored top-left; from Sprint 3: alpha honoured, strokes centred, fractional coordinates
anti-aliased (D-003/4/5, one deliberate golden regeneration).

## 7. Text

Bundled TTF → uharfbuzz (glyph ids, advances, offsets) → fontTools outlines (cached per glyph) →
`FillPath` ops. Deterministic on every platform and renderer; 0.44–0.48 ms per line cached
(Spike 06); kerning, ligatures and Devanagari conjuncts correct. Accepted limitation: exported
PDF text is outlines, not searchable, until fonts are embedded (S-032). Detail:
`Text_Subsystem_Note.md`.

## 8. Phases, sprints, checkpoints

| Phase | Sprint | Checkpoint | Status |
|---|---|---|---|
| 0 Stabilise v0.5 | 0 | 73 tests; 12 Session-1 sketches; 11 exact goldens; API + semantics frozen | done |
| 1a Refactor under pygame drawing | 1 | `Sketch`, platform split, state, colour — goldens byte-identical | done |
| 1b Draw-op IR | 2 | IR + `LegacyPygameRenderer` — goldens byte-identical; IR snapshots; bake-off | done (D-011 pending) |
| 1c Vector renderer | 3 | D-011 engine consumes the IR; D-003/4/5 applied; goldens regenerated once; HiDPI; headless; export; legacy renderer deleted | next |
| 2 Public API on the vector model | 4+ | transforms, paths, `saved_state()`, text subsystem v1, Quick Reference v0.6 | planned |
| 3 Creative media · 4 GPU/3D | — | images, SVG import, sound, document model · OpenGL/GPU | directional |

## 9. Test hierarchy

1. Public API semantics — `test_api_contract`, `test_semantics` (42 pixel tests)
2. **IR snapshots** — `test_ops_snapshot` (primary cross-backend contract)
3. Per-backend semantics — pixel rows of `test_semantics`
4. Per-backend goldens — `test_examples_golden` (exact today; tolerance once a second renderer exists)

Plus: `test_color`, `test_state`, `test_geometry`, `test_ir`, `test_sketch`, `test_capabilities`,
`test_boundaries`. 153 tests, headless (`SDL_VIDEODRIVER=dummy`), CI matrix 3 OS × Python 3.11–3.14.

## 10. Packaging

Base install: `pygame-ce` + the Sprint-3 renderer (+ `fontTools`, `uharfbuzz`, one font ≈ 5 MB
when text lands). Extras, independently installable, before any separate distribution:
`playground[fast]` (Blend2D, gated), `[media]`, `[gpu]`. Missing capabilities fail at `p.size()`
with a message naming the extra.

## 11. Alternatives considered

| Candidate | Kind | Verdict | Evidence |
|---|---|---|---|
| pygame.draw as renderer | raster API | rejected — cannot implement transforms/paths/clip/AA strokes | Spike 01 |
| Skia (skia-python) | 2D engine, CPU/GPU | complete but 81 MB (numpy) and 3–25× slower than Cairo on CPU in this binding; future IR consumer if typography/GPU need it | Spikes 03, 05, 07 |
| Cairo (pycairo) | CPU 2D + PDF/SVG | complete, 2 MB, mature binding; reference implementation | Spikes 05, 07 |
| Blend2D (blend2d-py) | JIT/SIMD CPU 2D | fastest measured (3–10× Cairo), 2 MB, conic gradients, font-from-file; binding lacks clip/matrix/fill rule, no macOS x86_64, one company since 2025 — gated | Spike 07 |
| Vello | Rust CPU/GPU vector | no Python package, API in flux — watch list | — |
| WebRender | GPU renderer for web display lists | browser-scale retained rendering; wrong complexity trade | — |
| GSK | GTK scene graph | would pull in GTK as platform — study the render-node idea, not the dependency | — |
| Moz2D / Azure | abstraction over backends | validates our IR-over-backends design; not itself an engine | — |
| WebKitGTK | browser engine | not a renderer; evidence that Cairo→Skia moves are GPU-workload-driven | — |
| pyglet / arcade / moderngl-window | pygame alternatives | not re-evaluated: pygame-ce's platform role is settled and works | ADR-001 |

## 12. Risks

| Risk | Mitigation |
|---|---|
| Engine choice regretted | IR + snapshots make a renderer a ~100-line file; Spike 07 harness re-runs in minutes |
| `blend2d-py` binding stalls | It is optional and gated; Cairo remains complete |
| CPU rasterisation limits at 1080p | Default examples ≤ 720p; GPU is a Phase 4 concern; Blend2D headroom if adopted |
| Text as outlines: no searchable PDF | Accepted (D-006); `TextRun` reserved for embedded-font export (S-032) |
| Python cost of walking the IR | Included in every Spike 07 number; acceptable at teaching scale; hot loops can move to the renderer later |
| Font licence / coverage | DejaVu Sans (Bitstream Vera licence, shipped); per-script Noto fonts added when needed |

## 13. References

`ADR-001-renderer-topology.md` · `ADR-002-renderer-selection-reopened.md` · `Decision_Log.md`
(D-001…D-011) · `Semantic_Contract.md` · `Text_Subsystem_Note.md` · `Playground_Architecture_Review.md`
· `spikes/RESULTS.md` (§1–7) · `docs/PROCESS.md` · `docs/qa/Test_Strategy.md` · `docs/backlog/`.
