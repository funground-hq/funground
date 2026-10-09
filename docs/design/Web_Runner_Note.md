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
  microphone is an AudioWorklet posting chunks to the worker (see Sound and microphone, below).

## Sound and microphone (S-137)

**Playback.** funground makes every sound in Python and keeps its own clock (contract A1 to A3), as on the
desktop. `sound.py` talks to a device through a few calls on `pygame.mixer` (open it, make a sound from samples
or a file, play with loops, stop, pause and unpause a channel, set volumes). Those calls are the seam:
`sound.use_host_mixer(mixer)` replaces pygame's mixer with `HostMixer` (`platform/browser_audio.py`), which answers
the same calls and hands each to the host as a command. `Session` installs it, `BrowserPlatform` owns it and
`Session.stop()` removes it. Nothing else in `sound.py` changed; with no Session the desktop path is as before.
pygame is not imported (a test checks it), so the runner no longer loads pygame-ce for a sketch that only
plays sound: 1.53 MB less to download for it (RESULTS.md of the runner).

The host callback is `on_sound(command, voice, fields, samples)`. A sound's samples (32-bit floats, stereo
interleaved, 44 100 Hz, exactly the 16-bit samples pygame would get divided by 32768) go once, with the first
play, as `load`; then `play {loops, volume, left, right}`, `pause`, `resume`, `volume`, `pan`, `stop`, `free` (the
sound was dropped) and `stop_all` (the run ended). Pan is two gains, funground's own balance law, which the page
applies with a splitter and two gain nodes, not a `StereoPannerNode`. The page never has to tell Python that a
sound ended: Python's clock knows (A2).

In the browser the worker posts these as `sound` messages (the samples' buffer transferred) and `runner/audio.js`
plays them with Web Audio after a first click or key (Run counts). A sound asked for before then is skipped with
one line of output. A paused sound resumes at the position the page measured. Contract rows: W1.

**Microphone.** The reverse direction, into the ring buffer the desktop code fills. `microphone_input` already
had one function that opens a device and returns `(device, rate)`; under a host it returns a `HostMicrophone`
device (`microphone_input.use_host_input`). `mic.start()` makes the host a `microphone start` request; the page
opens `getUserMedia` (echo cancellation, noise suppression and gain off, as the desktop applies none), runs an
`AudioWorklet` (`runner/microphone-worklet.js`) that posts 1024-sample mono chunks, and the worker passes each to
`Session.push_microphone(samples)`. Nothing after the ring buffer changed, so `level()`, `pitch()`, `is_onset()`,
`capture()` and the rest read as on the desktop (tests compare them with the desktop path on the same samples).
Until permission is granted the ring buffer is empty, which reads as the not-listening values. A refusal is one
line of output. The microphone is never played back (its path to the speakers has a gain of 0, only so the
browser keeps the worklet running).

**Limits, proposed for W1.** WAV (16-bit) is the only file `f.load_sound()` reads; a sound started before the
first gesture is not started later; a refused microphone does not raise at `start()`; choosing an input by name is
desktop-only (`f.microphone("name")` raises, `f.microphones()` is `[]`). Tests: `tests/test_web_sound.py`
(here) and `tools/test_sound.py` (`funground-web`, headless Chrome with a fake microphone).

## Origins and safety (D-078)

- The site (`funground-hq.github.io`) runs **our** code: gallery examples and guide sketches.
- The editor runs **anyone's** code from a shared link, so the sketch runs in an iframe on a separate
  origin, `funground-run.github.io` (a second GitHub organisation), sandboxed with `allow-scripts` and
  without `allow-same-origin`, talking to the editor only by `postMessage`. Pyodide can reach any browser
  API, so the origin is the boundary, not the worker.

## Limits in 0.2

Chrome first. Desktop-only, each with a clear message: `system_font()`, `input()`, MP4 (GIF works),
choosing a microphone by name, the gallery app's subprocess runner.
