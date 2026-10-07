"""Ground: the composition surface (story S-132 part 1, contract G1).

``Ground`` is the canvas as a rectangle, with its margins. ``Cell`` is one box of a grid. Both are
small frozen values with the same names for the edges (left, top, right, bottom, width, height,
cx, cy), so a cell can be used as the ``area`` of another grid.
"""
from __future__ import annotations

from dataclasses import dataclass

POINTS_PER_INCH = 72.0
MM_PER_INCH = 25.4


def mm(n: float) -> float:
    """Millimetres as funground units (points, 72 to the inch)."""
    _number(n, "f.mm()")
    return n * POINTS_PER_INCH / MM_PER_INCH


def inch(n: float) -> float:
    """Inches as funground units (points, 72 to the inch)."""
    _number(n, "f.inch()")
    return n * POINTS_PER_INCH


def _number(value, where: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{where} needs a number, not {value!r}")


def check_margin(margin, width: float, height: float) -> tuple[float, float, float, float]:
    """Return margin as (top, right, bottom, left). Raise if it is wrong or leaves no content area."""
    if isinstance(margin, (tuple, list)):
        if len(margin) != 4:
            raise ValueError(f"margin needs one number or four, (top, right, bottom, left), not {len(margin)} values")
        top, right, bottom, left = margin
    else:
        top = right = bottom = left = margin
    for value in (top, right, bottom, left):
        _number(value, "margin")
        if value < 0:
            raise ValueError(f"margin cannot be negative, but got {margin!r}")
    if left + right >= width:
        raise ValueError(f"the left and right margins ({left} + {right}) leave no room in a width of {width}")
    if top + bottom >= height:
        raise ValueError(f"the top and bottom margins ({top} + {bottom}) leave no room in a height of {height}")
    return (top, right, bottom, left)


@dataclass(frozen=True)
class Ground:
    """A rectangle with margins. ``f.ground`` is the whole canvas; ``f.ground.content`` is inside the margins."""

    left: float
    top: float
    width: float
    height: float
    margin: tuple = (0, 0, 0, 0)

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def bottom(self) -> float:
        return self.top + self.height

    @property
    def cx(self) -> float:
        return self.left + self.width / 2

    @property
    def cy(self) -> float:
        return self.top + self.height / 2

    @property
    def content(self) -> "Ground":
        """The area inside the margins. With no margin it is this same object. Its own margin is (0, 0, 0, 0)."""
        top, right, bottom, left = self.margin
        if not (top or right or bottom or left):
            return self
        return Ground(self.left + left, self.top + top, self.width - left - right, self.height - top - bottom)

    def __repr__(self) -> str:
        return (f"Ground(left={self.left}, top={self.top}, right={self.right}, bottom={self.bottom}, "
                f"width={self.width}, height={self.height}, margin={self.margin})")


@dataclass(frozen=True)
class Cell:
    """One box of a grid. x, y is its top-left corner; w, h its size. Aliases make it usable as an area."""

    x: float
    y: float
    w: float
    h: float
    col: int
    row: int
    index: int

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    left = property(lambda self: self.x)
    top = property(lambda self: self.y)
    width = property(lambda self: self.w)
    height = property(lambda self: self.h)
    right = property(lambda self: self.x + self.w)
    bottom = property(lambda self: self.y + self.h)


def make_grid(cols, rows, gutter, area: object) -> list[Cell]:
    """Cells over ``area``, row by row, left to right."""
    for name, value in (("cols", cols), ("rows", rows)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"f.grid() needs a whole number for {name}, not {value!r}")
        if value <= 0:
            raise ValueError(f"f.grid() needs {name} above 0, but got {value}")
    if isinstance(gutter, (tuple, list)):
        if len(gutter) != 2:
            raise ValueError("gutter needs one number or two, (column_gutter, row_gutter)")
        gx, gy = gutter
    else:
        gx = gy = gutter
    for g in (gx, gy):
        _number(g, "gutter")
        if g < 0:
            raise ValueError(f"gutter cannot be negative, but got {gutter!r}")
    try:
        left, top, width, height = area.left, area.top, area.width, area.height
    except AttributeError:
        raise TypeError("area needs left, top, width and height, like f.ground.content or a grid cell") from None
    w = (width - gx * (cols - 1)) / cols
    h = (height - gy * (rows - 1)) / rows
    if w <= 0 or h <= 0:
        raise ValueError(f"the gutter {gutter!r} leaves no room for {cols} columns and {rows} rows "
                         f"in an area {width} wide and {height} high")
    return [Cell(left + col * (w + gx), top + row * (h + gy), w, h, col, row, row * cols + col)
            for row in range(rows) for col in range(cols)]
