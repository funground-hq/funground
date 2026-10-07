"""Marks: a drawing kept as a value (story S-132, contract K1-K3, decisions D-069 and D-070).

``with f.mark() as m:`` records the drawing calls in its block instead of drawing them. ``m.place(x, y)``
then draws that drawing, as often as you like, at any position, scale, rotation and opacity.

How it works:

- **Recording.** A block swaps the drawing sketch's frame and state stack for fresh ones (an internal
  ``_Recorder``), so every drawing call in the block appends its op, with its style snapshot, to the
  mark instead of the canvas. The fresh state stack starts from the current style; the fresh frame
  starts with no transform and no clip, so the mark's coordinates are its own. On the way out, normal
  or not, the frame, the state stack, an open shape and the smoothing setting are put back exactly,
  so nothing recorded reaches the canvas and nothing leaks from the block.
- **The finished mark** keeps a tuple of frozen ops. ``reset_matrix()`` in a block is rewritten into
  the inverse of the transform made so far in the block, so it returns to the mark's own origin and
  never to the canvas's.
- **Placing** appends ``Save``, one ``Concat`` (translate, rotate, scale, then the anchor offset),
  the mark's ops and ``Restore`` to the active sketch's frame. Inside a layer block that is the layer;
  inside another mark's block that is the other mark, so marks nest by flattening.
- **Groups.** Opacity below 1 wraps the ops in ``BeginGroup``/``EndGroup`` (a Cairo group, a PDF
  transparency group), so the mark fades as one piece. A mark that erases or calls ``no_clip()`` is
  always grouped, so its erasing stays inside the mark and the clip around a placement still holds.
- **Bounds** come from the renderer (``ink_bounds``, a Cairo recording surface), measured once and
  kept. This module never imports Cairo (tests/test_boundaries.py).
"""
from __future__ import annotations

import math
import warnings
from dataclasses import replace

from . import ir
from .capabilities import FungroundWarning
from .color import BLACK, WHITE
from .geometry import Path, Transform
from .paths import PathBuilder
from .state import StateStack

# Where each anchor sits on the mark's bounds, as fractions of its width and height.
ANCHORS: dict[str, tuple[float, float] | None] = {
    "origin": None,
    "center": (0.5, 0.5),
    "top-left": (0.0, 0.0),
    "top": (0.5, 0.0),
    "top-right": (1.0, 0.0),
    "left": (0.0, 0.5),
    "right": (1.0, 0.5),
    "bottom-left": (0.0, 1.0),
    "bottom": (0.5, 1.0),
    "bottom-right": (1.0, 1.0),
}


class _NotGiven:
    """The default of an argument that takes its value from the current style when left out."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<not given>"


NOT_GIVEN = _NotGiven()

# What cannot be done while a mark is being recorded, and why (contract K1).
_SAVE = "a mark records drawing and draws nothing, so there is nothing to save or show yet. Do it after the block ends."
_PIXELS = "a mark keeps drawing steps, not pixels, so there are no pixels to read or change. Do it after the block ends."
_WHOLE = "a mark has no edges, so it has no whole area to fill or clear. Draw a rect() of the size you want instead."
REFUSED: dict[str, str] = {
    "f.layer()": "a layer cannot be opened inside a mark. Open the layer first; you can record or place a mark inside it.",
    "f.create_slider()": "controls belong to the window, not to a mark. Make them in setup(), outside the block.",
    "f.create_checkbox()": "controls belong to the window, not to a mark. Make them in setup(), outside the block.",
    "f.create_button()": "controls belong to the window, not to a mark. Make them in setup(), outside the block.",
    "f.save()": _SAVE, "f.save_frames()": _SAVE, "f.save_gif()": _SAVE, "f.save_movie()": _SAVE,
    "f.show()": _SAVE, "f.new_page()": _SAVE, "f.keep()": _SAVE,
    "f.size()": "a mark has no size of its own; bounds() measures its drawing. Set the canvas size before the block.",
    "f.get()": _PIXELS, "f.set()": _PIXELS, "f.load_pixels()": _PIXELS, "f.update_pixels()": _PIXELS,
    "f.filter()": _PIXELS,
    "f.background()": _WHOLE, "f.clear()": _WHOLE,
    "grid.show()": "guides help you see a layout in the window and are not part of a mark. Call show() after "
                   "the block ends, or give in_files=True to record the guide lines in the mark as ordinary drawing.",
}

# The mark blocks open now, innermost last.
_open: list["_Recorder"] = []


def recording() -> bool:
    """Whether a ``with f.mark()`` block is open now."""
    return bool(_open)


def refuse_in_mark(call: str) -> None:
    """Raise RuntimeError when *call* (a key of REFUSED) is made inside a ``with f.mark()`` block."""
    if _open:
        raise RuntimeError(f"{call} cannot be used inside a `with f.mark() as ...:` block: {REFUSED[call]}")


class _Recorder:
    """The mutable side of a mark, alive only during its block: it redirects one sketch's drawing."""

    __slots__ = ("sketch", "saved")

    def __init__(self, sketch) -> None:
        self.sketch = sketch
        self.saved: tuple | None = None

    def begin(self) -> None:
        s = self.sketch
        if s._pending_pixels:                    # set() calls made before the block belong to the canvas
            s._flush_pixel_patch()
        self.saved = (s.frame, s._states, s._shape, s._smooth, s._has_window)
        s.frame = ir.Frame()
        s._states = StateStack(s._states.current)   # the current style; no pushes; a fresh transform and clip
        s._shape = None
        s._has_window = True                     # a mark may be recorded before the window opens (at the top)

    def end(self) -> tuple[tuple, int, bool]:
        """Stop recording and put the sketch back exactly. Returns (ops, pushes left open, shape left open)."""
        s = self.sketch
        try:
            ops = s.frame.ops
            pushes = s._states.depth
            shape = s._shape is not None
        finally:
            s.frame, s._states, s._shape, s._smooth, s._has_window = self.saved
        return ops, pushes, shape


