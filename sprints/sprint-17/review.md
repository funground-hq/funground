# Sprint 17 review — 0.2 web spikes

**Dates:** 8 October 2026. **Not yet signed off.**

## Outcome

All four spikes answered their question. In short: the browser can run funground unchanged, the
canvas can draw its IR within tolerance, Cairo and the text shaper run in the browser byte-identically,
and the loop inversion keeps the desktop green.

| Spike | Criterion (from the options note) | Result |
|---|---|---|
| S-135 Canvas 2D | ≤ 3 % pixels differing, mean ≤ 3, edges only, all 20 op types | **Pass in Chrome**: 63/63 cases (CPU raster), 61/63 (GL; two thin-line frames at 3.6–3.8 %). All differences on edges. Cannot match: `no_smooth` beyond axis-aligned rectangles, byte-exact pixel round trips, scaled-image borders. 0.5–2 ms a frame; shadow-heavy frames 20–63 ms (unbounded shadow layers) |
| S-134 Cairo in Pyodide | (a) builds (b) goldens byte-identical (c) ≤ 12 ms at 1280×800 (d) ≤ 6 MB | (a) pass (b) **pass**, 13/13 Session-1; 70/74 gallery (4 JPEG-decoding differences, not Cairo) (c) **fail as written**: Cairo 16.5 ms average on the 10 heaviest examples (native 7.8) — but the sketches' own `draw()` costs more (46.5 ms Node, 18.5 native) (d) pass, 1.65 MB |
| S-136 inverted loop | 60 fps steady; Stop ≤ 1 s; input ≤ 2 frames; desktop suite green | **Pass**: 59.99–60.06 fps; Stop immediate; input to drawn frame ≤ 1.25 frames; `3620 passed`. Cold load 6.4 s median, warm 3.6 s |
| S-133 text | outlines identical to native | **Pass with the PyPI wheel** (`uharfbuzz` 0.56.3, `pyemscripten_2026_0`, 0.98 MB): 1405 strings, glyphs, clusters and FillPath data identical; Session-1 05/13/14 in the browser within tolerance. Shaping ~4× slower than native. harfbuzzjs shim also identical, kept as fallback |

## Findings that change later work

1. **No C build is needed for text.** uharfbuzz already publishes Pyodide wheels; Q7 shrinks to pycairo
   and skia-pathops, which build with three small patches and a 6-minute CI job.
2. **Python, not drawing, is the bottleneck on heavy frames.** Any renderer inherits it.
3. **Handing a frame from Python to the page is expensive for busy frames** (10 ms to encode 500
   circles as JSON). A compact encoding is needed whichever renderer is chosen.
4. **Shaping is not cached.** A shaped-line cache would help the web (4× slower) and the desktop.
5. **HarfBuzz versions differ** between the desktop and web wheels (14.5 vs 14.6); identical today, but
   nothing pins them. The S-133 corpus re-checks in a minute.
6. **funground needs a proper web entry point**: the spike replaced `f.run()` from outside, and stubbed
   `cairo2d`, `pathops` and `uharfbuzz` imports.

## Decisions

- D-074 (Q1–Q3, Q5, Q6, Q8, Q9) accepted before the spikes.
- **D-075 pending**: how the browser draws — B (canvas only), C (Cairo only) or D (canvas on screen,
  Cairo loaded for files and exact pixels). Recommended: D.
- `funground-cairo-wasm` raised its own D-007 on the same question; it becomes CW-D-007 and points to
  D-075 when PR #1 merges.

## Built by

S-135, S-136 and S-133 by Sonnet subagents from briefs; S-134 by a Claude cloud session (its own sprint
records in `funground-cairo-wasm`). Reviewed, committed and pushed by the main session.

## Gaps

Chrome 154 headless only; no Firefox or Safari. No real GPU, vsync or scan-out measurement. Sound,
microphone, files, pictures and controls in the browser are untested (S-137, S-138). First-load budget
on a throttled link untested (S-139).

## Retrospective

- Parallel work across a local machine and a cloud session worked; the C toolchain never touched the
  maintainer's machine.
- Process instructions had to be pasted into the first cloud session; the `funground-sdlc` skill now
  travels with every repository.
- Redirecting S-133 mid-flight to try the existing wheel first saved the shim from becoming product
  code. Check PyPI for existing wasm wheels before planning a build.
