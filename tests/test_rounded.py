"""Rounded corners (story S-089; contract row F14, decision D-040).

Corners are checked by pixels on the live 200x100 canvas: a red shape on a white background.
"""
from __future__ import annotations

import re
import zlib

import pytest

import funground as p
from funground import api, ir
from funground.geometry import Path, rect_radii
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

RED = (255, 0, 0)
WHITE = (255, 255, 255)


def last(sketch):
    return sketch.frame.ops[-1]


def px(canvas, x, y):
    return tuple(canvas.get_at((x, y)))[:3]


def red_shape():
    p.background("white")
    p.fill("red")
    p.no_stroke()


# ---- how many radii
def test_no_radius_is_a_sharp_rect_with_nothing_new_recorded(canvas, sketch):
    p.rect(10, 10, 50, 40)
    op = last(sketch)
    assert op.radii == ()
    assert "radii" not in ir.op_to_jsonable(op)


def test_one_radius_rounds_all_four_corners(canvas, sketch):
    p.rect(10, 10, 50, 40, 7)
    assert last(sketch).radii == (7, 7, 7, 7)


def test_four_radii_are_kept_in_order(canvas, sketch):
    p.rect(10, 10, 50, 40, 1, 2, 3, 4)
    assert last(sketch).radii == (1, 2, 3, 4)


@pytest.mark.parametrize("count", [2, 3, 5])
def test_any_other_count_is_a_value_error(canvas, count):
    radii = range(1, count + 1)
    with pytest.raises(ValueError, match="one radius or four"):
        p.rect(10, 10, 50, 40, *radii)
    with pytest.raises(ValueError, match="one radius or four"):
        p.square(10, 10, 40, *radii)
    with pytest.raises(ValueError, match="one radius or four"):
        p.path().rect(10, 10, 50, 40, *radii)


@pytest.mark.parametrize("radii", [(-1,), (5, 5, -0.5, 5), (0, 0, 0, -3)])
def test_negative_radius_is_a_value_error(canvas, radii):
    with pytest.raises(ValueError, match="negative"):
        p.rect(10, 10, 50, 40, *radii)
    with pytest.raises(ValueError, match="negative"):
        p.square(10, 10, 40, *radii)
    with pytest.raises(ValueError, match="negative"):
        p.path().rect(10, 10, 50, 40, *radii)


def test_all_zero_radii_record_nothing(canvas, sketch):
    p.rect(10, 10, 50, 40, 0)
    assert last(sketch).radii == ()
    p.rect(10, 10, 50, 40, 0, 0, 0, 0)
    assert last(sketch).radii == ()


# ---- clamping
def test_a_huge_radius_is_cut_to_half_the_shorter_side(canvas, sketch):
    p.rect(10, 10, 50, 40, 999)
    assert last(sketch).radii == (20, 20, 20, 20)
    p.rect(10, 10, 30, 80, 999)
    assert last(sketch).radii == (15, 15, 15, 15)


def test_each_radius_is_cut_on_its_own(canvas, sketch):
    p.rect(10, 10, 100, 40, 5, 500, 19, 20)
    assert last(sketch).radii == (5, 20, 19, 20)


def test_neighbouring_corners_never_overlap():
    for w, h in [(50, 40), (40, 50), (10, 100), (100, 10), (7, 7)]:
        tl, tr, br, bl = rect_radii((1000, 1000, 1000, 1000), w, h)
        assert tl + tr <= w and bl + br <= w          # along the top and the bottom
        assert tl + bl <= h and tr + br <= h          # down the left and the right


def test_a_negative_size_still_spans_the_same_box(canvas, sketch):
    p.rect(60, 50, -50, -40, 6)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (10, 10, 50, 40)
    assert op.radii == (6, 6, 6, 6)


# ---- p5 corner order, by pixels
CORNER_TIPS = {
    "top-left": (22, 12),
    "top-right": (107, 12),
    "bottom-right": (107, 67),
    "bottom-left": (22, 67),
}


