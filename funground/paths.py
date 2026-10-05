"""PathBuilder: the object ``f.path()`` returns (story S-028, contract F3).

A chainable wrapper over the immutable :class:`funground.geometry.Path`:
every call swaps in a new Path and returns the builder itself, so a shape can
be written as one expression and then drawn (``f.draw_path``) or used as a
clip (``f.clip``) as many times as the sketch likes. The geometry underneath
never changes once built, which is what makes reuse safe.
"""
from __future__ import annotations

from . import pathops
from .geometry import Path, Transform, rect_radii


class PathBuilder:
    """A path that you build step by step, then draw, clip with, cut, outline or measure.

    You get one from f.path(), f.text_path() and f.svg_paths(). Draw it with f.draw_path(p) or use it as
    a clip with f.clip(p). A path does not draw anything until you do that, so you can reuse it as often
    as you like.

    Most methods change the path and give it back, so you can chain calls: f.path().move_to(0, 0).line_to(50, 0).
    The building methods are move_to, line_to, curve_to, quad_to, close, rect, ellipse, circle and
    polygon. They change this builder. The methods that make a new shape (union, intersection, difference,
    xor, remove_overlap, expand_stroke, translate, scale, rotate and copy) give you a new builder and leave
    this one alone. The operators do the same: a | b is union, a & b is intersection, a - b and a % b are
    difference, and a ^ b is xor.

    Only closed paths are filled. An open path is stroked.

    Example:
        star = f.path().polygon([(0, -50), (15, -15), (50, -10), (22, 10), (30, 45), (0, 25), (-30, 45), (-22, 10), (-50, -10), (-15, -15)])
        f.translate(200, 200)
        f.draw_path(star)

    See also: path, draw_path, clip, text_path, svg_paths
    """
    __slots__ = ("_path",)

    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else Path()

    # ---- building (each returns self so calls chain)
    def move_to(self, x: float, y: float) -> "PathBuilder":
        """Start a new part of the path at a point, without drawing.

        Arguments:
            x, y: the point.

        Returns:
            this builder, changed.

        Example:
            p = f.path().move_to(10, 10).line_to(90, 10)

        See also: line_to, close
        """
        self._path = self._path.move_to(x, y)
        return self

    def line_to(self, x: float, y: float) -> "PathBuilder":
        """Add a straight line from the current point to a new point.

        Arguments:
            x, y: the end of the line.

        Returns:
            this builder, changed.

        Raises:
            ValueError: if the path has no starting point yet. Begin with move_to().

        Example:
            p = f.path().move_to(10, 10).line_to(90, 10).line_to(50, 80).close()

        See also: move_to, curve_to, close
        """
        self._require_start("line_to")
        self._path = self._path.line_to(x, y)
        return self

    def curve_to(self, cx1: float, cy1: float, cx2: float, cy2: float, x: float, y: float) -> "PathBuilder":
        """Add a smooth curve from the current point to a new point (a cubic Bezier curve).

        The two control points pull the curve towards them.

        Arguments:
            cx1, cy1: the first control point.
            cx2, cy2: the second control point.
            x, y: the end of the curve.

        Returns:
            this builder, changed.

        Raises:
            ValueError: if the path has no starting point yet. Begin with move_to().

        Example:
            p = f.path().move_to(10, 90).curve_to(10, 10, 90, 10, 90, 90)

        See also: quad_to, line_to
        """
        self._require_start("curve_to")
        self._path = self._path.cubic_to(cx1, cy1, cx2, cy2, x, y)
        return self

    def quad_to(self, cx: float, cy: float, x: float, y: float) -> "PathBuilder":
        """Add a curve from the current point to a new point, pulled towards one control point (a quadratic Bezier curve).

        Arguments:
            cx, cy: the control point.
            x, y: the end of the curve.

        Returns:
            this builder, changed.

        Raises:
            ValueError: if the path has no starting point yet. Begin with move_to().

        Example:
            p = f.path().move_to(10, 90).quad_to(50, 10, 90, 90)

        See also: curve_to, line_to
        """
        self._require_start("quad_to")
        self._path = self._path.quad_to(cx, cy, x, y)
        return self

    def close(self) -> "PathBuilder":
        """Join the current point back to where the part of the path began.

        Only closed paths are filled.

        Returns:
            this builder, changed.

        Raises:
            ValueError: if the path has no starting point yet. Begin with move_to().

        Example:
            p = f.path().move_to(10, 10).line_to(90, 10).line_to(50, 80).close()

        See also: move_to, line_to, is_closed
        """
        self._require_start("close")
        self._path = self._path.close()
        return self

    # ---- shapes (each adds a closed sub-path and returns self; contract F11)
    def rect(self, x: float, y: float, w: float, h: float, *radii: float) -> "PathBuilder":
        """Add a rectangle as a closed part of the path.

        Arguments:
            x, y: the top left corner.
            w, h: the width and the height.
            *radii: no radius, one radius for all four corners, or four radii (top left, top right, bottom right, bottom left). A radius is cut down to half the shorter side.

        Returns:
            this builder, changed.

        Raises:
            ValueError: if the number of radii is not 0, 1 or 4, or a radius is negative.

        Example:
            p = f.path().rect(10, 10, 80, 50, 8)

        See also: ellipse, circle, polygon
        """
        r = rect_radii(radii, w, h, "rect")
        if any(r):
            if w < 0:
                x, w = x + w, -w
            if h < 0:
                y, h = y + h, -h
            shape = Path.rounded_rect(x, y, w, h, rect_radii(r, w, h, "rect"))
        else:
            shape = Path.rect(x, y, w, h)
        self._path = Path(self._path.segments + shape.segments)
        return self

    def ellipse(self, x: float, y: float, w: float, h: float) -> "PathBuilder":
        """Add an ellipse as a closed part of the path.

        Arguments:
            x, y: the centre.
            w, h: the width and the height.

        Returns:
            this builder, changed.

        Example:
            p = f.path().ellipse(50, 50, 80, 40)

        See also: circle, rect
        """
        self._path = Path(self._path.segments + Path.ellipse(x, y, w / 2, h / 2).segments)
        return self

    def circle(self, x: float, y: float, d: float) -> "PathBuilder":
        """Add a circle as a closed part of the path.

        Arguments:
            x, y: the centre.
            d: the diameter, which is the distance across.

        Returns:
            this builder, changed.

        Example:
            p = f.path().circle(50, 50, 60)

        See also: ellipse, rect
        """
        return self.ellipse(x, y, d, d)

    def polygon(self, points) -> "PathBuilder":
        """Add a closed shape through a list of corners.

        Arguments:
            points: a list of at least 3 (x, y) pairs.

        Returns:
            this builder, changed.

        Raises:
            ValueError: if there are fewer than 3 points.

        Example:
            p = f.path().polygon([(50, 10), (90, 80), (10, 80)])

        See also: rect, line_to
        """
        pts = [(float(x), float(y)) for x, y in points]
        if len(pts) < 3:
            raise ValueError(f"polygon() needs at least 3 points, not {len(pts)}")
        segs = [("move", pts[0])] + [("line", pt) for pt in pts[1:]] + [("close",)]
        self._path = Path(self._path.segments + tuple(segs))
        return self

    # ---- booleans (each returns a NEW builder; contract F11)
    def union(self, other: "PathBuilder") -> "PathBuilder":
        """Make a new path of everything that either path covers.

        Arguments:
            other: another path made with f.path().

        Returns:
            a new PathBuilder. Neither original is changed.

        Raises:
            TypeError: if other is not a path from f.path().

        Example:
            both = f.path().circle(40, 50, 60).union(f.path().circle(70, 50, 60))

        See also: intersection, difference, xor
        """
        return PathBuilder(pathops.union(self._path, self._other(other, "union")))

    def intersection(self, other: "PathBuilder") -> "PathBuilder":
        """Make a new path of only what both paths cover.

        Arguments:
            other: another path made with f.path().

        Returns:
            a new PathBuilder. Neither original is changed.

        Raises:
            TypeError: if other is not a path from f.path().

        Example:
            lens = f.path().circle(40, 50, 60).intersection(f.path().circle(70, 50, 60))

        See also: union, difference, xor
        """
        return PathBuilder(pathops.intersection(self._path, self._other(other, "intersection")))

    def difference(self, other: "PathBuilder") -> "PathBuilder":
        """Make a new path of what this path covers, minus what another path covers.

        Arguments:
            other: another path made with f.path().

        Returns:
            a new PathBuilder. Neither original is changed.

        Raises:
            TypeError: if other is not a path from f.path().

        Example:
            ring = f.path().circle(50, 50, 80).difference(f.path().circle(50, 50, 40))

        See also: union, intersection, xor
        """
        return PathBuilder(pathops.difference(self._path, self._other(other, "difference")))

    def xor(self, other: "PathBuilder") -> "PathBuilder":
        """Make a new path of what exactly one of the two paths covers.

        Arguments:
            other: another path made with f.path().

        Returns:
            a new PathBuilder. Neither original is changed.

        Raises:
            TypeError: if other is not a path from f.path().

        Example:
            p = f.path().circle(40, 50, 60).xor(f.path().circle(70, 50, 60))

        See also: union, intersection, difference
        """
        return PathBuilder(pathops.xor(self._path, self._other(other, "xor")))

    def remove_overlap(self) -> "PathBuilder":
        """Make a new path that fills the same area, drawn as one clean outline with no overlapping parts.

        Returns:
            a new PathBuilder. This one is not changed.

        Example:
            clean = f.path().circle(40, 50, 60).circle(70, 50, 60).remove_overlap()

        See also: union, expand_stroke
        """
        return PathBuilder(pathops.remove_overlap(self._path))

    def __or__(self, other: "PathBuilder") -> "PathBuilder":
        return self.union(other)

    def __and__(self, other: "PathBuilder") -> "PathBuilder":
        return self.intersection(other)

    def __sub__(self, other: "PathBuilder") -> "PathBuilder":
        return self.difference(other)

    def __mod__(self, other: "PathBuilder") -> "PathBuilder":
        """``a % b`` is ``a - b``: DrawBot writes difference with ``%`` (D-038)."""
        return self.difference(other)

    def __xor__(self, other: "PathBuilder") -> "PathBuilder":
        return self.xor(other)

    # ---- outlines, queries and moves (each returns a NEW builder or a value; contract F12)
    def expand_stroke(self, width: float, cap: str = "round", join: str = "round",
                      miter_limit: float = 10, dash=None) -> "PathBuilder":
        """Make a new path that is the outline a stroke would paint, so you can fill, cut or clip with it.

        Open parts of the path are included. Overlaps are removed.

        Arguments:
            width: how thick the stroke is. It must be more than 0.
            cap: the ends of open parts: "round", "square" or "butt". It is "round" at first.
            join: the corners: "round", "miter" or "bevel". It is "round" at first.
            miter_limit: how long a pointed corner may get, at least 1. It is 10 at first.
            dash: None for a solid line, or a length, or a list of lengths for dashes and gaps, such as [10, 5]. It is None at first.

        Returns:
            a new closed PathBuilder.

        Raises:
            ValueError: if width, cap, join, miter_limit or dash is not allowed.

        Example:
            line = f.path().move_to(10, 50).line_to(90, 50)
            outline = line.expand_stroke(8, cap="butt", dash=[10, 5])

        See also: remove_overlap, contains
        """
        return PathBuilder(pathops.expand_stroke(self._path, width, cap, join, miter_limit, dash))

    def bounds(self):
        """The box that exactly holds the path.

        Returns:
            (x, y, w, h), the top left corner and the size, or None when the path has no lines or curves.

        Example:
            x, y, w, h = f.path().circle(50, 50, 60).bounds()

        See also: contains
        """
        return pathops.exact_bounds(self._path)

    def contains(self, x: float, y: float) -> bool:
        """Whether a point is inside the shape that the path fills.

        Arguments:
            x, y: the point.

        Returns:
            True when the point is inside what is filled, otherwise False.

        Example:
            button = f.path().rect(10, 10, 80, 30)
            if button.contains(f.mouse_x, f.mouse_y):
                f.fill("gold")

        See also: bounds
        """
        return pathops.contains(self._path, x, y)

    def translate(self, dx: float, dy: float) -> "PathBuilder":
        """Make a new path that is this path moved.

        Arguments:
            dx, dy: how far to move it across and down.

        Returns:
            a new PathBuilder. This one is not changed.

        Example:
            moved = f.path().circle(0, 0, 40).translate(100, 100)

        See also: scale, rotate
        """
        return PathBuilder(self._path.transformed(Transform.translation(dx, dy)))

    def scale(self, sx: float, sy: float | None = None) -> "PathBuilder":
        """Make a new path that is this path scaled about the point (0, 0).

        Arguments:
            sx: how much to scale across. 2 makes it twice as wide.
            sy: how much to scale down. If you leave it out, it is the same as sx.

        Returns:
            a new PathBuilder. This one is not changed.

        Example:
            big = f.path().circle(0, 0, 40).scale(2)

        See also: translate, rotate
        """
        return PathBuilder(self._path.transformed(Transform.scaling(sx, sy)))

    def rotate(self, degrees: float, cx: float = 0, cy: float = 0) -> "PathBuilder":
        """Make a new path that is this path turned about a point.

        Arguments:
            degrees: how far to turn it. A positive angle turns clockwise on the screen.
            cx, cy: the point to turn about. It is (0, 0) at first.

        Returns:
            a new PathBuilder. This one is not changed.

        Example:
            bar = f.path().rect(-40, -5, 80, 10).rotate(45)

        See also: translate, scale
        """
        t = (Transform.translation(-cx, -cy).then(Transform.rotation(degrees))
             .then(Transform.translation(cx, cy)))
        return PathBuilder(self._path.transformed(t))

    def copy(self) -> "PathBuilder":
        """Make a new builder with the same path.

        Building on the copy does not change the original.

        Returns:
            a new PathBuilder.

        Example:
            a = f.path().move_to(0, 0).line_to(50, 0)
            b = a.copy().line_to(50, 50)    # a is not changed

        See also: translate
        """
        return PathBuilder(self._path)

    @staticmethod
    def _other(other, name: str) -> Path:
        if not isinstance(other, PathBuilder):
            raise TypeError(f"f.path().{name}() needs another path made with f.path(), not {other!r}")
        return other._path

    # ---- queries
    @property
    def geometry(self) -> Path:
        """The plain path data built so far.

        It cannot be changed. It is what funground draws.

        Returns:
            a Path (from funground.geometry).

        See also: is_empty, is_closed
        """
        return self._path

    @property
    def is_empty(self) -> bool:
        """Whether nothing has been added to the path.

        Returns:
            True when the path has no parts, otherwise False.

        Example:
            print(f.path().is_empty)    # True

        See also: is_closed
        """
        return self._path.is_empty

    @property
    def is_closed(self) -> bool:
        """Whether every part of the path that draws something is closed.

        Only closed paths are filled. Open ones are stroked.

        Returns:
            True when the path is closed, otherwise False. An empty path is not closed.

        Example:
            print(f.path().circle(50, 50, 60).is_closed)    # True

        See also: close, is_empty
        """
        return self._path.is_closed

    def __len__(self) -> int:
        return len(self._path)

    def __repr__(self) -> str:
        return f"PathBuilder({len(self._path)} segments{', closed' if self._path.is_closed else ''})"

    def _require_start(self, name: str) -> None:
        if self._path.is_empty:
            raise ValueError(f"{name}() needs a starting point: begin the path with move_to(x, y)")
