"""Export: pictures and documents from a sketch (story S-034).

- **PNG** (`save_pixels`): exactly what is on screen - the rendered pixels, including
  everything earlier frames left on the canvas.
- **PDF / SVG** (`save_frame`): a *replay* of the frame's ops onto a document surface,
  so the output is true vector. A vector file therefore contains what *this* frame drew,
  not earlier frames. Every PDF carries real text with an embedded font subset (S-094, contract
  T15: see `pdf_text`). Every SVG holds its text as live, editable `<text>` naming the font by
  family, with a subset of each font embedded for browsers (S-097, contract T19: see `svg_text`).
  Layers (S-095) become real file layers: optional content groups in PDF, Inkscape layer groups in SVG (S-096, contract F16: see
  `layers`).
  Colours (S-170, contract D4): a colour made by `f.cmyk()` is exact DeviceCMYK in a PDF, and every other RGB colour is tagged as
  sRGB (see `cmyk` and `pdf_colour`).
- **`save_picture`** (S-052): the same idea for a Picture's own `g.save(path)` - PNG is its
  pixels, PDF/SVG replay its history when one is available, or embed its pixels when it is
  not (contract P2/P3). Cairo stays behind this provider, per funground's boundary rule: a
  Picture (funground/picture.py) never imports it directly.
"""
from __future__ import annotations

import io
import math
import os
import struct
import zlib

import cairo

from ..ir import Frame
from ..platform.base import Pixels
from ..renderers.cairo2d import CairoRenderer, paint_picture_pixels
from ..surface import POINTS_PER_INCH
from .cmyk import CmykStandins
from .layers import LayerMarkers
from .pdf_colour import finish_colour
from .pdf_text import PdfTextCollector
from .printing import PrintSetup, write_print_boxes
from .svg_text import SvgTextCollector

FORMATS = ("png", "pdf", "svg")
TEXT_MODES = ("live", "shapes")


def check_text_mode(text) -> str:
    """Validate a ``text=`` choice for saving (contract T20): "live" or "shapes"."""
    if not isinstance(text, str) or text not in TEXT_MODES:
        raise ValueError(f'save(text=...) must be "live" or "shapes", not {text!r}')
    return text


# S-163 (D3): a PNG at a stated resolution is drawn afresh, and Cairo needs 4 bytes for each pixel. 120 million
# pixels is 480 MB: A1 at 300 dpi (70 million) fits; A0 (139 million) does not, and a PDF suits it better.
MAX_PNG_PIXELS = 120_000_000


def check_dpi(dpi: object, name: str = "f.save()") -> float | None:
    """Validate a ``dpi=`` choice (contract D3): None, or a number of dots per inch above 0."""
    if dpi is None:
        return None
    if isinstance(dpi, bool) or not isinstance(dpi, (int, float)):
        raise TypeError(f"{name}: dpi must be a number of dots per inch, such as 300, not {dpi!r}")
    if not (math.isfinite(dpi) and dpi > 0):
        raise ValueError(f"{name}: dpi must be above 0, such as 300, not {dpi!r}")
    return float(dpi)


def pixel_size(width: float, height: float, dpi: float) -> tuple[int, int]:
    """The pixels of a *width* x *height* page (points) at *dpi*: each side is points x dpi / 72, rounded
    to the nearest whole pixel, a half going up (contract D3)."""
    return (math.floor(width * dpi / POINTS_PER_INCH + 0.5), math.floor(height * dpi / POINTS_PER_INCH + 0.5))


def check_png_size(width: float, height: float, dpi: float, path: str) -> tuple[int, int]:
    """The pixel size of the page at *dpi*, or a ValueError when it is over MAX_PNG_PIXELS. Nothing is allocated."""
    pw, ph = pixel_size(width, height, dpi)
    if pw * ph > MAX_PNG_PIXELS:
        raise ValueError(
            f"f.save({path!r}): at {dpi:g} dpi a {width:g} x {height:g} page is {pw} x {ph} pixels, "
            f"{pw * ph / 1e6:.0f} million. The limit is {MAX_PNG_PIXELS // 1_000_000} million. "
            "Use a lower dpi, or save a PDF, which has no resolution and prints sharp at any size.")
    return pw, ph


