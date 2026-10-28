# ADR-007: A core and libraries imported as modules

## Status

Accepted, 28 October 2026 (maintainer, D-120). The reasoning, every name's group and the maintainer's answers are in
[Core_and_Libraries_Note.md](Core_and_Libraries_Note.md).

## Context

All 211 public names were on `f`. The maintainer asked whether funground should, like Processing and p5.js, keep a core
and put fields such as sound, the camera and machine learning in libraries. On the desktop, splitting saves nothing to
install: pygame-ce gives the window, sound and the camera. Play already loads packages only when a sketch needs them.
The gain is in concepts: a smaller `f.` for a beginner and an import line that says what a sketch uses. Machine learning
is the exception, because its downloads are large and must not reach every install.

## Options

1. **Keep current behaviour:** every name stays on `f`.
2. **One install, libraries imported as modules:** `from funground import sound`. A library with a heavy dependency is
   a separate package, imported the same way.
3. **Importing a library adds its names to `f`:** this is Processing's style, but a hidden side effect in Python.
4. **A separate package per library:** this is p5's route, with versions to match.

## Decision

Option 2:
- **Three libraries ship with funground:**
  - `sound` (18 names);
  - `sangeet`, Indian music: ragas and talas (6 names);
  - `camera` (3 names).
- **`ml` is a separate package,** `funground-ml`, imported as `from funground import ml` (E-37).
- **The core keeps the other 184 names on `f`.** Controls and studio are included.
- **No alias period.** funground has no users yet (maintainer, 28 Oct), so the moved names leave `f` in 0.2.
  - Calling a moved name on `f` gives one plain sentence that names the import line, never a bare `AttributeError`.
  - The sentence stays for good.
- **Each library meets the core's rules:**
  - the same file runs on the desktop and in Play;
  - contract rows, goldens and a reference page;
  - completions, its own part of `llms.txt`, a gallery area and Since markers.
- **Names are designed as they move.** For example, `camera.open()` rather than `camera.camera()`. The maintainer
  approves each library's names before it is built.
- **The course teaches the import line from the first lesson that uses the library.**

## Consequences

- **Released 0.1 code that calls a moved name breaks in 0.2.** The forgotten-import sentence says how to fix it.
- **Internal modules move or are renamed:**
  - `funground/sound.py` and `synth.py`, so that `sound` can be the library;
  - `hindustani.py`, into `sangeet`;
  - `camera_input.py`, into `camera`.
- **The naming trap** (a submodule must not share a public function's name) is checked again for each new module name.
- **The semantic contract's sound and music rows change their spelling,** for example `sound.note` rather than `f.note`.
  Their meaning stays. The camera's rows change too.
- **`tests/test_boundaries.py` gains rows for the libraries.** A library imports the core; the core never imports a
  library.
- **Play's runner** may load a library's packages from its import line.
- **A future library needs** a field of its own, plus its own dependency or platform path, or enough names to crowd `f.`.
  It also needs a new decision.
