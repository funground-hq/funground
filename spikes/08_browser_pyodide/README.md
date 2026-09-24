# Spike 08 — Playground's core under Pyodide (story S-059, epic E-31)

Question: can the pure-Python core (`api` → `Sketch` → IR) run in the browser via Pyodide, and how
fast are the pieces a browser mode needs? Write-up: `spikes/RESULTS.md` §8; design context:
`docs/design/Browser_Mode_Note.md`.

## Part 1 — Node + Pyodide (`feasibility.mjs`, `feasibility.py`)

```
npm install                 # pyodide@0.28.3 (13 MB, node_modules/ is git-ignored)
node feasibility.mjs        # prints one JSON line, writes results.json; needs network once
```

`feasibility.mjs` loads Pyodide, `loadPackage("fonttools")`, mounts `../../playground/` into the
Pyodide FS (skipping `platform/pygame_platform.py`, `renderers/cairo2d.py`, `export/`,
`__pycache__`) and runs `feasibility.py` inside the wasm interpreter. That file imports the core,
defines a rAF-style `BrowserPlatform` stub (no waiting) and a `Canvas2DStubRenderer` that walks the
IR counting the Canvas 2D calls it would make, runs a 50-circles + text `draw()` for 60 frames
through `Sketch.run_namespace`, then times `Frame.to_jsonable()` and fontTools outline extraction
for `"Hello, Playground!"`.

The same Python file runs under native CPython for a wasm/native ratio:

```
SPIKE_ROOT=C:/Projects/playground ../../.venv/Scripts/python feasibility.py   # -> results_native.json
```

## Part 2 — a `<canvas>` consumer of the IR JSON (`page/`)

`page/ir_canvas.js` draws a `Frame.to_jsonable()` list with the Canvas 2D API, op for op as
`playground/renderers/cairo2d.py` does; `page/index.html` picks one of the 11 real snapshots copied
from `tests/snapshots/` into `page/snapshots/` and shows the desktop golden beside it. Text uses
`ctx.fillText` with the bundled DejaVu Sans as a `FontFace` — browser shaping, **not** the
deterministic outline route; the page says so.

Serve the **repo root** (the page reaches the font and goldens with `../../../`):

```
python -m http.server 8765          # from C:\Projects\playground
http://127.0.0.1:8765/spikes/08_browser_pyodide/page/index.html?snapshot=05_text
```

`page/screenshots/*.png` were taken with headless Edge 153 (Chromium) at DPR 1
(`msedge --headless=new --screenshot=... --window-size=640,400 ...?snapshot=NAME&shot=1`) and
compared with `tests/golden/*.png` by `compare.py` → `page/screenshots/compare.json`.