def _local(ops: tuple) -> tuple[tuple, bool]:
    """The recorded ops made self-contained, and whether a placement must group them.

    ``ResetMatrix`` becomes the inverse of the transform made so far in the block, so it returns to the
    mark's own origin wherever the mark is placed. A mark that removes clipping or erases is grouped."""
    out: list = []
    stack: list[Transform] = []
    m = Transform()
    group = False
    for op in ops:
        t = type(op)
        if t is ir.Save or t is ir.BeginGroup:
            stack.append(m)
        elif t is ir.Restore or t is ir.EndGroup:
            if stack:
                m = stack.pop()
        elif t is ir.Concat:
            m = m.concat(op.transform)
        elif t is ir.ResetMatrix:
            if not m.is_identity:
                out.append(ir.Concat(m.invert()))
            m = Transform()
            continue
        elif t is ir.ResetClip:
            group = True
        if not group and _erases(op):
            group = True
        out.append(op)
    return tuple(out), group


def _erases(op) -> bool:
    if type(op) in (ir.FillPath, ir.StrokePath, ir.Image):
        return op.erase is not None
    style = getattr(op, "style", None)
    return style is not None and style.erasing is not None


def _number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"mark.place(): {name} must be a number, not {value!r}")
    if not math.isfinite(value):
        raise ValueError(f"mark.place(): {name} must be a finite number, not {value!r}")
    return float(value)


def _scale(value) -> tuple[float, float]:
    if isinstance(value, (tuple, list)):
        if len(value) != 2:
            raise ValueError(f"mark.place(): scale is one number, or two as (sx, sy), not {value!r}")
        sx, sy = _number(value[0], "scale"), _number(value[1], "scale")
    else:
        sx = sy = _number(value, "scale")
    if sx == 0 or sy == 0:
        raise ValueError("mark.place(): scale must not be 0 (the mark would be squashed flat)")
    return sx, sy


_UNMEASURED = object()


