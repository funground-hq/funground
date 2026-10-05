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
    "blend_mode", "opacity", "shadow", "no_shadow", "color_mode", "tint", "no_tint", "erase", "no_erase",
    # drawing
    "background", "clear",
    "rect_mode", "ellipse_mode", "image_mode",
    "circle", "ellipse", "rect", "line", "point", "square", "triangle", "quad", "polygon", "arc",
    # text
    "text", "text_align", "text_ascent", "text_descent", "text_leading", "text_box", "text_path",
    "text_width", "text_size", "load_font", "text_font", "text_style",
    "text_tracking", "text_features", "font_variations", "text_fallback", "system_font",
    # transforms and the state stack
    "translate", "rotate", "scale", "shear_x", "shear_y", "apply_matrix", "reset_matrix",
    "push", "pop", "saved_state",
    # shapes, paths and clipping
    "begin_shape", "vertex", "bezier_vertex", "quadratic_vertex", "curve_vertex",
    "begin_contour", "end_contour", "curve_tightness", "end_shape",
    "bezier", "curve", "curve_point", "curve_tangent",   # curve_* use the picture's curve_tightness
    "path", "draw_path", "clip", "no_clip",
    # S-079 pixels (contract P7, P8); the buffer itself is the ``pixels`` property below
    "get", "set", "load_pixels", "update_pixels",
    # S-080 filters (contract P10); copy, resize and mask are real Picture methods below
    "filter",
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
    """A frozen copy of a picture at one moment.

    funground makes one for you when you draw a picture with image() or save it, so that drawing on the
    picture later cannot change what was already drawn. You do not make one yourself.

    It holds the picture's name and version, its pixels (as bytes, blue, green, red and alpha for each
    pixel, in the layout that Cairo uses), its size in pixels and in logical units, its scale, and its
    drawing history (the drawing steps since the last opaque background() or clear, or None when only the
    pixels are known).

    See also: Picture
    """

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
    """A surface that you can draw on and then draw onto the canvas, save, copy or use as a mask.

    You get one from f.create_graphics(width, height) (an empty, see-through canvas), f.layer(name) (a
    layer that sits over the canvas), f.load_image(path) (a picture file), f.load_svg(path) (a vector
    file), f.get(x, y, w, h) (a copy of part of the canvas) and f.spectrogram() (a picture of a sound).

    A picture has its own state and its own transform, and nothing about it is cleared between frames. It
    starts see-through. Draw on it with the same commands as f.: fill, stroke, circle, rect, line, text,
    push, pop, translate, rotate, scale, begin_shape, path, clip, background, clear, get, set, filter and
    so on. For example, g.circle(50, 50, 20) draws on the picture g. Window-only commands such as size(),
    run() and cursor(), and plain helpers such as random() and noise(), are not on a picture.

    The picture's width and height, in pixels, are g.width and g.height. Its name is g.name.

    A layer made by f.layer() is a picture too. Use it with with: everything drawn inside the block goes to
    the layer.

    Example:
        g = f.create_graphics(100, 100)
        g.fill("tomato")
        g.circle(50, 50, 80)
        f.image(g, 10, 10)
        f.image(g, 120, 10, 50, 50)    # the same picture, smaller

    See also: create_graphics, layer, load_image, image, copy, save
    """

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
        self._sketch._render_hook = self._flush_ops    # reading pixels draws what is recorded first (S-079)
        self._persistent_depth = 0
        self._version = 0
        self._history: list[ir.Op] | None = []     # [] to start: a fresh, transparent picture
        self._save_stack: list[bool] = []             # push()es not yet popped, over the picture's whole life (True = a layer block's own)
        self._snapshot_cache: dict[int, Snapshot] = {}
        self._layer_owner: Sketch | None = None    # S-095 (F16): the canvas sketch that made this layer
        self._layer_name: str | None = None

    @classmethod
    def from_pixels(cls, width: int, height: int, bgra: bytes, name: str) -> "Picture":
        """Make a picture from decoded image pixels.

        f.load_image() uses it. You do not need to call it.

        Arguments:
            width, height: the size of the image in pixels.
            bgra: the pixels as bytes: blue, green, red and alpha for each pixel, with the colour already multiplied by the alpha.
            name: the name for the picture.

        Returns:
            a new Picture whose scale is 1.

        Raises:
            RuntimeError: if bgra is not the right length for the size.

        See also: copy
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

    # ------------------------------------------------------------ layers (S-095, contract F16)
    def __enter__(self) -> "Picture":
        """``with f.layer("sky") as sky:`` - drawing in the block goes to this picture (a layer only)."""
        owner = self._layer_owner
        if owner is None:
            raise TypeError("only a layer can be used with 'with'. Make one with f.layer(\"name\"); "
                            "to draw on a picture from f.create_graphics(), call its methods, e.g. g.circle(...)")
        owner._enter_layer(self)
        self._sketch._push_layer_block()     # each block starts from a fresh transform and leaves no state behind
        self._sketch.reset_matrix()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        owner = self._layer_owner
        if owner is not None and owner._layer_open is self:
            self._sketch.pop()
            owner._layer_open = None
        return False

    def __getattr__(self, name: str):
        if name in ALLOWED_METHODS:
            return getattr(self._sketch, name)
        raise AttributeError(
            f"a Picture has no {name!r}. It draws with the same commands as f. - fill, circle, "
            "text, push/pop, transforms, paths, clip, image, save and so on - but not "
            "window-only functions like size()/run()/cursor() or pure helpers like random()/noise()."
        )

    @property
    def pixels(self) -> bytearray | None:
        """The colour of every pixel, after load_pixels().

        It is a list of numbers, four for each pixel (red, green, blue, alpha, each from 0 to 255), row by row
        from the top left. Change the numbers, then call update_pixels() to put them back on the picture.

        Returns:
            the numbers, or None before g.load_pixels() has been called.

        Example:
            g = f.create_graphics(10, 10)
            g.background("white")
            g.load_pixels()
            g.pixels[0] = 0       # no red in the first pixel
            g.update_pixels()

        See also: copy, mask
        """
        return self._sketch.pixels

    @pixels.setter
    def pixels(self, value) -> None:
        self._sketch.pixels = value

    # ------------------------------------------------------------ flushing (contract P2)
    def _flush(self) -> None:
        """Render whatever has been drawn since the last flush onto the persistent surface."""
        self._sketch._flush_pixel_patch()          # waiting g.set() calls become their one Pixels op
        self._flush_ops()

    def _flush_ops(self) -> None:
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
        for op in ops:
            if isinstance(op, ir.Pixels):
                self._history = None               # raster writes cannot be replayed as vectors (P7)
            elif _resets_history(op):
                # A reset inside a learner's open push() would leave its pop() unmatched (and lose the transform
                # the push() was guarding), so history stops until a reset with no push() open; files use pixels.
                # A reset inside only a layer block's own implicit push is safe: the block reset the matrix and
                # nothing else is open, so history restarts with that Save, so the block's Restore is matched.
                if not self._save_stack:
                    self._history = [op]
                elif self._save_stack == [True]:
                    self._history = [ir.Save(layer_block=True), ir.ResetMatrix(), op]
                else:
                    self._history = None
            elif self._history is not None:
                self._history.append(op)
            if isinstance(op, ir.Save):
                self._save_stack.append(op.layer_block)
            elif isinstance(op, ir.Restore) and self._save_stack:
                self._save_stack.pop()
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

    # ------------------------------------------------------------ copy, resize, mask (contract P9)
    def copy(self) -> "Picture":
        """Make a new picture with the same pixels and drawing history.

        Changing one picture never changes the other. The copy starts with the default drawing state and
        transform, like any new picture.

        Returns:
            a new Picture.

        Example:
            g = f.create_graphics(100, 100)
            g.circle(50, 50, 80)
            h = g.copy()
            h.background("black")    # g is not changed

        See also: resize, mask
        """
        snap = self._snapshot()
        other = Picture(self.width, self.height, self._scale, self._sketch._next_graphics_name())
        other._sketch._name_root = self._sketch._name_root
        other._write_pixels(snap.pixels)
        other._history = None if self._history is None else list(self._history)
        return other

    def resize(self, width: int, height: int) -> None:
        """Change the size of the picture, in place, scaling its pixels smoothly.

        Put a 0 for one side to keep the shape of the picture. The drawing history is dropped. The transform,
        the clip and any open push() start again.

        Arguments:
            width, height: the new size in pixels, whole numbers. One of them may be 0 to keep the shape. Both may not be 0.

        Raises:
            ValueError: if a side is not a whole number, is negative, or both are 0.

        Example:
            photo = f.load_image("photo.png")    # your own file
            photo.resize(200, 0)                 # 200 wide, with the height to match

        See also: copy, mask
        """
        from . import imaging

        w, h = _size(width, "width"), _size(height, "height")
        if w < 0 or h < 0:
            raise ValueError("g.resize(): width and height cannot be negative")
        if w == 0 and h == 0:
            raise ValueError("g.resize(): give a width, a height, or both (a 0 keeps the shape)")
        if w == 0:
            w = max(1, round(self.width * h / self.height))
        elif h == 0:
            h = max(1, round(self.height * w / self.width))
        snap = self._snapshot()
        pw, ph = max(1, round(w * self._scale)), max(1, round(h * self._scale))
        out = imaging.resize_bgra(snap.pixels, snap.phys_width, snap.phys_height, pw, ph)
        sketch = self._sketch
        sketch._states.unwind()
        self.width = sketch.width = w
        self.height = sketch.height = h
        renderer = sketch._renderer
        renderer.attach(pw, ph, self._scale)
        renderer._base_matrix = renderer._ctx.get_matrix()
        self._persistent_depth = 0
        if not sketch._smooth:
            sketch._append(ir.SetAntialias(False))
        self._write_pixels(out)
        self._history = None

    def mask(self, other: "Picture") -> None:
        """Make this picture see-through where another picture is see-through, in place.

        Each pixel's alpha is multiplied by the alpha of the other picture, which is scaled to this picture's
        size first. Only how see-through the mask is matters, not its colours. Draw a shape on a see-through picture to use it as a stencil.

        Arguments:
            other: the Picture to use as the mask.

        Raises:
            TypeError: if other is not a Picture.

        Example:
            photo = f.load_image("photo.png")           # your own file
            stencil = f.create_graphics(photo.width, photo.height)
            stencil.circle(photo.width / 2, photo.height / 2, photo.width)
            photo.mask(stencil)                         # now it is a circle

        See also: copy, image
        """
        from . import imaging

        if not isinstance(other, Picture):
            raise TypeError(f"g.mask() needs a picture, not {type(other).__name__}")
        snap = self._snapshot()
        osnap = other._snapshot()
        scaled = imaging.resize_bgra(osnap.pixels, osnap.phys_width, osnap.phys_height,
                                     snap.phys_width, snap.phys_height)
        self._write_pixels(imaging.mask_bgra(snap.pixels, scaled[3::4]))
        self._history = None

    def _write_pixels(self, bgra: bytes) -> None:
        """Put premultiplied BGRA (this picture's physical size) on the surface; a new version."""
        surface = self._sketch._renderer.surface
        surface.flush()
        surface.get_data()[:] = bgra
        surface.mark_dirty()
        self._version += 1
        self._snapshot_cache.clear()

    # ------------------------------------------------------------ image() (contract P3)
    def image(self, picture: "Picture", x: float, y: float,
              width: float | None = None, height: float | None = None,
              sx: float | None = None, sy: float | None = None,
              sw: float | None = None, sh: float | None = None) -> None:
        """Draw another picture onto this one, the same as f.image() does on the canvas.

        You can give a box to fit it in, and a part of the picture to use. It uses this picture's current
        transform, clip, blend mode and opacity.

        Arguments:
            picture: the Picture to draw. It cannot be this picture.
            x, y: where to put it (the top left corner, unless image_mode() says otherwise).
            width, height: the size to draw it, in pixels. They are the picture's own size if left out.
            sx, sy, sw, sh: the part of the picture to use, as a box in its own pixels. Give all four or none.

        Raises:
            TypeError: if picture is not a Picture.
            ValueError: if picture is this picture, if only some of sx, sy, sw and sh are given, or if sw or sh is 0 or less.

        Example:
            g = f.create_graphics(200, 200)
            stamp = f.create_graphics(20, 20)
            stamp.fill("gold")
            stamp.circle(10, 10, 18)
            g.image(stamp, 50, 50)

        See also: copy, save
        """
        draw_image(self._sketch, picture, x, y, width, height, sx, sy, sw, sh)

    # ------------------------------------------------------------ save() (contract P2)
    def save(self, path: str, *, text: str = "live") -> None:
        """Write the picture to a file straight away.

        The file type comes from the name. A PNG file gets the picture's pixels. A PDF or SVG file replays the
        drawing as shapes when it can. It cannot when the picture drew more than 10 000 things since its last
        opaque background or clear, or when its pixels were changed directly. Then the pixels are put in the
        file as an image instead, so saving never fails for being too big.

        Arguments:
            path: the file name, such as "art.png", "art.pdf" or "art.svg".
            text: for PDF and SVG files only. "live" keeps text as text. "shapes" draws every letter as a shape. It is "live" at first.

        Example:
            g = f.create_graphics(200, 200)
            g.circle(100, 100, 150)
            g.save("circle.png")    # writes a new file

        See also: copy, image
        """
        from .export import save_picture

        snap = self._snapshot()
        pixels = self._sketch._renderer.pixels()
        save_picture(pixels, snap.history, self.width, self.height, path, text)


def draw_image(target: Sketch, picture: Any, x: float, y: float,
                width: float | None = None, height: float | None = None,
                sx: float | None = None, sy: float | None = None,
                sw: float | None = None, sh: float | None = None) -> None:
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
    given = [v is not None for v in (sx, sy, sw, sh)]
    if any(given) and not all(given):
        raise ValueError("f.image(): to draw part of a picture give all four of sx, sy, sw and sh")
    part = all(given)
    if part:
        sx, sy, sw, sh = (_number(v, n) for v, n in zip((sx, sy, sw, sh), ("sx", "sy", "sw", "sh")))
        if sw <= 0 or sh <= 0:
            raise ValueError("f.image(): sw and sh must be above 0")
    snap = picture._snapshot()
    if part:
        w = sw if width is None else float(width)         # contract P6: the box is sw x sh by default
        h = sh if height is None else float(height)
    else:
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
    if not part:
        target._emit(ir.Image(picture.name, snap.version, float(x), float(y), w, h,
                               style.blend_mode, style.opacity, style.tint, snapshot=snap,
                               erase=None if style.erasing is None else style.erasing[0]))
        return
    # contract P6: clip the source rectangle to the picture; scale the destination so the visible
    # part keeps its place. A part wholly outside the picture draws nothing.
    x0, y0 = max(sx, 0.0), max(sy, 0.0)
    x1, y1 = min(sx + sw, float(picture.width)), min(sy + sh, float(picture.height))
    if x1 <= x0 or y1 <= y0:
        return
    kx, ky = w / sw, h / sh
    target._emit(ir.Image(picture.name, snap.version, float(x) + (x0 - sx) * kx, float(y) + (y0 - sy) * ky,
                           (x1 - x0) * kx, (y1 - y0) * ky, style.blend_mode, style.opacity, style.tint,
                           x0, y0, x1 - x0, y1 - y0, snap,
                           None if style.erasing is None else style.erasing[0]))


def _number(v: Any, name: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError(f"f.image(): {name} must be a number, not {v!r}")
    return float(v)


def _size(v: Any, name: str) -> int:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != int(v):
        raise ValueError(f"g.resize(): {name} must be a whole number, not {v!r}")
    return int(v)
