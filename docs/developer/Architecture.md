# Architecture

How funground is built, as the code stands through Sprint 10. This page is kept true to the code
in the same change as the code (see [PROCESS](../PROCESS.md), "Sprint lifecycle"). If this page and
the source disagree, the source and the tests win.

The older record, [Playground_Technology_Architecture_v2.md](../design/Playground_Technology_Architecture_v2.md),
describes Sprint 2. It is history. Read it for the reasons behind the first design, not for the
current code.

The one-sentence version: **funground owns the programming model and the drawing meaning. The
draw-op IR is the contract. Cairo draws. pygame-ce runs the window. Learners never see the seam.**

## 1. The layers

```text
 learner code           import funground as f ;  f.circle(100, 100, 50)
        |
        v
 +------------------+   funground/__init__.py   the public names, __all__, live values
 |  public facade   |   funground/api.py        one function per name; talks to the active Sketch
 +--------+---------+
          |
          v
 +------------------+   funground/sketch.py     lifecycle, live values, validation,
 |      Sketch      |                           the Frame of ops, saving
 |  + GraphicsState |   funground/state.py      immutable style + the push/pop stack
 +--------+---------+
          |  appends ops
          v
 +------------------+   funground/ir.py         Frame = ordered list of frozen op dataclasses
 |   draw-op IR     |                           (the contract; JSON-serialisable)
 +----+--------+----+
      |        |
      v        v
 +---------+  +-----------------+
 | Cairo   |  | export/         |   PNG / PDF / SVG, replaying the same ops
 | Renderer|  | (cairo, pypdf)  |
 +----+----+  +--------+--------+
      |                |
      v                v
  BGRA pixels       a file on disk
      |
      v
 +------------------+   funground/platform/     pygame-ce window, input, timing, present;
 |    platform      |                           or the headless platform (no window)
 +------------------+
      |
      v
   the window
```

Read it top to bottom for one drawing call:

1. The learner calls `f.circle(...)`. `__init__.py` re-exports the function from `api.py`.
2. `api.py` forwards it to the active `Sketch` (`active_sketch()`).
3. The `Sketch` checks the arguments, applies the drawing modes, takes the current
   `GraphicsState` and appends an `ir.Circle` op to `self.frame`. Nothing is drawn yet.
4. At the end of `draw()` the `Sketch` hands the whole `Frame` to its renderer
   (`Sketch._render()`).
5. `CairoRenderer.render()` replays the ops onto a Cairo image surface at physical resolution.
6. The `Sketch` asks the renderer for `pixels()` and gives them to the platform to `present()`.
7. `f.save("x.png")` writes those pixels. `f.save("x.pdf")` replays the ops onto a PDF surface.

### The modules

| Module | What it does |
|---|---|
| `funground/__init__.py` | The public names and `__all__`. A module `__getattr__` serves the live values (`f.width`, `f.mouse_x` and so on) so they are never stale copies. |
| `funground/api.py` | The facade. One thin function per public name, forwarding to the active `Sketch`. Holds `active_sketch()`, `use_sketch()` (for tests), the exit hint for a forgotten `f.run()`, and `LIVE_NAMES`. Imports no backend. |
| `funground/sketch.py` | The `Sketch` class. It owns the platform, the renderer, the `StateStack`, the `Frame`, the random generators, loop control, pages and saving. `run_namespace()` is the callback loop. Choosing the platform and renderer happens here (`default_platform()`, `default_renderer()`). |
| `funground/state.py` | `GraphicsState` (frozen: fill, stroke, widths, text settings, blend mode, modes and so on) and `StateStack` (`save`, `restore`, `unwind`). |
| `funground/ir.py` | The op dataclasses (`Circle`, `Rect`, `Text`, `FillPath`, `Image`, `Pixels` and the rest), `Frame`, and JSON conversion (`to_jsonable`, `from_jsonable`). |
| `funground/renderers/__init__.py` | The `Renderer` protocol: `attach`, `render`, `pixels`, plus a set of `Capability` values. |
| `funground/renderers/cairo2d.py` | `CairoRenderer`, the only renderer today. Replays ops with Cairo. Turns `Text` ops into glyph outlines through `typography.py`. |
| `funground/platform/base.py` | The `Platform` protocol and the small data types (`InputEvent`, `InputState`, `Pixels`). |
| `funground/platform/pygame_platform.py` | `PygamePlatform`: window, events, mouse and keys, frame pacing, HiDPI detection, cursors. |
| `funground/platform/headless.py` | `HeadlessPlatform`: no window, no waiting, input always idle. Chosen by `FUNGROUND_HEADLESS=1`. Used by the tests and by the gallery tools. |
| `funground/export/__init__.py` | `save_pixels`, `save_frame`, `save_document`, `save_picture`. Replays ops onto Cairo PDF and SVG surfaces. |
| `funground/capabilities.py` | `Capability`, `FungroundError`, `FungroundWarning`, `missing_capability()`. |