@pytest.mark.parametrize("index, name", list(enumerate(["top-left", "top-right", "bottom-right", "bottom-left"])))
def test_each_radius_rounds_its_own_corner_only(canvas, index, name):
    radii = [0, 0, 0, 0]
    radii[index] = 25
    red_shape()
    p.rect(20, 10, 90, 60, *radii)
    for corner, pos in CORNER_TIPS.items():
        expected = WHITE if corner == name else RED       # the tip is cut away only where rounded
        assert px(canvas, *pos) == expected, corner


def test_the_straight_edges_stay_filled(canvas):
    red_shape()
    p.rect(20, 10, 90, 60, 25)
    assert px(canvas, 65, 40) == RED
    assert px(canvas, 65, 11) == RED            # the straight top edge
    assert px(canvas, 21, 40) == RED            # the straight left edge


def test_a_corner_is_a_quarter_circle(canvas):
    red_shape()
    p.rect(20, 10, 90, 60, 30)                  # the top-left arc is centred on (50, 40)
    assert px(canvas, 30, 20) == RED            # 28.3 from the centre: inside the radius of 30
    assert px(canvas, 25, 15) == WHITE          # 35.4 from the centre: outside


# ---- rect_mode first
def test_rect_mode_places_the_box_before_the_radii(canvas, sketch):
    p.rect_mode("center")
    p.rect(60, 40, 50, 30, 100)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (35, 25, 50, 30)
    assert op.radii == (15, 15, 15, 15)


def test_rect_mode_corners_with_radii(canvas, sketch):
    p.rect_mode("corners")
    p.rect(110, 70, 10, 20, 3)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (10, 20, 100, 50)
    assert op.radii == (3, 3, 3, 3)


def test_rect_mode_radius_with_radii(canvas, sketch):
    p.rect_mode("radius")
    p.rect(60, 40, 25, 15, 1, 2, 3, 4)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (35, 25, 50, 30)
    assert op.radii == (1, 2, 3, 4)


# ---- square
def test_square_takes_radii(canvas, sketch):
    p.square(10, 10, 40, 8)
    op = last(sketch)
    assert isinstance(op, ir.Rect) and (op.width, op.height) == (40, 40)
    assert op.radii == (8, 8, 8, 8)
    p.square(10, 10, 40, 1, 2, 3, 4)
    assert last(sketch).radii == (1, 2, 3, 4)
    p.square(10, 10, 40, 999)
    assert last(sketch).radii == (20, 20, 20, 20)


def test_square_follows_rect_mode(canvas, sketch):
    p.rect_mode("center")
    p.square(50, 50, 40, 5)
    op = last(sketch)
    assert (op.x, op.y) == (30, 30)


def test_square_without_radius_is_unchanged(canvas, sketch):
    p.square(10, 10, 40)
    assert last(sketch).radii == ()


def test_square_with_the_biggest_radius_is_a_circle(canvas):
    red_shape()
    p.square(20, 10, 60, 999)
    assert px(canvas, 21, 11) == WHITE
    assert px(canvas, 50, 40) == RED


# ---- stroke and shadow follow the corners
def test_stroke_follows_the_round_corner(canvas):
    p.background("white")
    p.no_fill()
    p.stroke("red")
    p.stroke_width(4)
    p.rect(20, 10, 90, 60, 25)
    assert px(canvas, 21, 11) == WHITE          # no stroke in the cut-away corner
    assert px(canvas, 65, 10) == RED            # the straight top edge
    assert px(canvas, 27, 17) == RED            # on the arc, 45 degrees from its centre (45, 35)


def test_shadow_follows_the_round_corner(canvas):
    p.background("white")
    p.no_stroke()
    p.fill("white")
    p.shadow(20, 20, blur=0)
    p.rect(20, 10, 60, 40, 20)                  # its shadow is the same shape moved to (40, 30)
    p.no_shadow()
    assert px(canvas, 41, 69) == WHITE          # the shadow's bottom-left corner is cut away
    assert px(canvas, 98, 68) == WHITE          # and so is its bottom-right
    assert px(canvas, 70, 60) != WHITE          # the middle of the shadow