class Mark:
    """A drawing kept as a value, which you can place as often as you like.

    Make one with a block: ``with f.mark() as m:``. The drawing calls inside the block are recorded, not
    drawn, each with the fill, stroke and font it was drawn with. Or make one from a path with
    f.mark(path, fill=..., stroke=...). Then m.place(x, y) draws it, with its own origin (0, 0) at
    (x, y), and with any scale, rotation and opacity.

    A mark keeps the drawing steps, not pixels. It is sharp at any size on screen, and real shapes and
    text in a saved PDF or SVG. A finished mark cannot be changed, and placing it never changes it. To
    make a variation, make a new mark, for example in a function that takes the parts that vary.

    A mark's block starts with the current style and with no transform, so its coordinates are its own.
    When the block ends, the transform, style and clip are exactly as before it, even if the block
    raised an error. Inside the block you cannot open a layer, make controls, save files or read pixels.

    Example:
        with f.mark() as flower:
            for a in range(0, 360, 60):
                with f.saved_state():
                    f.rotate(a)
                    f.fill("tomato")
                    f.ellipse(0, -30, 18, 40)
            f.fill("gold")
            f.circle(0, 0, 24)
        flower.place(150, 200)
        flower.place(400, 200, scale=0.5, rotate=15, opacity=0.6)

    See also: mark, path, layer, saved_state
    """

    __slots__ = ("_status", "_ops", "_group", "_bounds", "_recorder", "_restyled")

    def __init__(self) -> None:
        object.__setattr__(self, "_status", "new")   # new -> recording -> finished, or failed
        object.__setattr__(self, "_ops", ())
        object.__setattr__(self, "_group", False)
        object.__setattr__(self, "_bounds", _UNMEASURED)
        object.__setattr__(self, "_recorder", None)
        object.__setattr__(self, "_restyled", {})     # style="current": {GraphicsState: (ops, ink bounds)}, a few kept

    def __setattr__(self, name, value) -> None:
        raise AttributeError("a mark cannot be changed. Make a new mark instead, e.g. in a function that returns one.")

    def __delattr__(self, name) -> None:
        raise AttributeError("a mark cannot be changed. Make a new mark instead, e.g. in a function that returns one.")

    def __copy__(self) -> "Mark":
        return self                              # an immutable value: a copy would be the same

    def __deepcopy__(self, memo) -> "Mark":
        return self

    def __repr__(self) -> str:
        if self._status != "finished":
            return f"<Mark ({'being recorded' if self._status == 'recording' else 'unfinished'})>"
        b = self._measure()
        return "<Mark (empty)>" if b is None else f"<Mark {b[2]:g} x {b[3]:g}>"

    # ---- recording (contract K1)
    def __enter__(self) -> "Mark":
        if self._status != "new":
            raise RuntimeError("this mark has already been recorded, and a mark is recorded only once. "
                               "Make a new one with `with f.mark() as m:`.")
        from .api import active_sketch

        recorder = _Recorder(active_sketch())
        recorder.begin()
        _open.append(recorder)
        object.__setattr__(self, "_recorder", recorder)
        object.__setattr__(self, "_status", "recording")
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        recorder = self._recorder
        try:
            ops, pushes, shape = recorder.end()
        finally:
            if recorder in _open:
                _open.remove(recorder)
            object.__setattr__(self, "_recorder", None)
        if exc_type is not None:
            object.__setattr__(self, "_status", "failed")
            return False
        if pushes:
            ops = ops + (ir.Restore(),) * pushes
            warnings.warn(f"a `with f.mark()` block finished with {pushes} f.push() call(s) still open; "
                          "funground closed them for you. Add a matching f.pop(), or use `with f.saved_state():`.",
                          FungroundWarning, stacklevel=2)
        if shape:
            warnings.warn("a `with f.mark()` block finished inside a shape: f.begin_shape() had no "
                          "f.end_shape(), so nothing was recorded for it.", FungroundWarning, stacklevel=2)
        body, group = _local(ops)
        object.__setattr__(self, "_ops", body)
        object.__setattr__(self, "_group", group)
        object.__setattr__(self, "_status", "finished")
        return False

    def _finished(self, call: str) -> None:
        status = self._status
        if status == "finished":
            return
        if status == "recording":
            raise RuntimeError(f"mark.{call}: this mark is still being recorded. Use it after its "
                               "`with f.mark()` block ends.")
        if status == "failed":
            raise RuntimeError(f"mark.{call}: this mark is unfinished, because an error stopped its "
                               "`with f.mark()` block. Fix the error and record it again.")
        raise RuntimeError(f"mark.{call}: this mark is unfinished: it was never recorded. Use f.mark() in a "
                           "`with` block (`with f.mark() as m:`), or give it a path: f.mark(path).")

    # ---- measuring
    def _measure(self):
        if self._bounds is _UNMEASURED:
            bounds = None
            if self._ops:
                from .sketch import default_renderer

                bounds = default_renderer().ink_bounds(self._ops)
            object.__setattr__(self, "_bounds", bounds)
        return self._bounds

    def bounds(self) -> tuple[float, float, float, float] | None:
        """Return the area the mark covers, in its own coordinates.

        The area includes stroke widths, joins and caps, and text. It is never smaller than what the mark
        paints, and at most a tiny bit larger. The mark's origin (0, 0) is where place() puts (x, y), so x
        and y are often negative.

        Returns:
            (x, y, w, h): the left, the top, the width and the height. None for an empty mark.

        Raises:
            RuntimeError: the mark is unfinished.

        Example:
            x, y, w, h = flower.bounds()

        See also: width, height, is_empty, place
        """
        self._finished("bounds()")
        return self._measure()

    @property
    def is_empty(self) -> bool:
        """Whether the mark paints nothing.

        Returns:
            True when the mark paints nothing (and bounds() is None), otherwise False.

        Raises:
            RuntimeError: the mark is unfinished.

        Example:
            if not flower.is_empty:
                flower.place(100, 100)

        See also: bounds
        """
        self._finished("is_empty")
        return self._measure() is None

    @property
    def width(self) -> float:
        """The width of the area the mark covers, from bounds(); 0 for an empty mark.

        Raises:
            RuntimeError: the mark is unfinished.

        Example:
            gap = flower.width + 10

        See also: height, bounds
        """
        self._finished("width")
        b = self._measure()
        return 0.0 if b is None else b[2]

    @property
    def height(self) -> float:
        """The height of the area the mark covers, from bounds(); 0 for an empty mark.

        Raises:
            RuntimeError: the mark is unfinished.

        Example:
            f.size(400, int(flower.height) + 20)

        See also: width, bounds
        """
        self._finished("height")
        b = self._measure()
        return 0.0 if b is None else b[3]

    # ---- placing (contract K2)
    def _styled(self, current) -> tuple[tuple, tuple | None]:
        """The mark's ops drawn with the style *current* (style="current"), and the area they cover."""
        cache = self._restyled
        found = cache.get(current)
        if found is None:
            ops = restyle(self._ops, current)
            from .sketch import default_renderer

            found = (ops, default_renderer().ink_bounds(ops) if ops else None)
            if len(cache) >= 8:
                cache.pop(next(iter(cache)))
            cache[current] = found
        return found

    def place(self, x: float, y: float, *, scale: float | tuple[float, float] | None = None, rotate: float = 0,
              opacity: float = 1, anchor: str = "origin", width: float | None = None, height: float | None = None,
              style: str = "own") -> None:
        """Draw the mark now, with its origin at (x, y).

        The mark follows the current transform and clip, so it works inside saved_state() and translate(), inside a layer block, and inside another mark's block (marks can be made of marks). The mark itself never changes.

        The mark is moved to (x, y), then turned by rotate, then sized by scale, all around the anchor point. So with anchor="center" the centre of the mark lands on (x, y) and stays there.

        width and height size the mark from its bounds, keeping its proportions. Give one of them, and the mark is scaled to that width or height. Give both, and the mark is scaled to fit inside a box of that size and centred in it; then anchor places the box ("origin" counts as "top-left"). This happens before rotate.

        style="own" (the default) draws every part with the style it was recorded with. style="current" draws every part with the style in force now instead, so f.fill("black") then place(..., style="current") gives a black silhouette. It replaces, for each part: on closed shapes and paths, the fill, stroke, stroke width, caps, joins, miter limit and dash (a gradient fill too, and no_fill() or no_stroke() now take the fill or stroke away); on lines and open paths, the stroke, its width, caps and dash; on text, its colour, which comes from the fill as text() does (font, size and shaping stay). Pictures are unchanged. Marks inside the mark follow the same rules. Blend mode and opacity never come from the current style: opacity is the argument here.

        Arguments:
            x, y: where the anchor point lands.
            scale: one number to size both ways, or two as (sx, sy). Left out (None), the mark keeps its own size. A negative number mirrors it. 0 is an error.
            rotate: degrees to turn, clockwise on screen.
            opacity: from 0 (invisible) to 1 (solid, the default). The whole mark fades as one piece, so its overlapping parts do not show through each other.
            anchor: which point of the mark lands on (x, y). "origin" (the default) is the mark's own (0, 0). The others use bounds(): "center", "top-left", "top", "top-right", "left", "right", "bottom-left", "bottom" and "bottom-right".
            width, height: the size to make the mark, in pixels, keeping its proportions (see above). They cannot be used with scale.
            style: "own" (the default) or "current" (see above).

        Raises:
            RuntimeError: the mark is unfinished, or still being recorded.
            ValueError: the anchor or style is unknown, the mark is empty and the anchor is not "origin" or a width or height is given, opacity is outside 0 to 1, scale is 0, width or height is not above 0, or scale is given with width or height.
            TypeError: a number is not a number.

        Example:
            flower.place(150, 200)
            flower.place(400, 200, scale=0.5, rotate=15, opacity=0.6)
            flower.place(200, 150, anchor="center", width=80)
            f.fill("black")
            flower.place(300, 200, style="current")

        See also: mark, bounds, saved_state
        """
        self._finished("place()")
        x, y = _number(x, "x"), _number(y, "y")
        turn = _number(rotate, "rotate")
        alpha = _number(opacity, "opacity")
        if not 0 <= alpha <= 1:
            raise ValueError(f"mark.place(): opacity goes from 0 to 1, not {opacity!r}")
        if not isinstance(anchor, str) or anchor not in ANCHORS:
            raise ValueError(f"mark.place(): anchor must be one of {', '.join(map(repr, ANCHORS))}, not {anchor!r}")
        if style not in ("own", "current"):
            raise ValueError(f"mark.place(): style is \"own\" or \"current\", not {style!r}")
        fit = width is not None or height is not None
        if fit and scale is not None:
            raise ValueError("mark.place(): give scale, or width and height, not both")
        box_w = None if width is None else _number(width, "width")
        box_h = None if height is None else _number(height, "height")
        for v, name in ((box_w, "width"), (box_h, "height")):
            if v is not None and v <= 0:
                raise ValueError(f"mark.place(): {name} must be above 0, not {v!r}")
        at = ANCHORS[anchor]
        b = None
        if at is not None or fit:
            b = self._measure()
            if b is None:
                why = f"anchor={anchor!r}" if at is not None else "a width or height"
                raise ValueError(f"mark.place(): the mark is empty, so it has no bounds to place by {why}. "
                                 "Check mark.is_empty first.")
        if not fit:
            sx, sy = _scale(1 if scale is None else scale)
            ax, ay = (0.0, 0.0) if at is None else (b[0] + b[2] * at[0], b[1] + b[3] * at[1])
            m = Transform.translation(-ax, -ay).then(Transform.scaling(sx, sy))
        elif box_w is not None and box_h is not None:
            # "contain": the largest uniform scale that fits the box; the mark is centred in the box,
            # and the anchor places the box ("origin" is the box's top-left).
            k = min(box_w / b[2], box_h / b[3])
            fx, fy = (0.0, 0.0) if at is None else at
            m = Transform.translation(-(b[0] + b[2] / 2), -(b[1] + b[3] / 2)).then(Transform.scaling(k, k)).then(
                Transform.translation((0.5 - fx) * box_w, (0.5 - fy) * box_h))
        else:
            k = box_w / b[2] if box_w is not None else box_h / b[3]
            ax, ay = (0.0, 0.0) if at is None else (b[0] + b[2] * at[0], b[1] + b[3] * at[1])
            m = Transform.translation(-ax, -ay).then(Transform.scaling(k, k))
        m = m.then(Transform.rotation(turn)).then(Transform.translation(x, y))
        from .api import active_sketch

        sketch = active_sketch()
        sketch._require_window()
        if not self._ops or alpha == 0:
            return
        if style == "current":
            body, ink = self._styled(sketch.style)
        else:
            body, ink = self._ops, None
        if not body:
            return
        if sketch._pending_pixels:
            sketch._flush_pixel_patch()
        head = [ir.Save()] if m.is_identity else [ir.Save(), ir.Concat(m)]
        if alpha < 1 or self._group:
            if style != "current":
                ink = self._measure()
            if ink is None:                      # it paints nothing
                return
            ops = [*head, ir.BeginGroup(alpha, "normal", ink), *body, ir.EndGroup(), ir.Restore()]
        else:
            ops = [*head, *body, ir.Restore()]
        sketch.frame.extend(ops)


