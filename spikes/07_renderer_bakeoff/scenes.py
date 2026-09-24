"""Spike 07 scenes, expressed in the real Sprint-2 IR (playground.ir).

Every engine adapter consumes the same Frame objects, so the spike doubles as
a test of the IR's backend-neutrality. Scenes follow ADR-002 / S-035.3:
  A primitive-heavy animation   B complex paths   C translucency
  D gradients (native API, IR has no gradient op yet)   E text via outlines
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from playground import ir  # noqa: E402
from playground.color import Color  # noqa: E402
from playground.geometry import Path, Transform  # noqa: E402
from playground.state import GraphicsState  # noqa: E402

FONT = os.path.join(ROOT, "spikes", "06_text_outlines", "fonts", "DejaVuSans.ttf")


def _rng(seed):
    import random

    return random.Random(seed)


# ------------------------------------------------------------------ A
def scene_a(w, h, frame):
    """500 circles + 500 rects, translucent fills, per-shape rotation (Concat)."""
    r = _rng(1)
    f = ir.Frame([ir.Clear(Color(255, 255, 255))])
    for i in range(500):
        x, y = r.uniform(0, w), r.uniform(0, h)
        st = GraphicsState(fill=Color(r.randrange(256), r.randrange(256), r.randrange(256), 120),
                           stroke=Color(0, 0, 0, 180), stroke_width=2)
        f.append(ir.Circle(x, y, r.uniform(10, 60), st))
    for i in range(500):
        x, y = r.uniform(0, w), r.uniform(0, h)
        st = GraphicsState(fill=Color(r.randrange(256), r.randrange(256), r.randrange(256), 120),
                           stroke=Color(0, 0, 0, 180), stroke_width=2)
        f.append(ir.Save())
        f.append(ir.Concat(Transform.translation(x, y).concat(Transform.rotation(frame * 3 + i * 7))))
        f.append(ir.Rect(-20, -8, 40, 16, st))
        f.append(ir.Restore())
    return f


# ------------------------------------------------------------------ B
def scene_b(w, h, frame):
    """100 stroked cubic Béziers with round joins, inside a circular clip, nested transforms."""
    r = _rng(2)
    f = ir.Frame([ir.Clear(Color(255, 255, 255))])
    f.append(ir.Save())
    f.append(ir.ClipPath(Path.ellipse(w / 2, h / 2, w * 0.4, h * 0.4)))
    f.append(ir.Concat(Transform.translation(w / 2, h / 2).concat(Transform.rotation(frame))))
    for i in range(100):
        f.append(ir.Save())
        f.append(ir.Concat(Transform.rotation(i * 3.6).concat(Transform.scaling(1 + (i % 5) * 0.1))))
        p = (Path().move_to(-w * 0.3, 0)
             .cubic_to(-w * 0.1, r.uniform(-h * 0.3, h * 0.3), w * 0.1, r.uniform(-h * 0.3, h * 0.3), w * 0.3, 0)
             .line_to(w * 0.3, 20).close())
        f.append(ir.StrokePath(p, Color(r.randrange(256), r.randrange(256), r.randrange(256), 255), 3 + i % 4))
        f.append(ir.Restore())
    f.append(ir.Restore())
    return f


# ------------------------------------------------------------------ C
def scene_c(w, h, frame):
    """300 large overlapping translucent ellipses (compositing load)."""
    r = _rng(3)
    f = ir.Frame([ir.Clear(Color(20, 20, 30))])
    for i in range(300):
        st = GraphicsState(fill=Color(r.randrange(256), r.randrange(256), r.randrange(256), 40), stroke=None)
        f.append(ir.Ellipse(r.uniform(0, w), r.uniform(0, h), r.uniform(w * 0.2, w * 0.5), r.uniform(h * 0.2, h * 0.5), st))
    return f


# ------------------------------------------------------------------ E
class _FontResource:
    """Same route as Spike 06: uharfbuzz shaping + fontTools outlines, cached per glyph."""

    def __init__(self, path):
        import uharfbuzz as hb
        from fontTools.pens.basePen import BasePen
        from fontTools.ttLib import TTFont

        class OpsPen(BasePen):
            def __init__(s, gs):
                super().__init__(gs); s.path = Path()
            def _moveTo(s, p): s.path = s.path.move_to(*p)
            def _lineTo(s, p): s.path = s.path.line_to(*p)
            def _curveToOne(s, c1, c2, p): s.path = s.path.cubic_to(*c1, *c2, *p)
            def _qCurveToOne(s, q, p): s.path = s.path.quad_to(*q, *p)
            def _closePath(s): s.path = s.path.close()
            def _endPath(s): s.path = s.path.close()

        self.tt = TTFont(path); self.upem = self.tt["head"].unitsPerEm; self.ascent = self.tt["hhea"].ascent
        self.order = self.tt.getGlyphOrder(); self.gs = self.tt.getGlyphSet(); self._Pen = OpsPen
        with open(path, "rb") as fh:
            self.hb = hb.Font(hb.Face(fh.read()))
        self.hb.scale = (self.upem, self.upem); self._hbmod = hb; self._cache = {}

    def outline(self, gid):
        p = self._cache.get(gid)
        if p is None:
            pen = self._Pen(self.gs); self.gs[self.order[gid]].draw(pen); p = self._cache[gid] = pen.path
        return p

    def ops(self, text, x, y, size, color):
        hb = self._hbmod
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        s = size / self.upem; pen_x = x; base = y + self.ascent * s
        out = []
        for i, pos in zip(buf.glyph_infos, buf.glyph_positions):
            t = Transform.scaling(s, -s).then(Transform.translation(pen_x + pos.x_offset * s, base - pos.y_offset * s))
            out.append(ir.FillPath(self.outline(i.codepoint).transformed(t), color))
            pen_x += pos.x_advance * s
        return out


_font = None


def scene_e(w, h, frame):
    """40 lines of text as outline FillPath ops (DejaVu Sans, D-009)."""
    global _font
    if _font is None:
        _font = _FontResource(FONT)
    f = ir.Frame([ir.Clear(Color(255, 255, 255))])
    y = 4
    for i in range(40):
        size = 12 + (i % 6) * 6
        f.append(ir.Save())
        f.append(ir.Concat(Transform.translation(0, 0)))
        for op in _font.ops(f"Hello, Playground! {frame + i} — नमस्ते Привет", 10, y, size, Color(0, 0, 0)):
            f.append(op)
        f.append(ir.Restore())
        y += size + 4
        if y > h - 50:
            y = 4
    return f


SCENES = {"A_primitives": scene_a, "B_paths": scene_b, "C_translucency": scene_c, "E_text": scene_e}
