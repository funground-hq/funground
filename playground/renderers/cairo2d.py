"""CairoRenderer: the vector renderer (D-011), consuming the IR.

Implements the v0.6 semantics: alpha honoured (D-003), strokes centred on the
edge with round joins/caps (D-004), fractional coordinates anti-aliased
(D-005). Renders into a Cairo ImageSurface that pygame presents zero-copy
(BGRA premultiplied on little-endian == pygame "BGRA" frombuffer for opaque
frames). Text is materialised through the outline route (playground.typography).
"""
from __future__ import annotations

import math

import cairo

from .. import ir
from ..capabilities import Capability
from ..color import Color
from ..geometry import Path
from ..state import GraphicsState


class CairoRenderer:
    name = "cairo"
    capabilities = frozenset({
        Capability.RASTER_2D, Capability.ALPHA, Capability.ANTIALIAS, Capability.TRANSFORMS,
        Capability.VECTOR_PATHS, Capability.CLIP_PATH, Capability.TEXT_OUTLINES,
        Capability.PNG_EXPORT, Capability.PDF_EXPORT, Capability.SVG_EXPORT,
    })

    def __init__(self, scale: float = 1.0) -> None:
        self._target = None            # pygame Surface (or None)
        self._surface: cairo.ImageSurface | None = None
        self._ctx: cairo.Context | None = None
        self._scale = scale            # backing scale (HiDPI, S-024)
        self._text_runs: dict[tuple[str, int], list] = {}

    # ---- lifecycle
    def attach(self, target) -> None:
        self._target = target
        self._text_runs.clear()
        if target is None:
            self._surface = self._ctx = None
            return
        w, h = target.get_size()
        self._surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        self._ctx = self._base_context(self._surface)

    def _base_context(self, surface) -> cairo.Context:
        ctx = cairo.Context(surface)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_antialias(cairo.ANTIALIAS_DEFAULT)
        if self._scale != 1.0:
            ctx.scale(self._scale, self._scale)
        return ctx

    @property
    def surface(self) -> cairo.ImageSurface | None:
        return self._surface

    # ---- entry point
    def render(self, frame: ir.Frame) -> None:
        if self._ctx is None:
            raise RuntimeError("renderer has no target")
        self.draw(self._ctx, frame)
        self._present()

    def draw(self, ctx: cairo.Context, frame: ir.Frame) -> None:
        """Replay *frame* onto any Cairo context (window, PNG, PDF or SVG surface)."""
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
            run = self._text_runs[key] = default_font().shape(op.text, op.style.text_size)
        return run.outline_ops(op.x, op.y, op.color)

    def _present(self) -> None:
        if self._target is None:
            return
        import pygame  # presentation only; the platform owns the window

        self._surface.flush()
        w, h = self._surface.get_width(), self._surface.get_height()
        self._target.blit(pygame.image.frombuffer(self._surface.get_data(), (w, h), "BGRA"), (0, 0))
