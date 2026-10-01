"""Path shapes and booleans (story S-086; contract row F11; ADR-005).

Areas are checked by drawing a result on the live 200x100 canvas and adding up how red it is.
"""
from __future__ import annotations

import math
import re
import zlib

import pytest

import funground as p
from funground import api
from funground.geometry import Path
from funground.paths import PathBuilder
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)


def painted_area(canvas) -> float:
    """Area covered by red on white: edge pixels count in part."""
    data = bytes(canvas._pixels().data)          # BGRA; red is (b=0, g=0), white is (255, 255)
    return sum((255 - data[i]) / 255 for i in range(0, len(data), 4))


def fill_area(canvas, *paths) -> float:
    p.background("white")
    p.fill("red")
    p.no_stroke()
    for path in paths:
        p.draw_path(path)
    return painted_area(canvas)


def two_rects():
    a = p.path().rect(10, 10, 80, 80)       # 6400
    b = p.path().rect(50, 30, 80, 60)       # 4800, overlap 40 x 60 = 2400
    return a, b


def pentagram(cx=100, cy=50, r=45):
    return p.path().polygon([(cx + r * math.cos(math.radians(-90 + i * 144)),
                              cy + r * math.sin(math.radians(-90 + i * 144))) for i in range(5)])


def segment_kinds(path: PathBuilder) -> set[str]:
    return {seg[0] for seg in path.geometry.segments}


def count(path: PathBuilder, kind: str) -> int:
    return sum(1 for s in path.geometry.segments if s[0] == kind)


# ---------------------------------------------------------------- shape helpers
def test_helpers_add_closed_subpaths_and_return_the_builder():
    b = p.path()
    assert b.rect(1, 2, 3, 4) is b
    assert b.circle(50, 50, 10) is b
    assert b.ellipse(50, 50, 20, 10) is b
    assert b.polygon([(0, 0), (5, 0), (5, 5)]) is b
    assert b.is_closed
    assert count(b, "move") == 4 and count(b, "close") == 4


def test_rect_is_anchored_at_its_top_left():
    assert p.path().rect(10, 20, 30, 40).geometry == Path.rect(10, 20, 30, 40)


def test_ellipse_and_circle_are_centred_on_their_point_with_diameters():
    assert p.path().ellipse(100, 50, 60, 20).geometry == Path.ellipse(100, 50, 30, 10)
    assert p.path().circle(100, 50, 40).geometry == Path.ellipse(100, 50, 20, 20)
    assert p.path().circle(100, 50, 40).geometry.bounds() == (80, 30, 120, 70)


def test_polygon_goes_through_its_points_in_order():
    pts = [(1, 2), (30, 4), (15, 40)]
    assert p.path().polygon(pts).geometry.segments == (
        ("move", (1, 2)), ("line", (30, 4)), ("line", (15, 40)), ("close",))


def test_polygon_needs_three_points():
    with pytest.raises(ValueError, match="at least 3 points"):
        p.path().polygon([(0, 0), (1, 1)])


def test_helpers_ignore_the_drawing_modes(canvas):
    p.rect_mode("center")
    p.ellipse_mode("corner")
    assert p.path().rect(10, 10, 20, 20).geometry == Path.rect(10, 10, 20, 20)
    assert p.path().circle(50, 50, 10).geometry == Path.ellipse(50, 50, 5, 5)


def test_helpers_add_to_what_is_already_there():
    b = p.path().move_to(0, 0).line_to(5, 5).close().rect(10, 10, 5, 5)
    assert len(b) == 3 + 5


# ---------------------------------------------------------------- areas
def test_union_area(canvas):
    a, b = two_rects()
    assert fill_area(canvas, a.union(b)) == pytest.approx(8800, abs=1)


def test_intersection_area(canvas):
    a, b = two_rects()
    assert fill_area(canvas, a.intersection(b)) == pytest.approx(2400, abs=1)


def test_difference_area(canvas):
    a, b = two_rects()
    assert fill_area(canvas, a.difference(b)) == pytest.approx(4000, abs=1)
    assert fill_area(canvas, b.difference(a)) == pytest.approx(2400, abs=1)


def test_xor_area(canvas):
    a, b = two_rects()
    assert fill_area(canvas, a.xor(b)) == pytest.approx(6400, abs=1)


