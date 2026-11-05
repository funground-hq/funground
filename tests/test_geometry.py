"""Transform and Path (story S-018.3)."""
from __future__ import annotations

import math

import pytest

from funground.geometry import Path, Transform


def close(p, q, eps=1e-9):
    return all(abs(a - b) < eps for a, b in zip(p, q))


# ---------------------------------------------------------------- Transform
def test_identity_and_translation():
    assert Transform().is_identity
    assert Transform.translation(10, 20).apply(1, 2) == (11, 22)


def test_rotation_is_degrees_clockwise_on_screen():
    # +90° with y-down turns +x into +y (visually clockwise), contract C1/F1.
    assert close(Transform.rotation(90).apply(1, 0), (0, 1))
    assert close(Transform.rotation(180).apply(1, 0), (-1, 0))
    assert close(Transform.rotation(360).apply(3, 4), (3, 4))


def test_scaling():
    assert Transform.scaling(2).apply(3, 4) == (6, 8)
    assert Transform.scaling(2, 0.5).apply(3, 4) == (6, 2)


def test_then_applies_left_first():
    t = Transform.scaling(2).then(Transform.translation(10, 0))
    assert t.apply(1, 1) == (12, 2)             # scale first, then translate
    u = Transform.translation(10, 0).then(Transform.scaling(2))
    assert u.apply(1, 1) == (22, 2)             # translate first, then scale


def test_concat_matches_translate_then_rotate_call_order():
    # p.translate(100, 50); p.rotate(90); draw at (10, 0) -> rotate applies to the local point first
    ctm = Transform().concat(Transform.translation(100, 50)).concat(Transform.rotation(90))
    assert close(ctm.apply(10, 0), (100, 60))


def test_invert_roundtrip_and_singular():
    t = Transform.translation(3, 4).then(Transform.rotation(30)).then(Transform.scaling(2, 3))
    x, y = t.invert().apply(*t.apply(7, -2))
    assert close((x, y), (7, -2))
    with pytest.raises(ValueError):
        Transform.scaling(0).invert()


def test_transform_is_hashable_and_immutable():
    assert len({Transform(), Transform.identity()}) == 1
    with pytest.raises(AttributeError):
        Transform().a = 2  # type: ignore[misc]


# ---------------------------------------------------------------- Path
def test_builders_are_immutable_and_chain():
    p = Path().move_to(0, 0).line_to(10, 0)
    q = p.line_to(10, 10).close()
    assert len(p) == 2 and len(q) == 4
    assert q.segments[-1] == ("close",)


def test_rect_and_ellipse_helpers():
    r = Path.rect(1, 2, 3, 4)
    assert r.bounds() == (1, 2, 4, 6)
    e = Path.ellipse(50, 50, 20, 10)
    assert len(e) == 6 and e.segments[0] == ("move", (70, 50))
    x0, y0, x1, y1 = e.bounds()
    assert x0 == 30 and x1 == 70 and y0 == 40 and y1 == 60


def test_quad_to_becomes_cubic():
    p = Path().move_to(0, 0).quad_to(3, 3, 6, 0)
    seg = p.segments[1]
    assert seg[0] == "cubic" and close(seg[1], (2, 2)) and close(seg[2], (4, 2)) and seg[3] == (6, 0)


def test_current_point_follows_close():
    p = Path().move_to(1, 1).line_to(5, 5).close()
    assert p.current_point() == (1, 1)
    with pytest.raises(ValueError):
        Path().current_point()


def test_transformed_applies_to_every_point():
    p = Path.rect(0, 0, 10, 10).transformed(Transform.translation(5, 5))
    assert p.bounds() == (5, 5, 15, 15)
    assert Path.rect(0, 0, 1, 1).transformed(Transform()) is not None


def test_translated_moves_every_point():
    p = Path().move_to(0, 0).cubic_to(1, 2, 3, 4, 5, 6).line_to(7, 8).close()
    moved = p.translated(10, -1)
    assert moved.segments == (
        ("move", (10, -1)), ("cubic", (11, 1), (13, 3), (15, 5)), ("line", (17, 7)), ("close",))


def test_translated_returns_a_new_path_and_leaves_the_original():
    p = Path.rect(0, 0, 10, 10)
    before = p.segments
    moved = p.translated(5, 5)
    assert moved is not p
    assert p.segments == before
    assert Path().translated(3, 4) == Path()


