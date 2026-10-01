"""Drawing modes (S-081, D-030 = B, contract F10): rect_mode, ellipse_mode, image_mode."""
from __future__ import annotations

import pytest

import funground as p
from funground import api, ir


def last(sketch):
    return sketch.frame.ops[-1]


def rect_numbers(op):
    return (op.x, op.y, op.width, op.height)


@pytest.mark.parametrize("mode, expected", [
    ("corner", (10, 20, 30, 40)),
    ("center", (-5, 0, 30, 40)),
    ("radius", (-20, -20, 60, 80)),
    ("corners", (10, 20, 20, 20)),       # (10, 20) and (30, 40) are opposite corners
])
def test_rect_under_each_mode_records_top_left_geometry(canvas, sketch, mode, expected):
    p.rect_mode(mode)
    p.rect(10, 20, 30, 40)
    assert isinstance(last(sketch), ir.Rect)
    assert rect_numbers(last(sketch)) == expected


def test_default_rect_keeps_its_original_numbers(canvas, sketch):
    p.rect(10, 20, 30, 40)
    op = last(sketch)
    assert rect_numbers(op) == (10, 20, 30, 40)
    assert all(type(v) is int for v in rect_numbers(op))


@pytest.mark.parametrize("args", [(50, 60, 10, 20), (10, 60, 50, 20), (50, 20, 10, 60), (10, 20, 50, 60)])
def test_corners_may_be_given_in_any_order(canvas, sketch, args):
    p.rect_mode("corners")
    p.rect(*args)
    assert rect_numbers(last(sketch)) == (10, 20, 40, 40)


def test_ellipse_corners_may_be_given_in_any_order(canvas, sketch):
    p.ellipse_mode("corners")
    p.ellipse(50, 60, 10, 20)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (30, 40, 40, 40)


@pytest.mark.parametrize("mode, expected", [
    ("center", (10, 20, 30, 40)),
    ("radius", (10, 20, 60, 80)),
    ("corner", (25, 40, 30, 40)),
    ("corners", (20, 30, 20, 20)),
])
def test_ellipse_under_each_mode_records_centre_geometry(canvas, sketch, mode, expected):
    p.ellipse_mode(mode)
    p.ellipse(10, 20, 30, 40)
    op = last(sketch)
    assert isinstance(op, ir.Ellipse)
    assert (op.x, op.y, op.width, op.height) == expected


def test_default_ellipse_keeps_its_original_numbers(canvas, sketch):
    p.ellipse(10, 20, 30, 40)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (10, 20, 30, 40)
    assert all(type(v) is int for v in (op.x, op.y, op.width, op.height))


@pytest.mark.parametrize("mode, expected", [
    ("corner", (10, 20, 30, 30)),
    ("corners", (10, 20, 30, 30)),       # one size: "corners" behaves as "corner"
    ("center", (-5, 5, 30, 30)),
    ("radius", (-20, -10, 60, 60)),
])
def test_square_under_each_mode(canvas, sketch, mode, expected):
    p.rect_mode(mode)
    p.square(10, 20, 30)
    assert rect_numbers(last(sketch)) == expected


@pytest.mark.parametrize("mode, expected", [
    ("center", (10, 20, 30)),
    ("radius", (10, 20, 60)),
    ("corner", (25, 35, 30)),
    ("corners", (25, 35, 30)),           # one size: "corners" behaves as "corner"
])
def test_circle_under_each_mode(canvas, sketch, mode, expected):
    p.ellipse_mode(mode)
    p.circle(10, 20, 30)
    op = last(sketch)
    assert isinstance(op, ir.Circle)
    assert (op.x, op.y, op.diameter) == expected


def test_rect_mode_does_not_change_ellipses_and_the_reverse(canvas, sketch):
    p.rect_mode("center")
    p.ellipse(10, 20, 30, 40)
    assert (last(sketch).x, last(sketch).y) == (10, 20)
    p.rect_mode("corner")
    p.ellipse_mode("corner")
    p.rect(10, 20, 30, 40)
    assert rect_numbers(last(sketch)) == (10, 20, 30, 40)


@pytest.mark.parametrize("mode", ["center", "radius", "corner", "corners"])
def test_arc_follows_ellipse_mode_exactly_like_ellipse(canvas, sketch, mode):
    """The arc's bounding ellipse is placed as ellipse() would place it."""
    p.ellipse_mode(mode)
    p.arc(10, 20, 30, 40, 0, 270, "pie")
    arc_op = last(sketch)
    p.ellipse_mode("center")
    ex, ey, ew, eh = {
        "center": (10, 20, 30, 40), "radius": (10, 20, 60, 80),
        "corner": (25, 40, 30, 40), "corners": (20, 30, 20, 20),
    }[mode]
    p.arc(ex, ey, ew, eh, 0, 270, "pie")
    assert arc_op.path == last(sketch).path