def restyle(ops: tuple, cur) -> tuple:
    """*ops* with every part drawn in the style *cur* instead of its own (place(style="current"), contract K2).

    Shapes (circle, ellipse, rect) and closed paths take the fill and the whole stroke style; a fill followed
    by its outline (one draw_path, end_shape, arc or SVG shape) counts as one shape. Lines, points and open
    paths take the stroke, its width, caps and dash. Text takes the text colour from the fill (contract T4).
    Pictures, transforms, clips and groups are kept. A part's blend mode, opacity, shadow and erasing stay."""
    shape = dict(fill=cur.fill, stroke=cur.stroke, stroke_width=cur.stroke_width, stroke_cap=cur.stroke_cap,
                 stroke_join=cur.stroke_join, miter_limit=cur.miter_limit, dash=cur.dash, dash_offset=cur.dash_offset)
    line = dict(stroke=cur.stroke, stroke_width=cur.stroke_width, stroke_cap=cur.stroke_cap, dash=cur.dash,
                dash_offset=cur.dash_offset)
    text_color = cur.fill or cur.stroke or WHITE
    out: list = []
    i, n = 0, len(ops)

    def stroke_of(op, path, closed: bool):
        if cur.stroke is None:
            return None
        return ir.StrokePath(path, cur.stroke, float(cur.stroke_width), cur.stroke_cap,
                             cur.stroke_join if closed else op.join, cur.miter_limit if closed else op.miter_limit,
                             cur.dash, cur.dash_offset, op.blend_mode, op.opacity, op.shadow, op.erase)

    def fill_of(op, path):
        if cur.fill is None:
            return None
        return ir.FillPath(path, cur.fill, op.blend_mode, op.opacity, op.shadow, getattr(op, "erase", None))

    while i < n:
        op = ops[i]
        t = type(op)
        if t in (ir.Circle, ir.Ellipse, ir.Rect):
            out.append(replace(op, style=op.style.with_(**shape)))
        elif t in (ir.Line, ir.Point):
            out.append(replace(op, style=op.style.with_(**line)))
        elif t is ir.Text:
            out.append(replace(op, color=text_color))
        elif t is ir.FillPath:
            nxt = ops[i + 1] if i + 1 < n else None
            outline = nxt.path if type(nxt) is ir.StrokePath else op.path
            if type(nxt) is ir.StrokePath:
                i += 1
            parts = (fill_of(op, op.path), stroke_of(nxt if type(nxt) is ir.StrokePath else _AS_STROKE(op), outline, True))
            out.extend(p for p in parts if p is not None)
        elif t is ir.StrokePath:
            if op.path.is_closed:
                parts = (fill_of(op, op.path), stroke_of(op, op.path, True))
                out.extend(p for p in parts if p is not None)
            else:
                part = stroke_of(op, op.path, False)
                if part is not None:
                    out.append(part)
        else:
            out.append(op)
        i += 1
    return tuple(out)