def test_circle_areas_within_a_tolerance(canvas):
    a = p.path().circle(60, 50, 60)
    b = p.path().circle(100, 50, 60)
    r, d = 30.0, 40.0
    lens = 2 * r * r * math.acos(d / (2 * r)) - d / 2 * math.sqrt(4 * r * r - d * d)
    disc = math.pi * r * r
    assert fill_area(canvas, a | b) == pytest.approx(2 * disc - lens, rel=0.01)
    assert fill_area(canvas, a & b) == pytest.approx(lens, rel=0.02)
    assert fill_area(canvas, a - b) == pytest.approx(disc - lens, rel=0.01)
    assert fill_area(canvas, a ^ b) == pytest.approx(2 * disc - 2 * lens, rel=0.01)


def test_each_input_is_read_with_the_non_zero_rule(canvas):
    star = pentagram()
    plain = fill_area(canvas, star)                      # centre filled (F3)
    everything = p.path().rect(0, 0, 200, 100)
    assert fill_area(canvas, star & everything) == pytest.approx(plain, rel=0.01)
    assert fill_area(canvas, star | p.path()) == pytest.approx(plain, rel=0.01)


# ---------------------------------------------------------------- curves, inputs, operators
def test_curves_stay_curves():
    a = p.path().circle(60, 50, 60)
    b = p.path().circle(100, 50, 60)
    for result in (a | b, a & b, a - b, a ^ b):
        assert segment_kinds(result) <= {"move", "line", "cubic", "close"}
        assert count(result, "cubic") >= 2
        assert result.is_closed


def test_results_are_funground_paths():
    a, b = two_rects()
    r = a.union(b)
    assert isinstance(r, PathBuilder) and isinstance(r.geometry, Path)


def test_inputs_are_unchanged():
    a = p.path().circle(60, 50, 60)
    b = p.path().circle(100, 50, 60)
    ga, gb = a.geometry, b.geometry
    for op in (a.union, a.intersection, a.difference, a.xor):
        r = op(b)
        assert r is not a and r is not b
    assert a.remove_overlap() is not a
    assert a.geometry == ga and b.geometry == gb


def test_operators_equal_the_methods():
    a = p.path().circle(60, 50, 60)
    b = p.path().rect(70, 20, 60, 60)
    assert (a | b).geometry == a.union(b).geometry
    assert (a & b).geometry == a.intersection(b).geometry
    assert (a - b).geometry == a.difference(b).geometry
    assert (a ^ b).geometry == a.xor(b).geometry


def test_a_result_can_be_combined_again(canvas):
    a, b = two_rects()
    c = p.path().rect(0, 0, 200, 100)
    assert fill_area(canvas, (a | b) & c) == pytest.approx(8800, abs=1)
    assert fill_area(canvas, c - (a | b)) == pytest.approx(20000 - 8800, abs=1)


# ---------------------------------------------------------------- open sub-paths
def test_open_subpaths_take_no_part(canvas):
    a, b = two_rects()
    zigzag = p.path().move_to(100, 5).line_to(190, 5).line_to(190, 95)          # never closed
    mixed = p.path().rect(10, 10, 80, 80).move_to(100, 5).line_to(190, 5).line_to(190, 95)
    assert fill_area(canvas, mixed | b) == pytest.approx(8800, abs=1)
    assert fill_area(canvas, a | zigzag) == pytest.approx(6400, abs=1)
    assert (zigzag | a).geometry.bounds() == (10, 10, 90, 90)
    assert (zigzag | zigzag).is_empty
    assert fill_area(canvas, mixed.remove_overlap()) == pytest.approx(6400, abs=1)


# ---------------------------------------------------------------- empty results
def test_an_empty_result_is_an_empty_path_drawn_as_nothing(canvas):
    a = p.path().rect(10, 10, 20, 20)
    b = p.path().rect(100, 10, 20, 20)
    for r in (a & b, a - a, a ^ a, p.path() | p.path(), p.path().remove_overlap()):
        assert r.is_empty
        assert r.geometry == Path()
    assert fill_area(canvas, a & b) == 0


# ---------------------------------------------------------------- remove_overlap
def test_remove_overlap_of_two_overlapping_rectangles(canvas):
    both = p.path().rect(10, 10, 80, 80).rect(50, 30, 80, 60)
    clean = both.remove_overlap()
    assert fill_area(canvas, clean) == pytest.approx(8800, abs=1)
    assert count(clean, "move") == 1