The `Sketch` is big (about 1800 lines) on purpose: it is the one place that turns a learner's call
into ops. Helpers with no state live in their own modules (see section 4).

### Choosing a renderer and platform

- `FUNGROUND_HEADLESS=1` (or `true`, `yes`) selects `HeadlessPlatform`. Anything else selects
  `PygamePlatform`.
- `FUNGROUND_RENDERER` selects a renderer by name from `RENDERERS` in `sketch.py`. Only `cairo`
  exists. The table is where an optional second renderer would register (see ADR-002 and D-011).
- `FUNGROUND_BACKING_SCALE` forces the HiDPI scale (see section 5).

## 2. The two run modes

A learner file is one of two kinds. The `Sketch` tells them apart.

### Callbacks: `setup()`, `draw()` and `f.run()`

```text
f.run()  ->  Sketch.run_namespace(globals)
              find setup() and draw() and the event callbacks by name
              platform.start()
              setup()                       (usually calls f.size(), which opens the window)
              loop:
                  platform.poll()           events, input state
                  dispatch callbacks        mouse_pressed(), key_pressed(), ...
                  draw()                    ops are appended to the Frame
                  _end_draw()               unwinds pushes left open, with a warning
                  _render()                 renderer draws, platform presents, saves happen
                  platform.tick(fps)
```

`f.run(max_frames=n)` stops after n loop iterations. The test suite uses it through
`tests/conftest.py::run_sketch`.

### Script mode: top-level drawing, `f.show()` and pages

A file with no `draw()` is a script. A top-level `f.size()` starts a canvas with **no window**
(`Sketch._begin_script()`). Each drawing call appends an op to `self.frame`, and the ops are
drawn onto a persistent surface when something needs pixels. The ops are never cleared, so a
PDF or SVG save can replay the whole drawing.

- `f.show()` opens a window on the finished drawing and waits until it is closed.
- `f.new_page()` ends the current page and starts a blank one. Each earlier page keeps its ops
  and its pixels in `Sketch._pages`. `f.save("x.pdf")` writes one multi-page PDF.
  `f.show()` lets the viewer turn pages with Left and Right.
- Mixing the two styles (drawing at the top level and also calling `f.run()`) raises a clear
  error. So does `f.new_page()` in a running sketch.

The contract rows are R13 to R17 in
[Semantic_Contract.md](../design/Semantic_Contract.md). A design note on scripts and pages is in
[Scripts_and_Pages_Note.md](../design/Scripts_and_Pages_Note.md).

## 3. The provider boundary

**The rule: a backend library is imported only by the module that provides that capability.**
The public facade and the core never import one. Learners never see a backend type.

[`tests/test_boundaries.py`](../../tests/test_boundaries.py) enforces it by reading the imports of
every file in `funground/`. Its `ALLOWED` table is the truth:

| Library | May be imported by | Why there |
|---|---|---|
| pygame-ce (`pygame`) | `funground/platform/`, `funground/imaging.py` | pygame-ce is the window, input and timing layer, and it decodes image files. It draws nothing (D-008, a test checks for `pygame.draw` and `pygame.font`). `imaging.py` reads image files with it so that no second image library is needed (ADR-004, D-028). |
| Cairo (`cairo`, pycairo) | `funground/renderers/`, `funground/export/` | Cairo is the renderer and the PDF and SVG writer. Keeping it in two folders means one place to change if the renderer changes (ADR-001, ADR-002, D-011). |
| pypdf | `funground/export/` | To rewrite Cairo's PDF so that text is real, searchable text (D-043; S-094). It belongs with the other file-writing code. |
| skia-pathops (`pathops`) | `funground/pathops.py` | Path booleans and stroke expansion. One module converts between funground's `Path` and Skia's, so the rest of the code never sees Skia (ADR-005, D-037). |
| svgelements | `funground/svg.py` | Reads SVG files and gives back funground geometry (D-041). |

Other backend names are reserved in the test (`skia`, `blend2d`, `moderngl`, `OpenGL`) so that a
future provider has to be added to `ALLOWED` on purpose. `renderers/` is already allowed `skia`,
`blend2d` and `pygame` for that reason.

A second test, `test_public_facade_imports_no_backend`, checks that `api.py`, `__init__.py`,
`sketch.py`, `state.py` and `color.py` import no backend at all.

Not every third-party library is a backend. `fontTools` and `uharfbuzz` (shaping and outlines in
`typography.py`) are not in the table, because they produce plain funground geometry, not drawing.
Pillow is optional and only `imaging.py` reaches for it.

**To add a provider**, add its directory or file to `ALLOWED` in the same change. A new runtime
dependency is a decision for the maintainer (D-034) and needs a decision-log row and, if it is
long-lived, an ADR.

Where to read the reasons:

- [ADR-001](../design/ADR-001-renderer-topology.md): the topology. funground owns the meaning and
  the IR. pygame-ce is the window. Renderers consume the IR.
- [ADR-002](../design/ADR-002-renderer-selection-reopened.md): Cairo is the reference renderer;
  an engine is picked by measurement, not by reputation.
- [ADR-003](../design/ADR-003-out-of-scope.md): what funground deliberately does not do.
- [ADR-004](../design/ADR-004-image-provider.md): pygame-ce reads images; Pillow is optional.
- [ADR-005](../design/ADR-005-path-operations.md): skia-pathops for path booleans.
- [Decision_Log.md](../design/Decision_Log.md): D-008, D-011, D-028, D-037, D-041, D-043.

## 4. Subsystems

Each subsystem is small. Some have a design note in `docs/design/`.

### Text: `typography.py` and `formatted.py`

Text is turned into glyph outlines. `uharfbuzz` shapes the text. `fontTools` reads the outlines.
Each glyph becomes a cached `Path`. `CairoRenderer` does this when it meets an `ir.Text` op
(`_text_ops`), so every platform draws the same letters. The bundled font is DejaVu Sans in
`funground/fonts/`. `typography.py` also holds `load_font`, font variations and OpenType features,
wrapping (`wrap_lines`) and measuring (`text_width`, `text_metrics`).

`formatted.py` holds `FormattedString`: a list of runs, each with its own settings. It holds the
data and the line breaking. The `Sketch` does the measuring and drawing (`_fs_*` methods).

Notes: [Text_Subsystem_Note.md](../design/Text_Subsystem_Note.md) and
[Typography_Note.md](../design/Typography_Note.md). Contract rows T1 to T15.

PDF text (T15, D-043, S-094): every PDF carries real text. The renderer draws each text run as a
marker group; `export/pdf_text.py` swaps the markers for text with an embedded font subset after
Cairo has written the file. See [PDF_Text_Note.md](../design/PDF_Text_Note.md). SVG keeps outlines.

### Colour and paint: `color.py` and `paint.py`

`color.py` holds `Color`, an immutable RGBA value. Learners pass names, tuples, hex strings or
objects. The parsing happens once, in the `Sketch` (`read_color`), so renderers only ever see
`Color`. `_colornames.py` is the bundled name table. `color_mode` (RGB, HSB, HSL and their ranges)
is part of `GraphicsState`, so `push` and `pop` save it.

