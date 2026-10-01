"""Stroke outlines, path queries and path transforms (story S-087; contract row F12)."""
from __future__ import annotations

import math

import pytest

import funground as p
from funground.paths import PathBuilder

from test_path_booleans import fill_area, pentagram


def subpaths(path: PathBuilder) -> int:
    return sum(1 for s in path.geometry.segments if s[0] == "move")


def line(x1=20, y1=50, x2=120, y2=50) -> PathBuilder:
    return p.path().move_to(x1, y1).line_to(x2, y2)


def corner() -> PathBuilder:
    return p.path().move_to(20, 80).line_to(80, 80).line_to(80, 20)


# ---------------------------------------------------------------- expand_stroke
def test_expand_stroke_returns_a_new_closed_builder():
    a = line()
    before = a.geometry
    out = a.expand_stroke(10)
    assert isinstance(out, PathBuilder) and out is not a
    assert out.is_closed and not out.is_empty
    assert a.geometry == before and not a.is_closed


def test_straight_line_area_is_width_times_length(canvas):
    out = line().expand_stroke(10, cap="butt")
    assert fill_area(canvas, out) == pytest.approx(10 * 100, abs=2)


def test_caps_change_the_area(canvas):
    butt = fill_area(canvas, line().expand_stroke(10, cap="butt"))
    square = fill_area(canvas, line().expand_stroke(10, cap="square"))
    rnd = fill_area(canvas, line().expand_stroke(10, cap="round"))
    assert square == pytest.approx(10 * 110, abs=2)          # half the width past each end
    assert rnd == pytest.approx(10 * 100 + math.pi * 25, rel=0.01)
    assert butt < rnd < square


def test_default_cap_and_join_are_round(canvas):
    default = fill_area(canvas, corner().expand_stroke(10))
    named = fill_area(canvas, corner().expand_stroke(10, cap="round", join="round"))
    assert default == pytest.approx(named, abs=0.5)


def test_joins_differ_at_a_corner(canvas):
    areas = {j: fill_area(canvas, corner().expand_stroke(12, cap="butt", join=j))
             for j in ("miter", "round", "bevel")}
    assert areas["bevel"] < areas["round"] < areas["miter"]
    # the sharp corner adds a 6 x 6 square; the bevel cuts it in half
    assert areas["miter"] - areas["bevel"] == pytest.approx(18, abs=1)


def test_miter_limit_turns_a_long_spike_into_a_bevel(canvas):
    sharp = p.path().move_to(20, 60).line_to(100, 50).line_to(20, 40)
    spike = fill_area(canvas, sharp.expand_stroke(6, cap="butt", join="miter", miter_limit=100))
    cut = fill_area(canvas, sharp.expand_stroke(6, cap="butt", join="miter", miter_limit=1))
    assert cut < spike


def test_dash_splits_the_outline_into_pieces():
    solid = line().expand_stroke(6, cap="butt")
    dashed = line().expand_stroke(6, cap="butt", dash=[10, 10])
    assert subpaths(solid) == 1
    assert subpaths(dashed) == 5                  # 100 long: dashes at 0, 20, 40, 60, 80


def test_dash_area_is_the_painted_part(canvas):
    dashed = line().expand_stroke(6, cap="butt", dash=[10, 10])
    assert fill_area(canvas, dashed) == pytest.approx(6 * 50, abs=2)


def test_dash_accepts_one_length_and_odd_lists():
    assert subpaths(line().expand_stroke(6, cap="butt", dash=10)) == 5
    assert subpaths(line().expand_stroke(6, cap="butt", dash=[10, 5, 5])) >= 3


def test_open_paths_are_stroked():
    assert not line().is_closed
    assert not line().expand_stroke(8).is_empty


def test_closed_paths_are_stroked_as_a_ring(canvas):
    square = p.path().rect(40, 20, 40, 40)
    ring = square.expand_stroke(8, cap="butt", join="miter")
    # a 40 x 40 square outline, 8 wide, centred on the edge: 48 x 48 minus 32 x 32
    assert fill_area(canvas, ring) == pytest.approx(48 * 48 - 32 * 32, abs=3)
    assert ring.contains(40, 40) and not ring.contains(60, 40)


def test_overlaps_are_removed(canvas):
    cross = p.path().move_to(20, 50).line_to(100, 50).move_to(60, 10).line_to(60, 90)
    out = cross.expand_stroke(10, cap="butt", join="miter")
    # two 80 x 10 bars crossing in a 10 x 10 square: the crossing is counted once
    assert fill_area(canvas, out) == pytest.approx(80 * 10 * 2 - 100, abs=2)
    assert out.contains(60, 50)


def test_an_empty_path_gives_an_empty_outline():
    assert p.path().expand_stroke(4).is_empty


@pytest.mark.parametrize("width", [0, -3])
def test_bad_width_is_an_error(width):
    with pytest.raises(ValueError, match="width"):
        line().expand_stroke(width)


def test_unknown_names_are_errors():
    with pytest.raises(ValueError, match="cap"):
        line().expand_stroke(4, cap="pointy")
    with pytest.raises(ValueError, match="join"):
        line().expand_stroke(4, join="curly")


def test_bad_dash_and_miter_limit_are_errors():
    with pytest.raises(ValueError, match="dash"):
        line().expand_stroke(4, dash=[0, 0])
    with pytest.raises(ValueError, match="dash"):
        line().expand_stroke(4, dash=[-1, 2])
    with pytest.raises(ValueError, match="miter_limit"):
        line().expand_stroke(4, miter_limit=0.5)


