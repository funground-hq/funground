"""PathBuilder: the object ``p.path()`` returns (story S-028, contract F3).

A chainable wrapper over the immutable :class:`playground.geometry.Path`:
every call swaps in a new Path and returns the builder itself, so a shape can
be written as one expression and then drawn (``p.draw_path``) or used as a
clip (``p.clip``) as many times as the sketch likes. The geometry underneath
never changes once built, which is what makes reuse safe.
"""
from __future__ import annotations

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
