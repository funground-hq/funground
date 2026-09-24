"""Cairo consumer of the Playground IR with the v0.6 vector semantics
(D-003 alpha, D-004 centred strokes, D-005 sub-pixel + AA)."""
from __future__ import annotations

import math

import cairo

from playground import ir
from playground.geometry import Path

NAME = "cairo"
FEATURES = {"clip_path": True, "scale": True, "fill_rule": True, "stroke_join_cap": True,
            "gradients": "linear, radial, mesh (no conic)", "native_font_file": False,
            "pdf": True, "svg": True, "comp_ops": "cairo operators (multiply, add, screen ...)"}


class CairoRenderer:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        self.ctx = cairo.Context(self.surface)
        self.ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)

    def buffer(self):
        self.surface.flush()
        return self.surface.get_data(), "BGRA"

    # ---- helpers
    def _path(self, p: Path):
        c = self.ctx
        c.new_path()
        for seg in p:
            k = seg[0]
            if k == "move": c.move_to(*seg[1])
            elif k == "line": c.line_to(*seg[1])
            elif k == "cubic": c.curve_to(*seg[1], *seg[2], *seg[3])
            elif k == "close": c.close_path()

    def _rgba(self, col):
        return (col.r / 255, col.g / 255, col.b / 255, col.a / 255)

    def _paint(self, st):
        c = self.ctx
        if st.fill is not None:
            c.set_source_rgba(*self._rgba(st.fill)); c.fill_preserve()
        if st.stroke is not None:
            c.set_source_rgba(*self._rgba(st.stroke)); c.set_line_width(st.stroke_width); c.stroke_preserve()
        c.new_path()

    # ---- entry
    def render(self, frame: ir.Frame):
        c = self.ctx
        for op in frame:
            t = type(op)
            if t is ir.Clear:
                c.save(); c.identity_matrix(); c.reset_clip(); c.set_source_rgba(*self._rgba(op.color)); c.paint(); c.restore()
            elif t is ir.Save: c.save()
            elif t is ir.Restore: c.restore()
            elif t is ir.Concat:
                m = op.transform; c.transform(cairo.Matrix(m.a, m.b, m.c, m.d, m.e, m.f))
            elif t is ir.ClipPath:
                self._path(op.path); c.clip()
            elif t is ir.FillPath:
                self._path(op.path); c.set_source_rgba(*self._rgba(op.color)); c.fill()
            elif t is ir.StrokePath:
                self._path(op.path); c.set_source_rgba(*self._rgba(op.color)); c.set_line_width(op.width); c.stroke()
            elif t is ir.Circle:
                c.new_path(); c.arc(op.x, op.y, op.diameter / 2, 0, 2 * math.pi); self._paint(op.style)
            elif t is ir.Ellipse:
                c.save(); c.translate(op.x, op.y); c.scale(max(op.width / 2, 1e-6), max(op.height / 2, 1e-6))
                c.new_path(); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore(); self._paint(op.style)
            elif t is ir.Rect:
                c.rectangle(op.x, op.y, op.width, op.height); self._paint(op.style)
            elif t is ir.Line:
                if op.style.stroke is not None:
                    c.move_to(op.x1, op.y1); c.line_to(op.x2, op.y2)
                    c.set_source_rgba(*self._rgba(op.style.stroke)); c.set_line_width(op.style.stroke_width); c.stroke()
            elif t is ir.Point:
                if op.style.stroke is not None:
                    c.new_path(); c.arc(op.x, op.y, max(0.5, op.style.stroke_width / 2), 0, 2 * math.pi)
                    c.set_source_rgba(*self._rgba(op.style.stroke)); c.fill()
            elif t is ir.Text:
                raise NotImplementedError("Text ops are materialised to FillPath by the text subsystem")
            else:
                raise NotImplementedError(t.__name__)


def export(frame: ir.Frame, w, h, path):
    kind = path.rsplit(".", 1)[1]
    surf = cairo.PDFSurface(path, w, h) if kind == "pdf" else cairo.SVGSurface(path, w, h)
    r = CairoRenderer.__new__(CairoRenderer)
    r.w, r.h, r.surface, r.ctx = w, h, surf, cairo.Context(surf)
    r.ctx.set_line_join(cairo.LINE_JOIN_ROUND); r.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    r.render(frame); surf.finish()


def gradient_demo(w, h, n=50):
    """Native-API check for D: linear + radial gradient fills."""
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h); c = cairo.Context(s)
    for i in range(n):
        g = cairo.LinearGradient(0, 0, w, 0) if i % 2 else cairo.RadialGradient(w / 2, h / 2, 10, w / 2, h / 2, w / 2)
        g.add_color_stop_rgba(0, 1, 0, 0, 0.5); g.add_color_stop_rgba(1, 0, 0, 1, 0.5)
        c.set_source(g); c.rectangle(i * 5, i * 3, w * 0.5, h * 0.5); c.fill()
    return True
