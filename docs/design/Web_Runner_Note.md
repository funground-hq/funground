# Design note: the web runner (0.2)

**Status:** design for Sprint 20 (S-152, S-153, S-137, S-151), 9 October 2026. The funground side is implemented in S-152 (`platform/browser.py`, `web.py`, contract W1, `tests/test_web_session.py`); the browser side is S-153. Decisions behind it: D-074
(target W2, Chrome first, L1 loop, editor H1, GitHub Pages), D-075 (Cairo draws in the browser), D-077
(website), D-078 (preview origin). Evidence: Sprints 17–19 and `funground-web` `spikes/`.

## Shape

```
page (site or preview origin)                         module worker
  canvas  <── frame pixels (BGRA, transferred) ──┐    Pyodide 314
  input events ── postMessage ──────────────────►│    funground (pure-Python wheel)
  requestAnimationFrame: "step(now)" ───────────►│    pycairo, uharfbuzz, skia-pathops wheels
  Web Audio  <── sound buffers ──────────────────┤    funground.web.Session
  mic AudioWorklet ── chunks ───────────────────►│      start(source) / step(now) / stop()
  Stop: worker.terminate()                       └─   BrowserPlatform (no window)
```

## funground side (repo `funground`, `release-0.2-web`)

- **`funground/platform/browser.py`, `BrowserPlatform`.** Implements the `Platform` protocol for a host
  that owns the window. No window is opened; the canvas size, backing scale and input come from the host.
  `tick()` never sleeps: it returns the seconds since the previous step, from the host's clock
  (`Loop_Inversion_Note.md`). `present()` hands the finished Cairo surface's bytes to a host callback.
  Escape does not stop the sketch (the page has a Stop button).
  The platform says `host_driven = True`; `Sketch` reads that one flag (see the `web.py` docstring).
- **`funground/web.py`, `Session`: the host API** (not learner API; learners never import it).
  `Session(width, height, scale, on_frame, on_sound, ...)`; `start(source, filename)` executes the
  learner's file; `step(now) -> bool`; `push_event(...)`; `stop()`. While a session is active, `f.run()`
  calls `Sketch.start()` and returns instead of looping, and `f.show()` presents the drawing and returns
  instead of waiting. This is the only behaviour that differs from the desktop; it gets its own contract
  row (W1), with a clear message wherever a desktop-only feature is used (the D-074 Q4 list).
- **No stubs.** The real `CairoRenderer`, `typography` and `pathops` run, from the wasm wheels. Imports
  that only the desktop needs (pygame, subprocess) stay lazy.

## Browser side (repo `funground-web`)

- `runner/worker.js`: loads Pyodide from jsDelivr, the wheels (funground built from the branch; the three
  C-extension wheels from a `funground-cairo-wasm` release), the bundled fonts, then the learner's source.
- `runner/page.js`: a small API for the site and the editor: `run(source, canvas)`, `stop()`, an output
  panel for `print` and tracebacks.
- Sound (S-137): synthesis stays in Python; buffers go to Web Audio on the page after a first click; the
  microphone is an AudioWorklet posting chunks to the worker.

## Origins and safety (D-078)

- The site (`funground-hq.github.io`) runs **our** code: gallery examples and guide sketches.
- The editor runs **anyone's** code from a shared link, so the sketch runs in an iframe on a separate
  origin, `funground-run.github.io` (a second GitHub organisation), sandboxed with `allow-scripts` and
  without `allow-same-origin`, talking to the editor only by `postMessage`. Pyodide can reach any browser
  API, so the origin is the boundary, not the worker.

## Limits in 0.2

Chrome first. Desktop-only, each with a clear message: `system_font()`, `input()`, MP4 (GIF works),
choosing a microphone by name before permission, the gallery app's subprocess runner.