def test_remove_overlap_on_a_figure_eight(canvas):
    eight = (p.path().move_to(100, 50).curve_to(130, 10, 170, 10, 170, 50)
             .curve_to(170, 90, 130, 90, 100, 50).curve_to(70, 10, 30, 10, 30, 50)
             .curve_to(30, 90, 70, 90, 100, 50).close())
    area = fill_area(canvas, eight)
    clean = eight.remove_overlap()
    assert clean.is_closed and not clean.is_empty
    assert fill_area(canvas, clean) == pytest.approx(area, rel=0.01)
    assert count(clean, "cubic") >= 4


def test_remove_overlap_on_a_star_leaves_one_outline(canvas):
    star = pentagram()
    area = fill_area(canvas, star)
    clean = star.remove_overlap()
    assert fill_area(canvas, clean) == pytest.approx(area, rel=0.01)
    assert count(clean, "move") == 1 and count(clean, "close") == 1
    assert count(clean, "line") in (9, 10)             # ten outline corners, no inner crossings


def test_remove_overlap_keeps_holes(canvas):
    donut = p.path().circle(100, 50, 80) - p.path().circle(100, 50, 40)
    area = fill_area(canvas, donut)
    assert area == pytest.approx(math.pi * (40 ** 2 - 20 ** 2), rel=0.01)
    assert fill_area(canvas, donut.remove_overlap()) == pytest.approx(area, rel=0.01)


# ---------------------------------------------------------------- errors
@pytest.mark.parametrize("method", ["union", "intersection", "difference", "xor"])
@pytest.mark.parametrize("bad", [None, 3, "rect", Path.rect(0, 0, 1, 1)])
def test_methods_need_a_path_builder(method, bad):
    with pytest.raises(TypeError, match=rf"f\.path\(\)\.{method}\(\) needs another path"):
        getattr(p.path().rect(0, 0, 5, 5), method)(bad)


@pytest.mark.parametrize("op", [lambda a, b: a | b, lambda a, b: a & b, lambda a, b: a - b, lambda a, b: a ^ b])
def test_operators_need_a_path_builder_too(op):
    with pytest.raises(TypeError, match="needs another path"):
        op(p.path().rect(0, 0, 5, 5), 7)


# ---------------------------------------------------------------- use of results
def test_result_works_with_draw_path_fill_and_stroke(canvas):
    a, b = two_rects()
    p.background("white")
    p.fill("red")
    p.stroke("blue")
    p.stroke_width(2)
    p.draw_path(a & b)
    assert tuple(canvas.get_at((70, 60)))[:3] == RED
    assert tuple(canvas.get_at((20, 20)))[:3] == WHITE
    assert tuple(canvas.get_at((50, 60)))[:3] == BLUE        # the left edge of the overlap


def test_result_works_as_a_clip(canvas):
    a, b = two_rects()
    p.background("white")
    p.no_stroke()
    p.fill("red")
    with p.saved_state():
        p.clip(a - b)
        p.rect(0, 0, 200, 100)
    assert tuple(canvas.get_at((20, 20)))[:3] == RED         # in a, not in b
    assert tuple(canvas.get_at((70, 60)))[:3] == WHITE       # in both
    assert tuple(canvas.get_at((120, 60)))[:3] == WHITE      # only in b


# ---------------------------------------------------------------- vector output
def _pdf_text(path) -> bytes:
    data = path.read_bytes()
    parts = [data]
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            parts.append(zlib.decompress(m.group(1)))
        except zlib.error:
            pass
    return b"\n".join(parts)


def test_pdf_with_a_boolean_result_is_vector(tmp_path):
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(200, 100)
    p.background("white")
    p.fill("red")
    p.draw_path(p.path().circle(60, 50, 60) | p.path().circle(100, 50, 60))
    p.save(str(tmp_path / "b.pdf"))
    text = _pdf_text(tmp_path / "b.pdf")
    assert re.search(rb"\d m\s", text) and re.search(rb"\d c\s", text)     # move and curve operators
    assert b"/Subtype /Image" not in text and b"/Subtype/Image" not in text


def test_percent_is_difference_as_in_drawbot():
    a = p.path().rect(0, 0, 100, 100)
    b = p.path().circle(50, 50, 60)
    assert list((a % b).geometry) == list(a.difference(b).geometry)