# ---------------------------------------------------------------- bounds
def test_bounds_of_a_rect():
    assert p.path().rect(10, 20, 30, 40).bounds() == (10, 20, 30, 40)


def test_bounds_of_a_circle_is_tight():
    x, y, w, h = p.path().circle(50, 50, 40).bounds()
    assert (x, y, w, h) == pytest.approx((30, 30, 40, 40), abs=1e-6)


def test_bounds_of_a_bulging_curve_is_tighter_than_its_control_points():
    arc = p.path().move_to(0, 0).curve_to(0, 100, 100, 100, 100, 0)
    x, y, w, h = arc.bounds()
    assert (x, y, w) == (0, 0, 100)
    assert h == pytest.approx(75)                 # the curve peaks at 3/4 of the control height
    ctrl = arc.geometry.bounds()                  # the old, looser box over all control points
    assert ctrl[3] - ctrl[1] == 100


def test_bounds_of_an_empty_path_is_none():
    assert p.path().bounds() is None
    assert p.path().move_to(5, 5).bounds() is None


def test_bounds_of_an_open_line():
    assert line(10, 20, 60, 20).bounds() == (10, 20, 50, 0)


# ---------------------------------------------------------------- contains
def test_contains_inside_and_outside():
    sq = p.path().rect(10, 10, 40, 40)
    assert sq.contains(30, 30) is True
    assert sq.contains(60, 30) is False
    assert sq.contains(30, 5) is False


def test_contains_is_false_inside_a_hole():
    ring = p.path().circle(50, 50, 80) - p.path().circle(50, 50, 30)
    assert ring.contains(50, 15) is True
    assert ring.contains(50, 50) is False


def test_contains_the_middle_of_a_pentagram_counts_as_inside():
    star = pentagram()
    assert star.contains(100, 50) is True            # the centre is wound twice: non-zero says inside
    assert star.contains(100, 2) is False


def test_contains_ignores_open_paths():
    assert line().contains(60, 50) is False
    assert p.path().contains(1, 1) is False


def test_contains_works_on_curves():
    c = p.path().circle(50, 50, 40)
    assert c.contains(50, 50) and c.contains(68, 50) and not c.contains(72, 50)


# ---------------------------------------------------------------- transforms
def test_translate():
    assert p.path().rect(10, 20, 30, 40).translate(5, -5).bounds() == (15, 15, 30, 40)


def test_scale_is_about_the_origin():
    r = p.path().rect(10, 20, 30, 40)
    assert r.scale(2).bounds() == (20, 40, 60, 80)
    assert r.scale(2, 0.5).bounds() == (20, 10, 60, 20)


def test_rotate_quarter_turn_about_the_origin_goes_clockwise_on_screen():
    out = p.path().rect(10, 0, 20, 10).rotate(90)
    # (x, y) -> (-y, x): the right-hand side of the screen swings down
    assert out.bounds() == pytest.approx((-10, 10, 10, 20), abs=1e-9)


def test_rotate_about_a_centre():
    out = p.path().rect(100, 40, 20, 20).rotate(90, 100, 50)
    assert out.bounds() == pytest.approx((90, 50, 20, 20), abs=1e-9)
    full = p.path().rect(0, 0, 10, 10).rotate(360, 5, 5)
    assert full.bounds() == pytest.approx((0, 0, 10, 10), abs=1e-9)


def test_rotate_direction_matches_f_rotate(canvas):
    shape = p.path().rect(120, 45, 50, 10)

    p.background("white")
    p.fill("red")
    p.no_stroke()
    p.draw_path(shape.rotate(37, 100, 50))
    by_path = bytes(canvas._pixels().data)

    p.background("white")
    p.fill("red")
    p.no_stroke()
    with p.saved_state():
        p.translate(100, 50)
        p.rotate(37)
        p.translate(-100, -50)
        p.draw_path(shape)
    by_canvas = bytes(canvas._pixels().data)
    assert by_path == by_canvas


def test_transforms_return_new_builders_and_leave_the_original_alone():
    a = p.path().rect(10, 20, 30, 40)
    before = a.geometry
    for out in (a.translate(1, 2), a.scale(2), a.rotate(10), a.copy()):
        assert isinstance(out, PathBuilder) and out is not a
    assert a.geometry == before


def test_originals_are_unchanged_by_queries_and_outlines():
    a = pentagram()
    before = a.geometry
    a.bounds(), a.contains(100, 50), a.expand_stroke(5)
    assert a.geometry == before


def test_copy_is_independent():
    a = p.path().rect(0, 0, 10, 10)
    b = a.copy()
    assert b.geometry == a.geometry
    b.line_to(50, 50)
    a.circle(100, 100, 20)
    assert len(a) != len(b)
    assert b.bounds() != a.bounds()


# ---------------------------------------------------------------- with the rest of the path tools
def test_outlines_work_with_booleans(canvas):
    band = line(20, 50, 120, 50).expand_stroke(20, cap="butt")
    disc = p.path().circle(70, 50, 40)
    assert fill_area(canvas, band & disc) < fill_area(canvas, band)
    assert (band - disc).bounds() is not None
    assert (band | disc).contains(70, 50)


def test_moved_paths_work_with_booleans(canvas):
    a = p.path().rect(10, 10, 40, 40)
    b = a.translate(20, 0)
    assert fill_area(canvas, a & b) == pytest.approx(20 * 40, abs=1)


def test_outline_draws_with_draw_path(canvas):
    assert fill_area(canvas, line().expand_stroke(10, cap="butt")) > 900
