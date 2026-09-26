"""Vector (S-055, contract H5): p5.js's meaning, degrees for angles, Python operators."""
from __future__ import annotations

import math

import pytest

import funground as p
from funground import api
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def close(v, x, y):
    return math.isclose(v.x, x, abs_tol=1e-9) and math.isclose(v.y, y, abs_tol=1e-9)


def test_construction_and_unpacking():
    v = p.Vector(3, 4)
    assert (v.x, v.y) == (3.0, 4.0) and tuple(v) == (3.0, 4.0) and v[1] == 4.0 and len(v) == 2
    x, y = v
    assert (x, y) == (3.0, 4.0)
    assert p.Vector() == (0, 0)
    assert repr(p.Vector(1.5, -2)) == "Vector(1.5, -2)"


def test_methods_change_the_vector_in_place_and_return_it_as_in_p5():
    position, velocity = p.Vector(10, 10), p.Vector(1, 2)
    result = position.add(velocity)
    assert result is position and position == (11, 12)
    assert position.sub(1, 2) is position and position == (10, 10)
    assert position.add((5, 5)) == (15, 15)
    assert position.mult(2) == (30, 30) and position.div(3) == (10, 10)
    assert velocity == (1, 2)                      # the argument is never changed


def test_chaining_like_p5():
    v = p.Vector(0, 0)
    v.add(p.Vector(0, 3)).add(p.Vector(4, 0)).limit(2.5)
    assert math.isclose(v.mag(), 2.5) and close(v, 2.0, 1.5)


def test_operators_return_new_vectors():
    a, b = p.Vector(1, 2), p.Vector(3, 4)
    c = a + b
    assert c == (4, 6) and a == (1, 2) and b == (3, 4)
    assert b - a == (2, 2) and a * 3 == (3, 6) and 3 * a == (3, 6) and b / 2 == (1.5, 2) and -a == (-1, -2)
    assert a + (1, 1) == (2, 3)


def test_length_and_direction():
    v = p.Vector(3, 4)
    assert v.mag() == 5 and v.mag_sq() == 25
    assert close(v.copy().normalize(), 0.6, 0.8)
    assert close(v.copy().set_mag(10), 6, 8)
    assert v.copy().limit(10) == (3, 4)            # already shorter: unchanged
    assert p.Vector(0, 0).normalize() == (0, 0)    # zero stays zero


def test_angles_are_degrees_and_follow_the_screen():
    assert p.Vector(1, 0).heading() == 0
    assert p.Vector(0, 1).heading() == 90          # y points down, as for p.rotate
    assert p.Vector(-1, 0).heading() == 180
    assert close(p.Vector(1, 0).rotate(90), 0, 1)
    assert close(p.Vector.from_angle(90, 2), 0, 2)
    assert close(p.Vector(2, 0).set_heading(180), -2, 0)
    assert math.isclose(p.Vector(1, 0).angle_between(p.Vector(0, 1)), 90)
    assert math.isclose(p.Vector(0, 1).angle_between(p.Vector(1, 0)), -90)


def test_products_distance_and_lerp():
    a, b = p.Vector(1, 0), p.Vector(0, 1)
    assert a.dot(b) == 0 and a.cross(b) == 1 and b.cross(a) == -1
    assert p.Vector(0, 0).dist(p.Vector(3, 4)) == 5
    assert p.Vector(0, 0).lerp(p.Vector(10, 20), 0.25) == (2.5, 5)


def test_random_2d_is_unit_length_and_repeatable_with_random_seed():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.random_seed(5)
    first = p.Vector.random_2d()
    p.random_seed(5)
    assert p.Vector.random_2d() == first and math.isclose(first.mag(), 1)


def test_learner_mistakes_get_clear_errors():
    with pytest.raises(TypeError, match="numbers"):
        p.Vector("3", 4)
    with pytest.raises(TypeError, match="Vector, an"):
        p.Vector(1, 1).add(5)
    with pytest.raises(ZeroDivisionError, match="divide a vector by 0"):
        p.Vector(1, 1).div(0)
    with pytest.raises(ValueError, match="not zero"):
        p.Vector(0, 0).angle_between(p.Vector(1, 0))
    with pytest.raises(TypeError):
        {p.Vector(1, 1): "mutable vectors are not dict keys"}