def _png_with_resolution(png: bytes, dpi: float) -> bytes:
    """*png* with a pHYs chunk stating *dpi* (pixels per metre), placed straight after the header chunk."""
    per_metre = round(dpi / 0.0254)
    body = b"pHYs" + struct.pack(">IIB", per_metre, per_metre, 1)
    chunk = struct.pack(">I", len(body) - 4) + body + struct.pack(">I", zlib.crc32(body))
    header_end = 8 + 12 + 13                       # the signature, then IHDR: length, type, 13 bytes, crc
    return png[:header_end] + chunk + png[header_end:]


def format_of(path: str) -> str:
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext not in FORMATS:
        raise ValueError(f"cannot save {path!r}: use one of {', '.join('.' + f for f in FORMATS)}")
    return ext


NO_PRINT_SETUP = PrintSetup()           # no bleed and no marks: the page is the canvas (contract D2)


def _write_pdf(path: str, draw, text_mode: str = "live", setup: PrintSetup = NO_PRINT_SETUP) -> None:
    """Write a PDF with real text (S-094, contract T15) and real layers (S-096, contract F16).

    ``draw(renderer)`` writes the whole document to *path* with *renderer* and finishes the
    surface. It is called once with a renderer that collects text runs and layers as markers. Then
    two steps rewrite the file, one after the other: the text step swaps text markers for real text,
    and the layer step makes each layer an optional content group. Each step leaves the other's
    markers alone (they use different marker grids). Should a step fail, the document is drawn again
    without it: text as glyph outlines (exactly what funground wrote before T15), layers as plain
    drawing with hidden layers left out (exactly what S-095 wrote). A save never fails because of them.

    Then the colour step (S-170, contract D4) swaps each cmyk() stand-in for its exact inks and tags every other
    RGB colour as sRGB. For a file with cmyk() colours it is not optional: should it fail, there is no file
    (`ColourError`), never a wrong one. For a file without, a failure leaves the file as drawn.

    With a print *setup* (S-164, contract D2) a last step sets each page's TrimBox and BleedBox. It is
    not optional: a file asked to be print-ready that is not would be worse than an error.
    """
    text, layers = text_mode == "live", True        # T20: "shapes" = never set up the text collector
    while True:
        renderer = CairoRenderer()
        renderer.cmyk_standins = CmykStandins()
        if text:
            renderer.pdf_text = PdfTextCollector()
        if layers:
            renderer.file_layers = LayerMarkers()
        draw(renderer)
        if not (text or layers):
            break
        try:
            if text:
                renderer.pdf_text.finish(path)
        except Exception:
            text = False
            continue
        try:
            if layers:
                renderer.file_layers.finish_pdf(path)
        except Exception:
            layers = False
            continue
        break
    finish_colour(path, renderer.cmyk_standins)
    write_print_boxes(path, setup)


def _write_svg(path: str, draw, text_mode: str = "live") -> None:
    """Write an SVG with real layers (S-096, contract F16): Inkscape layer groups, and with each
    line of text as live, editable `<text>` (S-097, contract T19).

    As `_write_pdf`: the layer step runs first, then the text step, and should a step fail, the
    file is drawn again without it (text as outlines, exactly what funground wrote before S-097;
    layers as S-095 wrote them)."""
    text, layers = text_mode == "live", True        # T20: "shapes" = never set up the text collector
    while True:
        renderer = CairoRenderer()
        if text:
            renderer.svg_text = SvgTextCollector()
        if layers:
            renderer.file_layers = LayerMarkers()
        draw(renderer)
        if not (text or layers):
            return
        try:
            if layers:
                renderer.file_layers.finish_svg(path)
        except Exception:
            layers = False
            continue
        try:
            if text:
                renderer.svg_text.finish(path)
        except Exception:
            text = False
            continue
        return


def save_pixels(pixels: Pixels, path: str) -> None:
    """Write rendered BGRA (premultiplied, Cairo layout) pixels to a PNG file."""
    if pixels.format != "BGRA":
        raise ValueError(f"cannot save {pixels.format} pixels as PNG")
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, pixels.width)
    data = bytearray(bytes(pixels.data))
    if len(data) != stride * pixels.height:
        raise ValueError("pixel buffer size does not match its width and height")
    surface = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, pixels.width, pixels.height, stride)
    surface.write_to_png(path)
    surface.finish()


