"""More shapes, clear and no_clip (S-041, contract F5-F7)."""
from __future__ import annotations

import math

import pytest

import funground as p
from funground import ir

WHITE, RED, BLACK = (255, 255, 255), (255, 0, 0), (0, 0, 0)


def px(canvas, x, y):
    return tuple(canvas.get_at((x, y))[:3])


def red_no_stroke():
    p.background("white")
    p.no_stroke()
    p.fill("red")


def test_square_is_placed_by_its_top_left_corner(canvas):
    red_no_stroke()
    p.square(20, 10, 30)
    assert px(canvas, 21, 11) == RED and px(canvas, 48, 38) == RED
    assert px(canvas, 19, 20) == WHITE and px(canvas, 51, 20) == WHITE


def test_triangle_is_filled_and_closed(sketch, canvas):
    red_no_stroke()
    p.triangle(10, 90, 90, 90, 50, 10)
    assert sketch.frame.ops[-1].path.is_closed  # check ops before pixels: reading a pixel renders the frame
    assert px(canvas, 50, 70) == RED            # inside
    assert px(canvas, 12, 20) == WHITE          # outside


def test_quad_goes_through_its_corners_in_order(canvas):
    red_no_stroke()
    p.quad(20, 20, 80, 20, 80, 80, 20, 80)
    assert px(canvas, 50, 50) == RED and px(canvas, 90, 50) == WHITE


def test_polygon_accepts_a_list_of_points(canvas):
    red_no_stroke()
    p.polygon([(100, 10), (190, 50), (100, 90)])
    assert px(canvas, 130, 50) == RED and px(canvas, 180, 20) == WHITE


@pytest.mark.parametrize("bad", [[(1, 2)], [(1, 2, 3), (4, 5, 6)], [1, 2, 3]])
def test_polygon_rejects_malformed_points(canvas, bad):
    with pytest.raises((ValueError, TypeError)):
        p.polygon(bad)


def test_arc_angles_are_degrees_clockwise_from_the_right(canvas):
    """F6: 0..90 is the quarter from +x down to +y (bottom-right on screen)."""
    red_no_stroke()
    p.arc(100, 50, 80, 80, 0, 90, "pie")
    assert px(canvas, 115, 65) == RED            # bottom-right quarter
    assert px(canvas, 85, 65) == WHITE           # bottom-left
    assert px(canvas, 115, 35) == WHITE          # top-right


def test_arc_stop_before_start_wraps_around(sketch, canvas):
    red_no_stroke()
    p.arc(100, 50, 80, 80, 270, 90, "pie")        # 270 -> 450: the right half
    assert px(canvas, 120, 50) == RED and px(canvas, 80, 50) == WHITE


def test_arc_modes(sketch, canvas):
    p.background("white")
    p.fill("red")
    p.stroke("black")
    p.arc(50, 50, 60, 60, 0, 180)                 # open: fill chord area, stroke curve only
    fill, stroke = sketch.frame.ops[-2], sketch.frame.ops[-1]
    assert isinstance(fill, ir.FillPath) and fill.path.is_closed
    assert isinstance(stroke, ir.StrokePath) and not stroke.path.is_closed
    p.arc(50, 50, 60, 60, 0, 180, "chord")
    assert sketch.frame.ops[-1].path.is_closed
    p.arc(50, 50, 60, 60, 0, 90, "pie")
    assert sketch.frame.ops[-1].path.segments[0] == ("move", (50, 50))   # through the centre
    with pytest.raises(ValueError, match="mode"):
        p.arc(0, 0, 10, 10, 0, 90, "wedge")


def test_arc_is_close_to_a_true_circle():
    from funground.geometry import Path

    path = Path().arc_to(0, 0, 100, 100, 0, 360)
    for seg in path.segments[1:]:
        x, y = seg[-1]
        assert math.isclose(math.hypot(x, y), 100, rel_tol=1e-9)


def test_clear_makes_pixels_transparent(sketch, frame_canvas):
    p.background("red")
    p.clear()
    op = sketch.frame.ops[-1]
    assert isinstance(op, ir.Clear) and op.color.a == 0
    sketch._render()
    assert sketch._renderer.surface.get_data()[3] == 0     # alpha byte of the first pixel


def test_clear_is_kept_in_a_saved_png(tmp_path):
    import cairo

    from funground import api

    out = tmp_path / "clear.png"

    def draw():
        p.clear()
        p.fill("red")
        p.circle(50, 50, 20)
        p.save(str(out))

    api.active_sketch().run_namespace({"setup": lambda: p.size(100, 100), "draw": draw}, max_frames=1)
    surf = cairo.ImageSurface.create_from_png(str(out))
    data, stride = surf.get_data(), surf.get_stride()
    assert data[3] == 0                                     # corner: transparent
    assert data[50 * stride + 50 * 4 + 3] == 255            # circle: opaque


def test_no_clip_lifts_the_clip_until_pop(canvas):
    p.background("white")
    p.no_stroke()
    p.fill("red")
    with p.saved_state():
        p.clip(p.path().move_to(0, 0).line_to(20, 0).line_to(20, 20).line_to(0, 20).close())
        with p.saved_state():
            p.no_clip()
            p.rect(50, 50, 10, 10)              # drawn although outside the clip
        p.rect(80, 80, 10, 10)                  # clip is back: not drawn
    assert px(canvas, 55, 55) == RED
    assert px(canvas, 85, 85) == WHITE
