# Sprint 3 review — Phase 1c: Cairo via the IR, semantic migration

**Dates:** 25 September 2026
**Goal:** Cairo consumes the IR and presents through pygame; v0.6 semantics take effect with one
deliberate golden regeneration; text moves to the outline route; HiDPI, headless and export land;
the legacy renderer is deleted.

## Outcome

All six stories done. **Phase 1 checkpoint 3 (D-007) met — Phase 1 is complete:** learner code
unchanged, IR snapshots byte-identical, goldens regenerated exactly once, no `pygame.draw` in the
package. One decision raised: D-012 (`text_size` meaning), accepted as A at sign-off.

| Story | Result | Commit |
|---|---|---|
| S-029 Text subsystem v1 | `typography.py`: `FontResource`, `TextRun`, DejaVu Sans + licence bundled | 54e35c6 |
| S-023 `CairoRenderer` | Every IR op incl. clip/transform/paths/text; v0.6 semantics; `PLAYGROUND_RENDERER` | c730711, 93751b8 |
| S-025 Semantic migration | Cairo default; 5 semantic tests to v0.6 rules; 11 goldens regenerated; snapshots unchanged | 3e4eccd |
| S-026 Delete legacy renderer | pygame is platform-only; lint asserts per-provider backend imports | 9fa90ca |
| S-024 HiDPI | physical window + base scale; logical `p.width`; mouse logical; verified at 125 % | 888b8a3 |
| S-034 Headless + export | `HeadlessPlatform`; `p.save()` PNG/PDF/SVG by replaying the frame's ops | 8bf07c9 |

## Test results

```
185 passed
  api_contract 7 · semantics 42 · examples_golden 24 (11 goldens) · ops_snapshot 13
  color 33 · state 4 · sketch 5 · boundaries 3 · geometry 13 · ir 4 · capabilities 6
  text 7 · cairo_renderer 10 · hidpi 5 · headless 3 · export 6
```

Windows 11, Python 3.14.7, pygame-ce 2.5.8, pycairo 1.29.1, fontTools 4.66.0, uharfbuzz 0.56.2.

## The one golden regeneration — every visual change, listed

Composites in this folder (`before_after_*.png`, v0.5 left, Cairo right):

| Change | Contract | Where visible |
|---|---|---|
| Edges anti-aliased; fractional coordinates honoured | C6 (D-005) | every shape edge |
| Strokes centred on the edge (half outside), round joins and caps | S4 (D-004) | `04_fill_stroke`: the 8 px navy line now has round ends; outlines sit half a stroke further out |
| Translucent colours composite | S2 (D-003) | none of the Session-1 sketches use alpha — no visible change in goldens |
| Points are anti-aliased dots | S7 | `04_fill_stroke` |
| Text is DejaVu Sans via outlines, regular weight; **em-size semantics make it ~1.4× larger** than pygame's `Font(None, n)` at the same `text_size` | T2, T3 → **D-012** | `05_text` |

IR snapshot diff before/after the switch: **empty** — the learner-facing request did not change.

## Findings

1. **Module naming can break the public API silently.** A new `playground/text.py` shadowed `p.text()`
   the moment anything imported it. Renamed to `typography.py`; the API-contract test caught it in
   the full run, not in isolation — worth remembering that shadowing only shows once the module is imported.
2. **Presentation belongs to the platform.** Moving the blit out of the renderer made renderers
   pygame-free and made `HeadlessPlatform` 60 lines. `Renderer.attach(w, h, scale)` + `pixels()`
   is the whole renderer-side contract now.
3. **HiDPI on Windows needs a process-level call.** Per-monitor DPI awareness must be declared before
   SDL creates the window; the dummy driver is always 1.0 so tests and goldens are stable;
   `PLAYGROUND_BACKING_SCALE` forces a scale for tests. macOS/Linux HiDPI is a follow-up (SDL
   reports logical sizes there; needs the `SDL_WINDOW_ALLOW_HIGHDPI` route).
4. **Export is a replay, and that is enough.** PDF/SVG of a Session-1 sketch is true vector; PNG
   honours the backing scale. `p.save()` writes at frame end so it captures the whole frame,
   regardless of where in `draw()` it is called.
5. **Text size semantics changed visibly** — raised as D-012 rather than decided quietly.
6. **Base install grew** from pygame-ce alone to pygame-ce + pycairo (2 MB) + fontTools (2.5 MB)
   + uharfbuzz (1.5 MB) + DejaVu Sans (0.75 MB): ≈ +7 MB, all cp314 wheels.

## Decisions

- Applied: D-003, D-004, D-005, D-006/D-009, D-008, D-011.
- **D-012 — what `text_size` means: accepted as A (em-size in logical pixels), 25 Sept 2026.**

## Sign-off (25 September 2026)

Maintainer accepted D-012 = A; Sprint 3 **closed**; Phase 1 complete.

## Retrospective

- *Went well:* the three-checkpoint plan (D-007) paid off exactly as intended — the only golden
  diff in the whole phase is the one this sprint made on purpose, and the snapshot layer proved it.
- *Went badly:* two refactor slips reached the full-suite run (a stale `present()` call, a renamed
  helper in a test). Both were caught by the suite within a minute; neither reached a commit.
- *Carry-over:* none. Phase 2 (Sprint 4) can start on D-012.
