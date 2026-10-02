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

## Tests

`tests/test_layer_files.py`: OCG names, order and `/OFF`; one Form XObject per layer carrying its
OCG; real text inside a layer; pdfium render against the PNG and against the PDF without OCGs;
one OCG per name across pages, and two for a name hidden on one page only; the P3-limit fallback
(pixels inside the OCG and the `<g>`); animated saves; the fallback when the layer step fails; SVG
groups, labels, `groupmode`, unique valid ids, `display:none`, order and content inside its group;
the shapes drawn compared with an SVG written without the layer step; empty layers; SVG pages;
byte-identical PDF and SVG without layers; hidden layers kept out of the window, PNG and `get()`;
the marker grids. `tests/test_layers.py` covers the picture side.
