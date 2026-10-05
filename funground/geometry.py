"""Backend-neutral geometry: affine Transform and Path (story S-018.3).

Internal in Phase 1 (PROCESS: internal capability first); the public
`f.translate()` (S-027) and `f.path()` (S-028, `funground.paths.PathBuilder`)
vocabulary arrived in Sprint 4.

Conventions (contract C1, F1): y grows downward; angles in degrees; a
Transform maps a point (x, y) to (a*x + c*y + e, b*x + d*y + f).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterator

Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class Transform:
    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    # ---- constructors
    @classmethod
    def identity(cls) -> "Transform":
        return cls()

    @classmethod
    def translation(cls, tx: float, ty: float) -> "Transform":
        return cls(e=tx, f=ty)

    @classmethod
    def rotation(cls, degrees: float) -> "Transform":
        r = math.radians(degrees)
        cos, sin = math.cos(r), math.sin(r)
        return cls(a=cos, b=sin, c=-sin, d=cos)

    @classmethod
    def shearing(cls, x_degrees: float = 0.0, y_degrees: float = 0.0) -> "Transform":
        """x' = x + tan(x_degrees) * y ; y' = y + tan(y_degrees) * x (S-043)."""
        return cls(b=math.tan(math.radians(y_degrees)), c=math.tan(math.radians(x_degrees)))

    @classmethod
    def scaling(cls, sx: float, sy: float | None = None) -> "Transform":
        return cls(a=sx, d=sx if sy is None else sy)

    # ---- algebra
    def then(self, other: "Transform") -> "Transform":
        """Apply *self* first, then *other*."""
        return Transform(
            a=other.a * self.a + other.c * self.b,
            b=other.b * self.a + other.d * self.b,
            c=other.a * self.c + other.c * self.d,
            d=other.b * self.c + other.d * self.d,
            e=other.a * self.e + other.c * self.f + other.e,
            f=other.b * self.e + other.d * self.f + other.f,
        )

    def concat(self, local: "Transform") -> "Transform":
        """The CTM after a `translate()`/`rotate()` call: *local* applies to geometry first."""
        return local.then(self)

    def apply(self, x: float, y: float) -> Point:
        return (self.a * x + self.c * y + self.e, self.b * x + self.d * y + self.f)

    def determinant(self) -> float:
        return self.a * self.d - self.b * self.c

    def invert(self) -> "Transform":
        det = self.determinant()
        if det == 0:
            raise ValueError("transform is not invertible")
        a, b, c, d = self.d / det, -self.b / det, -self.c / det, self.a / det
        return Transform(a, b, c, d, -(a * self.e + c * self.f), -(b * self.e + d * self.f))

    @property
    def is_identity(self) -> bool:
        return self == Transform()

    def as_tuple(self) -> tuple[float, float, float, float, float, float]:
        return (self.a, self.b, self.c, self.d, self.e, self.f)


# ----------------------------------------------------------------- Path
# Segments are plain tuples so a Path is hashable and trivially serialisable:
#   ("move", (x, y)) · ("line", (x, y)) · ("cubic", (c1x, c1y), (c2x, c2y), (x, y)) · ("close",)
Segment = tuple


@dataclass(frozen=True, slots=True)
class Path:
    """The plain data of a path: a fixed list of moves, lines, curves and closes.

    You get one from PathBuilder.geometry. Most sketches never need it, because f.path() gives you a
    PathBuilder with friendlier methods. A Path cannot be changed. Every method that builds returns a new
    Path and leaves the first alone.

    The parts are in Path.segments, a tuple. Each part is a tuple: ("move", (x, y)), ("line", (x, y)),
    ("cubic", (cx1, cy1), (cx2, cy2), (x, y)) or ("close",). A Path is also a sequence: len(p)
    counts the parts and you can loop over them. y grows downward and angles are in degrees.

    Example:
        p = f.path().circle(50, 50, 60).geometry
        print(len(p), p.is_closed)

    See also: path
    """
    segments: tuple[Segment, ...] = ()

    # ---- builders (each returns a new Path)
    def move_to(self, x: float, y: float) -> "Path":
        """Make a new path with a new part started at a point.

        Arguments:
            x, y: the point.

        Returns:
            a new Path.

        See also: line_to, close
        """
        return Path(self.segments + (("move", (x, y)),))

    def line_to(self, x: float, y: float) -> "Path":
        """Make a new path with a straight line added.

        Arguments:
            x, y: the end of the line.

        Returns:
            a new Path.

        See also: move_to, cubic_to
        """
        return Path(self.segments + (("line", (x, y)),))

    def cubic_to(self, c1x: float, c1y: float, c2x: float, c2y: float, x: float, y: float) -> "Path":
        """Make a new path with a cubic Bezier curve added.

        Arguments:
            c1x, c1y: the first control point.
            c2x, c2y: the second control point.
            x, y: the end of the curve.

        Returns:
            a new Path.

        See also: quad_to, line_to
        """
        return Path(self.segments + (("cubic", (c1x, c1y), (c2x, c2y), (x, y)),))

    def quad_to(self, cx: float, cy: float, x: float, y: float) -> "Path":
        """Make a new path with a quadratic Bezier curve added.

        It is stored as the same curve written as a cubic, so a path only needs one kind of curve.

        Arguments:
            cx, cy: the control point.
            x, y: the end of the curve.

        Returns:
            a new Path.

        Raises:
            ValueError: if the path has no current point.

        See also: cubic_to
        """
        px, py = self.current_point()
        c1 = (px + 2 / 3 * (cx - px), py + 2 / 3 * (cy - py))
        c2 = (x + 2 / 3 * (cx - x), y + 2 / 3 * (cy - y))
        return Path(self.segments + (("cubic", c1, c2, (x, y)),))

    def close(self) -> "Path":
        """Make a new path with the current part closed.

        Returns:
            a new Path.

        See also: move_to, is_closed
        """
        return Path(self.segments + (("close",),))

    @classmethod
    def rect(cls, x: float, y: float, w: float, h: float) -> "Path":
        """Make a new path that is one closed rectangle.

        Arguments:
            x, y: the top left corner.
            w, h: the width and the height.

        Returns:
            a new Path.

        See also: rounded_rect, ellipse
        """
        return cls().move_to(x, y).line_to(x + w, y).line_to(x + w, y + h).line_to(x, y + h).close()

    @classmethod
    def rounded_rect(cls, x: float, y: float, w: float, h: float, radii: tuple[float, float, float, float]) -> "Path":
        """Make a new path that is one closed rectangle with rounded corners.

        Arguments:
            x, y: the top left corner.
            w, h: the width and the height.
            radii: four corner radii: top left, top right, bottom right, bottom left. They must already be no more than half the shorter side. A radius of 0 gives a sharp corner.

        Returns:
            a new Path.

        See also: rect
        """
        tl, tr, br, bl = radii
        path = cls()
        corners = (
            (tl, x + tl, y + tl, 180, (x, y)),
            (tr, x + w - tr, y + tr, 270, (x + w, y)),
            (br, x + w - br, y + h - br, 0, (x + w, y + h)),
            (bl, x + bl, y + h - bl, 90, (x, y + h)),
        )
        for r, cx, cy, start, corner in corners:
            if r > 0:
                path = path.arc_to(cx, cy, r, r, start, start + 90)
            else:
                path = path.move_to(*corner) if path.is_empty else path.line_to(*corner)
        return path.close()

    @classmethod
    def ellipse(cls, cx: float, cy: float, rx: float, ry: float) -> "Path":
        """Make a new path that is one closed ellipse.

        It is built from four curves, and is within about 0.03 per cent of a true ellipse.

        Arguments:
            cx, cy: the centre.
            rx, ry: the radii across and down.

        Returns:
            a new Path.

        See also: rect
        """
        k = 0.5522847498307936
        return (
            cls()
            .move_to(cx + rx, cy)
            .cubic_to(cx + rx, cy + ry * k, cx + rx * k, cy + ry, cx, cy + ry)
            .cubic_to(cx - rx * k, cy + ry, cx - rx, cy + ry * k, cx - rx, cy)
            .cubic_to(cx - rx, cy - ry * k, cx - rx * k, cy - ry, cx, cy - ry)
            .cubic_to(cx + rx * k, cy - ry, cx + rx, cy - ry * k, cx + rx, cy)
            .close()
        )

    def arc_to(self, cx: float, cy: float, rx: float, ry: float, start: float, stop: float) -> "Path":
        """Make a new path with an arc of an ellipse added.

        The point at angle a is (cx + rx * cos a, cy + ry * sin a), so 0 degrees is right and 90 degrees is
        straight down. The arc begins with a line from the current point to the start of the arc, or with a
        move if the path is empty.

        Arguments:
            cx, cy: the centre of the ellipse.
            rx, ry: the radii across and down.
            start, stop: the angles where the arc begins and ends, in degrees, turning clockwise on the screen. If stop is not above start, only the line to the start is added.

        Returns:
            a new Path.

        See also: ellipse, line_to
        """
        start_pt = (cx + rx * math.cos(math.radians(start)), cy + ry * math.sin(math.radians(start)))
        path = self.move_to(*start_pt) if self.is_empty else self.line_to(*start_pt)
        sweep = stop - start
        if sweep <= 0:
            return path
        pieces = max(1, math.ceil(sweep / 90 - 1e-9))
        step = math.radians(sweep / pieces)
        k = 4 / 3 * math.tan(step / 4)
        a = math.radians(start)
        for _ in range(pieces):
            b = a + step
            ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
            path = path.cubic_to(
                cx + rx * (ca - k * sa), cy + ry * (sa + k * ca),
                cx + rx * (cb + k * sb), cy + ry * (sb - k * cb),
                cx + rx * cb, cy + ry * sb,
            )
            a = b
        return path

    # ---- queries
    def __iter__(self) -> Iterator[Segment]:
        return iter(self.segments)

    def __len__(self) -> int:
        return len(self.segments)

    @property
    def is_empty(self) -> bool:
        """Whether the path has no parts.

        Returns:
            True when there are no parts, otherwise False.

        See also: is_closed
        """
        return not self.segments

    @property
    def is_closed(self) -> bool:
        """Whether every part that draws something ends with a close.

        Only closed shapes are filled. A move at the end on its own draws nothing, and does not count.

        Returns:
            True when the path is closed. An empty path is not closed.

        See also: close, is_empty
        """
        pending = False  # a sub-path with segments that has not been closed yet
        for seg in self.segments:
            k = seg[0]
            if k == "move":
                if pending:
                    return False
            elif k == "close":
                pending = False
            else:
                pending = True
        return bool(self.segments) and not pending

    def current_point(self) -> Point:
        """The point where the path now ends.

        Returns:
            an (x, y) pair.

        Raises:
            ValueError: if the path is empty, so it has no current point.

        See also: move_to, points
        """
        start: Point | None = None
        current: Point | None = None
        for seg in self.segments:
            if seg[0] == "move":
                start = current = seg[1]
            elif seg[0] == "close":
                current = start
            else:
                current = seg[-1]
        if current is None:
            raise ValueError("path has no current point (start with move_to)")
        return current

    def points(self) -> Iterator[Point]:
        """Every point in the path, including curve control points, in order.

        Returns:
            an iterator of (x, y) pairs.

        See also: bounds, current_point
        """
        for seg in self.segments:
            for pt in seg[1:]:
                yield pt

    def bounds(self) -> tuple[float, float, float, float] | None:
        """The box that holds every point of the path, including curve control points.

        Because it counts control points, a curved path may have a smaller real extent. PathBuilder.bounds()
        gives the exact one.

        Returns:
            (min_x, min_y, max_x, max_y), or None for an empty path.

        See also: points
        """
        pts = list(self.points())
        if not pts:
            return None
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def transformed(self, t: Transform) -> "Path":
        """Make a new path with every point moved by a transform.

        Arguments:
            t: a Transform from funground.geometry, which turns a point (x, y) into (a*x + c*y + e, b*x + d*y + f).

        Returns:
            a new Path. It is this path itself when the transform changes nothing.

        See also: bounds
        """
        if t.is_identity:
            return self
        out = []
        for seg in self.segments:
            out.append((seg[0], *(t.apply(*pt) for pt in seg[1:])))
        return Path(tuple(out))


def rect_radii(radii: tuple, w: float, h: float, name: str = "rect") -> tuple[float, float, float, float]:
    """Four corner radii (top-left, top-right, bottom-right, bottom-left) from 0, 1 or 4 numbers.

    Each is cut down to half the shorter side (as p5 does), so neighbouring corners never overlap.
    Returns (0, 0, 0, 0) for no radii. Contract F14."""
    if len(radii) == 0:
        return (0.0, 0.0, 0.0, 0.0)
    if len(radii) == 1:
        four = tuple(radii) * 4
    elif len(radii) == 4:
        four = tuple(radii)
    else:
        raise ValueError(f"{name}() takes no radius, one radius or four radii, not {len(radii)}")
    if any(r < 0 for r in four):
        raise ValueError(f"{name}() corner radii cannot be negative")
    limit = min(abs(w), abs(h)) / 2
    return tuple(float(min(r, limit)) for r in four)


# ----------------------------------------------------------------- sampling (S-104, contract T16)
FLATNESS = 0.01      # pixels: a curve is cut into straight pieces that stay this close to it


def _flatten_cubic(p0, c1, c2, p3, tolerance: float) -> list[Point]:
    """Points along a cubic after its start, in equal steps of t. The step count keeps every
    straight piece within *tolerance* of the curve (standard bound for a uniform split)."""
    ddx = max(abs(p0[0] - 2 * c1[0] + c2[0]), abs(c1[0] - 2 * c2[0] + p3[0]))
    ddy = max(abs(p0[1] - 2 * c1[1] + c2[1]), abs(c1[1] - 2 * c2[1] + p3[1]))
    dd = math.hypot(ddx, ddy)
    n = max(1, math.ceil(math.sqrt(0.75 * dd / tolerance)))
    out = []
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        out.append((
            u * u * u * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t * t * t * p3[0],
            u * u * u * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t * t * t * p3[1],
        ))
    out[-1] = p3
    return out


def contours(path: Path, tolerance: float = FLATNESS) -> list[tuple[list[Point], bool]]:
    """The sub-paths of *path* as polylines (curves flattened to *tolerance*), each with a flag
    for whether it was closed. A closing segment is added as a straight piece back to the start."""
    result: list[tuple[list[Point], bool]] = []
    pts: list[Point] = []
    closed = False

    def finish() -> None:
        if len(pts) > 0:
            result.append((list(pts), closed))

    for seg in path.segments:
        kind = seg[0]
        if kind == "move":
            finish()
            pts, closed = [seg[1]], False
        elif kind == "line":
            if not pts:
                pts = [seg[1]]
            else:
                pts.append(seg[1])
        elif kind == "cubic":
            if not pts:
                pts = [seg[1]]
            pts.extend(_flatten_cubic(pts[-1], seg[1], seg[2], seg[3], tolerance))
        elif kind == "close":
            if pts:
                if pts[-1] != pts[0]:
                    pts.append(pts[0])
                closed = True
                finish()
                pts, closed = [], False
    finish()
    return result


def sample_path(path: Path, spacing: float, tolerance: float = FLATNESS) -> list[Point]:
    """Points every *spacing* pixels along each sub-path of *path*, starting at its start point.
    The leftover distance carries across the pieces of a sub-path; each sub-path starts afresh."""
    out: list[Point] = []
    for pts, closed in contours(path, tolerance):
        first = len(out)
        out.append(pts[0])
        need = spacing                      # distance still to walk before the next point
        for a, b in zip(pts, pts[1:]):
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            if length == 0:
                continue
            walked = 0.0
            while length - walked >= need:
                walked += need
                t = walked / length
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
                need = spacing
            need -= length - walked
        if closed and len(out) - first > 1 and math.hypot(out[-1][0] - pts[0][0], out[-1][1] - pts[0][1]) < 1e-6 * spacing:
            out.pop()                       # the walk ended exactly on the start: do not repeat it
    return out
