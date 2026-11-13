# How the code is laid out

Where each part of funground lives, the provider boundary and the rules that hold everywhere: what you need to
change the code safely. If this page and the source disagree, the source and the tests win.

The one-sentence version: **funground owns the programming model and the drawing meaning. The draw-op IR is the
contract. Cairo draws. pygame-ce runs the window. Learners never see the seam.**

## The modules

**Core and libraries (ADR-007, S-246, S-247).** `f` holds the core. A **library** is a subpackage that a sketch imports
(`from funground import sound`) and that imports the core. The core never imports a library, and
`tests/test_boundaries.py` checks it. A library keeps its code in modules whose names start with an underscore
(`sound/_engine.py`), so no module can take the name of a public function. There are three today:

- `funground/sound/`: the sound library, 18 names. `_engine.py` (the `Sound` class and the mixer), `_synth.py` (sound
  from numbers), `_swaras.py` (the drone and the singing analysis), `_microphone.py` and `_views.py`.
- `funground/sangeet/`: the sangeet library, 6 names (ragas and talas). `_tables.py` holds the table. sangeet imports
  sound to make sounds; sound never imports sangeet.
- `funground/camera/`: the camera library, 3 names (`camera.open`, `camera.names`, `camera.load_clip`). `_device.py`
  holds the `Camera` and `Clip` classes and the device behind them (pygame.camera, or the page's camera).

What a host supplies (a web page's mixer, microphone and camera) is set in `funground/host_services.py`, a plain
registry in the core. `web.py` sets it, the libraries read it. On a computer it is empty and pygame is used.

Three small things in the core let the camera work without the core importing it:

- `funground/frame_inputs.py` is a registry of inputs the sketch serves each frame. The camera library registers its
  `take_frames` and `stop_all` when it is imported. `Sketch` calls `frame_inputs.take_all(self)` once before each
  `draw()` (the frame is taken once, like the mouse: contract I4) and `frame_inputs.stop_all()` when the sketch ends.
- `picture.FrameSource` is a protocol: an object with a `_current_picture()` method. `f.image()` draws any such object as
  its latest picture, and a `Camera` is one.
- `host_services.camera` is the page's camera, set and cleared by `Session` as the mixer and microphone are.

`from funground import camera` also gives the library module its own class (`camera/__init__.py`), so that a call
`f.camera()` in old code raises one `TypeError` with the sentence naming `camera.open()` (D-123). Before the library is
imported, `f.camera` raises an `AttributeError` with the same sentence.

| Module | What it does |
|---|---|
| `funground/__init__.py` | The public names (`_PUBLIC_NAMES`) and `__all__` (the same less `STAR_LEAVES_OUT`, for `from funground import *`, D-088). A module `__getattr__` serves the live values (`f.width`, `f.mouse_x` and so on) so they are never stale copies. |
| `funground/api.py` | The facade. One thin function per public name. Holds `canvas_sketch()` and `active_sketch()` (the layers rule, section 5), `use_sketch()` (for tests), the exit hint for a forgotten `f.run()`, and `LIVE_NAMES`. Imports no backend. The sound, music and drawing-sound modules are imported lazily inside the functions that need them. |
| `funground/sketch.py` | The `Sketch` class. It owns the platform, the renderer, the `StateStack`, the `Frame`, the random generators, loop control, pages and saving. `run_namespace()` is the callback loop. Choosing the platform and renderer happens here (`default_platform()`, `default_renderer()`). |
| `funground/state.py` | `GraphicsState` (frozen: fill, stroke, widths, text settings, blend mode, modes and so on) and `StateStack` (`save`, `restore`, `unwind`). |
| `funground/ir.py` | The op dataclasses (`Circle`, `Rect`, `Text`, `FillPath`, `Image`, `Pixels` and the rest), `Frame`, and JSON conversion (`to_jsonable`, `from_jsonable`). |
| `funground/renderers/__init__.py` | The `Renderer` protocol: `attach`, `render`, `pixels`, plus a set of `Capability` values. |
| `funground/renderers/cairo2d.py` | `CairoRenderer`, the only renderer today. Replays ops with Cairo. Turns `Text` ops into glyph outlines through `typography.py`. |
| `funground/platform/base.py` | The `Platform` protocol and the small data types (`InputEvent`, `InputState`, `Pixels`). |
| `funground/platform/pygame_platform.py` | `PygamePlatform`: window, events, mouse and keys, frame pacing, HiDPI detection, cursors. |
| `funground/platform/headless.py` | `HeadlessPlatform`: no window, no waiting, input always idle. Chosen by `FUNGROUND_HEADLESS=1`. Used by the tests and by the gallery tools. |
| `funground/platform/browser.py` | `BrowserPlatform`: for a host that owns the window (a web page). Headless plus the host's clock (`tick` never waits), pushed input and a frame callback; Escape does not quit. Not selectable by environment variable: `funground.web.Session` builds it (S-152, contract W1). |
| `funground/web.py` | `Session`, the host API (not learner API): `start(source)`, `step(now)`, `push_event`, `stop`. While a Session runs, `f.run()` returns after `setup()` and `f.show()` returns after presenting. |
| `funground/export/__init__.py` | `save_pixels`, `save_frame`, `save_document`, `save_picture`. Replays ops onto Cairo PDF and SVG surfaces, then hands the file to `pdf_text.py`, `svg_text.py` and `layers.py`. |
| `funground/export/pdf_text.py` | Real, searchable text in PDFs (T15, D-043). Swaps marker groups for text with an embedded font subset, using pypdf. Also holds the marker geometry that `svg_text.py` and `layers.py` share. |
| `funground/export/svg_text.py` | Live, editable `<text>` in SVG files (T19, D-059). |
| `funground/export/layers.py` | Named layers in PDF (optional content groups) and SVG (Inkscape layer groups) (F16, D-053). |
| `funground/export/motion.py` | GIF and MP4 files (M1, D-048): Pillow for a GIF when installed, else ffmpeg; MP4 always through ffmpeg (D-045). The only module that finds or runs ffmpeg. |
| `funground/marks.py` | `Mark`, a drawing kept as a value (S-132, K1-K3): the recorder behind `with f.mark()`, placement, the current-style rewrite and the guard that refuses layers, controls, saves and pixel calls inside a block. No backend; bounds come from the renderer's `ink_bounds`. |
| `funground/controls.py` | Sliders, checkboxes and buttons and their panel (U1, D-047). Plain Python; no pygame. |
| `funground/sound/_engine.py` | `Sound` objects: playback on a clock, level, spectrum, pitch, rhythm and harmony methods. The only user of `pygame.mixer`. |
| `funground/sound/_synth.py` | Sound from numbers (A3, A9): waves, envelopes, notes, plucks, melodies. Plain Python, no device. |
| `funground/analysis.py` | Onsets, tempo, beats, chroma, chords, key (A5, A6). Plain Python. |
| `funground/sangeet/_tables.py`, `funground/data/ragas.json` | Ragas and talas: drone, tala, tonic, swara histogram, raga matching (A8). The table names its sources. |
| `funground/frame_inputs.py` | The registry of inputs the sketch serves each frame (S-247): `register(take, stop)`, `take_all(sketch)`, `stop_all()`. The core never imports a library, so a library registers itself here. |
| `funground/camera/_device.py` | `Camera` and `Clip` (I4, I5): the device (pygame.camera, or the host's camera), the frame taken once before each `draw()`, recording and saving clips. The only user of `pygame.camera`. |
| `funground/sound/_microphone.py` | `Microphone` (A4, D-058). Uses pygame's experimental `pygame._sdl2.audio`, in three small functions. |
| `funground/sound/_views.py` | Ready-made drawings of a sound or microphone: wave, spectrum, spectrogram, pitch line (A7). |
| `funground/gallery.py` | The Examples Gallery browser, `python -m funground.gallery`. Holds `AREAS`, the locator and the explanation reader. |
| `funground/fonts/` | The bundled fonts: DejaVu Sans, and the Noto fallback fonts (emoji, symbols, Devanagari). |
| `funground/capabilities.py` | `Capability`, `FungroundError`, `FungroundWarning`, `missing_capability()`. |

The `Sketch` is big (over 2000 lines) on purpose: it is the one place that turns a learner's call
into ops. Helpers with no state live in their own modules (see section 4).

## The provider boundary

**The rule: a backend library is imported only by the module that provides that capability.**
The public facade and the core never import one. Learners never see a backend type.

[`tests/test_boundaries.py`](../../tests/test_boundaries.py) enforces it by reading the imports of
every file in `funground/`. Its `ALLOWED` table is the truth:

| Library | May be imported by | Why there |
|---|---|---|
| pygame-ce (`pygame`), window and images | `funground/platform/`, `funground/imaging.py` | pygame-ce is the window, input and timing layer, and it decodes image files. It draws nothing (D-008, a test checks for `pygame.draw` and `pygame.font`). `imaging.py` reads image files with it so that no second image library is needed (ADR-004, D-028). |
| pygame-ce audio (`pygame.mixer`, `pygame._sdl2.audio`) | `funground/sound/_engine.py`, `funground/sound/_microphone.py` | Sound playback and microphone input (D-046, D-058). One file for each. `microphone_input.py` uses pygame-ce's experimental module, kept in three small functions so a change is easy to follow. |
| pygame-ce camera (`pygame.camera`) | `funground/camera/_device.py` | Camera input (D-089). Imported only when a camera is asked for, never when funground is imported. |
| Cairo (`cairo`, pycairo) | `funground/renderers/`, `funground/export/` | Cairo is the renderer and the PDF and SVG writer. Keeping it in two folders means one place to change if the renderer changes (ADR-001, ADR-002, D-011). |
| pypdf | `funground/export/` | To rewrite Cairo's PDF so that text is real, searchable text and layers are real layers (D-043, D-053). It belongs with the other file-writing code. |
| imageio-ffmpeg (`imageio_ffmpeg`) | `funground/export/` | The optional `funground[video]` extra: an ffmpeg program for MP4 export, found by `find_ffmpeg()` in `export/motion.py` (D-045). |
| skia-pathops (`pathops`) | `funground/pathops.py` | Path booleans and stroke expansion. One module converts between funground's `Path` and Skia's, so the rest of the code never sees Skia (ADR-005, D-037). |
| svgelements | `funground/svg.py` | Reads SVG files and gives back funground geometry (D-041). |

`BACKENDS` in the test lists `pygame`, `cairo`, `skia`, `blend2d`, `moderngl`, `OpenGL`, `pathops`,
`svgelements`, `pypdf` and `imageio_ffmpeg`. The names nobody uses yet (`skia`, `blend2d`, `moderngl`,
`OpenGL`) are reserved, so that a future provider has to be added to `ALLOWED` on purpose. `renderers/` is already allowed `skia`,
`blend2d` and `pygame` for that reason.

A second test, `test_public_facade_imports_no_backend`, checks that `api.py`, `__init__.py`,
`sketch.py`, `state.py` and `color.py` import no backend at all.

Not every third-party library is a backend. `fontTools` and `uharfbuzz` (shaping and outlines in
`typography.py`) are not in the table, because they produce plain funground geometry, not drawing.
Pillow is optional. `imaging.py` reaches for it for rarer filters, and `export/motion.py` for GIFs;
each imports it inside one small function and falls back when it is missing. The plain-Python modules
(`sound/_synth.py`, `analysis.py`, `sangeet/_tables.py`, `controls.py`) import no backend at all.

**To add a provider**, add its directory or file to `ALLOWED` in the same change. A new runtime
dependency is a decision for the maintainer (D-034) and needs a decision-log row and, if it is
long-lived, an ADR.

The decisions behind it:

- ADR-001: the topology. funground owns the meaning and
  the IR. pygame-ce is the window. Renderers consume the IR.
- ADR-002: Cairo is the reference renderer;
  an engine is picked by measurement, not by reputation.
- ADR-003: what funground deliberately does not do.
- ADR-004: pygame-ce reads images; Pillow is optional.
- ADR-005: skia-pathops for path booleans.
- ADR-006: simple tones and notes, without a synthesis engine.
- and the decisions D-008, D-011, D-028, D-037, D-041, D-043, D-045,
  D-046, D-058.

## Key invariants

### Snapshots stay byte-identical: `OMIT_WHEN_DEFAULT`

IR snapshots in `tests/snapshots/` were frozen in Sprint 2. A field added later must not change
them. `ir.OMIT_WHEN_DEFAULT` is the set of field names that are written to JSON **only when they
differ from their default**. Reading JSON back leaves an omitted field at its default.

So when you add a field to an op or to `GraphicsState`:

1. Give it a default.
2. Add its name to `OMIT_WHEN_DEFAULT` in `ir.py`.
3. If its value is not plain JSON (a tuple of tuples, a `Color`), teach `_extra_from_jsonable` how
   to read it back.

Then every existing snapshot is unchanged. Never regenerate an old snapshot to make a change pass.

### HiDPI: logical pixels in, physical pixels drawn

Learners work in **logical** pixels. `f.width` is exactly the number passed to `f.size()`.
The platform reports `backing_scale`, the physical pixels per logical pixel. The renderer's surface
is physical, and a base scale matrix makes logical coordinates land in the right place, so shapes
are crisp on a scaled display. Input comes back in logical units. `FUNGROUND_BACKING_SCALE` forces a
value (the HiDPI tests use it). The dummy video driver always gives 1.0. Contract row C3.

Windows is verified on real hardware. macOS and Wayland paths are exercised only by simulated tests
(contract C3).

### One logical pixel is one PDF point

In a PDF or SVG, the document unit is the logical pixel, so one logical pixel is one point
(1/72 inch). A page of `f.page_size("A4")` is 595 by 842 units. This is why page sizes are in
points (`pages.py`) and why a saved PDF has no scale factor to explain.

### The frozen v0.5 API

The v0.5 public names and signatures are an executable contract in
[`tests/test_api_contract.py`](../../tests/test_api_contract.py) (`V05_FUNCTIONS`). Anything added
since is in `ADDED_FUNCTIONS`, and `test_public_all_is_exactly_the_contract` fails if `_PUBLIC_NAMES`
differs from the two lists plus the live values.

- **Adding** a name is allowed. It needs a contract row and an entry in `ADDED_FUNCTIONS`.
- **Changing or removing** a v0.5 name or signature is a decision for the maintainer.
  D-034 lets Claude take routine design decisions, but it still brings "changes to the frozen v0.5
  API" to the maintainer. Do not edit `V05_FUNCTIONS` without that approval, and write the
  decision in Decision_Log.md.

`src_v0.5/` is the pristine v0.5 baseline. Never edit it.

### The naming trap: a submodule must never share a public function's name

`funground/__init__.py` has `f.<name>` for every public function. Suppose a submodule has the same
name as a public function. When something imports the submodule lazily (`from . import ragas` inside a
function), Python sets `funground.ragas` to the **module**. That replaces the function `sangeet.ragas`, and
the learner's next `sangeet.ragas()` fails with "module is not callable". This happened twice in Sprint 14,
with `ragas` and `microphone`. The modules were renamed, and in 0.2 they became the underscore modules of the sound and sangeet libraries.

Before you add a module, check its name against `_PUBLIC_NAMES`. The `sound` and `sangeet` packages are safe because there is no
public function `f.sound` or `f.sangeet`, and their own modules start with an underscore. When in doubt, give the file a longer name.

### The layers rule: drawing uses `active_sketch()`, everything else `canvas_sketch()`

Inside `with f.layer(...)` the drawing must go to the layer, but `f.width`, `f.mouse_x`, `f.random()`,
`f.save()`, `f.size()`, loop control and time must keep their canvas meaning. So `api.py` has two
accessors:

- `active_sketch()`: the open layer's sketch inside a layer block, otherwise the canvas's. **Drawing
  functions use it** (shapes, colour and style, transforms, text, images, `push` and `pop`).
- `canvas_sketch()`: always the canvas's own sketch. **Every other function uses it.**

A new public function picks one on purpose. If it draws, use `active_sketch()`. If it reads or
changes the canvas, the loop, input, time, randomness or files, use `canvas_sketch()`. Mixing them up
is the usual layers bug: a drawing call that ignores the layer, or a `size()` that lands in it.

### Other rules that hold everywhere

- Two correct renderers may differ in pixels. They may not differ in ops.
- Ops are frozen dataclasses. `GraphicsState` is immutable and replaced on every style call.
- `draw()` never leaks state: `_end_draw()` pops open `push()` calls with a warning.
- A pinned row in the contract changes only by an ADR or contract row first, then code.
