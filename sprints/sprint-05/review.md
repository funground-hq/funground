# Sprint 5 review — Phase 2b: vocabulary, events, helpers

**Dates:** 25–26 September 2026; closed by the maintainer 30 September 2026
**Goal:** the drawing vocabulary, colour, input events, helpers and loop control that a typical
p5/Processing 2D sketch uses, each with pinned semantics, tests, a gallery example and a guide
section; plus the gallery and guide foundations and the Sprint 4 follow-ups.

## Outcome

Every planned story is done except S-039 (CI first run), which is **still blocked on a git
remote** and carries to Sprint 6. **Checkpoint met:** no pre-existing Session-1 golden, IR snapshot
or reference image changed (`git diff --stat --diff-filter=MD 6c8984b..HEAD -- tests/golden
tests/snapshots docs/reference/images` is empty). **62 public names added** (45 → 106 in
`__all__`) and one removed by the approved D-016 rename (`mouse_pressed` → `is_mouse_pressed`).
The Examples Gallery holds 31 examples in 13 areas and covers every public name: the coverage
allowlist is empty. The User Guide has chapters 1–13 complete; 14 and 15 are Sprint 6 work (S-071).

Mid-sprint the maintainer changed the release plan: the first PyPI release will be **0.1**, not
v0.7 (D-019). That raised D-020, the package name, because `playground` is taken on PyPI.

| Story | Result | Commit |
|---|---|---|
| S-070 Version bump | `0.7.0.dev0`, since replaced by `0.1.0.dev0` (D-019) | 76d07e0, b330099 |
| S-067 Sprint 4 follow-ups | Contract F2 wording; empty `clip()` warns; Linux window route; `StateStack.unwind()` test | 21ccd08 |
| S-040 Feature Map verified | Against p5.js 2.3.3, Processing 4, DrawBot 3.132; found the `curve_vertex` conflict (D-018) and six small gaps; added S-074 | 46d2c46 |
| S-068 Gallery foundation | `examples/gallery/`, `tools/make_gallery.py`, generated index, coverage test | 6b9ef79, 2a526c3 |
| S-069 Guide skeleton | `docs/guide/` with 15 chapters; every `python` block runs as a test | 6c20219 |
| S-041 Shapes | `square`, `triangle`, `quad`, `polygon`, `arc` (open/chord/pie), `clear`, `no_clip` | 22b8c59 |
| S-042 Strokes | `stroke_cap`, `stroke_join`, `miter_limit`, `stroke_dash`/`no_dash`, `no_smooth`/`smooth` | 7f8b10d |
| S-043 Matrix | `shear_x`, `shear_y`, `apply_matrix`, `reset_matrix` (keeps the HiDPI base) | d767b3b |
| S-074 Curves (D-018) | `bezier_vertex`, `quadratic_vertex`, Catmull-Rom `curve_vertex`, `curve_tightness`, contours, `bezier`/`curve` and their point/tangent helpers | 5ad6223 |
| S-046 Maths helpers | `map_range`, `lerp`, `norm`, `mag`, `random_gaussian`, `random_choice` | c5beaad |
| S-047 Noise | p5.js's algorithm ported value for value | 7c705a1 |
| S-048 Loop and time | `no_loop`, `loop`, `redraw`, `is_looping`, `exit`, `millis`, `frame_rate`, `second` … `year` | dd184c7 |
| S-044 Colour (D-017 = C) | `hsb`, `hsl`, `color` objects, `lerp_color`; no `color_mode` | 3e14144 |
| S-045 Input events (D-016) | Nine callbacks, `pmouse_x/y`, `mouse_button`, `key`, `key_code`, `is_key_pressed` | 89d8200 |
| S-058 ADR-003 | Out-of-scope list with "use instead" for each item | 5200be0 |
| S-039 CI first run | **Not done: blocked, no remote.** Carried to Sprint 6 | — |

## Test results

```
506 passed in 123 s   (Sprint 4 close: 275)
  api_contract 7 · semantics 42 · examples_golden 28 · ops_snapshot 15 · gallery 93 · guide 20
  reference 25 · color 38 · colour_objects 24 · shapes 14 · strokes 18 · curves 11 · paths 24
  transforms 26 · helpers 6 · noise 9 · loop 7 · events 8 · export 7 · hidpi 21 · text 13
  cairo_renderer 10 · geometry 13 · state 5 · ir 5 · capabilities 6 · sketch 5 · headless 3 · boundaries 3
```

