# Design note: Playground in the browser — how Pyxel does it, what it would take for us

**Status:** research, 25 September 2026. Proposes epic E-31 and a feasibility spike (S-059); no code.

## 1. How Pyxel runs in the browser

Pyxel is a Rust engine on SDL2 with Python bindings. Its browser mode is not a rewrite; it is the
same engine compiled to WebAssembly and loaded into **Pyodide** (CPython compiled to wasm):

| Piece | What Pyxel does | Evidence |
|---|---|---|
| Runtime | Pyodide from a CDN (`cdn.jsdelivr.net/pyodide/v314.0.4/full/pyodide.js`) | `wasm/pyxel.js` |
| Engine | Rust + SDL2 built for `wasm32-unknown-emscripten` with **maturin**, `embuilder build sdl2 --pic`, pinned to *"Emscripten 5.0.3 (the version Pyodide uses)"*; shipped as `pyxel-2.9.9-cp311-abi3-emscripten_5_0_3_wasm32.whl` | `Makefile`, `pyxel.js` |
| Loading | `pyxel.js` prefetches the wheel in parallel with Pyodide, then `pyodide.loadPackage(wheelUrl)` | `pyxel.js` |
| Canvas | A `<canvas>` handed to SDL via `pyodide.canvas.setCanvas2D(canvas)`; SDL2's Emscripten port draws into it | `pyxel.js`, Pyodide PR #3508 |
| Game loop | **Emscripten's main loop** (`emscripten_set_main_loop`) — the browser drives frames; Python is called back. Pyodide had to learn to ignore SDL's deliberate `unwind` exception (flag `_skip_unwind_fatal_error`), still marked *experimental* with a stack-unwinding caveat (pyodide #3697) | issue kitao/pyxel #418, Pyodide SDL docs |
| Input | DOM listeners on the canvas; Safari arrow-key normalisation; a virtual gamepad for touch (`gamepad="enabled"`) read by Rust as a bitmask | `pyxel.js` |
| Audio | Web Audio through SDL2; audio context suspended/resumed around resets | `pyxel.js` |
| Authoring surface | Custom elements `<pyxel-run script="…">` / `root`+`name`, `<pyxel-play root="app.pyxapp">`, `<pyxel-edit editor="image">`; a **Web Launcher** URL `https://kitao.github.io/pyxel/web/launcher/?run=user/repo/branch/path/file.py` that loads straight from GitHub; needs a server (no `file://`) | `docs/web-usage.md` |

Two things make this work for Pyxel: its engine is a **single self-contained native module with
SDL2 as the only system dependency**, and SDL2 has a first-class Emscripten port. Pyodide added
SDL support specifically for it (PR #3508).

## 2. What that means for Playground

Playground's dependencies split cleanly by "is there a wasm build":

| Dependency | Pyodide package | pygbag (CPython-emscripten + pygame-ce) |
|---|---|---|
| pygame-ce | ✅ present (SDL route, experimental) | ✅ the whole point of pygbag |
| fontTools | ✅ present (pure Python) | ✅ pure Python |
| **pycairo** | ✗ absent | ✗ absent |
| **uharfbuzz** | ✗ absent | ✗ absent |
| numpy, pillow | ✅ | ✅ |

So the desktop stack does not go to the browser as-is — the renderer (Cairo) and the shaper
(HarfBuzz) are the two gaps. But the architecture was built for exactly this: **the browser is a
third `Platform` + `Renderer` pair consuming the same IR**, not a port.

```
        learner sketch  →  api  →  Sketch  →  IR
                                              │
                    ┌─────────────────────────┼──────────────────────┐
                    ▼                         ▼                      ▼
             CairoRenderer            Canvas2DRenderer        (future: WebGL)
             + PygamePlatform         + BrowserPlatform
             (desktop)                (Pyodide: JS bridge to <canvas>, rAF, DOM events)
```

The IR maps almost one-to-one onto the Canvas 2D API: `Save/Restore` → `save()/restore()`,
`Concat` → `transform(a,b,c,d,e,f)`, `ClipPath` → `clip()`, `FillPath/StrokePath` → path commands
+ `fill()/stroke()`, shapes → `arc`/`rect`/`ellipse`, alpha → `rgba()`, gradients/blend modes →
`createLinearGradient`/`globalCompositeOperation`. A Canvas2D renderer is the same ~100-line
exercise as the three Spike 07 adapters, written against `js.document` from Python (or as a JS
consumer of the serialised frame — `Frame.to_jsonable()` already exists).

### Three routes

| | A. Pyodide + our own BrowserPlatform + Canvas2DRenderer *(recommended)* | B. pygbag (pygame-ce in the browser) | C. Pyodide + pygame-ce via SDL |
|---|---|---|---|
| Runtime | Pyodide (~10 MB, CDN-cached) | CPython-emscripten via pygbag's hosted runtime | Pyodide |
| Loop | **inverted**: JS `requestAnimationFrame` calls `sketch.step()` — no infinite loop, no `unwind` hack | `async def main()` with `await asyncio.sleep(0)` each frame — learner code must change shape | Emscripten main loop, experimental flag, stack caveat |
| Drawing | Canvas 2D (GPU-composited by the browser) | pygame.draw — the renderer we deleted (D-008) | pygame.draw — same problem |
| Text | outlines via fontTools (present); shaping: HarfBuzz missing → see below | same gap | same gap |
| Export | PNG via `canvas.toBlob` → download; SVG from the IR by our own writer; PDF not in browser (or `jsPDF` later) | as A | as A |
| Learner code | **unchanged** (`setup/draw/run`) if `run()` detects the browser and registers instead of looping | must be rewritten to async | unchanged but fragile |
| Risk | our own JS glue (~300 lines) | depends on pygbag's runtime cadence; pygame drawing semantics contradict the contract | Pyodide marks it experimental |

**Recommendation: A.** It keeps every contract row (alpha, centred strokes, AA, degrees) because
Canvas 2D honours them natively, keeps learner code byte-identical, and avoids both the pygbag
async rewrite and Pyodide's experimental SDL path. pygame-ce is not needed in the browser at all;
the browser *is* the platform.

### The text question in the browser

uharfbuzz has no wasm wheel. Options, in the order I would try them:
1. **Build uharfbuzz for Pyodide** with `pyodide-build` (Cython + HarfBuzz C++, no system deps) — likely
   a day; then the browser text route is byte-identical to desktop. Cleanest.
2. **harfbuzzjs** (HarfBuzz's own official wasm build) called from Python via the JS bridge — same
   shaping engine, different binding; deterministic; adds ~1 MB JS.
3. **fontTools-only fallback**: advances from `hmtx` + GPOS kerning via fontTools — no ligatures or
   complex scripts; fine for Latin teaching text, wrong for Devanagari.
4. Canvas `fillText` with the bundled font as a `FontFace` — fastest, but non-deterministic across
   browsers and breaks the text contract; acceptable only as an explicit "browser-native text" mode.

### What Pyxel has that we would want to copy

- The **loader script + custom element** pattern (`<playground-run src="sketch.py">`) — one script
  tag on any static page.
- The **launcher URL** loading a sketch straight from GitHub — the zero-install classroom story.
- Prefetching the wheel in parallel with the runtime; CDN caching; explicit "needs a server" note.
- A virtual gamepad is irrelevant for us, but **touch → mouse mapping** is (contract I1).

### Constraints to accept

- First load: Pyodide ~10 MB + fontTools + DejaVu Sans + our package — roughly 3–8 s cold, ~1 s
  cached. Pyxel lives with the same.
- No threads, no `time.sleep` in `draw()`, no file system: `save()` becomes a download.
- Browser audio autoplay rules — irrelevant until E-17.
- Performance: Canvas 2D is fast for shapes; Python-in-wasm is roughly 3–5× slower than native
  CPython for the IR walk. Teaching-scale sketches (hundreds of ops) stay well inside 16 ms; Spike 08
  measures this.

## 3. Proposed epic

**E-31 Playground in the browser** (TH-1 Teaching Core Stability — it is an *access* feature:
no install, runs on Chromebooks/tablets)

| Story | Content | Phase |
|---|---|---|
| S-059 **Spike 08** | Pyodide (Node first, then a page): mount the pure-Python package, run a Session-1 sketch through a stub platform, time IR frames and fontTools outlines in wasm; then a real `<canvas>` page with a Canvas2D consumer of `Frame.to_jsonable()`; measure fps for the 12 sample sketches | 2 (parallel to Sprint 5) |
| S-060 Loop inversion | Split `Sketch.run_namespace` into `start()` / `step()` / `finish()` so any host can drive frames; desktop `run()` becomes a loop over `step()` — also useful for tests and tooling | 2 |
| S-061 `BrowserPlatform` | rAF-driven `step()`, DOM mouse/keyboard/touch → `InputState`, `backing_scale` from `devicePixelRatio`, `present` is a no-op (renderer draws straight to the canvas) | 2–3 |
| S-062 `Canvas2DRenderer` | every IR op → Canvas 2D; capabilities incl. gradients/blend modes when those ops exist | 2–3 |
| S-063 Browser text | decide between uharfbuzz-for-Pyodide, harfbuzzjs, fontTools-only; a decision row (D-013) with Spike 08 numbers | 3 |
| S-064 Loader + element + launcher | `playground.js`, `<playground-run>`, GitHub launcher URL, static-host deployment recipe (copy of Pyxel's pattern) | 3 |
| S-065 Export in the browser | PNG download; SVG writer from the IR (also useful on desktop, removes Cairo from the SVG path) | 3 |
| S-066 Classroom page | an editor beside the canvas (CodeMirror), run/stop, share-by-URL — the "no install" lesson page | 3 |

**Exit:** every Session-1 sketch runs unchanged in a browser page with identical IR snapshots and
visually equivalent output; a lesson can be shared as a URL.

## Sources

Pyxel `wasm/pyxel.js`, `Makefile`, `docs/web-usage.md` (kitao/pyxel, main, 25 Sept 2026);
kitao/pyxel issue #418; Pyodide PR #3508 and "Using SDL-based packages in Pyodide" (v314);
Pyodide packages list (v314); pygbag 0.9.3 on PyPI (Feb 2026); PyScript 2026.3.1 `py-game` docs.