`paint.py` holds `Gradient`, plain data for a linear or radial gradient. A fill, stroke or
background is a `Color` or a `Gradient`. The renderer turns a gradient into a Cairo pattern.
PDF and SVG keep it as a true vector gradient. Contract rows S1 to S16.

### Geometry and paths: `geometry.py`, `shapes.py`, `paths.py`, `pathops.py`

- `geometry.py`: `Transform` (affine) and `Path` (immutable segments). No backend.
- `shapes.py`: the shape being built between `begin_shape()` and `end_shape()`, including
  Catmull-Rom curves.
- `paths.py`: `PathBuilder`, what `f.path()` returns. It wraps an immutable `Path` and swaps in a
  new one on each call. Booleans, queries and transforms return new paths.
- `pathops.py`: the skia-pathops bridge. Booleans, `remove_overlap`, `expand_stroke` and the
  even-odd to non-zero conversion that SVG import needs.

Contract rows F1 to F14. Note: [Paths_Note.md](../design/Paths_Note.md).
Decision: [ADR-005](../design/ADR-005-path-operations.md).

### Pictures and images: `picture.py` and `imaging.py`

A `Picture` (from `f.create_graphics()`, `f.load_image()` or `f.load_svg()`) owns a **private
`Sketch`** with its own `CairoRenderer` and a persistent surface that starts transparent. Its drawing
calls are ops, just like the main sketch's. They are drawn when the picture is flushed: drawn with
`f.image()`, saved, or used as the source of another picture. A picture also keeps a bounded
**history** of its ops, so a PDF or SVG save can stay vector. Past 10 000 ops since the last opaque
background or clear, it embeds pixels instead.

An `ir.Image` op names its picture (`"graphics-1"`) and carries a snapshot so it can be drawn.
The snapshot is never written to JSON and never compared.

