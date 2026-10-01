"""CairoRenderer: the vector renderer (D-011), consuming the IR.

Implements the v0.6 semantics: alpha honoured (D-003), strokes centred on the
edge with round joins/caps (D-004), fractional coordinates anti-aliased
(D-005). Draws into a Cairo ImageSurface at physical resolution behind a
HiDPI base scale (S-024); the platform presents the pixels (BGRA
premultiplied on little-endian == pygame "BGRA" for opaque frames). Text is
materialised through the outline route (funground.typography).
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
from ..paint import Gradient
from ..platform.base import Pixels
from ..state import GraphicsState

if TYPE_CHECKING:
    from ..typography import TextRun

# S-037: shaped text runs are cached per (text, size); an LRU cap keeps
# `f.text(f.frame_count, ...)` from growing the cache without bound.
TEXT_RUN_CACHE_SIZE = 256


class CairoRenderer:
    name = "cairo"
    capabilities = frozenset({
        Capability.RASTER_2D, Capability.ALPHA, Capability.ANTIALIAS, Capability.TRANSFORMS,
        Capability.VECTOR_PATHS, Capability.CLIP_PATH, Capability.TEXT_OUTLINES,
        Capability.PNG_EXPORT, Capability.PDF_EXPORT, Capability.SVG_EXPORT,
    })

    def __init__(self) -> None:
        self._alpha = 1.0      # S-051 opacity of the op being drawn
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
        """A context with funground's stroke defaults and the HiDPI base transform."""
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
        self._base_matrix = ctx.get_matrix()      # reset_matrix() returns here (keeps the HiDPI scale)
        try:
            depth = self._draw_ops(ctx, frame, 0)
            while depth:                          # an unbalanced frame must not leak state
                ctx.restore(); depth -= 1
        finally:
            ctx.restore()

    def draw_batch(self, ctx: cairo.Context, frame: ir.Frame, depth: int = 0) -> int:
        """Draw *frame* onto *ctx* without the per-frame Save/Restore wrapper or unwind that
        ``draw()`` uses (contract P2, pictures): an open Save (from ``g.push()``) and the
        transform/clip it holds carry over to the next batch instead of being reset. *depth*
        is the Save depth carried in from the previous batch on this same *ctx* (0 to start);
        the return value is what the next call should pass back in. ``self._base_matrix``
        (what ``g.reset_matrix()`` returns to) is fixed by the caller once, before the first
        batch on a given *ctx*, and is left untouched here."""
        return self._draw_ops(ctx, frame, depth)

    def _draw_ops(self, ctx: cairo.Context, frame: ir.Frame, depth: int) -> int:
        for op in frame:
            t = type(op)
            composite = self._composite_of(op) if t in self._DRAWING else None
            if composite is not None:
                self._begin_composite(ctx, op, composite)
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
            elif t is ir.ResetMatrix:
                ctx.set_matrix(self._base_matrix)
            elif t is ir.FillPath:
                self._path(ctx, op.path); self._source(ctx, op.color); ctx.fill()
            elif t is ir.StrokePath:
                self._path(ctx, op.path); self._source(ctx, op.color); ctx.set_line_width(op.width)
                self._stroke_style(ctx, op.cap, op.join, op.miter_limit, op.dash, op.dash_offset)
                ctx.stroke()
            elif t is ir.SetAntialias:
                ctx.set_antialias(cairo.ANTIALIAS_DEFAULT if op.on else cairo.ANTIALIAS_NONE)
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
                    self._source(ctx, op.style.stroke); ctx.set_line_width(op.style.stroke_width)
                    self._state_stroke_style(ctx, op.style); ctx.stroke()
            elif t is ir.Point:
                if op.style.stroke is not None:
                    ctx.new_path(); ctx.arc(op.x, op.y, max(0.5, op.style.stroke_width / 2), 0, 2 * math.pi)
                    self._source(ctx, op.style.stroke); ctx.fill()
            elif t is ir.Text:
                for sub in self._text_ops(op):
                    self._path(ctx, sub.path); self._source(ctx, sub.color); ctx.fill()
            elif t is ir.Image:
                self._draw_image(ctx, op, self._alpha)
            else:
                raise NotImplementedError(f"{self.name} renderer cannot draw {t.__name__}")
            if composite is not None:
                ctx.restore(); self._alpha = 1.0
        return depth

    # ---- compositing: blend mode, opacity, shadow (S-051, contract S14)
    _DRAWING = frozenset({ir.Circle, ir.Ellipse, ir.Rect, ir.Line, ir.Point, ir.Text, ir.FillPath, ir.StrokePath,
                          ir.Image})
    _BLENDS = {
        "normal": cairo.OPERATOR_OVER, "multiply": cairo.OPERATOR_MULTIPLY, "screen": cairo.OPERATOR_SCREEN,
        "overlay": cairo.OPERATOR_OVERLAY, "darken": cairo.OPERATOR_DARKEN, "lighten": cairo.OPERATOR_LIGHTEN,
        "add": cairo.OPERATOR_ADD, "difference": cairo.OPERATOR_DIFFERENCE, "exclusion": cairo.OPERATOR_EXCLUSION,
        "dodge": cairo.OPERATOR_COLOR_DODGE, "burn": cairo.OPERATOR_COLOR_BURN,
        "hard_light": cairo.OPERATOR_HARD_LIGHT, "soft_light": cairo.OPERATOR_SOFT_LIGHT,
        "hue": cairo.OPERATOR_HSL_HUE, "saturation": cairo.OPERATOR_HSL_SATURATION,
        "color": cairo.OPERATOR_HSL_COLOR, "luminosity": cairo.OPERATOR_HSL_LUMINOSITY,
    }
    MAX_SHADOW_LAYERS = 12

    @staticmethod
    def _composite_of(op):
        if type(op) is ir.Image:                       # no shadow field: shadow never applies (P3)
            blend, opacity = op.blend_mode, op.opacity
            if blend == "normal" and opacity == 255:
                return None
            return blend, opacity, None
        src = getattr(op, "style", op)
        blend, opacity, shadow = src.blend_mode, src.opacity, src.shadow
        if blend == "normal" and opacity == 255 and shadow is None:
            return None
        return blend, opacity, shadow

    def _begin_composite(self, ctx, op, composite) -> None:
        blend, opacity, shadow = composite
        ctx.save()
        ctx.set_operator(self._BLENDS[blend])
        self._alpha = opacity / 255
        if shadow is not None:
            self._draw_shadow(ctx, op, shadow)

    def _geometry(self, ctx, op):
        """The op's shape as (make_path, filled, stroke_width) parts, for drawing its shadow."""
        t = type(op)
        st = getattr(op, "style", None)
        if t is ir.FillPath:
            return [(lambda: self._path(ctx, op.path), True, None)]
        if t is ir.StrokePath:
            return [(lambda: self._path(ctx, op.path), False, op.width)]
        if t is ir.Text:
            return [((lambda p=sub.path: self._path(ctx, p)), True, None) for sub in self._text_ops(op)]
        if t is ir.Point:
            if st.stroke is None:
                return []
            r = max(0.5, st.stroke_width / 2)
            return [(lambda: (ctx.new_path(), ctx.arc(op.x, op.y, r, 0, 2 * math.pi)), True, None)]
        if t is ir.Line:
            make = lambda: (ctx.new_path(), ctx.move_to(op.x1, op.y1), ctx.line_to(op.x2, op.y2))
            return [(make, False, st.stroke_width)] if st.stroke is not None else []
        if t is ir.Circle:
            make = lambda: (ctx.new_path(), ctx.arc(op.x, op.y, max(0.0, op.diameter / 2), 0, 2 * math.pi))
        elif t is ir.Ellipse:
            make = lambda: self._ellipse(ctx, op.x, op.y, op.width / 2, op.height / 2)
        else:  # Rect
            make = lambda: (ctx.new_path(), ctx.rectangle(op.x, op.y, op.width, op.height))
        return [(make, st.fill is not None, st.stroke_width if st.stroke is not None else None)]

    def _draw_shadow(self, ctx, op, shadow) -> None:
        """A soft shadow as layers of the shape grown outward, so it stays vector in PDF/SVG.

        Offset and blur are in canvas pixels, whatever the transform. N layers grow the shape by
        blur, (N-1)/N x blur, ... blur/N; each is painted as one group, so overlapping parts never
        double up. Painted largest first, with alphas chosen so that a point covered by k layers ends
        at k/N of the shadow's alpha: the shadow fades evenly from the edge to *blur* pixels out."""
        dx, dy, blur, color = shadow
        parts = self._geometry(ctx, op)
        if not parts:
            return
        base = self._base_matrix
        ddx, ddy = base.transform_distance(dx, dy)
        ctx.save()
        ctx.set_matrix(ctx.get_matrix().multiply(cairo.Matrix(x0=ddx, y0=ddy)))
        per_px = math.hypot(*ctx.device_to_user_distance(*base.transform_distance(1, 0)))
        total = (color.a / 255) * self._alpha
        n = 1 if blur <= 0 else max(1, min(self.MAX_SHADOW_LAYERS, math.ceil(blur)))
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in range(1, n + 1):
            grow = (blur * (n - k + 1) / n) * per_px if blur > 0 else 0.0
            layer_alpha = (total / n) / (1 - total * (k - 1) / n)
            ctx.push_group()
            ctx.set_source_rgb(color.r / 255, color.g / 255, color.b / 255)
            for make, filled, width in parts:
                make()
                if filled:
                    ctx.fill_preserve()
                    if grow > 0:
                        ctx.set_line_width(2 * grow); ctx.stroke_preserve()
                    ctx.new_path()
                if width is not None:
                    make()
                    ctx.set_line_width(width + 2 * grow); ctx.stroke()
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(layer_alpha)
        ctx.restore()

    # ---- pictures (S-052, contract P3): draw a Picture's snapshot
    def _draw_image(self, ctx: cairo.Context, op: "ir.Image", alpha: float) -> None:
        snap = op.snapshot
        if snap is None:
            raise RuntimeError(
                "this Image op has no snapshot to draw with (an Image op loaded back from a "
                "saved IR snapshot cannot be rendered - snapshots never carry pixels, S-052)"
            )
        pixels = snap.pixels
        if op.tint is not None:                 # S-078 (P5): RGB multiplied, alpha multiplied (below)
            from ..imaging import tint_pixels
            t = op.tint
            pixels = tint_pixels(pixels, snap.phys_width, snap.phys_height, t.r, t.g, t.b)
            alpha = alpha * t.a / 255
        target = ctx.get_target()
        # A tinted picture is embedded as (tinted) pixels in PDF/SVG: its colours changed, and
        # the pixels are exactly what was tinted (a vector replay could only approximate partly
        # transparent edges).
        if not isinstance(target, cairo.ImageSurface) and snap.history is not None and op.tint is None:
            saved_base = self._base_matrix          # a nested picture's ResetMatrix must not
            try:                                      # disturb the frame around this Image op
                self._replay_image_history(ctx, op, snap, alpha)
            finally:
                self._base_matrix = saved_base
            return
        if op.sw is None:
            paint_picture_pixels(ctx, pixels, snap.phys_width, snap.phys_height,
                                  op.x, op.y, op.width, op.height, alpha)
            return
        # S-078 (P6): the source rectangle (picture pixels) fills the destination box, clipped to it
        ctx.save()
        ctx.new_path(); ctx.rectangle(op.x, op.y, op.width, op.height); ctx.clip()
        ctx.translate(op.x, op.y)
        ctx.scale(op.width / op.sw, op.height / op.sh)
        paint_picture_pixels(ctx, pixels, snap.phys_width, snap.phys_height,
                              -op.sx, -op.sy, snap.logical_width, snap.logical_height, alpha)
        ctx.restore()

    def _replay_image_history(self, ctx: cairo.Context, op: "ir.Image", snap, alpha: float) -> None:
        """PDF/SVG targets: replay the picture's history as vectors (contract P3)."""
        ctx.save()
        if op.sw is not None:        # S-078 (P6): the source rectangle fills the destination box
            ctx.new_path(); ctx.rectangle(op.x, op.y, op.width, op.height); ctx.clip()
            ctx.translate(op.x, op.y)
            ctx.scale(op.width / op.sw, op.height / op.sh)
            ctx.translate(-op.sx, -op.sy)
        else:
            ctx.translate(op.x, op.y)
            if snap.logical_width and snap.logical_height:
                ctx.scale(op.width / snap.logical_width, op.height / snap.logical_height)
        ctx.rectangle(0, 0, snap.logical_width, snap.logical_height)
        ctx.clip()
        self._base_matrix = ctx.get_matrix()
        ctx.push_group()
        depth = self._draw_ops(ctx, ir.Frame(list(snap.history)), 0)
        while depth:
            ctx.restore(); depth -= 1
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
        ctx.restore()

    # ---- helpers
    def _source(self, ctx, c) -> None:
        k = self._alpha                                 # S-051 opacity multiplies every alpha
        if isinstance(c, Gradient):                     # S-050: in user space, so it follows the transform
            if c.kind == "linear":
                pattern = cairo.LinearGradient(*c.points)
            else:
                x, y, r = c.points
                pattern = cairo.RadialGradient(x, y, 0.0, x, y, r)
            for offset, stop in c.stops:
                pattern.add_color_stop_rgba(offset, stop.r / 255, stop.g / 255, stop.b / 255, stop.a / 255 * k)
            ctx.set_source(pattern)
            return
        ctx.set_source_rgba(c.r / 255, c.g / 255, c.b / 255, c.a / 255 * k)

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
            self._source(ctx, st.stroke); ctx.set_line_width(st.stroke_width)
            self._state_stroke_style(ctx, st); ctx.stroke_preserve()
        ctx.new_path()

    _CAPS = {"round": cairo.LINE_CAP_ROUND, "square": cairo.LINE_CAP_SQUARE, "butt": cairo.LINE_CAP_BUTT}
    _JOINS = {"round": cairo.LINE_JOIN_ROUND, "miter": cairo.LINE_JOIN_MITER, "bevel": cairo.LINE_JOIN_BEVEL}

    def _stroke_style(self, ctx, cap, join, miter_limit, dash, dash_offset) -> None:
        ctx.set_line_cap(self._CAPS[cap])
        ctx.set_line_join(self._JOINS[join])
        ctx.set_miter_limit(miter_limit)
        ctx.set_dash(list(dash), dash_offset)

    def _state_stroke_style(self, ctx, st: GraphicsState) -> None:
        self._stroke_style(ctx, st.stroke_cap, st.stroke_join, st.miter_limit, st.dash, st.dash_offset)

    def _text_ops(self, op: ir.Text):
        from ..typography import effective_font

        style = op.style
        # S-054: the cache key gains the effective font only away from the plain default, so the
        # default (text, size) key - and the S-037 cache tests that pin it - stay unchanged.
        if style.font is None and style.text_style == "normal":
            key = (op.text, style.text_size)
        else:
            key = (op.text, style.text_size, style.font if style.font is not None else style.text_style)
        run = self._text_runs.get(key)
        if run is None:
            run = effective_font(op.style).shape(op.text, op.style.text_size)
            self._text_runs[key] = run
            while len(self._text_runs) > TEXT_RUN_CACHE_SIZE:
                self._text_runs.popitem(last=False)       # evict least recently used
        else:
            self._text_runs.move_to_end(key)              # mark as most recently used
        return run.outline_ops(op.x, op.y, op.color)


def paint_picture_pixels(ctx: cairo.Context, pixel_bytes, phys_w: int, phys_h: int,
                          x: float, y: float, logical_w: float, logical_h: float, alpha: float = 1.0) -> None:
    """Paint a Picture's raw pixels (BGRA premultiplied, contract P3's raster path).

    *pixel_bytes* is exactly what ``CairoRenderer.pixels()`` returns copied to bytes: Cairo's
    own ARGB32 layout, so it can be wrapped in an ``ImageSurface`` with no conversion. The
    surface is scaled so its *phys_w* x *phys_h* physical pixels fill *logical_w* x
    *logical_h* logical units at (x, y) on *ctx* - crisp when that matches the picture's own
    HiDPI scale. Used both to draw an ``Image`` op on a raster target and, without a history,
    as ``Picture.save()``'s PDF/SVG fallback (funground.picture).
    """
    if phys_w <= 0 or phys_h <= 0:
        return
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, phys_w)
    data = bytearray(pixel_bytes)
    img = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, phys_w, phys_h, stride)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(logical_w / phys_w, logical_h / phys_h)
    ctx.set_source_surface(img, 0, 0)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