@pytest.mark.parametrize("dx,dy", [(5, 5), (3.5, -2.25), (0, 0), (0.1, 0.7)])
def test_translated_equals_transformed_by_a_translation(dx, dy):
    p = Path().move_to(0.3, 1.7).cubic_to(2.1, 3.3, -4.4, 5.5, 6.6, -7.7).close()
    assert p.translated(dx, dy) == p.transformed(Transform.translation(dx, dy))


def test_translated_refuses_a_non_number():
    with pytest.raises(TypeError):
        Path.rect(0, 0, 1, 1).translated("5", 0)


def test_path_is_hashable():
    assert hash(Path.rect(0, 0, 1, 1)) == hash(Path.rect(0, 0, 1, 1))


# ---------------------------------------------------------------- spike 21 (mutation testing)
def test_then_is_applying_one_transform_after_the_other_for_any_pair():
    # Transform.then docstring: "Apply *self* first, then *other*". Rotations, shears and unequal scales
    # fill every entry of the matrix, so a wrong sign or product in the composition shows.
    parts = [Transform.rotation(30), Transform.shearing(20, -15), Transform.scaling(2, 3),
             Transform.translation(5, -7), Transform.rotation(-110)]
    for first in parts:
        for second in parts:
            both = first.then(second)
            for x, y in ((7, -2), (0.5, 3), (-4, -9)):
                assert close(both.apply(x, y), second.apply(*first.apply(x, y)))


def test_rounded_rect_corners_are_quarter_circles_meeting_the_sides():
    # Contract F14: "Corners are quarter-circle arcs"; rounded_rect docstring: "A radius of 0 gives a sharp
    # corner". Each arc runs from one side's tangent point to the next, and its middle is at 45 degrees.
    path = Path.rounded_rect(10, 10, 80, 50, (8, 1, 6, 0))
    ends = [seg[-1] for seg in path.segments if seg[0] != "close"]
    expected = [(10, 18), (18, 10), (89, 10), (90, 11), (90, 54), (84, 60), (10, 60)]
    assert len(ends) == len(expected) and all(close(a, b, 1e-9) for a, b in zip(ends, expected))
    centres = {(18, 10): ((18, 18), 8), (90, 11): ((89, 11), 1), (84, 60): ((84, 54), 6)}
    start = None
    for seg in path.segments:
        if seg[0] == "cubic":
            (c1, c2, end), (cx, cy) = seg[1:], centres[tuple(round(v, 9) for v in seg[3])][0]
            r = centres[tuple(round(v, 9) for v in seg[3])][1]
            mid = tuple(0.125 * a + 0.375 * b + 0.375 * c + 0.125 * d for a, b, c, d in zip(start, c1, c2, end))
            assert abs(math.hypot(mid[0] - cx, mid[1] - cy) - r) < 1e-3 * r
            assert abs(abs(mid[0] - cx) - abs(mid[1] - cy)) < 1e-3 * r      # at 45 degrees
        start = seg[-1] if seg[0] != "close" else start
    only_bottom_left = Path.rounded_rect(10, 10, 80, 50, (0, 0, 0, 5))
    ends = [seg[-1] for seg in only_bottom_left.segments if seg[0] != "close"]
    assert all(close(a, b, 1e-9) for a, b in zip(ends, [(10, 10), (90, 10), (90, 60), (15, 60), (10, 55)]))
    assert len(ends) == 5


def _cubics_lie_on_ellipse(path, cx, cy, rx, ry):
    """Every cubic's end and middle (t = 0.5) are on the ellipse, to 0.1 % of its size."""
    start = None
    for seg in path.segments:
        if seg[0] == "cubic":
            c1, c2, end = seg[1:]
            mid = tuple(0.125 * a + 0.375 * b + 0.375 * c + 0.125 * d for a, b, c, d in zip(start, c1, c2, end))
            for x, y in (end, mid):
                assert abs(math.hypot((x - cx) / rx, (y - cy) / ry) - 1) < 1e-3
        if seg[0] != "close":
            start = seg[-1]


