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
    """A 2D vector: two numbers, x and y, that you can add, scale, turn and measure.

    Make one with f.Vector(3, 4). Read and change its parts as v.x and v.y. Use it for a position, a speed
    or a push. Angles are in degrees, like every angle in funground. y grows downward, so 90 degrees points
    down.

    The methods add, sub, mult, div, normalize, limit, set_mag, set_heading, rotate, lerp and set change
    the vector in place and give it back, so calls can be chained: position.add(velocity). The operators
    +, -, * and / make a new vector instead, and leave the first one alone. A vector can be unpacked like a
    pair, as in x, y = v, and compared with == against another vector or an (x, y) pair. It is changeable,
    so it cannot be a dictionary key.

    Arguments:
        x, y: the two parts of the vector. Both are 0 at first.

    Example:
        v = f.Vector(3, 4)
        print(v.mag())            # 5.0
        v.add(1, 1).mult(2)       # now (8, 10)
        w = v + f.Vector(1, 0)    # a new vector, v is not changed

    See also: from_angle, random_2d, mag, add
    """

    __slots__ = ("x", "y")
    __hash__ = None  # mutable: never a dict key

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = _number(x, "Vector")
        self.y = _number(y, "Vector")

    # --- making vectors -------------------------------------------------------------------
    @classmethod
    def from_angle(cls, angle: float, length: float = 1.0) -> Vector:
        """Make a vector that points at an angle.

        0 degrees points right and 90 degrees points down, as on the screen.

        Arguments:
            angle: the direction in degrees.
            length: how long the vector is. It is 1 at first.

        Returns:
            a new Vector.

        Example:
            v = f.Vector.from_angle(90, 10)    # (0, 10): ten pixels down

        See also: heading, random_2d
        """
        a = math.radians(_number(angle, "from_angle"))
        return cls(math.cos(a) * length, math.sin(a) * length)

    @classmethod
    def random_2d(cls) -> Vector:
        """Make a vector of length 1 that points in a random direction.

        f.random_seed() makes the choice repeatable.

        Returns:
            a new Vector of length 1.

        Example:
            push = f.Vector.random_2d().mult(5)

        See also: from_angle, set_mag
        """
        from . import api

        return cls.from_angle(api.canvas_sketch()._rng.uniform(0.0, 360.0))

    def copy(self) -> Vector:
        """Make a new vector with the same x and y.

        Changing the copy does not change the original.

        Returns:
            a new Vector.

        Example:
            a = f.Vector(1, 2)
            b = a.copy()
            b.add(5, 5)       # a is still (1, 2)

        See also: set
        """
        return Vector(self.x, self.y)

    def set(self, x, y=None) -> Vector:
        """Give the vector new x and y values, in place.

        Arguments:
            x, y: either two numbers, or x can be a Vector or an (x, y) pair with y left out.

        Returns:
            this vector, changed.

        Raises:
            TypeError: if the values are not numbers, a Vector or an (x, y) pair.

        Example:
            v = f.Vector(1, 2)
            v.set(10, 20)
            v.set((3, 4))

        See also: copy, add
        """
        self.x, self.y = _pair(x, y, "set")
        return self

    # --- changing the vector (in place, returns it, as in p5) ------------------------------
    def add(self, x, y=None) -> Vector:
        """Add to the vector, in place.

        Arguments:
            x, y: either two numbers, or x can be a Vector or an (x, y) pair with y left out.

        Returns:
            this vector, changed.

        Raises:
            TypeError: if the values are not numbers, a Vector or an (x, y) pair.

        Example:
            position = f.Vector(100, 100)
            velocity = f.Vector(2, 1)
            position.add(velocity)

        See also: sub, mult
        """
        dx, dy = _pair(x, y, "add")
        self.x += dx
        self.y += dy
        return self

    def sub(self, x, y=None) -> Vector:
        """Take away from the vector, in place.

        Arguments:
            x, y: either two numbers, or x can be a Vector or an (x, y) pair with y left out.

        Returns:
            this vector, changed.

        Raises:
            TypeError: if the values are not numbers, a Vector or an (x, y) pair.

        Example:
            to_mouse = f.Vector(f.mouse_x, f.mouse_y).sub(position)

        See also: add, dist
        """
        dx, dy = _pair(x, y, "sub")
        self.x -= dx
        self.y -= dy
        return self

    def mult(self, n: float) -> Vector:
        """Multiply both parts by a number, in place.

        Arguments:
            n: the number to multiply by. A negative number turns the vector round.

        Returns:
            this vector, changed.

        Example:
            velocity.mult(0.99)    # slow down a little

        See also: div, set_mag, limit
        """
        n = _number(n, "mult")
        self.x *= n
        self.y *= n
        return self

    def div(self, n: float) -> Vector:
        """Divide both parts by a number, in place.

        Arguments:
            n: the number to divide by.

        Returns:
            this vector, changed.

        Raises:
            ZeroDivisionError: if n is 0.

        Example:
            v = f.Vector(10, 20).div(2)    # (5, 10)

        See also: mult
        """
        n = _number(n, "div")
        if n == 0:
            raise ZeroDivisionError("cannot divide a vector by 0")
        self.x /= n
        self.y /= n
        return self

    def normalize(self) -> Vector:
        """Make the length 1, keeping the direction, in place.

        A zero vector stays zero.

        Returns:
            this vector, changed.

        Example:
            direction = f.Vector(3, 4).normalize()    # (0.6, 0.8)

        See also: set_mag, limit, mag
        """
        m = self.mag()
        if m > 0:
            self.x /= m
            self.y /= m
        return self

    def limit(self, maximum: float) -> Vector:
        """Shorten the vector, in place, if it is longer than a maximum length.

        A vector that is already short enough is not changed.

        Arguments:
            maximum: the longest the vector may be.

        Returns:
            this vector, changed.

        Example:
            velocity.add(acceleration).limit(8)

        See also: set_mag, normalize
        """
        maximum = _number(maximum, "limit")
        if self.mag_sq() > maximum * maximum:
            self.normalize().mult(maximum)
        return self

    def set_mag(self, length: float) -> Vector:
        """Give the vector a new length, in place, keeping its direction.

        A zero vector stays zero, because it has no direction.

        Arguments:
            length: the new length.

        Returns:
            this vector, changed.

        Example:
            v = f.Vector(3, 4).set_mag(10)    # (6, 8)

        See also: mag, normalize, limit
        """
        return self.normalize().mult(_number(length, "set_mag"))

    def set_heading(self, angle: float) -> Vector:
        """Turn the vector to point at an angle, in place, keeping its length.

        Arguments:
            angle: the new direction in degrees. 0 is right and 90 is down.

        Returns:
            this vector, changed.

        Example:
            v = f.Vector(5, 0).set_heading(90)    # about (0, 5)

        See also: heading, rotate
        """
        m = self.mag()
        a = math.radians(_number(angle, "set_heading"))
        self.x, self.y = math.cos(a) * m, math.sin(a) * m
        return self

    def rotate(self, angle: float) -> Vector:
        """Turn the vector by an angle, in place.

        A positive angle turns clockwise on the screen, like f.rotate().

        Arguments:
            angle: how far to turn, in degrees.

        Returns:
            this vector, changed.

        Example:
            v = f.Vector(1, 0).rotate(90)    # about (0, 1)

        See also: set_heading, heading
        """
        a = math.radians(_number(angle, "rotate"))
        c, s = math.cos(a), math.sin(a)
        self.x, self.y = self.x * c - self.y * s, self.x * s + self.y * c
        return self

    def lerp(self, target, amount: float) -> Vector:
        """Move part of the way towards another vector, in place.

        Arguments:
            target: the vector to move towards, or an (x, y) pair.
            amount: how much of the way to go, from 0 (stay) to 1 (arrive). Numbers outside 0 to 1 go past.

        Returns:
            this vector, changed.

        Example:
            position.lerp(f.Vector(f.mouse_x, f.mouse_y), 0.1)    # follow the mouse

        See also: add, dist
        """
        tx, ty = _pair(target, None, "lerp")
        t = _number(amount, "lerp")
        self.x += (tx - self.x) * t
        self.y += (ty - self.y) * t
        return self

    # --- questions (return a number) -------------------------------------------------------
    def mag(self) -> float:
        """The length of the vector.

        Returns:
            the length, as a number that is 0 or more.

        Example:
            print(f.Vector(3, 4).mag())    # 5.0

        See also: mag_sq, set_mag, normalize
        """
        return math.hypot(self.x, self.y)

    def mag_sq(self) -> float:
        """The length of the vector, squared.

        It is quicker than mag(), because it needs no square root. Use it to compare lengths.

        Returns:
            x * x + y * y.

        Example:
            print(f.Vector(3, 4).mag_sq())    # 25.0

        See also: mag
        """
        return self.x * self.x + self.y * self.y

    def heading(self) -> float:
        """The direction the vector points in.

        Returns:
            the angle in degrees, from -180 to 180. 0 is right and 90 is down.

        Example:
            print(f.Vector(0, 1).heading())    # 90.0

        See also: set_heading, angle_between, from_angle
        """
        return math.degrees(math.atan2(self.y, self.x))

    def dist(self, other) -> float:
        """The distance from this point to another.

        Arguments:
            other: a Vector or an (x, y) pair.

        Returns:
            the distance, as a number that is 0 or more.

        Example:
            if position.dist(target) < 5:
                print("arrived")

        See also: mag, sub
        """
        ox, oy = _pair(other, None, "dist")
        return math.hypot(self.x - ox, self.y - oy)

    def dot(self, other) -> float:
        """The dot product of this vector and another.

        It is x * other.x + y * other.y. It is 0 when the two are at right angles.

        Arguments:
            other: a Vector or an (x, y) pair.

        Returns:
            a number.

        Example:
            print(f.Vector(1, 0).dot(f.Vector(0, 1)))    # 0.0

        See also: cross, angle_between
        """
        ox, oy = _pair(other, None, "dot")
        return self.x * ox + self.y * oy

    def cross(self, other) -> float:
        """The 2D cross product of this vector and another.

        It is positive when the other vector is clockwise from this one on the screen.

        Arguments:
            other: a Vector or an (x, y) pair.

        Returns:
            a number.

        Example:
            print(f.Vector(1, 0).cross(f.Vector(0, 1)))    # 1.0

        See also: dot, angle_between
        """
        ox, oy = _pair(other, None, "cross")
        return self.x * oy - self.y * ox

    def angle_between(self, other) -> float:
        """The angle that turns this vector's direction onto another's.

        Arguments:
            other: a Vector or an (x, y) pair. Neither vector may be zero.

        Returns:
            the signed angle in degrees.

        Raises:
            ValueError: if either vector is zero.

        Example:
            print(f.Vector(1, 0).angle_between(f.Vector(0, 1)))    # 90.0

        See also: heading, dot, cross
        """
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
