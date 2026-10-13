# Design note: the inverted run loop (start / step / finish)

**Status:** accepted with D-074 (L1); merged into `release-0.2-web` as S-060 on 8 October 2026 (prototyped in spike S-136). It carries out the maintainer's
choice L1 in D-074 (Q8): invert the loop in the desktop code, desktop behaviour unchanged.
The browser half of the evidence is in `funground-web/spikes/S-136_RESULTS.md`.

## Problem

`Sketch.run_namespace` was one `while` loop that never returned until the sketch ended, and its only
blocking call was `platform.tick()`. A browser page cannot lend its thread to a loop that never returns.
Python in a Web Worker could block, but then the page cannot reach the worker's memory without
cross-origin isolation (COOP/COEP), which GitHub Pages cannot send (Web_Target_Options.md, section 2, L3).
So the caller of a frame has to be the host: the page, once per `requestAnimationFrame`.

## Design

`run_namespace` is now three methods and a loop over them:

```python
def run_namespace(self, namespace, *, fps=None, max_frames=None):
    self.start(namespace, fps=fps, max_frames=max_frames)
    try:
        while self.step():
            pass
    finally:
        self.finish()
```

| Method | What it is | Taken from |
|---|---|---|
| `start(namespace, fps=, max_frames=)` | Everything before the loop: the mixed-style check, reset of per-run state, `platform.start()`, `setup()`, the default `size()` | the top of the old `run_namespace` |
| `step() -> bool` | One loop iteration: `poll`, input state, events, `draw()` (when looping, after `redraw()` or on the first frame), render and present, `keep` work, the `max_frames` check, then `platform.tick()` and the delta time and frame-rate measurement. Returns whether the sketch goes on | the old loop body, line for line |
| `finish()` | The old `finally` block: drop unfinished recordings and saves, detach the renderer, `platform.close()`, close the panel | the old `finally` |

What the loop body used to keep in locals now lives on the sketch: `_draw_fn` (the `draw` found in the
namespace), `_iterations` and `_max_frames`. They are set in `start()`.

**Where the tick is.** `step()` ends with `platform.tick(self.fps)`, exactly where the old loop had it, so
on the desktop the frame is still paced by the platform. The `Platform` protocol did not change.

**Where the time comes from on the web.** `Platform.tick()` is documented as "wait for the frame budget; return
seconds since the previous tick". A host-driven platform does not wait: its `tick()` returns the seconds
between the two timestamps the page gave it (the `requestAnimationFrame` times of this step and the previous
one), and `1/fps` for the first step. `delta_time` and `frame_rate()` therefore follow the display, not
a sleep. This is the same shape as `HeadlessPlatform.tick`, which already returns the elapsed time without
sleeping, so nothing in `Sketch` had to know which kind of platform it has.

**What the host does** (the browser, a test, a live-reload editor):

```python
sketch.start(namespace)        # setup() has run; no frame yet
while host_wants_a_frame():
    if not sketch.step(): break
sketch.finish()                # always, also after an exception from step()
```

## Alternatives rejected (D-074, Web_Target_Options.md section 2)

- **L2, stack switching (JSPI).** Keeps the `while` loop and awaits a frame promise in `tick()`. Experimental in
  Pyodide and on by default only in Chrome 137+; Firefox and Safari unverified. Kept as a later enhancement
  for a blocking `show()` and `input()`; it does not need this refactor undone.
- **L3, a worker that blocks on `Atomics.wait`.** Needs SharedArrayBuffer, so COOP/COEP headers GitHub Pages
  cannot send (the `coi-serviceworker` workaround reloads the page once; Safari lacks `credentialless`).
- **L4, `async def draw()` (pygbag).** Breaks "learner code never changes shape".
- **A generator** (`yield` once per frame inside `run_namespace`). Needs no state on the sketch, but the
  generator holds the `try/finally` open in a way a host can forget to close, and it is awkward to call from
  JavaScript through Pyodide. Three plain methods are easier to read, test and call.

## Invariants

1. `run_namespace` behaves as before: same order of calls, same exceptions, same `finally`. The existing suite
   is the proof; `tests/test_loop.py` has two new tests for the split.
2. If `start()` raises (a bad `max_frames`, a mixed-style file, an error in `setup()`), `finish()` is not
   needed and not called by `run_namespace`, as before: the old `try` began after `setup()`.
3. `finish()` is safe after an exception raised by `step()` (it is what the `finally` always ran) and it
   resets `running`.
4. `step()` after the sketch has ended returns False and draws nothing.
5. `max_frames` still counts loop iterations (so `no_loop()` sketches end too), now in `_iterations`.
6. Learner code is unchanged: `setup()`, `draw()` and `f.run()` at the end of the file.

## Limits

- `f.run()` still runs to the end on the desktop. On the web, `f.run()` has to register the sketch and
  return, so the host calls `step()`. The spike does this by replacing `funground.run` in the page's
  Python; the product needs a small switch (for example a platform attribute that says it is host-driven).
  Not part of this change.
- `f.show()` for scripts still loops on `platform.poll()`. A browser version must show the drawing and
  return (the R15w idea in Web_Target_Options.md).
- Anything that waits inside `draw()` (a `while True` in learner code, `time.sleep`) still blocks the worker.
  The page stops it with `worker.terminate()`; no cooperation from the sketch is possible.
- Synchronous file loads in `draw()` still need preloading on the web.
- One run at a time per sketch object, as before: `start()` resets the per-run state.

## Tests

- Existing: `tests/test_loop.py` (no_loop, redraw, max_frames, loop control), `tests/test_sketch.py`,
  `tests/test_headless.py`, `tests/test_play.py`, `tests/test_events.py`, `tests/test_controls.py`,
  `tests/test_motion.py`, `tests/test_save_frames.py`, `tests/test_script_mode.py`, and the whole suite.
- New in `tests/test_loop.py`: `test_step_runs_one_frame_and_finish_closes`,
  `test_finish_is_safe_after_an_error_in_draw`.
- Not covered by tests in this branch: a real window (needs a display), and the browser (see the web repo).
