"""Skia consumer of the Playground IR (same vector semantics as the Cairo adapter)."""
from __future__ import annotations

import numpy as np
import skia

from playground import ir
from playground.geometry import Path

NAME = "skia"
FEATURES = {"clip_path": True, "scale": True, "fill_rule": True, "stroke_join_cap": True,
            "gradients": "linear, radial, sweep(conic), two-point conical", "native_font_file": True,
            "pdf": True, "svg": True, "comp_ops": "SkBlendMode (multiply, screen, plus ...)"}


class SkiaRenderer:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.arr = np.zeros((h, w, 4), dtype=np.uint8)
        self.surface = skia.Surface.MakeRasterDirect(skia.ImageInfo.MakeN32Premul(w, h), self.arr, w * 4)
        self.canvas = self.surface.getCanvas()
        self._fmt = "BGRA" if skia.kN32_ColorType == skia.kBGRA_8888_ColorType else "RGBA"

    def buffer(self):
        return self.arr, self._fmt

    def _path(self, p: Path):
        sp = skia.Path()
        for seg in p:
            k = seg[0]
            if k == "move": sp.moveTo(*seg[1])
            elif k == "line": sp.lineTo(*seg[1])
            elif k == "cubic": sp.cubicTo(*seg[1], *seg[2], *seg[3])
            elif k == "close": sp.close()
        return sp

    def _col(self, c):
        return skia.ColorSetARGB(c.a, c.r, c.g, c.b)

    def _fill(self, path, col):
        self.canvas.drawPath(path, skia.Paint(AntiAlias=True, Color=self._col(col)))

    def _stroke(self, path, col, width):
        self.canvas.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width,
                                              StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap,
                                              Color=self._col(col)))

    def _paint(self, path, st):
        if st.fill is not None: self._fill(path, st.fill)
        if st.stroke is not None: self._stroke(path, st.stroke, st.stroke_width)

    def render(self, frame: ir.Frame):
        c = self.canvas
        for op in frame:
            t = type(op)
            if t is ir.Clear: c.clear(self._col(op.color))
            elif t is ir.Save: c.save()
            elif t is ir.Restore: c.restore()
            elif t is ir.Concat:
                m = op.transform; c.concat(skia.Matrix.MakeAll(m.a, m.c, m.e, m.b, m.d, m.f, 0, 0, 1))
            elif t is ir.ClipPath: c.clipPath(self._path(op.path), doAntiAlias=True)
            elif t is ir.FillPath: self._fill(self._path(op.path), op.color)
            elif t is ir.StrokePath: self._stroke(self._path(op.path), op.color, op.width)
            elif t is ir.Circle:
                p = skia.Path(); p.addCircle(op.x, op.y, op.diameter / 2); self._paint(p, op.style)
            elif t is ir.Ellipse:
                p = skia.Path(); p.addOval(skia.Rect.MakeXYWH(op.x - op.width / 2, op.y - op.height / 2, op.width, op.height)); self._paint(p, op.style)
            elif t is ir.Rect:
                p = skia.Path(); p.addRect(skia.Rect.MakeXYWH(op.x, op.y, op.width, op.height)); self._paint(p, op.style)
            elif t is ir.Line:
                if op.style.stroke is not None:
                    p = skia.Path(); p.moveTo(op.x1, op.y1); p.lineTo(op.x2, op.y2); self._stroke(p, op.style.stroke, op.style.stroke_width)
            elif t is ir.Point:
                if op.style.stroke is not None:
                    p = skia.Path(); p.addCircle(op.x, op.y, max(0.5, op.style.stroke_width / 2)); self._fill(p, op.style.stroke)
            else:
                raise NotImplementedError(t.__name__)


def gradient_demo(w, h, n=50):
    surf = skia.Surface(w, h); c = surf.getCanvas()
    for i in range(n):
        if i % 3 == 0:
            sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(w, 0)], [0x80FF0000, 0x800000FF])
        elif i % 3 == 1:
            sh = skia.GradientShader.MakeRadial(skia.Point(w / 2, h / 2), w / 2, [0x80FF0000, 0x800000FF])
        else:
            sh = skia.GradientShader.MakeSweep(w / 2, h / 2, [0x80FF0000, 0x800000FF])
        p = skia.Paint(AntiAlias=True); p.setShader(sh)
        c.drawRect(skia.Rect.MakeXYWH(i * 5, i * 3, w * 0.5, h * 0.5), p)
    return True
