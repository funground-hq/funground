"""Vector: a 2D vector with p5.js's meaning (story S-055, contract H5).

Methods such as ``add`` change the vector *in place* and return it, exactly as in p5, so ported
code like ``position.add(velocity)`` keeps working. Operators (``+ - * /``) return a *new*
vector, which is the Python habit. Angles are in degrees, like every angle in funground (D-002).
"""
from __future__ import annotations

import math
from collections.abc import Iterator
from numbers import Real


def _pair(a, b=None, what: str = "vector") -> tuple[float, float]:
    """Accept a Vector, an (x, y) pair, or two numbers."""
    if b is not None:
        return _number(a, what), _number(b, what)
    if isinstance(a, Vector):
        return a.x, a.y
    if isinstance(a, (tuple, list)) and len(a) == 2:
        return _number(a[0], what), _number(a[1], what)
    raise TypeError(f"{what} needs a Vector, an (x, y) pair, or two numbers, not {a!r}")


def _number(v, what: str) -> float:
    if isinstance(v, bool) or not isinstance(v, Real):
        raise TypeError(f"{what} needs numbers, not {v!r}")
    return float(v)


class Vector:
    """A 2D vector: ``v = f.Vector(3, 4)``; ``v.x``, ``v.y``; ``v.mag()`` is 5."""

    __slots__ = ("x", "y")
    __hash__ = None  # mutable: never a dict key

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = _number(x, "Vector")
        self.y = _number(y, "Vector")

    # --- making vectors -------------------------------------------------------------------
    @classmethod
    def from_angle(cls, angle: float, length: float = 1.0) -> Vector:
        """A vector pointing at *angle* degrees (0 = right, 90 = down), *length* long."""
        a = math.radians(_number(angle, "from_angle"))
        return cls(math.cos(a) * length, math.sin(a) * length)

    @classmethod
    def random_2d(cls) -> Vector:
        """A vector of length 1 in a random direction. ``f.random_seed()`` makes it repeatable."""
        from . import api

        return cls.from_angle(api.canvas_sketch()._rng.uniform(0.0, 360.0))

    def copy(self) -> Vector:
        return Vector(self.x, self.y)

    def set(self, x, y=None) -> Vector:
        self.x, self.y = _pair(x, y, "set")
        return self

    # --- changing the vector (in place, returns it, as in p5) ------------------------------
    def add(self, x, y=None) -> Vector:
        dx, dy = _pair(x, y, "add")
        self.x += dx
        self.y += dy
        return self

    def sub(self, x, y=None) -> Vector:
        dx, dy = _pair(x, y, "sub")
        self.x -= dx
        self.y -= dy
        return self

    def mult(self, n: float) -> Vector:
        n = _number(n, "mult")
        self.x *= n
        self.y *= n
        return self

    def div(self, n: float) -> Vector:
        n = _number(n, "div")
        if n == 0:
            raise ZeroDivisionError("cannot divide a vector by 0")
        self.x /= n
        self.y /= n
        return self

    def normalize(self) -> Vector:
        """Make the length 1, keeping the direction. A zero vector stays zero."""
        m = self.mag()
        if m > 0:
            self.x /= m
            self.y /= m
        return self

    def limit(self, maximum: float) -> Vector:
        """Shorten the vector to *maximum* if it is longer."""
        maximum = _number(maximum, "limit")
        if self.mag_sq() > maximum * maximum:
            self.normalize().mult(maximum)
        return self

    def set_mag(self, length: float) -> Vector:
        return self.normalize().mult(_number(length, "set_mag"))

    def set_heading(self, angle: float) -> Vector:
        m = self.mag()
        a = math.radians(_number(angle, "set_heading"))
        self.x, self.y = math.cos(a) * m, math.sin(a) * m
        return self

    def rotate(self, angle: float) -> Vector:
        """Turn by *angle* degrees (positive turns clockwise on screen, like f.rotate)."""
        a = math.radians(_number(angle, "rotate"))
        c, s = math.cos(a), math.sin(a)
        self.x, self.y = self.x * c - self.y * s, self.x * s + self.y * c
        return self

    def lerp(self, target, amount: float) -> Vector:
        """Move a fraction *amount* (0-1) of the way towards *target*."""
        tx, ty = _pair(target, None, "lerp")
        t = _number(amount, "lerp")
        self.x += (tx - self.x) * t
        self.y += (ty - self.y) * t
        return self

    # --- questions (return a number) -------------------------------------------------------
    def mag(self) -> float:
        return math.hypot(self.x, self.y)

    def mag_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def heading(self) -> float:
        """The direction in degrees, from -180 to 180 (0 = right, 90 = down)."""
        return math.degrees(math.atan2(self.y, self.x))

    def dist(self, other) -> float:
        ox, oy = _pair(other, None, "dist")
        return math.hypot(self.x - ox, self.y - oy)

    def dot(self, other) -> float:
        ox, oy = _pair(other, None, "dot")
        return self.x * ox + self.y * oy

    def cross(self, other) -> float:
        """The 2D cross product: positive when *other* is clockwise from this vector on screen."""
        ox, oy = _pair(other, None, "cross")
        return self.x * oy - self.y * ox

    def angle_between(self, other) -> float:
        """The signed angle in degrees that turns this vector's direction onto *other*'s."""
        ox, oy = _pair(other, None, "angle_between")
        if (self.x == 0 and self.y == 0) or (ox == 0 and oy == 0):
            raise ValueError("angle_between needs two vectors that are not zero")
        return math.degrees(math.atan2(self.x * oy - self.y * ox, self.x * ox + self.y * oy))

    # --- Python conveniences ---------------------------------------------------------------
    def __add__(self, other) -> Vector:
        return self.copy().add(other)

    def __sub__(self, other) -> Vector:
        return self.copy().sub(other)

    def __mul__(self, n) -> Vector:
        if not isinstance(n, Real) or isinstance(n, bool):
            return NotImplemented
        return self.copy().mult(n)

    __rmul__ = __mul__

    def __truediv__(self, n) -> Vector:
        if not isinstance(n, Real) or isinstance(n, bool):
            return NotImplemented
        return self.copy().div(n)

    def __neg__(self) -> Vector:
        return Vector(-self.x, -self.y)

    def __eq__(self, other) -> bool:
        if isinstance(other, Vector):
            return self.x == other.x and self.y == other.y
        if isinstance(other, (tuple, list)) and len(other) == 2:
            return (self.x, self.y) == tuple(other)
        return NotImplemented

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __len__(self) -> int:
        return 2

    def __getitem__(self, i: int) -> float:
        return (self.x, self.y)[i]

    def __repr__(self) -> str:
        return f"Vector({self.x:g}, {self.y:g})"
