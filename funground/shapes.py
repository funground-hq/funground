"""The shape being built between begin_shape() and end_shape() (S-028, S-074).

Vertices are *recorded*, not drawn immediately, because a Catmull-Rom curve
(``curve_vertex``) needs the points on both sides of each segment. At
``end_shape()`` the record becomes one immutable :class:`Path`:

- ``vertex`` joins with straight lines; ``bezier_vertex`` / ``quadratic_vertex`` add
  curve segments from the previous point (contract F3/F9).
- A run of ``curve_vertex`` points is a Catmull-Rom spline as in Processing: the
  first and last points of the run only steer the curve; it is drawn from the
  second point to the next-to-last. Fewer than four points draw nothing (with a
  warning). ``curve_tightness`` 0 is Catmull-Rom, 1 gives straight lines.
- ``begin_contour``/``end_contour`` add closed holes. Holes are wound opposite to
  the outline automatically, so with the non-zero fill rule they are always cut out.
"""
from __future__ import annotations

import warnings

from .capabilities import FungroundWarning
from .geometry import Path


def catmull_rom_controls(p0, p1, p2, p3, tightness: float):
    """Bezier control points for the Catmull-Rom segment p1 -> p2 (Processing's curveTightness)."""
    k = (1 - tightness) / 6
    c1 = (p1[0] + k * (p2[0] - p0[0]), p1[1] + k * (p2[1] - p0[1]))
    c2 = (p2[0] - k * (p3[0] - p1[0]), p2[1] - k * (p3[1] - p1[1]))
    return c1, c2


class ShapeBuilder:
    """Records one shape: an outline plus any number of holes (contours)."""

    def __init__(self) -> None:
        self.contours: list[list[tuple]] = [[]]   # contours[0] is the outline
        self.in_contour = False

    @property
    def _entries(self) -> list[tuple]:
        return self.contours[-1] if self.in_contour else self.contours[0]

    # ---- recording
    def vertex(self, x: float, y: float) -> None:
        self._entries.append(("vertex", (x, y)))

    def bezier_vertex(self, cx1, cy1, cx2, cy2, x, y) -> None:
        self._require_point("bezier_vertex")
        self._entries.append(("bezier", (cx1, cy1), (cx2, cy2), (x, y)))

    def quadratic_vertex(self, cx, cy, x, y) -> None:
        self._require_point("quadratic_vertex")
        self._entries.append(("quad", (cx, cy), (x, y)))

    def curve_vertex(self, x: float, y: float) -> None:
        self._entries.append(("curve", (x, y)))

    def begin_contour(self) -> None:
        if self.in_contour:
            raise RuntimeError("f.begin_contour() called again before f.end_contour(); finish the first hole.")
        if not self.contours[0]:
            raise RuntimeError("f.begin_contour() comes after the outline's vertices: add them first.")
        self.contours.append([])
        self.in_contour = True

    def end_contour(self) -> None:
        if not self.in_contour:
            raise RuntimeError("f.end_contour() without f.begin_contour().")
        self.in_contour = False

    def _require_point(self, name: str) -> None:
        if not self._entries:
            raise RuntimeError(f"f.{name}() needs a starting point: call f.vertex(x, y) first.")

    # ---- building
    def build(self, close: bool, tightness: float) -> Path:
        if self.in_contour:
            raise RuntimeError("f.end_shape() inside a hole: call f.end_contour() first.")
        outline = _contour_path(self.contours[0], tightness)
        if close and not outline.is_empty:
            outline = outline.close()
        segments = list(outline.segments)
        outline_sign = _signed_area(outline)
        for entries in self.contours[1:]:
            hole = _contour_path(entries, tightness)
            if hole.is_empty:
                continue
            if outline_sign and _signed_area(hole) * outline_sign > 0:
                hole = _reversed(hole)                # wind opposite to the outline: a hole
            segments += list(hole.close().segments)
        return Path(tuple(segments))


def _contour_path(entries: list[tuple], tightness: float) -> Path:
    path = Path()
    run: list[tuple[float, float]] = []

    def to(pt):
        nonlocal path
        path = path.move_to(*pt) if path.is_empty else path.line_to(*pt)

    def flush():
        nonlocal path
        if not run:
            return
        if len(run) < 4:
            warnings.warn(
                f"f.curve_vertex() needs at least 4 points in a row to draw a curve; got {len(run)}, "
                "so they were skipped. The first and last points only steer the curve.",
                FungroundWarning, stacklevel=5,
            )
        else:
            to(run[1])
            for i in range(1, len(run) - 2):
                c1, c2 = catmull_rom_controls(run[i - 1], run[i], run[i + 1], run[i + 2], tightness)
                path = path.cubic_to(*c1, *c2, *run[i + 1])
        run.clear()

    for entry in entries:
        kind = entry[0]
        if kind == "curve":
            run.append(entry[1])
            continue
        flush()
        if kind == "vertex":
            to(entry[1])
        elif path.is_empty:
            raise RuntimeError(f"f.{'bezier_vertex' if kind == 'bezier' else 'quadratic_vertex'}() "
                               "needs a starting point: call f.vertex(x, y) first.")
        elif kind == "bezier":
            path = path.cubic_to(*entry[1], *entry[2], *entry[3])
        elif kind == "quad":
            path = path.quad_to(*entry[1], *entry[2])
    flush()
    return path


def _signed_area(path: Path) -> float:
    """Shoelace area of the polygon through every point (control points too): sign = winding."""
    pts = list(path.points())
    if len(pts) < 3:
        return 0.0
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])) / 2


def _reversed(path: Path) -> Path:
    """The same single sub-path, travelled backwards."""
    segs = [s for s in path.segments if s[0] != "close"]
    points = [segs[0][1]] + [s[-1] for s in segs[1:]]
    out = Path().move_to(*points[-1])
    for i in range(len(segs) - 1, 0, -1):
        seg, prev = segs[i], points[i - 1]
        if seg[0] == "line":
            out = out.line_to(*prev)
        else:                                          # cubic: swap the control points
            out = out.cubic_to(*seg[2], *seg[1], *prev)
    return out


# ---- point and tangent helpers (Processing bezierPoint / curvePoint)
def bezier_point(a: float, b: float, c: float, d: float, t: float) -> float:
    u = 1 - t
    return u * u * u * a + 3 * u * u * t * b + 3 * u * t * t * c + t * t * t * d


def bezier_tangent(a: float, b: float, c: float, d: float, t: float) -> float:
    u = 1 - t
    return 3 * u * u * (b - a) + 6 * u * t * (c - b) + 3 * t * t * (d - c)


def curve_point(a: float, b: float, c: float, d: float, t: float, tightness: float = 0.0) -> float:
    k = (1 - tightness) / 6
    return bezier_point(b, b + k * (c - a), c - k * (d - b), c, t)


def curve_tangent(a: float, b: float, c: float, d: float, t: float, tightness: float = 0.0) -> float:
    k = (1 - tightness) / 6
    return bezier_tangent(b, b + k * (c - a), c - k * (d - b), c, t)
