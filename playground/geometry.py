"""Backend-neutral geometry: affine Transform and Path (story S-018.3).

Internal in Phase 1 (PROCESS: internal capability first); the public
`p.translate()` / `p.path()` vocabulary arrives in Phase 2.

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
    segments: tuple[Segment, ...] = ()

    # ---- builders (each returns a new Path)
    def move_to(self, x: float, y: float) -> "Path":
        return Path(self.segments + (("move", (x, y)),))

    def line_to(self, x: float, y: float) -> "Path":
        return Path(self.segments + (("line", (x, y)),))

    def cubic_to(self, c1x: float, c1y: float, c2x: float, c2y: float, x: float, y: float) -> "Path":
        return Path(self.segments + (("cubic", (c1x, c1y), (c2x, c2y), (x, y)),))

    def quad_to(self, cx: float, cy: float, x: float, y: float) -> "Path":
        """Quadratic curve, stored as the equivalent cubic (renderers need only one curve kind)."""
        px, py = self.current_point()
        c1 = (px + 2 / 3 * (cx - px), py + 2 / 3 * (cy - py))
        c2 = (x + 2 / 3 * (cx - x), y + 2 / 3 * (cy - y))
        return Path(self.segments + (("cubic", c1, c2, (x, y)),))

    def close(self) -> "Path":
        return Path(self.segments + (("close",),))

    @classmethod
    def rect(cls, x: float, y: float, w: float, h: float) -> "Path":
        return cls().move_to(x, y).line_to(x + w, y).line_to(x + w, y + h).line_to(x, y + h).close()

    @classmethod
    def ellipse(cls, cx: float, cy: float, rx: float, ry: float) -> "Path":
        """Four-cubic approximation (max radial error ~0.03 %)."""
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

    # ---- queries
    def __iter__(self) -> Iterator[Segment]:
        return iter(self.segments)

    def __len__(self) -> int:
        return len(self.segments)

    @property
    def is_empty(self) -> bool:
        return not self.segments

    def current_point(self) -> Point:
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
        for seg in self.segments:
            for pt in seg[1:]:
                yield pt

    def bounds(self) -> tuple[float, float, float, float] | None:
        """(min_x, min_y, max_x, max_y) over all points incl. control points, or None."""
        pts = list(self.points())
        if not pts:
            return None
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def transformed(self, t: Transform) -> "Path":
        if t.is_identity:
            return self
        out = []
        for seg in self.segments:
            out.append((seg[0], *(t.apply(*pt) for pt in seg[1:])))
        return Path(tuple(out))