def test_modes_are_part_of_the_saved_state(canvas, sketch):
    p.rect_mode("center")
    with p.saved_state():
        p.rect_mode("radius")
        p.ellipse_mode("corner")
        p.image_mode("center")
        assert sketch.style.rect_mode == "radius"
    assert (sketch.style.rect_mode, sketch.style.ellipse_mode, sketch.style.image_mode) == ("center", "center", "corner")
    p.push()
    p.ellipse_mode("radius")
    p.pop()
    assert sketch.style.ellipse_mode == "center"


def test_a_mode_persists_across_frames():
    seen = []

    def setup():
        p.size(100, 100)

    def draw():
        if p.frame_count == 0:
            p.rect_mode("center")
        p.rect(50, 50, 20, 20)
        seen.append(api.active_sketch().frame.ops[-1])

    api.active_sketch().run_namespace({"setup": setup, "draw": draw}, max_frames=3)
    assert [rect_numbers(op) for op in seen] == [(40, 40, 20, 20)] * 3


def test_a_picture_keeps_its_own_modes(canvas, sketch):
    g = p.create_graphics(100, 100)
    g.rect_mode("center")
    g.ellipse_mode("corner")
    p.rect_mode("radius")
    g.rect(50, 50, 20, 20)
    p.rect(50, 50, 20, 20)
    assert rect_numbers(g._sketch.frame.ops[-1]) == (40, 40, 20, 20)
    assert rect_numbers(last(sketch)) == (30, 30, 40, 40)
    g.ellipse(10, 10, 20, 20)
    assert (g._sketch.frame.ops[-1].x, g._sketch.frame.ops[-1].y) == (20, 20)
    fresh = p.create_graphics(50, 50)
    fresh.rect(5, 6, 7, 8)
    assert rect_numbers(fresh._sketch.frame.ops[-1]) == (5, 6, 7, 8)


def test_a_picture_checks_mode_names_too(canvas):
    g = p.create_graphics(20, 20)
    with pytest.raises(ValueError, match="rect_mode"):
        g.rect_mode("middle")
    g.image_mode("center")
    assert g._sketch.style.image_mode == "center"


@pytest.mark.parametrize("mode, expected", [
    ("corner", (10, 20, 30, 40)),
    ("center", (-5, 0, 30, 40)),
    ("corners", (10, 20, 20, 20)),
])
def test_image_under_each_mode_with_a_size(canvas, sketch, mode, expected):
    pic = p.create_graphics(8, 6)
    p.image_mode(mode)
    p.image(pic, 10, 20, 30, 40)
    op = last(sketch)
    assert isinstance(op, ir.Image)
    assert (op.x, op.y, op.width, op.height) == expected


def test_image_center_without_a_size_uses_the_pictures_own_size(canvas, sketch):
    pic = p.create_graphics(8, 6)
    p.image_mode("center")
    p.image(pic, 10, 20)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (6, 17, 8, 6)


def test_image_corners_in_any_order(canvas, sketch):
    pic = p.create_graphics(8, 6)
    p.image_mode("corners")
    p.image(pic, 50, 60, 10, 20)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (10, 20, 40, 40)


@pytest.mark.parametrize("args", [(), (30,)])
def test_image_corners_needs_width_and_height(canvas, args):
    pic = p.create_graphics(8, 6)
    p.image_mode("corners")
    with pytest.raises(ValueError, match="corners"):
        p.image(pic, 10, 20, *args)


def test_default_image_keeps_its_original_numbers(canvas, sketch):
    pic = p.create_graphics(8, 6)
    p.image(pic, 10, 20)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (10, 20, 8, 6)


def test_default_ops_serialise_without_the_mode_fields(canvas, sketch):
    p.rect(1, 2, 3, 4)
    p.ellipse(1, 2, 3, 4)
    for op in sketch.frame.ops[-2:]:
        style = ir.op_to_jsonable(op)["style"]
        assert not {"rect_mode", "ellipse_mode", "image_mode"} & set(style)


def test_a_changed_mode_is_recorded_and_round_trips(canvas, sketch):
    p.rect_mode("center")
    p.rect(1, 2, 3, 4)
    data = ir.op_to_jsonable(last(sketch))
    assert data["style"]["rect_mode"] == "center"
    assert ir.op_from_jsonable(data).style.rect_mode == "center"


@pytest.mark.parametrize("name, valid", [
    ("rect_mode", ["corner", "corners", "center", "radius"]),
    ("ellipse_mode", ["center", "radius", "corner", "corners"]),
    ("image_mode", ["corner", "corners", "center"]),
])
def test_unknown_mode_names_raise_a_clear_error(canvas, name, valid):
    with pytest.raises(ValueError) as error:
        getattr(p, name)("middle")
    text = str(error.value)
    assert f"f.{name}()" in text and "'middle'" in text
    assert all(repr(v) in text for v in valid)


def test_radius_is_not_an_image_mode(canvas):
    with pytest.raises(ValueError, match="image_mode"):
        p.image_mode("radius")
