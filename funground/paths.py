"""PathBuilder: the object ``f.path()`` returns (story S-028, contract F3).

A chainable wrapper over the immutable :class:`funground.geometry.Path`:
every call swaps in a new Path and returns the builder itself, so a shape can
be written as one expression and then drawn (``f.draw_path``) or used as a
clip (``f.clip``) as many times as the sketch likes. The geometry underneath
never changes once built, which is what makes reuse safe.
"""
from __future__ import annotations

from . import pathops
from .geometry import Path


class PathBuilder:
    __slots__ = ("_path",)

    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else Path()

    # ---- building (each returns self so calls chain)
    def move_to(self, x: float, y: float) -> "PathBuilder":
        """Start a new sub-path at (x, y) without drawing."""
        self._path = self._path.move_to(x, y)
        return self

    def line_to(self, x: float, y: float) -> "PathBuilder":
        """Straight segment from the current point to (x, y)."""
        self._require_start("line_to")
        self._path = self._path.line_to(x, y)
        return self

    def curve_to(self, cx1: float, cy1: float, cx2: float, cy2: float, x: float, y: float) -> "PathBuilder":
        """Cubic Bezier: two control points, then the end point."""
        self._require_start("curve_to")
        self._path = self._path.cubic_to(cx1, cy1, cx2, cy2, x, y)
        return self

    def quad_to(self, cx: float, cy: float, x: float, y: float) -> "PathBuilder":
        """Quadratic Bezier: one control point, then the end point."""
        self._require_start("quad_to")
        self._path = self._path.quad_to(cx, cy, x, y)
        return self

    def close(self) -> "PathBuilder":
        """Join the current point back to where the sub-path started."""
        self._require_start("close")
        self._path = self._path.close()
        return self

    # ---- shapes (each adds a closed sub-path and returns self; contract F11)
    def rect(self, x: float, y: float, w: float, h: float) -> "PathBuilder":
        """Add a rectangle; (x, y) is its top-left corner."""
        self._path = Path(self._path.segments + Path.rect(x, y, w, h).segments)
        return self

    def ellipse(self, x: float, y: float, w: float, h: float) -> "PathBuilder":
        """Add an ellipse centred on (x, y) with width w and height h."""
        self._path = Path(self._path.segments + Path.ellipse(x, y, w / 2, h / 2).segments)
        return self

    def circle(self, x: float, y: float, d: float) -> "PathBuilder":
        """Add a circle centred on (x, y) with diameter d."""
        return self.ellipse(x, y, d, d)

    def polygon(self, points) -> "PathBuilder":
        """Add a closed shape through a list of (x, y) corners."""
        pts = [(float(x), float(y)) for x, y in points]
        if len(pts) < 3:
            raise ValueError(f"polygon() needs at least 3 points, not {len(pts)}")
        segs = [("move", pts[0])] + [("line", pt) for pt in pts[1:]] + [("close",)]
        self._path = Path(self._path.segments + tuple(segs))
        return self

    # ---- booleans (each returns a NEW builder; contract F11)
    def union(self, other: "PathBuilder") -> "PathBuilder":
        """Everything either path covers."""
        return PathBuilder(pathops.union(self._path, self._other(other, "union")))

    def intersection(self, other: "PathBuilder") -> "PathBuilder":
        """Only what both paths cover."""
        return PathBuilder(pathops.intersection(self._path, self._other(other, "intersection")))

    def difference(self, other: "PathBuilder") -> "PathBuilder":
        """What this path covers, minus what *other* covers."""
        return PathBuilder(pathops.difference(self._path, self._other(other, "difference")))

    def xor(self, other: "PathBuilder") -> "PathBuilder":
        """What exactly one of the two paths covers."""
        return PathBuilder(pathops.xor(self._path, self._other(other, "xor")))

    def remove_overlap(self) -> "PathBuilder":
        """The same filled area, drawn as one clean outline with no overlapping parts."""
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

    @staticmethod
    def _other(other, name: str) -> Path:
        if not isinstance(other, PathBuilder):
            raise TypeError(f"f.path().{name}() needs another path made with f.path(), not {other!r}")
        return other._path

    # ---- queries
    @property
    def geometry(self) -> Path:
        """The immutable Path built so far (what the IR carries)."""
        return self._path

    @property
    def is_empty(self) -> bool:
        return self._path.is_empty

    @property
    def is_closed(self) -> bool:
        """Only closed paths are filled (contract F3); open ones are stroked."""
        return self._path.is_closed

    def __len__(self) -> int:
        return len(self._path)

    def __repr__(self) -> str:
        return f"PathBuilder({len(self._path)} segments{', closed' if self._path.is_closed else ''})"

    def _require_start(self, name: str) -> None:
        if self._path.is_empty:
            raise ValueError(f"{name}() needs a starting point: begin the path with move_to(x, y)")
