# Design note: layers

**Status:** decided (D-053, "both in 0.1", by the maintainer, 3 Oct 2026). Built in Sprint 12:
S-095 (pictures) and S-096 (PDF and SVG files). Contract row F16 in
[Semantic_Contract.md](Semantic_Contract.md).
Code: `layer`, `_layer_ops`, `_with_layers` and `_view` in `funground/sketch.py`; `Picture.__enter__`
in `funground/picture.py`; `ir.Image.layer` and `ir.Image.layer_hidden`; `_draw_layer` in
`funground/renderers/cairo2d.py`; `funground/export/layers.py`; `_write_pdf` and `_write_svg` in
`funground/export/__init__.py`.

## The idea

One concept, `f.layer(name)`, with two faces:

- **On screen, in PNG and `get()`:** a layer is a canvas-sized **picture** (P1) that keeps its
  drawing (p5's off-screen graphics). `with f.layer("sky"):` sends the block's drawing to it. The
  visible layers are put over the canvas in the order they were first made.
- **In PDF and SVG:** each layer is a **real, named layer** that a drawing program can switch on
  and off: an optional content group (OCG) in a PDF, an Inkscape layer group in an SVG. A hidden
  layer is in the file, switched off.

## Pictures underneath (S-095)

- `Sketch._layers` maps names to pictures, in first-use order; `_layers_hidden` holds the hidden
  names. A new canvas (`size()`, `new_page()`, a new run) drops them.
- A `with` block is an implicit `push()` + `reset_matrix()` … `pop()` on the layer's picture, so
  settings and transforms never carry from one block to the next; the drawing stays.
- Drawing functions talk to `api.active_sketch()` (the open layer's sketch); everything else
  (`random`, `size`, `save`, queries) talks to `api.canvas_sketch()`.
- Layers are **never stored in the canvas frame**. `_layer_ops()` makes one `ir.Image` per layer,
  tagged `layer=name`, and `_with_layers(frame)` adds them on top of a copy of the frame whenever
  the canvas is drawn for the window, a PNG, a PDF or an SVG. IR snapshots stay exactly what the
  sketch drew.

## Real layers in files (S-096)

```text
 _with_layers(frame, files=True)  every layer, hidden ones tagged layer_hidden
        │
 CairoRenderer (file_layers set: PDF and SVG exporters only)
   ir.Image with a layer ──► push_group · clip(marker) · draw the layer as a picture · pop · paint
                              └─► LayerMarkers.add(name, hidden, box, matrix) → marker corners
 surface.finish()
        │
 PDF: text step (PdfTextCollector.finish), then layer step (LayerMarkers.finish_pdf), both pypdf
      find the marker in each Form XObject · the outermost one per layer gets /OC → its OCG
      remove the markers · /OCProperties: /OCGs, /D /Order (first use), /D /OFF (hidden)
 SVG: LayerMarkers.finish_svg (xml.etree)
      find the marker clip paths · follow <use> and url(#…) up to the body
      wrap the layer's drawing in <g id inkscape:groupmode="layer" inkscape:label>, moved out of <defs>
      remove the markers · display:none on hidden layers
```

1. **One group per layer.** Inside the group the layer is drawn exactly as a picture is drawn in a
   PDF or SVG (P3): its history replayed as vectors, or its pixels when the history passed P3's
   limit. Cairo writes the group as one Form XObject (`/xN Do`) in a PDF, and as one `<g>` in
   `<defs>` drawn by one `<use>` in an SVG. Groups Cairo draws inside the layer (pictures, text,
   shadows) are XObjects or `<g>`s nested inside that one.
2. **The marker.** The first thing in the group is a clip to the four-cornered shape P0, P1, Q, P2
   of [real PDF text](PDF_Text_Note.md), with Q = P0 + a (P1 − P0) + b (P2 − P0):
   - a and b lie in [1.1, 1.4) on a 0.001 grid, and give the layer's number (up to 90 000 per
     file). Text markers use [0.55, 0.95), so neither step ever reads the other's markers.
   - a + b > 1 keeps the shape convex, so it holds the square around the layer's whole box and the
     clip changes nothing. It is at least 2 000 device units across, for precision.
   - Affine maps keep a and b, so the number reads back under any transform Cairo applied. As a
     safety check, the axes read back must match the transform recorded at draw time.
   - It is never a rectangle: Cairo reduces an axis-aligned rectangle clip to a box.
3. **PDF.** The layer step walks every page's XObjects (and patterns and soft-mask groups). The
   outermost XObject holding a layer's marker gets `/OC`, which makes the whole XObject optional
   content; nested ones hold the same marker and are left alone. Every marker is removed. The
   catalogue gets `/OCProperties` with `/OCGs`, and a default configuration `/D` with `/Order` (first
   use in the document) and `/OFF` (hidden layers). The header is raised to PDF 1.5 when lower.
4. **SVG.** The layer step finds the marker `<clipPath>`s, spreads each layer number to every
   definition in `<defs>` that uses one (by `href` or `url(#…)`), and takes the outermost element
   of the body that uses it. That element is wrapped in the layer group, and each `<use>` inside it
   whose target nothing else uses is swapped for the target itself (with the use's transform), so
   the layer holds its own shapes, not links. Marker clips are removed, with the `<g>` that only
   carried them. A layer that drew nothing still gets an empty group in its place in the order.
5. **Ids.** The group's `id` is the name with anything but ASCII letters, digits, `_`, `-` and `.`
   turned into `_`, `layer-` in front when it does not start with a letter or `_`, and `-2`, `-3` …
   when the id is taken (by another layer or by Cairo's own `clip-0`, `source-12` …). The
   `inkscape:label` is the name exactly.

## How the two PDF steps compose

`_write_pdf` draws once with both collectors, then runs the text step and the layer step one after
the other on the file; each opens the file with pypdf and writes it back. The text step replaces
only its own markers and leaves the layer markers in place; the layer step then finds them. Text in
a layer is therefore real text inside the layer's OCG.

If a step fails, the document is drawn again without it, and the other step runs alone:

| Fails | Result |
|---|---|
| text step | text as glyph outlines (as before T15), layers still OCGs |
| layer step | real text, layers drawn plainly with hidden layers left out (as S-095 wrote them) |
| both | text as outlines, layers as S-095 wrote them |

SVG has only the layer step; if it fails the SVG is drawn again as S-095 wrote it.

## Choices

- **One OCG per name, per document.** A name used on several pages is one OCG, shared by every
  page's XObject. A name that is hidden on one page and shown on another cannot be one OCG (one
  OCG is either on or off), so it is two OCGs with the same name, the hidden one off: every page
  keeps the look it had on screen.
- **Hidden layers only in files.** `_layer_ops(files=True)` adds them, tagged `layer_hidden`; it is
  used for PDF and SVG saves and for the pages kept for them. Every renderer without the exporter's
  hook (the window, PNG, `get()`, pages shown in the window) leaves a `layer_hidden` op out.
- **`/OC` on the Form XObject**, not `/OC /ocN BDC … EMC` around its `Do`: Cairo already gives
  each layer one XObject, and the dictionary entry needs no edit of the page's content stream or
  its `/Properties`.

## Invariants

- Sketches without layers: the window, PNG, PDF, SVG and IR are byte for byte as before. No layer
  op is drawn, so no marker is made, and the layer step returns before opening the file.
- Window, PNG and `get()` never show a hidden layer.
- The renderer never imports pypdf; only `funground/export/` does (boundary test).

## Viewers

- **pdfium** (Chrome, Edge; pypdfium2 in the tests) honours `/OC` on a Form XObject and the
  default `/OFF` state: a hidden layer does not show. A PDF drawn by pdfium matches the PNG of the
  same frame (mean difference under 0.5 at 1×) and matches the PDF without OCGs (under 0.05 at 4×).
- **Not checked:** Acrobat, Illustrator, pdf.js (Firefox) and Inkscape could not be run here. The
  files follow the PDF 1.5 optional content and Inkscape layer conventions they use; a manual check
  in each is the next step.

## Limits and follow-ups

- **SVG markup is equivalent, not identical.** Because the layer's drawing sits in one more group
  under one more clip, Cairo sometimes writes it differently: a filled and stroked shape as two
  elements instead of one, a shadow's offset in the path rather than in a `transform`, larger filter
  regions for blend modes. It looks the same. With no SVG renderer in the project, the tests compare
  the shapes drawn (simple shapes and text give the very same list) rather than pixels.
- **A transform or clip left open on the canvas** (a `push()` with no `pop()` at the end of a
  script) applies to the layers in a PDF or SVG but not on screen. That is S-095 behaviour, not
  changed here.
- **An SVG layer under such a clip** sits inside the canvas's clip group, not at the top level,
  and drawing programs may then show it as a group rather than a layer.
- **pypdf rewrites the whole file once per step;** both steps use `PdfWriter._add_object`.
- **ElementTree's prefix table is global;** the SVG step sets the SVG, xlink and inkscape prefixes
  while it writes and puts the table back afterwards.

- **A wipe inside a layer block keeps the layer vector.** The block's own `push()` is an `ir.Save` marked `layer_block` (omitted from snapshots when false); a picture's history restarts at a `background` or `clear` inside only that Save as `[Save, ResetMatrix, wipe]`, but still stops if a learner's own `push()` is open.

## What an idle layer costs (S-258)

Spike 22 found that a new layer name each frame grows about 1 GB per 1,000 frames at 400 x 300. Each layer
held its pixels twice, on its surface and in a cached `Snapshot`, and each frame copied every layer again
to paint it. Layers are kept by design (F16), so the fix makes a kept layer cheap, not rarer.

**Showing makes no copy.** `Picture._for_showing()` gives the renderer the live surface. That is safe
because ops for the screen are drawn at once and never kept (`_layer_ops` without `files`). Files still
use `_snapshot()`, which is a frozen copy with its history.

**An idle layer rests.** After `LAYER_REST_SHOWS` (10) shows with no change, `rest_idle_layers()` calls `_rest()`
before the next show. It copies the box that holds pixels and gives up the surface and its context. The layer then
paints only that box. Resting comes before a show, never during one, because a show's ops hold live surfaces. Anything else that
needs the picture goes through `_flush_ops()`, and `_wake()` there rebuilds the surface. Rest and wake leave
`_version` and the history alone, so a resting layer still goes into a PDF or SVG as vectors.

**Who may rest.** A Cairo context holds state, and a new one starts plain. A layer rests only with no
`push()` open and with no transform, clip or `no_smooth()` made outside a push (`_KEEPS_CONTEXT_STATE`).
Inside a `with` block all of these end with the block, so ordinary layers rest. The others stay awake.

**A few at a time (S-267).** At most `LAYER_REST_PIXELS` (2,000,000) of layer pixels rest in one show: one 1080p
layer, or 16 at 400 x 300. Layers usually fall idle together, and S-258 rested them all in one frame: 20 layers at
1080p froze that frame for 0.6 s. The median frame times below could not show that. A budget in pixels and not in
layers keeps the frame short at any size, and small layers still rest as fast as a sketch makes them. Finding the box
also got faster, from 26 ms to about 4.4 ms at 1080p: a blank row is compared whole, and other rows are searched only
outside the box so far.

**Why a box is exact.** A see-through pixel over anything leaves that thing as it was, so leaving those
pixels out cannot change the result. `tests/test_layer_rest.py` compares the bytes at scales 1, 1.5 and 2.

**Measured** (private memory and the median of the last 30 frames, on an i5-1135G7, headless, with
`spikes/22_memory_soak/bench_layers.py`):

| Sketch | Before | After |
|---|---|---|
| A new layer each frame, 300 frames, 400 x 300 | +293 MB, 22.5 ms | +8.2 MB, 3.8 ms |
| The same, 1,000 frames | not run (about +980 MB at that rate) | +15.5 MB, 15.8 ms |
| 5 layers redrawn every frame, 400 x 300 | 2.35 ms | 1.24 ms |
| 20 layers, each redrawn once in 20 frames, 1920 x 1080 | +333 MB, 92 ms | +83 MB, 39 ms |
| The same at 400 x 300 | +20 MB, 1.38 ms | +5.6 MB, 2.41 ms |

The last row was the one that got slower: each frame there has one rest and one wake.

After S-267, the same five rows in the same order: +8.4 MB, 3.48 ms · +16.5 MB, 7.15 ms · +3.4 MB, 0.96 ms ·
+91.5 MB, 19.5 ms · +6.0 MB, 1.30 ms. The worst single frame when 20 layers fall idle: 615 ms to 7 ms at 1920 x 1080,
31 ms to 6.3 ms at 400 x 300.

**In Play** (7 November, headless Chrome, `tools/test_runner.py` on funground-web `main`): a sketch whose layers rest, wake,
are hidden, shown and read came out byte-identical to its desktop picture, with the layers shown resting at frame 20.
The gallery's four layer sketches were byte-identical to their goldens too. Memory and speed were not measured in a browser.

**Tried and rejected** (a prototype, 7 November; D-134 records the choice).

- *Compressing idle layers.* A sparse 400 x 300 layer takes 0.40 ms to expand and about 0.15 ms to paint.
  A shown layer is painted every frame, so it would have to stay expanded, or cost more each frame than
  it does now. A box saves the memory and also the paint.
- *Merging unchanged layers into one picture.* Putting 12 see-through layers together and then over the
  canvas, against one at a time: 16,944 of 480,000 bytes differ, by up to 2 levels. Rounding happens in a
  different order. The picture would then depend on when the merge happened, so it is out.

**Limits** (checked 7 November with small sketches). A busy layer that fills the canvas still holds one full canvas,
not two. The box is one rectangle: two dots in opposite corners of a 1080p layer keep 98.6% of it, and a faint wash over
the whole canvas keeps all of it. Opening a `with` block counts as a change even if it draws nothing, so a layer opened
every frame never rests. Touching every layer at once wakes them all, so the peak is what it was before S-258, not
what the idle sketch shows. A PDF or SVG save does this: 300 resting layers were all awake after it, and rested again 10
shows later, so a sketch that saves a PDF every few frames gets little from resting. A PNG does not wake them. A layer
that is saved keeps its cached snapshot until it next rests. A layer with state outside a block never rests, and that
stays true for the rest of its life. `_KEEPS_CONTEXT_STATE` is a list kept by hand: a new op that leaves state in
the context must be added to it, or a layer loses that state when it wakes. Layers rest in the order they were made. Each layer also holds about 15 KB of Python objects. A resting layer still costs time: `_layer_ops` takes about 2.6 microseconds for each,
and painting comes on top, so a frame with 1,000 layers takes 7 ms. None of this is a cap: 100,000
layer names still reach a limit, and a warning for that is a question for the maintainer (spike 22).

## Tests

`tests/test_layer_rest.py` covers S-258. `tests/test_layer_files.py`: OCG names, order and `/OFF`; one Form XObject per layer carrying its
OCG; real text inside a layer; pdfium render against the PNG and against the PDF without OCGs;
one OCG per name across pages, and two for a name hidden on one page only; the P3-limit fallback
(pixels inside the OCG and the `<g>`); animated saves; the fallback when the layer step fails; SVG
groups, labels, `groupmode`, unique valid ids, `display:none`, order and content inside its group;
the shapes drawn compared with an SVG written without the layer step; empty layers; SVG pages;
byte-identical PDF and SVG without layers; hidden layers kept out of the window, PNG and `get()`;
the marker grids. `tests/test_layers.py` covers the picture side.