def save_frame(frame: Frame, path: str, width: int, height: int, scale: float = 1.0, text: str = "live",
               setup: PrintSetup = NO_PRINT_SETUP, dpi: float | None = None) -> str:
    """Replay *frame* (logical width x height) to *path*; return the format used.

    *text* is "live" or "shapes" (contract T20); it only matters for PDF and SVG. *setup* is the bleed
    and crop marks of a PDF (contract D2). *dpi* is for a PNG: the frame is drawn at dpi / 72 pixels to
    the logical pixel (*scale* is then not used) and the file states that resolution (contract D3)."""
    fmt = format_of(path)
    check_text_mode(text)
    renderer = CairoRenderer()
    if fmt == "png":
        if dpi is None:
            pw, ph = round(width * scale), round(height * scale)
        else:
            pw, ph = check_png_size(width, height, dpi, path)
            scale = dpi / POINTS_PER_INCH
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, pw, ph)
        ctx = renderer.context_for(surface, scale)
        renderer.draw(ctx, frame)
        surface.flush()
        if dpi is None:
            surface.write_to_png(path)
        else:
            png = io.BytesIO()
            surface.write_to_png(png)
            with open(path, "wb") as file:
                file.write(_png_with_resolution(png.getvalue(), dpi))
        surface.finish()
    else:
        cls = cairo.PDFSurface if fmt == "pdf" else cairo.SVGSurface

        def draw(renderer: CairoRenderer) -> None:
            surface = cls(path, *setup.page_size(width, height))     # document units == logical pixels (points)
            ctx = renderer.context_for(surface, 1.0)
            setup.begin_page(renderer, ctx, width, height)
            renderer.draw(ctx, frame)
            setup.draw_marks(renderer, ctx, width, height)
            surface.finish()

        if fmt == "pdf":
            _write_pdf(path, draw, text, setup)
        else:
            _write_svg(path, draw, text)
    return fmt


def save_document(pages: list, path: str, text: str = "live", setup: PrintSetup = NO_PRINT_SETUP) -> None:
    """Write several pages, each ``(width, height, Frame)``, into one multi-page PDF (contract R17).

    Each page is replayed as vectors at its own size (points = logical pixels); rasters embed as
    they do on any PDF surface (contract P3, P7). Every page gets the same bleed and marks (*setup*, D2).
    """
    check_text_mode(text)
    if format_of(path) != "pdf":
        raise ValueError(f"a multi-page document is a .pdf, not {path!r}")
    first_width, first_height, _ = pages[0]

    def draw(renderer: CairoRenderer) -> None:
        surface = cairo.PDFSurface(path, *setup.page_size(first_width, first_height))
        for width, height, frame in pages:
            surface.set_size(*setup.page_size(width, height))   # takes effect for the page about to be drawn
            ctx = renderer.context_for(surface, 1.0)
            setup.begin_page(renderer, ctx, width, height)
            renderer.draw(ctx, frame)
            setup.draw_marks(renderer, ctx, width, height)
            surface.show_page()
        surface.finish()

    _write_pdf(path, draw, text, setup)                      # one font subset per document, shared by pages


def save_picture(pixels: Pixels, history: tuple | None, logical_width: int, logical_height: int, path: str,
                 text: str = "live") -> str:
    """Write a Picture to *path* immediately (contract P2): PNG = its pixels; PDF/SVG replay

    its drawing history as vectors when one is available, or embed its pixels when it is not
    (past 10 000 ops since the last opaque background/clear, or none collected yet) - the same
    fallback ``Image`` uses on a PDF/SVG target for a historyless picture (contract P3), so a
    save never fails just because a picture drew a lot; it only stops staying vector.
    """
    fmt = format_of(path)
    check_text_mode(text)
    if fmt == "png":
        save_pixels(pixels, path)
        return fmt
    cls = cairo.PDFSurface if fmt == "pdf" else cairo.SVGSurface

    def draw(renderer: CairoRenderer) -> None:
        surface = cls(path, logical_width, logical_height)     # document units == the picture's logical pixels
        ctx = renderer.context_for(surface, 1.0)
        if history is not None:
            renderer._base_matrix = ctx.get_matrix()
            depth = renderer._draw_ops(ctx, Frame(list(history)), 0)
            while depth:
                ctx.restore(); depth -= 1
        else:
            paint_picture_pixels(ctx, pixels.data, pixels.width, pixels.height, 0, 0, logical_width, logical_height)
        surface.finish()

    if fmt == "pdf" and history is not None:
        _write_pdf(path, draw, text)
    elif history is not None:
        _write_svg(path, draw, text)                        # S-097: its text, live
    else:
        draw(CairoRenderer())
    return fmt
