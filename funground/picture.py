"""Picture: off-screen drawing surfaces (story S-052, contract P1-P3).

A Picture owns a private Sketch, drawn through its own CairoRenderer onto a persistent
Cairo surface that starts transparent and is never cleared between frames - unlike the
window, nothing about a Picture resets on its own. Drawing calls accumulate as IR ops in
the inner sketch's frame, exactly as they do for the main sketch; they are rendered onto
the picture's persistent surface only when the picture is *flushed*: drawn with
``f.image()``/``g.image()``, saved, or used as another picture's source. Flushing keeps
the persistent Cairo context's Save depth and base (HiDPI) matrix from one call to the
next (``CairoRenderer.draw_batch``), so a picture's transform, clip and push/pop nesting
carry across flushes the same way its pixels do.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import ir
from .platform.base import InputState
from .renderers.cairo2d import CairoRenderer
from .sketch import Sketch

# contract P2: the drawing vocabulary exposed as picture methods, forwarded to the inner
# Sketch as-is. Window-only functions (size, run, input, frame_count, cursor, ...) and pure
# helpers (random, noise, lerp, radians, bezier_point, ...) are deliberately left out; g.save
# and g.image are real Picture methods (below), not forwarded, because their behaviour differs
# from the main sketch's (they write/draw immediately rather than queuing).
ALLOWED_METHODS = frozenset({
    # style
    "fill", "no_fill", "stroke", "no_stroke", "stroke_width",
    "stroke_cap", "stroke_join", "miter_limit", "stroke_dash", "no_dash",
    "no_smooth", "smooth",
    "blend_mode", "opacity", "shadow", "no_shadow", "color_mode",
    # drawing
    "background", "clear",
    "rect_mode", "ellipse_mode", "image_mode",
    "circle", "ellipse", "rect", "line", "point", "square", "triangle", "quad", "polygon", "arc",
    # text
    "text", "text_align", "text_ascent", "text_descent", "text_leading", "text_box",
    "text_width", "text_size", "load_font", "text_font", "text_style",
    # transforms and the state stack
    "translate", "rotate", "scale", "shear_x", "shear_y", "apply_matrix", "reset_matrix",
    "push", "pop", "saved_state",
    # shapes, paths and clipping
    "begin_shape", "vertex", "bezier_vertex", "quadratic_vertex", "curve_vertex",
    "begin_contour", "end_contour", "curve_tightness", "end_shape",
    "bezier", "curve", "curve_point", "curve_tangent",   # curve_* use the picture's curve_tightness
    "path", "draw_path", "clip", "no_clip",
})

# contract P3: a Clear op (background() or clear()) that fully replaces every pixel - opaque
# (alpha 255) or fully transparent - makes everything before it irrelevant to how the picture
# looks from here on, so it is safe to drop the history there. A partly transparent background
# is not enough on its own (what showed through underneath still matters) and does not reset it.
_HISTORY_RESET_ALPHAS = (0, 255)
HISTORY_LIMIT = 10_000


def _resets_history(op: ir.Op) -> bool:
    return isinstance(op, ir.Clear) and op.color.a in _HISTORY_RESET_ALPHAS


@dataclass(frozen=True, slots=True)
class Snapshot:
    """An immutable copy of a Picture at one version (contract P3): what ``image()``/``save()``

    capture at the moment they are called, so later drawing on the picture cannot change it."""

    name: str
    version: int
    pixels: bytes                  # physical BGRA premultiplied bytes (Cairo's ARGB32 layout)
    phys_width: int
    phys_height: int
    scale: float
    logical_width: int
    logical_height: int
    history: tuple | None          # ops since the last opaque background/clear, or None ("pixels only")


class _PictureBacking:
    """A minimal Platform for a Picture's inner Sketch (contract P1): reports the owning

    window's backing scale and never opens a real window; every other Platform method is
    either unused (window-only Sketch methods are not exposed on a Picture) or a no-op."""

    def __init__(self, backing_scale: float) -> None:
        self._scale = backing_scale

    @property
    def backing_scale(self) -> float:
        return self._scale

    def open_window(self, width, height, title):
        raise RuntimeError("a Picture never opens a window")

    def open_full_screen(self, title):
        raise RuntimeError("a Picture never opens a window")

    def set_cursor(self, kind):
        pass

    def start(self):
        pass

    def poll(self):
        return True

    def events(self):
        return []

    def input_state(self):
        return InputState()

    def key_down(self, key):
        return False

    def present(self, pixels):
        pass

    def tick(self, fps):
        return 0.0

    def capture(self):
        raise RuntimeError("a Picture is not captured directly")

    def close(self):
        pass


class Picture:
    """An off-screen canvas (contract P1): ``f.create_graphics(width, height)`` makes one."""

    def __init__(self, width: int, height: int, backing_scale: float, name: str) -> None:
        self.width = width
        self.height = height
        self.name = name
        self._scale = backing_scale
        self._sketch = Sketch(platform=_PictureBacking(backing_scale), renderer=CairoRenderer())
        self._sketch.width = width
        self._sketch.height = height
        self._sketch._has_window = True
        pw, ph = round(width * backing_scale), round(height * backing_scale)
        self._sketch._renderer.attach(pw, ph, backing_scale)
        # Fixed once, forever: g.reset_matrix() returns to this (contract P2), not to whatever
        # the transform happens to be at the start of a later flush.
        self._sketch._renderer._base_matrix = self._sketch._renderer._ctx.get_matrix()
        self._persistent_depth = 0
        self._version = 0
        self._history: list[ir.Op] | None = []     # [] to start: a fresh, transparent picture
        self._snapshot_cache: dict[int, Snapshot] = {}

    @classmethod
    def from_pixels(cls, width: int, height: int, bgra: bytes, name: str) -> "Picture":
        """A picture holding decoded image pixels (contract P4, ``f.load_image``).

        Its scale is 1, so its physical size is the image's own size in pixels. *bgra* is
        Cairo's ARGB32 layout (premultiplied, see ``funground.imaging``). The history is
        ``None`` ("pixels only", P3) until an opaque background/clear on it starts one.
        """
        pic = cls(width, height, 1.0, name)
        surface = pic._sketch._renderer.surface
        if surface.get_stride() != width * 4 or len(bgra) != width * height * 4:
            raise RuntimeError("image pixels do not fit the picture's surface")
        surface.flush()
        surface.get_data()[:] = bgra
        surface.mark_dirty()
        pic._history = None
        return pic

    def __repr__(self) -> str:
        return f"<Picture {self.width} x {self.height}>"

    def __getattr__(self, name: str):
        if name in ALLOWED_METHODS:
            return getattr(self._sketch, name)
        raise AttributeError(
            f"a Picture has no {name!r}. It draws with the same commands as f. - fill, circle, "
            "text, push/pop, transforms, paths, clip, image, save and so on - but not "
            "window-only functions like size()/run()/cursor() or pure helpers like random()/noise()."
        )

    # ------------------------------------------------------------ flushing (contract P2)
    def _flush(self) -> None:
        """Render whatever has been drawn since the last flush onto the persistent surface."""
        frame = self._sketch.frame
        if not frame:
            return
        ops = frame.ops
        self._update_history(ops)
        renderer = self._sketch._renderer
        self._persistent_depth = renderer.draw_batch(renderer._ctx, frame, self._persistent_depth)
        frame.clear()
        self._version += 1
        self._snapshot_cache.clear()

    def _update_history(self, ops: tuple) -> None:
        reset_at = None
        for i, op in enumerate(ops):
            if _resets_history(op):
                reset_at = i
        if reset_at is not None:
            self._history = list(ops[reset_at:])
        elif self._history is not None:
            self._history.extend(ops)
        # else: still unavailable, and nothing in this batch resumed collecting.
        if self._history is not None and len(self._history) > HISTORY_LIMIT:
            self._history = None

    def _snapshot(self) -> Snapshot:
        self._flush()
        cached = self._snapshot_cache.get(self._version)
        if cached is not None:
            return cached
        renderer = self._sketch._renderer
        pixels = renderer.pixels()
        snap = Snapshot(
            name=self.name, version=self._version,
            pixels=bytes(pixels.data), phys_width=pixels.width, phys_height=pixels.height,
            scale=self._scale, logical_width=self.width, logical_height=self.height,
            history=None if self._history is None else tuple(self._history),
        )
        self._snapshot_cache[self._version] = snap
        return snap

    # ------------------------------------------------------------ image() (contract P3)
    def image(self, picture: "Picture", x: float, y: float,
              width: float | None = None, height: float | None = None) -> None:
        """Draw *picture* onto this one (never itself), the same as ``f.image()``."""
        draw_image(self._sketch, picture, x, y, width, height)

    # ------------------------------------------------------------ save() (contract P2)
    def save(self, path: str) -> None:
        """Write this picture to *path* immediately: PNG = its pixels; PDF/SVG replay its

        drawing history as vectors when one is available. When it is not (past 10 000 ops
        since the last opaque background/clear, or none collected yet), the picture's pixels
        are embedded as a raster image instead - the same fallback ``f.image()`` uses for a
        historyless picture on a PDF/SVG target (contract P3) - so a save never fails just
        because a picture drew a lot; it only stops staying vector. The actual Cairo work
        lives in ``funground.export`` (Cairo stays behind that provider, S-052).
        """
        from .export import save_picture

        snap = self._snapshot()
        pixels = self._sketch._renderer.pixels()
        save_picture(pixels, snap.history, self.width, self.height, path)


def draw_image(target: Sketch, picture: Any, x: float, y: float,
                width: float | None = None, height: float | None = None) -> None:
    """The shared body of ``f.image()`` and ``Picture.image()`` (contract P3).

    *target* is whichever Sketch is issuing the call - the main sketch for ``f.image()``, or
    a picture's own inner sketch for ``g.image()`` - so the current transform, clip,
    blend_mode and opacity are always the *caller's*, never the source picture's.
    """
    if not isinstance(picture, Picture):
        raise TypeError(
            f"f.image() needs a picture made with f.create_graphics(), not {type(picture).__name__} "
            "(or an image file loaded with f.load_image())"
        )
    if picture._sketch is target:
        raise ValueError("f.image(): a picture cannot be drawn onto itself")
    snap = picture._snapshot()
    w = picture.width if width is None else float(width)
    h = picture.height if height is None else float(height)
    style = target.style
    if style.image_mode == "corners":           # contract F10: (x, y) and the opposite corner
        if width is None or height is None:
            raise ValueError("f.image() in image_mode('corners') needs both width and height: "
                             "the opposite corner, as image(picture, x1, y1, x2, y2)")
        x, y, w, h = target._box_from_corners(x, y, w, h)
    elif style.image_mode == "center":
        x, y = x - w / 2, y - h / 2
    target._emit(ir.Image(picture.name, snap.version, float(x), float(y), w, h,
                           style.blend_mode, style.opacity, snap))
