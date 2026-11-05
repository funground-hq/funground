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


def test_plain_numbers_take_the_fast_path_and_everything_else_is_as_before():
    from fractions import Fraction

    # int, float and Fraction are all accepted and stored as floats
    for value in (3, 2.5, Fraction(1, 2)):
        v = p.Vector(value, value)
        assert type(v.x) is float and v.x == float(value)
        assert (p.Vector(1, 1) * value).x == float(value)
        assert (p.Vector(1, 1) / value).x == 1 / float(value)
    # a bool is neither a number nor a fast-path type: refused with the same message, in every place
    for bad in (True, False, "3", None):
        with pytest.raises(TypeError, match=r"^Vector needs numbers, not "):
            p.Vector(bad, 1)
        with pytest.raises(TypeError, match=r"^mult needs numbers, not "):
            p.Vector(1, 1).mult(bad)
    # the operators hand a bool or a string back to Python, which then refuses the sum itself
    with pytest.raises(TypeError):
        p.Vector(1, 1) * True
    with pytest.raises(TypeError):
        p.Vector(1, 1) / "2"


# --- Spike 21 (mutation testing): cases where x and y are both non-zero and unequal, so a swapped
# sign, a swapped operator or a swapped index shows. Each states where the behaviour is written.


def test_an_x_y_pair_is_read_in_order():
    # Contract H5: add/sub/set/dist/dot/cross/lerp accept "an (x, y) pair".
    assert p.Vector(0, 0).add((1, 2)) == (1, 2)
    assert p.Vector(5, 5).sub([1, 2]) == (4, 3)


def test_from_angle_scales_by_the_length():
    # from_angle docstring: "length: how long the vector is"; 0 degrees points right.
    assert close(p.Vector.from_angle(0, 2), 2, 0)
    assert close(p.Vector.from_angle(90, 10), 0, 10)    # the docstring's example


def test_normalize_lengthens_a_short_vector_to_1():
    # normalize docstring: "Make the length 1, keeping the direction". It applies below length 1 too.
    assert close(p.Vector(0.3, 0.4).normalize(), 0.6, 0.8)


def test_set_heading_keeps_the_length():
    # set_heading docstring example: Vector(5, 0).set_heading(90) is about (0, 5).
    assert close(p.Vector(5, 0).set_heading(90), 0, 5)


def test_rotate_turns_any_vector_clockwise_and_keeps_its_length():
    # rotate docstring: "A positive angle turns clockwise on the screen" (90 = down, contract H5).
    v = p.Vector(3, 4)
    turned = v.copy().rotate(90)
    assert close(turned, -4, 3)
    assert math.isclose(turned.mag(), 5)
    assert math.isclose(turned.heading(), v.heading() + 90)
    assert close(p.Vector(3, 4).rotate(-90), 4, -3)
    sixty = v.copy().rotate(60)                     # an angle whose sine and cosine are both non-zero
    assert math.isclose(sixty.mag(), 5) and math.isclose(sixty.heading(), v.heading() + 60)


def test_lerp_moves_part_of_the_way_from_where_the_vector_is():
    # lerp docstring: "Move part of the way towards another vector"; 0 stays, 1 arrives.
    assert p.Vector(10, 10).lerp(p.Vector(20, 30), 0.5) == (15, 20)
    assert p.Vector(10, 10).lerp((20, 30), 1) == (20, 30)
    assert p.Vector(10, 10).lerp((20, 30), 0) == (10, 10)


def test_dist_from_a_point_that_is_not_the_origin():
    # dist docstring: "The distance from this point to another".
    assert p.Vector(1, 2).dist(p.Vector(4, 6)) == 5
    assert p.Vector(4, 6).dist((1, 2)) == 5


def test_dot_is_x_times_x_plus_y_times_y():
    # dot docstring: "It is x * other.x + y * other.y".
    assert p.Vector(2, 3).dot(p.Vector(4, 5)) == 23
    assert p.Vector(2, 3).dot((4, -5)) == -7


def test_angle_between_vectors_that_are_not_on_the_axes():
    # angle_between docstring: "The angle that turns this vector's direction onto another's", signed.
    assert math.isclose(p.Vector(1, 1).angle_between(p.Vector(-1, 1)), 90)
    assert math.isclose(p.Vector(-1, 1).angle_between(p.Vector(1, 1)), -90)
    assert math.isclose(p.Vector(2, 0).angle_between(p.Vector(1, 1)), 45)


def test_vectors_are_equal_only_when_both_x_and_y_match():
    # Contract H5: a vector is "equal to a vector or an (x, y) pair".
    assert p.Vector(1, 2) == p.Vector(1, 2)
    assert p.Vector(1, 2) != p.Vector(1, 3)
    assert p.Vector(1, 2) != p.Vector(0, 2)