def _AS_STROKE(fill_op):
    """A stand-in stroke op carrying a fill's blend mode, opacity, shadow and erasing, for a fill-only shape."""
    return ir.StrokePath(fill_op.path, BLACK, 1.0, blend_mode=fill_op.blend_mode, opacity=fill_op.opacity,
                         shadow=fill_op.shadow, erase=fill_op.erase)


def mark_from_path(path, fill, stroke, stroke_width) -> Mark:
    """f.mark(path, ...): a finished mark that draws *path* with the current style, changed as given."""
    if not isinstance(path, (PathBuilder, Path)):
        raise TypeError(f"f.mark() needs a path made with f.path(), not {type(path).__name__}. "
                        "To record drawing calls, use `with f.mark() as m:`.")
    m = Mark()
    with m:
        from .api import active_sketch

        s = active_sketch()
        if fill is not NOT_GIVEN:
            s.no_fill() if fill is None else s.fill(fill)
        if stroke is not NOT_GIVEN:
            s.no_stroke() if stroke is None else s.stroke(stroke)
        if stroke_width is not None:
            s.stroke_width(stroke_width)
        s.draw_path(path)
    return m


def mark_from_svg(path: str, base_dir: str | None) -> Mark:
    """f.mark("x.svg"): a finished mark of an SVG file's shapes, each with the file's own fill and stroke.

    The file is read as f.load_svg() reads it (found next to the sketch first; the same errors). The mark's
    origin is the file's top-left (its viewBox origin), so the shapes keep their places from the file."""
    from . import svg
    from .typography import _resolve_path

    resolved = _resolve_path(path, base_dir, "f.mark()", "SVG")
    doc = svg.read(resolved, "f.mark()")
    m = Mark()
    with m:
        from .api import active_sketch

        svg.draw_shapes(doc, active_sketch())
    return m