def test_ellipse_and_arc_curves_follow_the_ellipse():
    # Path.ellipse docstring (an ellipse with these radii) and Path.arc_to docstring: "The point at angle a is
    # (cx + rx * cos a, cy + ry * sin a)", turning clockwise, from start to stop.
    _cubics_lie_on_ellipse(Path.ellipse(50, 40, 30, 12), 50, 40, 30, 12)
    arc = Path().arc_to(50, 40, 30, 12, 20, 250)
    _cubics_lie_on_ellipse(arc, 50, 40, 30, 12)
    a, b = math.radians(20), math.radians(250)
    assert close(arc.segments[0][1], (50 + 30 * math.cos(a), 40 + 12 * math.sin(a)))
    assert close(arc.segments[-1][-1], (50 + 30 * math.cos(b), 40 + 12 * math.sin(b)))
    # clockwise on the screen: from 20 degrees the arc goes down (y grows) before it comes back up
    assert arc.segments[1][-1][1] > arc.segments[0][1][1]
    # "If stop is not above start, only the line to the start is added"; a small sweep is still an arc
    assert [s[0] for s in Path().move_to(0, 0).arc_to(50, 40, 30, 12, 45, 45).segments] == ["move", "line"]
    assert [s[0] for s in Path().move_to(0, 0).arc_to(50, 40, 30, 12, 45, 45.5).segments] == ["move", "line", "cubic"]


def test_contours_flatten_curves_to_the_tolerance_and_keep_the_sub_paths():
    # geometry.contours docstring: "The sub-paths of path as polylines (curves flattened to tolerance), each
    # with a flag for whether it was closed. A closing segment is added as a straight piece back to the start."
    # Path.ellipse is within 0.03 per cent of a true circle (its docstring), so every point and every chord
    # middle must be within that plus the tolerance of the circle.
    from funground.geometry import contours

    r, tol = 30, 0.01
    (poly, closed), = contours(Path.ellipse(50, 50, r, r), tol)
    assert closed and poly[0] == poly[-1] and len(poly) > 8
    slack = 0.0003 * r + tol + 1e-9
    for (ax, ay), (bx, by) in zip(poly, poly[1:]):
        assert abs(math.hypot(ax - 50, ay - 50) - r) < 0.0003 * r + 1e-9
        assert abs(math.hypot((ax + bx) / 2 - 50, (ay + by) / 2 - 50) - r) < slack
    parts = contours(Path().move_to(0, 0).line_to(10, 0).line_to(10, 10).close().move_to(50, 50).line_to(60, 50))
    assert parts == [([(0, 0), (10, 0), (10, 10), (0, 0)], True), ([(50, 50), (60, 50)], False)]


def test_sample_path_puts_a_point_every_spacing_along_the_outline():
    # Contract T16: points "one every spacing pixels of outline length, starting at the start of each outline";
    # sample_path docstring: the leftover distance carries across the pieces of a sub-path.
    from funground.geometry import sample_path

    line = sample_path(Path().move_to(0, 0).line_to(100, 0), 10)
    assert line == [(0, 0)] + [(float(x), 0.0) for x in range(10, 101, 10)]       # the end, at 100, too
    bend = sample_path(Path().move_to(0, 0).line_to(1, 0).line_to(1, 3), 1)
    assert bend == [(0, 0), (1.0, 0.0), (1.0, 1.0), (1.0, 2.0), (1.0, 3.0)]        # a piece 1 long counts
    square = sample_path(Path.rect(10, 20, 40, 40), 10)
    assert len(square) == 16 and square[0] == (10, 20) and len(set(square)) == 16    # the start is not repeated


def test_path_measure_follows_a_circle_and_faces_along_it():
    # PathMeasure docstring: the length is the sum of pieces made "exact for a circle"; point_at gives "a point
    # on it, and the direction of the curve itself there", as rotate() reads it (clockwise on the screen).
    # Path.ellipse is within 0.03 per cent of a true circle, so the checks allow that.
    from funground.geometry import PathMeasure

    r = 30
    route = PathMeasure(Path.ellipse(50, 50, r, r))
    assert route.length == pytest.approx(2 * math.pi * r, rel=0.0005)
    for d in (5, 10, 33.3, 50, 77, 120, 160):
        x, y, degrees = route.point_at(d)
        assert math.hypot(x - 50, y - 50) == pytest.approx(r, abs=0.0003 * r + 0.1)
        facing = math.degrees(math.atan2(y - 50, x - 50)) + 90                      # at right angles to the radius
        assert (degrees - facing + 180) % 360 - 180 == pytest.approx(0, abs=0.5)