`imaging.py` decodes files with pygame-ce into premultiplied BGRA (Cairo's layout), fixes phone-photo
orientation itself, and holds the pixel helpers behind `tint`, `resize`, `mask` and `filter`.
Contract rows P1 to P11. Note: [Pictures_and_Images_Note.md](../design/Pictures_and_Images_Note.md).
Decision: [ADR-004](../design/ADR-004-image-provider.md).

Layers (F16, D-053, S-095 and S-096): `f.layer(name)` is a canvas-sized picture, put over the
canvas as an `ir.Image` tagged with its name, never stored in the frame. In a PDF or SVG the
renderer draws each layer as a marker group; `export/layers.py` turns it into an optional content
group (PDF) or an Inkscape layer group (SVG) after Cairo has written the file. Note:
[Layers_Note.md](../design/Layers_Note.md).

### Pages: `pages.py`

`pages.py` is only the table of named page sizes (`A4`, `Letter` and so on) in points, and
`page_size()`. The page logic itself (`new_page`, `page_count`, `_pages`, `show()` paging) is in
`sketch.py`; the multi-page PDF is `export.save_document()`.
Contract rows R16, R17, D1. Note: [Scripts_and_Pages_Note.md](../design/Scripts_and_Pages_Note.md).

### SVG import: `svg.py`

`svg.py` uses svgelements to read a file. It gives back funground paths plus the style each shape
has. `Sketch.load_svg()` draws them onto a picture through the normal drawing commands, so a loaded
SVG has a full history and stays vector in PDF and SVG. `f.svg_paths()` returns the paths alone.
Even-odd fills go through `pathops.even_odd_to_nonzero`, because funground fills with the non-zero
rule only. Contract row P11. Note: [SVG_Import_Note.md](../design/SVG_Import_Note.md).

### Compositing

Blend modes, opacity and shadows are part of `GraphicsState` and are carried on each op. The
renderer applies them with Cairo groups. Contract row S14.
Note: [Compositing_Note.md](../design/Compositing_Note.md).

### Noise: `noise.py`

A Python translation of p5.js's `noise()`, `noiseSeed()` and `noiseDetail()`, so a seeded sketch
gives the same numbers as p5. **Licence note:** it is a translation of p5.js code, so it is
LGPL-2.1 (the funground licence is the same family), credited in the file header and in
[THIRD_PARTY_LICENSES.md](../../THIRD_PARTY_LICENSES.md). It is the one place where code from
another project is in the package. Do not copy more. See the "Examples are original" rule in
[PROCESS](../PROCESS.md).

### Capabilities: `capabilities.py`

A renderer declares a `frozenset` of `Capability` values. `Sketch.size()` calls
`_check_capabilities()`, so a feature the renderer cannot do fails there, with a message that names
the feature, and not half way through a loop (contract R9). `EXTRA_FOR` maps a capability to the pip
extra that would provide it. It is empty today. `FungroundError` and `FungroundWarning` are the
learner-facing error and warning classes.

## 5. Key invariants

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
since is in `ADDED_FUNCTIONS`, and `test_public_all_is_exactly_the_contract` fails if `__all__`
differs from the two lists plus the live values.

- **Adding** a name is allowed. It needs a contract row and an entry in `ADDED_FUNCTIONS`.
- **Changing or removing** a v0.5 name or signature is a decision for the maintainer.
  D-034 lets Claude take routine design decisions, but it still brings "changes to the frozen v0.5
  API" to the maintainer. Do not edit `V05_FUNCTIONS` without that approval, and write the
  decision in [Decision_Log.md](../design/Decision_Log.md).

`src_v0.5/` is the pristine v0.5 baseline. Never edit it.

### Other rules that hold everywhere

- Two correct renderers may differ in pixels. They may not differ in ops
  ([PROCESS](../PROCESS.md), the test hierarchy).
- Ops are frozen dataclasses. `GraphicsState` is immutable and replaced on every style call.
- `draw()` never leaks state: `_end_draw()` pops open `push()` calls with a warning.
- A pinned row in the contract changes only by an ADR or contract row first, then code.

## 6. Dependencies and licences

Runtime dependencies are listed in `pyproject.toml` (`dependencies`). Full licence text and notes
are in [THIRD_PARTY_LICENSES.md](../../THIRD_PARTY_LICENSES.md); check it when you add one.

| Dependency | Why it is there | Licence | Imported by |
|---|---|---|---|
| pygame-ce (>= 2.5) | Window, input, timing, presenting a frame, decoding image files | LGPL-2.1 (SDL inside is zlib) | `platform/`, `imaging.py` |
| pycairo (>= 1.27) | The renderer and the PNG, PDF and SVG writers | LGPL-2.1-only or MPL-1.1 | `renderers/`, `export/` |
| fonttools (>= 4.55) | Reads glyph outlines and font tables | MIT | `typography.py` |
| uharfbuzz (>= 0.45) | Shapes text: glyph choice, kerning, ligatures, features | Apache-2.0 (HarfBuzz inside is Old MIT) | `typography.py` |
| skia-pathops (>= 0.9) | Path booleans, overlap removal, stroke expansion | BSD-3-Clause | `pathops.py` |
| svgelements (>= 1.9) | Reads SVG files | MIT | `svg.py` |
| pypdf (>= 5) | Rewrites Cairo's PDF so text is real text (D-043) | BSD-3-Clause | `export/` |

Optional or development only:

| Dependency | Why | Licence |
|---|---|---|
| pytest (>= 8) | The test runner (`dev` extra) | MIT |
| Pillow (>= 11) | The `dev` extra tests both filter paths, with and without it. The `extras` extra adds it for rarer filters at full speed | MIT-CMU (HPND) |
| pypdfium2 (>= 4) | Renders PDFs in tests (`dev` extra) | Apache-2.0 or BSD-3-Clause |

The licences for these three are from memory of the projects, and `THIRD_PARTY_LICENSES.md` does not
list them (funground does not ship them). Check the package you install.

Bundled in the package: DejaVu Sans (Bitstream Vera licence), the p5-derived noise function (LGPL-2.1)
and the colour-name table (from pygame-ce, LGPL-2.1). The library itself is `LGPL-2.1-or-later`.
Example code is CC0 (D-026).

pypdf is used only by `funground/export/pdf_text.py` (S-094), to put real text into Cairo's PDFs.