Windows 11, Python 3.14.7, pygame-ce 2.5.8, pycairo 1.29.1. **CI has still never run** (S-039).

## Measurements

- **Noise speed:** about 7 µs per sample at 4 octaves; 10 000 samples take about 68 ms. Roughly
  1 500 samples per frame fit in 60 fps. The guide says so. A vectorised path would need numpy
  in the base install, so it was not added.
- **Noise fidelity:** after `noise_seed(42)`, values equal p5.js's own to 6 decimal places
  (checked by running p5's algorithm in Node; pinned in `tests/test_noise.py`).
- **Stability:** zero bytes changed in the Session-1 goldens and snapshots across 15 stories.

## Bugs found and fixed

1. **Fractional colour components were rejected** (de4eafb). v0.5 truncated them, as pygame does;
   Sprint 1's colour parser raised instead. Now truncated again, NaN rejected, parity-tested
   against pygame. A Sprint 1 regression that no test covered.
2. **`p.save()` to PNG saved only the current frame** (b86ca6b). Since S-034, a PNG was a replay
   of this frame's ops onto a blank page, so a sketch that paints across frames lost its earlier
   strokes. PNG now writes the rendered pixels. PDF and SVG still replay one frame, and the guide
   says so. Found by the paint gallery example.
3. **A frame that drew nothing was never presented**, so headless capture failed after
   `no_loop()`. `_render()` now always presents (dd184c7).
4. **pygame raised "Iterating over key states is not supported"** when asked whether any key was
   held. Key state is now tracked from key-down/key-up events and cleared on focus loss (89d8200).
5. **The gallery render tool gave no picture for a `no_loop()` sketch** (61ba72c). It hooked
   `draw()`, which stops running. It now saves the last frame shown when the run ends; every
   existing image came out byte-identical.

## Findings

1. **The Definition of Done rule from D-015 paid for itself.** Writing each story's gallery
   example exposed bugs 2 and 5; the unit tests had missed both.
2. **Contract changes were cheap because nobody uses v0.5** (D-016, D-018). Each rename came with
   a learner-readable error for the old name. This window closes at the 0.1 release.
3. **Input examples render blank headless.** `interaction/02_paint` shows only its status bar,
   because no mouse moves during the render. Acceptable, but the gallery page could explain it.
4. **macOS and Linux HiDPI remain unverified on real hardware** (from S-038).
5. **pygame is now platform only**: window, events, frame pacing, presentation, in one file.
   Replacing it is a contained change if ever wanted (discussed 26 Sept; no decision needed).

## Decisions

| ID | Question | Outcome |
|---|---|---|
| D-016 | Event-callback names | p5 names in snake_case; live booleans start with `is_` |
| D-017 | What `color_mode()` controls | C: no `color_mode()`; `hsb()`/`hsl()`/`color()` constructors |
| D-018 | Curve names | A: `bezier_vertex`; `curve_vertex` is Catmull-Rom |
| D-019 | Release numbering | First PyPI release is 0.1, after Sprint 6 |
| D-020 | PyPI distribution name | **Pending**, needed before the release story |

## Sign-off

**Closed 30 September 2026** by the maintainer ("Close sprint 5 and 6").

- The checklist in `reviewers_guide.md` was not ticked item by item; the maintainer closed the
  sprint by instruction.
- S-039 (first CI run) carried again. The remote now exists (D-023) and CI has run: Windows
  passes, Linux and macOS fail for environment reasons. It is the first story of Sprint 7.
- macOS and Linux HiDPI remain unverified on real hardware.
- Decisions taken while the sprint was open: D-016, D-017, D-018, D-019.

## Retrospective

- **Went well:** one story, one commit, each with its example and guide section. The coverage
  test made "every feature in the gallery" mechanical rather than a promise.
- **Went badly:** the test-run machinery cost time twice: a machine sleep looked like a hang,
  and shell/Python path differences broke a scripted partial commit.
- **Change for Sprint 6:** add the gallery example *first* in each story, before the unit tests.
  It found more bugs than the tests did.
