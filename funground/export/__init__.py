"""Export: pictures and documents from a sketch (story S-034).

- **PNG** (`save_pixels`): exactly what is on screen - the rendered pixels, including
  everything earlier frames left on the canvas.
- **PDF / SVG** (`save_frame`): a *replay* of the frame's ops onto a document surface,
  so the output is true vector (text as glyph outlines until S-032 embeds fonts). A
  vector file therefore contains what *this* frame drew, not earlier frames.
"""
from __future__ import annotations

import os

import cairo

from ..ir import Frame
from ..platform.base import Pixels
from ..renderers.cairo2d import CairoRenderer

FORMATS = ("png", "pdf", "svg")


def format_of(path: str) -> str:
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext not in FORMATS:
        raise ValueError(f"cannot save {path!r}: use one of {', '.join('.' + f for f in FORMATS)}")
    return ext


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


def save_frame(frame: Frame, path: str, width: int, height: int, scale: float = 1.0) -> str:
    """Replay *frame* (logical width x height) to *path*; return the format used."""
    fmt = format_of(path)
    renderer = CairoRenderer()
    if fmt == "png":
        pw, ph = round(width * scale), round(height * scale)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, pw, ph)
        ctx = renderer.context_for(surface, scale)
        renderer.draw(ctx, frame)
        surface.flush()
        surface.write_to_png(path)
        surface.finish()
    else:
        cls = cairo.PDFSurface if fmt == "pdf" else cairo.SVGSurface
        surface = cls(path, width, height)          # document units == logical pixels (points)
        ctx = renderer.context_for(surface, 1.0)
        renderer.draw(ctx, frame)
        surface.finish()
    return fmt
