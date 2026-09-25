"""CairoRenderer: the vector renderer (D-011), consuming the IR.

Implements the v0.6 semantics: alpha honoured (D-003), strokes centred on the
edge with round joins/caps (D-004), fractional coordinates anti-aliased
(D-005). Draws into a Cairo ImageSurface at physical resolution behind a
HiDPI base scale (S-024); the platform presents the pixels (BGRA
premultiplied on little-endian == pygame "BGRA" for opaque frames). Text is
materialised through the outline route (playground.typography).
"""
from __future__ import annotations

import math
from collections import OrderedDict
from typing import TYPE_CHECKING

import cairo

from .. import ir
from ..capabilities import Capability
from ..color import Color
from ..geometry import Path
from ..platform.base import Pixels
from ..state import GraphicsState

if TYPE_CHECKING:
    from ..typography import TextRun

# S-037: shaped text runs are cached per (text, size); an LRU cap keeps
# `p.text(p.frame_count, ...)` from growing the cache without bound.
TEXT_RUN_CACHE_SIZE = 256


class CairoRenderer:
    name = "cairo"
    capabilities = frozenset({
        Capability.RASTER_2D, Capability.ALPHA, Capability.ANTIALIAS, Capability.TRANSFORMS,
        Capability.VECTOR_PATHS, Capability.CLIP_PATH, Capability.TEXT_OUTLINES,
        Capability.PNG_EXPORT, Capability.PDF_EXPORT, Capability.SVG_EXPORT,
    })

    def __init__(self) -> None:
        self._surface: cairo.ImageSurface | None = None
        self._ctx: cairo.Context | None = None
        self._scale = 1.0
        self._text_runs: OrderedDict[tuple[str, int], TextRun] = OrderedDict()

    # ---- lifecycle
    def attach(self, width: int, height: int, scale: float = 1.0) -> None:
        self._text_runs.clear()
        if width <= 0 or height <= 0:
            self._surface = self._ctx = None
            return
        self._scale = scale
        self._surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self._ctx = self.context_for(self._surface, scale)

    def context_for(self, surface, scale: float = 1.0) -> cairo.Context:
        """A context with Playground's stroke defaults and the HiDPI base transform."""
        ctx = cairo.Context(surface)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_antialias(cairo.ANTIALIAS_DEFAULT)
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)   # contract F3: non-zero (Cairo's default, pinned here)
        if scale != 1.0:
            ctx.scale(scale, scale)
        return ctx

    @property
    def surface(self) -> cairo.ImageSurface | None:
        return self._surface

    def pixels(self) -> Pixels:
        if self._surface is None:
            raise RuntimeError("renderer has no surface")
        self._surface.flush()
        return Pixels(self._surface.get_data(), self._surface.get_width(), self._surface.get_height(), "BGRA")

    # ---- entry point
    def render(self, frame: ir.Frame) -> None:
        if self._ctx is None:
            raise RuntimeError("renderer has no surface")
        self.draw(self._ctx, frame)

    def draw(self, ctx: cairo.Context, frame: ir.Frame) -> None:
        """Replay *frame* onto any Cairo context (window, PNG, PDF or SVG surface)."""
        # Contract F2: the transform stack resets every frame, so a top-level
        # Concat must not carry over to the next frame on the window context.
        ctx.save()
        try:
            self._draw_ops(ctx, frame)
        finally:
            ctx.restore()

    def _draw_ops(self, ctx: cairo.Context, frame: ir.Frame) -> None:
        depth = 0
        for op in frame:
            t = type(op)
            if t is ir.Clear:
                ctx.save(); ctx.reset_clip(); self._source(ctx, op.color)
                ctx.set_operator(cairo.OPERATOR_SOURCE); ctx.paint(); ctx.restore()
            elif t is ir.Save:
                ctx.save(); depth += 1
            elif t is ir.Restore:
                if depth == 0:
                    raise RuntimeError("Restore without Save in frame")
                ctx.restore(); depth -= 1
            elif t is ir.Concat:
                m = op.transform
                ctx.transform(cairo.Matrix(m.a, m.b, m.c, m.d, m.e, m.f))
            elif t is ir.ClipPath:
                self._path(ctx, op.path); ctx.clip()
            elif t is ir.ResetClip:
                ctx.reset_clip()
            elif t is ir.FillPath:
                self._path(ctx, op.path); self._source(ctx, op.color); ctx.fill()
            elif t is ir.StrokePath:
                self._path(ctx, op.path); self._source(ctx, op.color); ctx.set_line_width(op.width); ctx.stroke()
            elif t is ir.Circle:
                ctx.new_path(); ctx.arc(op.x, op.y, max(0.0, op.diameter / 2), 0, 2 * math.pi)
                self._paint(ctx, op.style)
            elif t is ir.Ellipse:
                self._ellipse(ctx, op.x, op.y, op.width / 2, op.height / 2); self._paint(ctx, op.style)
            elif t is ir.Rect:
                ctx.new_path(); ctx.rectangle(op.x, op.y, op.width, op.height); self._paint(ctx, op.style)
            elif t is ir.Line:
                if op.style.stroke is not None:
                    ctx.new_path(); ctx.move_to(op.x1, op.y1); ctx.line_to(op.x2, op.y2)
                    self._source(ctx, op.style.stroke); ctx.set_line_width(op.style.stroke_width); ctx.stroke()
            elif t is ir.Point:
                if op.style.stroke is not None:
                    ctx.new_path(); ctx.arc(op.x, op.y, max(0.5, op.style.stroke_width / 2), 0, 2 * math.pi)
                    self._source(ctx, op.style.stroke); ctx.fill()
            elif t is ir.Text:
                for sub in self._text_ops(op):
                    self._path(ctx, sub.path); self._source(ctx, sub.color); ctx.fill()
            else:
                raise NotImplementedError(f"{self.name} renderer cannot draw {t.__name__}")
        while depth:                      # an unbalanced frame must not leak state
            ctx.restore(); depth -= 1

    # ---- helpers
    @staticmethod
    def _source(ctx, c: Color) -> None:
        ctx.set_source_rgba(c.r / 255, c.g / 255, c.b / 255, c.a / 255)

    @staticmethod
    def _path(ctx, p: Path) -> None:
        ctx.new_path()
        for seg in p:
            k = seg[0]
            if k == "move": ctx.move_to(*seg[1])
            elif k == "line": ctx.line_to(*seg[1])
            elif k == "cubic": ctx.curve_to(*seg[1], *seg[2], *seg[3])
            elif k == "close": ctx.close_path()

    @staticmethod
    def _ellipse(ctx, cx, cy, rx, ry) -> None:
        ctx.new_path()
        if rx <= 0 or ry <= 0:
            return
        ctx.save(); ctx.translate(cx, cy); ctx.scale(rx, ry); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()

    def _paint(self, ctx, st: GraphicsState) -> None:
        if st.fill is not None:
            self._source(ctx, st.fill); ctx.fill_preserve()
        if st.stroke is not None:
            self._source(ctx, st.stroke); ctx.set_line_width(st.stroke_width); ctx.stroke_preserve()
        ctx.new_path()

    def _text_ops(self, op: ir.Text):
        from ..typography import default_font

        key = (op.text, op.style.text_size)
        run = self._text_runs.get(key)
        if run is None:
            run = default_font().shape(op.text, op.style.text_size)
            self._text_runs[key] = run
            while len(self._text_runs) > TEXT_RUN_CACHE_SIZE:
                self._text_runs.popitem(last=False)       # evict least recently used
        else:
            self._text_runs.move_to_end(key)              # mark as most recently used
        return run.outline_ops(op.x, op.y, op.color)
