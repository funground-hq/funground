"""Export: replay a Frame of IR ops to a file (story S-034).

PNG, PDF and SVG through Cairo surfaces. Export is a *replay*: the same ops
that drew the window are drawn again onto a document surface, so PDF/SVG
output is true vector (text is glyph outlines until S-032 embeds fonts).
"""
from __future__ import annotations

import os

import cairo

from ..ir import Frame
from ..renderers.cairo2d import CairoRenderer

FORMATS = ("png", "pdf", "svg")


def format_of(path: str) -> str:
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext not in FORMATS:
        raise ValueError(f"cannot save {path!r}: use one of {', '.join('.' + f for f in FORMATS)}")
    return ext


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
