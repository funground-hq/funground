"""Blend2D consumer of the Playground IR, through blend2d-py 2025.5.0.

Binding-coverage gate (S-035.2): the binding has translate/rotate but no
scale, no general matrix and no clipping. This adapter therefore keeps the
CTM in Python and bakes it into every path before handing it to Blend2D
(possible only because the IR owns the geometry). ClipPath is *ignored* and
recorded as unsupported - scene B results are therefore not comparable.
"""
from __future__ import annotations

import blend2d as b

from playground import ir
from playground.geometry import Path, Transform

NAME = "blend2d"
FEATURES = {"clip_path": False, "scale": "emulated in Python (binding lacks it)", "fill_rule": "not exposed",
            "stroke_join_cap": True, "gradients": "linear, radial, conic", "native_font_file": True,
            "pdf": False, "svg": False, "comp_ops": "CompOp enum (multiply, screen, plus ...)"}


class Blend2DRenderer:
    unsupported_ops = 0

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.image = b.Image(w, h)
        self.ctx = b.Context(self.image)
        self.ctx.set_stroke_join(b.StrokeJoin.ROUND)
        self._ctm = [Transform()]
        self.unsupported_ops = 0

    def buffer(self):
        # Blend2D images are premultiplied BGRA (PRGB32) on little-endian.
        return self.image.memoryview(), "BGRA"

    def end(self):
        self.ctx.end()

    # ---- helpers
    def _bl_path(self, p: Path):
        t = self._ctm[-1]
        if not t.is_identity:
            p = p.transformed(t)
        bp = b.Path()
        for seg in p:
            k = seg[0]
            if k == "move": bp.move_to(*seg[1])
            elif k == "line": bp.line_to(*seg[1])
            elif k == "cubic": bp.cubic_to(*seg[1], *seg[2], *seg[3])
            elif k == "close": bp.close()
        return bp

    def _fill(self, path: Path, col):
        self.ctx.set_fill_style_rgba(col.r, col.g, col.b, col.a)
        self.ctx.fill_path(self._bl_path(path))

    def _stroke(self, path: Path, col, width):
        # stroke width must be scaled by the CTM's uniform scale since geometry is pre-transformed
        t = self._ctm[-1]
        s = (abs(t.determinant())) ** 0.5
        self.ctx.set_stroke_style_rgba(col.r, col.g, col.b, col.a)
        self.ctx.set_stroke_width(width * s)
        self.ctx.stroke_path(self._bl_path(path))

    def _paint(self, path: Path, st):
        if st.fill is not None: self._fill(path, st.fill)
        if st.stroke is not None: self._stroke(path, st.stroke, st.stroke_width)

    def render(self, frame: ir.Frame):
        for op in frame:
            t = type(op)
            if t is ir.Clear:
                self.ctx.set_fill_style_rgba(op.color.r, op.color.g, op.color.b, op.color.a)
                self.ctx.fill_all()
            elif t is ir.Save: self._ctm.append(self._ctm[-1])
            elif t is ir.Restore: self._ctm.pop()
            elif t is ir.Concat: self._ctm[-1] = self._ctm[-1].concat(op.transform)
            elif t is ir.ClipPath: self.unsupported_ops += 1        # cannot clip: recorded, not emulated
            elif t is ir.FillPath: self._fill(op.path, op.color)
            elif t is ir.StrokePath: self._stroke(op.path, op.color, op.width)
            elif t is ir.Circle: self._paint(Path.ellipse(op.x, op.y, op.diameter / 2, op.diameter / 2), op.style)
            elif t is ir.Ellipse: self._paint(Path.ellipse(op.x, op.y, op.width / 2, op.height / 2), op.style)
            elif t is ir.Rect: self._paint(Path.rect(op.x, op.y, op.width, op.height), op.style)
            elif t is ir.Line:
                if op.style.stroke is not None:
                    self._stroke(Path().move_to(op.x1, op.y1).line_to(op.x2, op.y2), op.style.stroke, op.style.stroke_width)
            elif t is ir.Point:
                if op.style.stroke is not None:
                    r = max(0.5, op.style.stroke_width / 2)
                    self._fill(Path.ellipse(op.x, op.y, r, r), op.style.stroke)
            else:
                raise NotImplementedError(t.__name__)


def gradient_demo(w, h, n=50):
    img = b.Image(w, h); c = b.Context(img)
    for i in range(n):
        g = b.Gradient()
        if i % 3 == 0: g.create_linear(0, 0, w, 0)
        elif i % 3 == 1: g.create_radial(w / 2, h / 2, w / 2, h / 2, w / 2)
        else: g.create_conic(w / 2, h / 2, 0)
        g.add_stop(0, 255, 0, 0, 128); g.add_stop(1, 0, 0, 255, 128)
        c.set_fill_style_gradient(g); c.fill_rect(i * 5, i * 3, w * 0.5, h * 0.5)
    c.end()
    return True


def native_font_check(path, w=640, h=100):
    face = b.FontFace.create_from_file(path)
    font = b.Font(face, 24.0)
    img = b.Image(w, h); c = b.Context(img)
    c.set_fill_style_rgba(0, 0, 0, 255); c.fill_utf8_text(10, 40, font, "Hello, Playground! नमस्ते"); c.end()
    return {"family": face.family_name, "ok": True}
