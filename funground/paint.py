"""Paint: what a fill, stroke or background can be - a colour or a gradient (story S-050, contract S13).

A Gradient is plain data carried through the IR. Its coordinates are in the drawing space at
the moment the shape is drawn, so a gradient follows translate/rotate/scale like the shape
does. The renderer turns it into a Cairo pattern, which PDF and SVG keep as a true vector
gradient.
"""
from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import Union

from .color import Color


@dataclass(frozen=True, slots=True)
class Gradient:
    kind: str                                   # "linear" | "radial"
    points: tuple[float, ...]                   # linear: x1, y1, x2, y2 · radial: x, y, radius
    stops: tuple[tuple[float, Color], ...]      # (offset 0-1, colour), offsets non-decreasing

    def __repr__(self) -> str:
        return f"<{self.kind} gradient, {len(self.stops)} colours>"


Paint = Union[Color, Gradient]


def parse_paint(value) -> Paint:
    """A Gradient passes through; anything else is parsed as a colour (contract S1)."""
    if isinstance(value, Gradient):
        return value
    return Color.parse(value)


def _number(v, what: str) -> float:
    if isinstance(v, bool) or not isinstance(v, Real):
        raise TypeError(f"{what} needs numbers, not {v!r}")
    return float(v)


def _stops(colors, stops, what: str) -> tuple[tuple[float, Color], ...]:
    if isinstance(colors, (str, bytes)) or not hasattr(colors, "__len__") or len(colors) < 2:
        raise ValueError(f"{what} needs a list of at least two colours, e.g. [\"red\", \"blue\"]")
    parsed = [Color.parse(c) for c in colors]
    if stops is None:
        offsets = [i / (len(parsed) - 1) for i in range(len(parsed))]
    else:
        offsets = [_number(s, what) for s in stops]
        if len(offsets) != len(parsed):
            raise ValueError(f"{what}: give one stop per colour ({len(parsed)} colours, {len(offsets)} stops)")
        if any(not 0 <= s <= 1 for s in offsets) or any(b < a for a, b in zip(offsets, offsets[1:])):
            raise ValueError(f"{what}: stops go from 0 to 1 and never go backwards, e.g. [0, 0.3, 1]")
    return tuple(zip(offsets, parsed))


def linear_gradient(x1, y1, x2, y2, colors, stops=None) -> Gradient:
    points = tuple(_number(v, "linear_gradient") for v in (x1, y1, x2, y2))
    return Gradient("linear", points, _stops(colors, stops, "linear_gradient"))


def radial_gradient(x, y, radius, colors, stops=None) -> Gradient:
    points = tuple(_number(v, "radial_gradient") for v in (x, y, radius))
    if points[2] <= 0:
        raise ValueError("radial_gradient needs a radius above 0")
    return Gradient("radial", points, _stops(colors, stops, "radial_gradient"))
