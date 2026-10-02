"""Text to points (story S-104; contract row T16).

The test font has a square-cornered "B" (a rectangle 420 x 700 font units), so at size 100 its
outline is a 42 x 70 pixel rectangle with a perimeter of 224 pixels.
"""
from __future__ import annotations

import math

import pytest

import funground as p
from funground import api
from funground.geometry import FLATNESS, contours
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from fontmaker import make_static_font


@pytest.fixture
def sketch():
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(400, 300)
    return s


@pytest.fixture
def box_font(tmp_path):
    return p.load_font(make_static_font(tmp_path))


def dist_to_polyline(pt, poly):
    best = math.inf
    for (ax, ay), (bx, by) in zip(poly, poly[1:]):
        dx, dy = bx - ax, by - ay
        length2 = dx * dx + dy * dy
        t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / length2))
        best = min(best, math.hypot(pt[0] - (ax + t * dx), pt[1] - (ay + t * dy)))
    return best


def arc_position(pt, poly):
    """How far along the polyline (from its start) the point nearest to *pt* is."""
    best, pos, walked = math.inf, 0.0, 0.0
    for (ax, ay), (bx, by) in zip(poly, poly[1:]):
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        t = 0.0 if length == 0 else max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / length ** 2))
        d = math.hypot(pt[0] - (ax + t * dx), pt[1] - (ay + t * dy))
        if d < best:
            best, pos = d, walked + t * length
        walked += length
    return pos


def test_count_follows_perimeter_over_spacing(sketch, box_font):
    p.text_font(box_font, 100)
    pts = p.text_to_points("B", 10, 10, 5)
    assert len(pts) == round(224 / 5)               # 44.8 -> the points at 0, 5, ... 220: 45 of them
    assert len(pts) in (44, 45)


def test_spacing_changes_the_count(sketch, box_font):
    p.text_font(box_font, 100)
    assert len(p.text_to_points("B", 10, 10, 2)) == 112
    assert len(p.text_to_points("B", 10, 10, 224)) == 1


def test_points_are_plain_float_tuples(sketch, box_font):
    p.text_font(box_font, 100)
    pts = p.text_to_points("B", 10, 10)
    assert isinstance(pts, list)
    assert all(isinstance(pt, tuple) and len(pt) == 2 and all(isinstance(v, float) for v in pt) for pt in pts)


def test_points_lie_on_the_outline_of_the_box(sketch, box_font):
    p.text_font(box_font, 100)
    poly = contours(p.text_path("B", 10, 10).geometry)[0][0]
    for pt in p.text_to_points("B", 10, 10, 3):
        assert dist_to_polyline(pt, poly) < 1e-6


def test_points_lie_on_a_curved_outline(sketch):
    p.text_size(120)
    geometry = p.text_path("Og", 5, 5).geometry
    polys = [poly for poly, _ in contours(geometry, 1e-5)]
    pts = p.text_to_points("Og", 5, 5, 4)
    assert len(pts) > 100
    for pt in pts:
        assert min(dist_to_polyline(pt, poly) for poly in polys) < 2 * FLATNESS


def test_spacing_is_accurate_along_curves(sketch):
    p.text_size(150)
    spacing = 6
    poly = contours(p.text_path("O", 5, 5).geometry, 1e-5)[0][0]       # the outer ring of the O
    pts = [pt for pt in p.text_to_points("O", 5, 5, spacing) if dist_to_polyline(pt, poly) < 0.05]
    positions = [arc_position(pt, poly) for pt in pts]
    gaps = [b - a for a, b in zip(positions, positions[1:])]
    assert len(gaps) > 20
    assert all(abs(g - spacing) / spacing < 0.01 for g in gaps)


def test_each_outline_starts_at_its_start_point(sketch):
    p.text_size(100)
    geometry = p.text_path("Bo", 10, 10).geometry
    starts = [seg[1] for seg in geometry.segments if seg[0] == "move"]
    pts = p.text_to_points("Bo", 10, 10, 7)
    assert len(starts) == 5                            # B has three outlines (outside, two holes), o has two
    for start in starts:
        assert any(math.hypot(pt[0] - start[0], pt[1] - start[1]) < 1e-9 for pt in pts)
    assert pts[0] == pytest.approx(starts[0])


def test_leftover_carries_between_straight_pieces(sketch, box_font):
    p.text_font(box_font, 100)
    pts = p.text_to_points("B", 10, 10, 30)             # 30 does not divide the 42 and 70 sides
    assert len(pts) == 8                                # 224 / 30 = 7.47 -> points at 0, 30, ... 210
    for a, b in zip(pts, pts[1:]):
        assert math.hypot(b[0] - a[0], b[1] - a[1]) <= 30 + 1e-9


def test_empty_and_blank_messages_give_no_points(sketch):
    assert p.text_to_points("", 10, 10) == []
    assert p.text_to_points("   ", 10, 10) == []
    assert p.text_to_points("\n", 10, 10) == []


@pytest.mark.parametrize("bad", [0, -1, -0.5, float("nan")])
def test_spacing_must_be_above_zero(sketch, bad):
    with pytest.raises(ValueError, match="spacing above 0"):
        p.text_to_points("A", 10, 10, bad)


def test_spacing_must_be_a_number(sketch):
    with pytest.raises(TypeError):
        p.text_to_points("A", 10, 10, "5")


def test_nothing_is_drawn_and_state_is_unchanged(sketch):
    p.text_to_points("Hello", 10, 10)
    assert list(sketch.frame) == []


def test_alignment_matches_text_path(sketch):
    p.text_size(40)
    p.text_align("center", "center")
    centred = p.text_to_points("Mid", 200, 100, 5)
    p.text_align("left", "top")
    left = p.text_to_points("Mid", 200, 100, 5)
    p.text_align("right", "baseline")
    right = p.text_to_points("Mid", 200, 100, 5)
    assert max(x for x, _ in left) > min(x for x, _ in left) + 40
    assert min(x for x, _ in left) > 195 and max(x for x, _ in right) < 205
    assert min(x for x, _ in centred) < 200 < max(x for x, _ in centred)
    xs = [x for x, _ in right]
    x0, _, x1, _ = p.text_path("Mid", 200, 100).geometry.bounds()
    assert min(xs) >= x0 - 1e-6 and max(xs) <= x1 + 1e-6


def test_points_stay_inside_the_text_path_bounds(sketch):
    p.text_size(30)
    p.text_leading(40)
    pts = p.text_to_points("one\ntwo", 20, 20, 4)
    x0, y0, x1, y1 = p.text_path("one\ntwo", 20, 20).geometry.bounds()
    assert all(x0 - 1e-6 <= x <= x1 + 1e-6 and y0 - 1e-6 <= y <= y1 + 1e-6 for x, y in pts)


def test_several_lines_give_more_points_and_lie_lower(sketch):
    p.text_size(30)
    p.text_leading(50)
    one = p.text_to_points("ab", 20, 20, 4)
    two = p.text_to_points("ab\nab", 20, 20, 4)
    assert len(two) == 2 * len(one)
    assert max(y for _, y in two) > max(y for _, y in one) + 40


def test_formatted_string_is_accepted(sketch):
    fs = p.FormattedString()
    fs.append("Hi")
    assert len(p.text_to_points(fs, 10, 10, 5)) > 5
