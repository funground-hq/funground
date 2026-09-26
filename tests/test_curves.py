"""Curves, contours and curve helpers (S-074, D-018, contract F9)."""
from __future__ import annotations

import math

import pytest

import funground as p
from funground import ir
from funground.shapes import catmull_rom_controls

WHITE, RED, BLUE = (255, 255, 255), (255, 0, 0), (0, 0, 255)


def px(canvas, x, y):
    return tuple(canvas.get_at((x, y))[:3])


def test_curve_vertex_passes_through_the_inner_points(sketch, canvas):
    pts = [(0, 50), (40, 20), (100, 80), (160, 20), (200, 50)]
    p.no_fill()
    p.begin_shape()
    for x, y in pts:
        p.curve_vertex(x, y)
    p.end_shape()
    path = sketch.frame.ops[-1].path
    assert path.segments[0] == ("move", (40, 20))                  # starts at the 2nd point
    ends = [seg[-1] for seg in path.segments[1:]]
    assert ends == [(100, 80), (160, 20)]                           # through the inner points, ends at the 4th
    assert len(path.segments) == 3                                  # 5 points -> 2 segments


def test_fewer_than_four_curve_points_warn_and_draw_nothing(sketch, canvas):
    from funground.capabilities import FungroundWarning

    p.begin_shape()
    p.curve_vertex(0, 0)
    p.curve_vertex(10, 10)
    p.curve_vertex(20, 0)
    with pytest.warns(FungroundWarning, match="at least 4"):
        p.end_shape()
    assert not sketch.frame.ops


def test_catmull_rom_controls_match_processing_formula():
    c1, c2 = catmull_rom_controls((0, 0), (10, 0), (20, 10), (30, 10), 0.0)
    assert c1 == pytest.approx((10 + 20 / 6, 10 / 6)) and c2 == pytest.approx((20 - 20 / 6, 10 - 10 / 6))
    c1, c2 = catmull_rom_controls((0, 0), (10, 0), (20, 10), (30, 10), 1.0)
    assert c1 == (10, 0) and c2 == (20, 10)                         # tightness 1: straight segment


def test_curve_tightness_is_style(sketch, canvas):
    with p.saved_state():
        p.curve_tightness(1)
        assert sketch.style.curve_tightness == 1.0
    assert sketch.style.curve_tightness == 0.0


def test_quadratic_vertex(sketch, canvas):
    p.no_fill()
    p.begin_shape()
    p.vertex(0, 100)
    p.quadratic_vertex(100, 0, 200, 100)
    p.end_shape()
    seg = sketch.frame.ops[-1].path.segments[1]
    assert seg[0] == "cubic" and seg[3] == (200, 100)
    with pytest.raises(RuntimeError, match=r"f\.vertex"):
        p.begin_shape()
        p.quadratic_vertex(0, 0, 1, 1)


def test_contour_cuts_a_hole_whichever_way_it_is_drawn(canvas):
    for hole in ([(80, 30), (120, 30), (120, 70), (80, 70)], [(80, 30), (80, 70), (120, 70), (120, 30)]):
        p.background("white")
        p.no_stroke()
        p.fill("red")
        p.begin_shape()
        for x, y in [(40, 10), (160, 10), (160, 90), (40, 90)]:
            p.vertex(x, y)
        p.begin_contour()
        for x, y in hole:
            p.vertex(x, y)
        p.end_contour()
        p.end_shape(close=True)
        assert px(canvas, 50, 50) == RED            # the outline is filled
        assert px(canvas, 100, 50) == WHITE         # the hole is not, in either winding


def test_contour_misuse_is_a_clear_error(canvas):
    p.begin_shape()
    with pytest.raises(RuntimeError, match="outline"):
        p.begin_contour()                            # before any outline vertex
    p.vertex(0, 0)
    with pytest.raises(RuntimeError, match="begin_contour"):
        p.end_contour()
    p.begin_contour()
    with pytest.raises(RuntimeError, match="end_contour"):
        p.end_shape()


def test_bezier_and_curve_are_stroked_only(sketch, canvas):
    p.fill("red")
    p.stroke("blue")
    p.bezier(20, 80, 20, 0, 180, 0, 180, 80)
    p.curve(0, 100, 40, 40, 160, 40, 200, 100)
    kinds = [type(op).__name__ for op in sketch.frame.ops]
    assert kinds == ["StrokePath", "StrokePath"]
    assert sketch.frame.ops[1].path.segments[0] == ("move", (40, 40))


def test_bezier_point_and_tangent():
    assert p.bezier_point(0, 0, 10, 10, 0.5) == pytest.approx(5)
    assert p.bezier_point(1, 2, 3, 4, 0) == 1 and p.bezier_point(1, 2, 3, 4, 1) == 4
    assert p.bezier_tangent(0, 1, 2, 3, 0.5) == pytest.approx(3)   # a straight line: constant slope


def test_curve_point_goes_through_the_middle_points(canvas):
    assert p.curve_point(0, 10, 20, 30, 0) == pytest.approx(10)
    assert p.curve_point(0, 10, 20, 30, 1) == pytest.approx(20)
    assert p.curve_tangent(0, 10, 20, 30, 0.5) == pytest.approx(10)


def test_mixed_vertices_join_in_order(sketch, canvas):
    p.no_fill()
    p.begin_shape()
    p.vertex(0, 0)
    for x, y in [(0, 0), (50, 50), (100, 0), (150, 50)]:
        p.curve_vertex(x, y)
    p.vertex(200, 0)
    p.end_shape()
    kinds = [seg[0] for seg in sketch.frame.ops[-1].path.segments]
    assert kinds == ["move", "line", "cubic", "line"]