def test_a_sharp_rect_has_a_sharp_shadow(canvas):
    p.background("white")
    p.no_stroke()
    p.fill("white")
    p.shadow(20, 20, blur=0)
    p.rect(20, 10, 60, 40)
    p.no_shadow()
    assert px(canvas, 41, 69) != WHITE
    assert px(canvas, 98, 68) != WHITE


# ---- pictures
def test_a_picture_rect_takes_radii(canvas):
    g = p.create_graphics(60, 60)
    g.fill("red")
    g.no_stroke()
    g.rect(0, 0, 60, 60, 30)
    p.background("white")
    p.image(g, 0, 0)
    assert px(canvas, 1, 1) == WHITE
    assert px(canvas, 30, 30) == RED


# ---- path builder
def test_builder_rect_takes_radii(canvas):
    red_shape()
    p.draw_path(p.path().rect(20, 10, 90, 60, 25))
    assert px(canvas, 21, 11) == WHITE
    assert px(canvas, 65, 40) == RED


def test_builder_rect_without_radii_is_unchanged():
    assert p.path().rect(1, 2, 3, 4).geometry == Path.rect(1, 2, 3, 4)


def test_builder_rect_clamps_and_orders_like_the_canvas(canvas):
    red_shape()
    p.draw_path(p.path().rect(20, 10, 90, 60, 0, 999, 0, 0))
    assert px(canvas, 21, 11) == RED            # top-left stays sharp
    assert px(canvas, 108, 11) == WHITE         # top-right is rounded (cut to 30)
    assert px(canvas, 108, 68) == RED           # bottom-right stays sharp


def test_builder_rect_adds_a_closed_sub_path():
    b = p.path().rect(0, 0, 10, 10, 2)
    assert b.is_closed
    assert any(seg[0] == "cubic" for seg in b.geometry)


def test_boolean_on_a_rounded_rect(canvas):
    tag = p.path().rect(20, 10, 60, 60, 25)
    dot = p.path().circle(90, 40, 40)
    red_shape()
    p.draw_path(tag | dot)
    assert px(canvas, 21, 11) == WHITE          # the rounded corner survives the union
    assert px(canvas, 105, 40) == RED           # the circle
    assert px(canvas, 50, 40) == RED
    red_shape()
    p.draw_path(tag - dot)
    assert px(canvas, 40, 40) == RED
    assert px(canvas, 75, 40) == WHITE          # cut out by the circle
    assert px(canvas, 21, 11) == WHITE


# ---- the IR
def test_ir_omits_radii_for_sharp_rects_and_round_trips_rounded_ones(canvas, sketch):
    p.rect(10, 10, 50, 40)
    sharp = last(sketch)
    assert "radii" not in ir.op_to_jsonable(sharp)
    assert ir.op_from_jsonable(ir.op_to_jsonable(sharp)) == sharp
    p.rect(10, 10, 50, 40, 1, 2, 3, 4)
    rounded = last(sketch)
    data = ir.op_to_jsonable(rounded)
    assert data["radii"] == [1.0, 2.0, 3.0, 4.0]
    assert ir.op_from_jsonable(data) == rounded
    assert ir.op_from_jsonable(data).radii == (1.0, 2.0, 3.0, 4.0)


# ---- vector output
def _pdf_text(path) -> bytes:
    data = path.read_bytes()
    parts = [data]
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            parts.append(zlib.decompress(m.group(1)))
        except zlib.error:
            pass
    return b"\n".join(parts)


def _pdf_of_rect(tmp_path, *radii):
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(200, 100)
    p.background("white")
    p.fill("red")
    p.rect(20, 10, 90, 60, *radii)
    p.save(str(tmp_path / "r.pdf"))
    return _pdf_text(tmp_path / "r.pdf")


def test_pdf_has_curved_corners(tmp_path):
    text = _pdf_of_rect(tmp_path, 20)
    assert re.search(rb"\d c\s", text)                          # curve operators
    assert b"/Subtype /Image" not in text and b"/Subtype/Image" not in text


def test_pdf_of_a_sharp_rect_has_no_curves(tmp_path):
    assert not re.search(rb"\d c\s", _pdf_of_rect(tmp_path))
