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
import zlib
from array import array
from collections import OrderedDict
from operator import itemgetter
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


def _u32(values) -> memoryview:
    """32-bit values as a memoryview (native order, which is what Cairo's surface uses)."""
    return memoryview(array("I", values))


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
        # S-094 (T15): set only by the PDF exporters (funground.export.pdf_text). When set, text
        # is drawn as marker groups that the exporter swaps for real PDF text after the file is
        # written. Never set for the window, PNG or SVG.
        self.pdf_text = None

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

    # ---- a frame drawn in several steps (S-079, contract P7: reading the canvas mid-frame)
    def begin_frame(self, ctx: cairo.Context) -> None:
        """What ``draw()`` does before the first op: open a Save and fix the base matrix. Follow it
        with any number of ``draw_batch()`` calls (carrying the depth along) and one ``end_frame()``;
        together they draw exactly what one ``draw()`` of the same ops draws."""
        ctx.save()
        self._base_matrix = ctx.get_matrix()

    def end_frame(self, ctx: cairo.Context, depth: int) -> None:
        """What ``draw()`` does after the last op: unwind pushes left open, then restore."""
        try:
            while depth:
                ctx.restore(); depth -= 1
        finally:
            ctx.restore()

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
                self._rect_path(ctx, op); self._paint(ctx, op.style)
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
                if self.pdf_text is None or not self._pdf_text_marker(ctx, op):
                    for sub in self._text_ops(op):
                        self._path(ctx, sub.path); self._source(ctx, sub.color); ctx.fill()
            elif t is ir.Image:
                self._draw_image(ctx, op, self._alpha)
            elif t is ir.Pixels:
                self._draw_pixels(ctx, op)
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
            make = lambda: self._rect_path(ctx, op)
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

    # ---- pixel access (S-079, contract P7/P8)
    # A logical pixel covers the physical pixels from ceil(x * scale) up to (not including)
    # ceil((x + 1) * scale): get reads the first of them, set paints all of them.
    @staticmethod
    def _up(v: float) -> int:
        return math.ceil(v - 1e-9)

    def _draw_pixels(self, ctx: cairo.Context, op: "ir.Pixels") -> None:
        """Replace the region's pixels: no transform, clip, tint, opacity or blend mode applies."""
        block = op.data
        if block is None:
            raise RuntimeError(
                "this Pixels op has no pixels to draw with (an op loaded back from a saved IR "
                "snapshot cannot be rendered - snapshots never carry pixels, S-079)"
            )
        image = cairo.ImageSurface.create_for_data(bytearray(block.bgra), cairo.FORMAT_ARGB32,
                                                   block.width, block.height, block.width * 4)
        s = block.scale
        m = cairo.Matrix(1 / s, 0, 0, 1 / s, block.x / s, block.y / s).multiply(self._base_matrix)
        if abs(m.xx - 1) < 1e-9 and abs(m.yy - 1) < 1e-9 and abs(m.xy) < 1e-9 and abs(m.yx) < 1e-9:
            x0 = round(m.x0) if abs(m.x0 - round(m.x0)) < 1e-6 else m.x0       # no blur from rounding noise
            y0 = round(m.y0) if abs(m.y0 - round(m.y0)) < 1e-6 else m.y0
            m = cairo.Matrix(1, 0, 0, 1, x0, y0)
        ctx.save()
        ctx.reset_clip()
        ctx.set_matrix(m)
        ctx.set_source_surface(image, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_NEAREST)
        # PDF and SVG cannot "replace"; they get the pixels laid over the drawing (it is raster anyway)
        ctx.set_operator(cairo.OPERATOR_SOURCE if isinstance(ctx.get_target(), cairo.ImageSurface)
                         else cairo.OPERATOR_OVER)
        ctx.new_path(); ctx.rectangle(0, 0, block.width, block.height); ctx.fill()
        ctx.restore()

    def _surface_view(self) -> memoryview:
        """The surface as one 32-bit value per physical pixel (premultiplied BGRA, little-endian)."""
        surface = self._surface
        surface.flush()
        if surface.get_stride() != surface.get_width() * 4:
            raise RuntimeError("unexpected surface layout")
        return memoryview(surface.get_data()).cast("B").cast("I")

    def _sample(self, view: memoryview, bx: int, by: int, bw: int, bh: int,
                x: int, y: int, w: int, h: int, limit: tuple[int, int]) -> bytearray:
        """Logical pixels x, y, w, h (premultiplied BGRA, w*h*4 bytes) from a physical buffer.

        *view* holds bw x bh physical pixels whose top-left is physical (bx, by). Each logical pixel
        takes its top-left physical pixel. Logical pixels outside 0..limit stay transparent."""
        out = bytearray(w * h * 4)
        xs0, xs1 = max(x, 0), min(x + w, limit[0])
        ys0, ys1 = max(y, 0), min(y + h, limit[1])
        if xs0 >= xs1 or ys0 >= ys1 or bw <= 0 or bh <= 0:
            return out
        ov = memoryview(out).cast("I")
        s, up = self._scale, self._up
        cols = [min(max(up(xx * s) - bx, 0), bw - 1) for xx in range(xs0, xs1)]
        n = len(cols)
        contiguous = cols[-1] - cols[0] == n - 1
        pick = None if contiguous or n == 1 else itemgetter(*cols)
        for yy in range(ys0, ys1):
            r = min(max(up(yy * s) - by, 0), bh - 1)
            o = (yy - y) * w + (xs0 - x)
            if contiguous:
                ov[o:o + n] = view[r * bw + cols[0]:r * bw + cols[0] + n]
            else:
                row = view[r * bw:(r + 1) * bw]
                ov[o:o + n] = _u32(pick(row))
        return out

    def read_logical(self, x: int, y: int, w: int, h: int, width: int, height: int) -> bytes:
        """The canvas's logical pixels x, y, w, h as premultiplied BGRA; outside the canvas
        (logical width x height) is transparent black (contract P7)."""
        if self._surface is None:
            raise RuntimeError("renderer has no surface")
        view = self._surface_view()
        return bytes(self._sample(view, 0, 0, self._surface.get_width(), self._surface.get_height(),
                                  x, y, w, h, (width, height)))

    def block_from_logical(self, bgra: bytes, x: int, y: int, w: int, h: int) -> "ir.PixelBlock":
        """Logical premultiplied BGRA for the region x, y, w, h as a physical block: each logical
        pixel fills all the physical pixels it covers."""
        s, up = self._scale, self._up
        px0, px1 = up(x * s), up((x + w) * s)
        py0, py1 = up(y * s), up((y + h) * s)
        if s == 1.0:
            return ir.PixelBlock(s, px0, py0, px1 - px0, py1 - py0, bytes(bgra))
        src = memoryview(bytes(bgra)).cast("I")
        cols = [min(max(math.floor(pc / s + 1e-9) - x, 0), w - 1) for pc in range(px0, px1)]
        pick = itemgetter(*cols) if len(cols) > 1 else None
        pw = px1 - px0
        out = bytearray(pw * (py1 - py0) * 4)
        ov = memoryview(out).cast("I")
        last_r, last = -1, None
        for i, pr in enumerate(range(py0, py1)):
            r = min(max(math.floor(pr / s + 1e-9) - y, 0), h - 1)
            if r != last_r:
                row = src[r * w:(r + 1) * w]
                last = _u32(pick(row) if pick else (row[cols[0]],))
                last_r = r
            ov[i * pw:(i + 1) * pw] = last
        return ir.PixelBlock(s, px0, py0, pw, py1 - py0, bytes(out))

    def pixels_op(self, bgra: bytes, x: int, y: int, w: int, h: int) -> "ir.Pixels":
        """A ``Pixels`` op for the logical region x, y, w, h whose pixels (premultiplied BGRA at
        logical resolution) are *bgra*."""
        return ir.Pixels(x, y, w, h, zlib.crc32(bgra), self.block_from_logical(bgra, x, y, w, h))

    def patch_op(self, patch: dict) -> "ir.Pixels":
        """One ``Pixels`` op for many single-pixel writes: *patch* maps a logical (x, y) to a Color.

        The op covers the patch's bounding box. Pixels in it that were not written keep what the
        canvas shows now (so the canvas must be up to date); written ones take their colour exactly."""
        if self._surface is None:
            raise RuntimeError("renderer has no surface")
        xs = [k[0] for k in patch]
        ys = [k[1] for k in patch]
        x0, y0 = min(xs), min(ys)
        w, h = max(xs) - x0 + 1, max(ys) - y0 + 1
        s, up = self._scale, self._up
        px0, py0 = up(x0 * s), up(y0 * s)
        bw, bh = up((x0 + w) * s) - px0, up((y0 + h) * s) - py0
        region = bytearray(bw * bh * 4)           # starts as what the canvas shows in that block
        rv = memoryview(region).cast("I")
        view = self._surface_view()
        sw, sh = self._surface.get_width(), self._surface.get_height()
        cx0, cx1 = max(px0, 0), min(px0 + bw, sw)
        if cx0 < cx1:
            for r in range(max(py0, 0), min(py0 + bh, sh)):
                rv[(r - py0) * bw + (cx0 - px0):(r - py0) * bw + (cx1 - px0)] = view[r * sw + cx0:r * sw + cx1]
        for (x, y), c in patch.items():
            a = c.a
            value = (((c.b * a + 127) // 255) | (((c.g * a + 127) // 255) << 8)
                     | (((c.r * a + 127) // 255) << 16) | (a << 24))
            bx0, by0 = up(x * s) - px0, up(y * s) - py0
            bx1, by1 = max(up((x + 1) * s) - px0, bx0 + 1), max(up((y + 1) * s) - py0, by0 + 1)
            if bx1 - bx0 == 1 and by1 - by0 == 1:
                rv[by0 * bw + bx0] = value
            else:
                run = _u32((value,) * (bx1 - bx0))
                for r in range(by0, by1):
                    rv[r * bw + bx0:r * bw + bx1] = run
        logical = self._sample(rv, px0, py0, bw, bh, x0, y0, w, h, (x0 + w, y0 + h))
        return ir.Pixels(x0, y0, w, h, zlib.crc32(logical), ir.PixelBlock(s, px0, py0, bw, bh, bytes(region)))

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
        # contract P3: under no_smooth (anti-aliasing off) pictures scale without blurring
        nearest = ctx.get_antialias() == cairo.ANTIALIAS_NONE
        if op.sw is None:
            paint_picture_pixels(ctx, pixels, snap.phys_width, snap.phys_height,
                                  op.x, op.y, op.width, op.height, alpha, nearest)
            return
        # S-078 (P6): the source rectangle (picture pixels) fills the destination box, clipped to it
        ctx.save()
        ctx.new_path(); ctx.rectangle(op.x, op.y, op.width, op.height); ctx.clip()
        ctx.translate(op.x, op.y)
        ctx.scale(op.width / op.sw, op.height / op.sh)
        paint_picture_pixels(ctx, pixels, snap.phys_width, snap.phys_height,
                              -op.sx, -op.sy, snap.logical_width, snap.logical_height, alpha, nearest)
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

    @classmethod
    def _rect_path(cls, ctx, op) -> None:
        if op.radii:
            cls._path(ctx, Path.rounded_rect(op.x, op.y, op.width, op.height, op.radii))
        else:
            ctx.new_path(); ctx.rectangle(op.x, op.y, op.width, op.height)

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

    def _pdf_text_marker(self, ctx, op: ir.Text) -> bool:
        """S-094 (T15): draw *op* as a marker group for real PDF text; False to draw outlines.

        The group holds the run's colour or gradient clipped to a marker shape that the PDF
        exporter recognises after ``surface.finish()`` and replaces with the run's glyphs in clip
        mode, so the paint fills exactly the glyphs. Painting the group back respects the clip,
        transform, opacity (already in the source) and blend mode, as the outline fill would."""
        run = self._text_run(op)
        marker = self.pdf_text.add(run, op.x, op.y, tuple(ctx.get_matrix()))
        if marker is None:
            return False
        ctx.push_group()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        ctx.new_path()
        ctx.move_to(*marker[0])
        for point in marker[1:]:
            ctx.line_to(*point)
        ctx.close_path()
        ctx.clip()
        self._source(ctx, op.color)
        ctx.paint()
        ctx.pop_group_to_source()
        ctx.paint()
        return True

    def _text_ops(self, op: ir.Text):
        return self._text_run(op).outline_ops(op.x, op.y, op.color)

    def _text_run(self, op: ir.Text) -> "TextRun":
        from ..typography import effective_font, text_settings

        style = op.style
        # S-054: the cache key gains the effective font only away from the plain default, so the
        # default (text, size) key - and the S-037 cache tests that pin it - stay unchanged.
        if style.font is None and style.text_style == "normal":
            key = (op.text, style.text_size)
        else:
            key = (op.text, style.text_size, style.font if style.font is not None else style.text_style)
        settings = text_settings(style)
        if style.text_tracking or style.text_features or style.font_variations:
            key += (style.text_tracking, style.text_features, style.font_variations)    # S-090 (T13)
        run = self._text_runs.get(key)
        if run is None:
            run = effective_font(op.style).shape(op.text, op.style.text_size, **settings)
            self._text_runs[key] = run
            while len(self._text_runs) > TEXT_RUN_CACHE_SIZE:
                self._text_runs.popitem(last=False)       # evict least recently used
        else:
            self._text_runs.move_to_end(key)              # mark as most recently used
        return run


def paint_picture_pixels(ctx: cairo.Context, pixel_bytes, phys_w: int, phys_h: int,
                          x: float, y: float, logical_w: float, logical_h: float, alpha: float = 1.0,
                          nearest: bool = False) -> None:
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
    if nearest:                                  # crisp enlarged pixels (contract P3, no_smooth)
        ctx.get_source().set_filter(cairo.FILTER_NEAREST)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
