"""Stroke styles and smoothing (S-042, contract S11 and C6a)."""
from __future__ import annotations

import pytest

import playground as p
from playground import api, ir

WHITE, BLACK = (255, 255, 255), (0, 0, 0)


def px(canvas, x, y):
    return tuple(canvas.get_at((x, y))[:3])


def thick_black():
    p.background("white")
    p.stroke("black")
    p.stroke_width(10)


def test_default_is_round_caps_and_joins(sketch, canvas):
    st = sketch.style
    assert (st.stroke_cap, st.stroke_join, st.miter_limit, st.dash) == ("round", "round", 10.0, ())


@pytest.mark.parametrize("cap, past_the_end_is_black", [("butt", False), ("square", True), ("round", True)])
def test_caps_extend_past_the_end_or_not(canvas, cap, past_the_end_is_black):
    thick_black()
    p.stroke_cap(cap)
    p.line(50, 50, 150, 50)
    assert (px(canvas, 152, 50) == BLACK) is past_the_end_is_black    # 2 px beyond the end, on the axis
    corner_black = px(canvas, 154, 54) == BLACK                       # only square covers the corner
    assert corner_black is (cap == "square")


def test_joins_change_the_corner(canvas):
    """A 90-degree corner at (100, 20): miter fills the outer corner, bevel and round do not."""
    results = {}
    for join in ("miter", "bevel", "round"):
        thick_black()
        p.no_fill()
        p.stroke_join(join)
        p.begin_shape()
        p.vertex(40, 20)
        p.vertex(100, 20)
        p.vertex(100, 80)
        p.end_shape()
        results[join] = px(canvas, 104, 16)            # the outer tip of the corner
    assert results["miter"] == BLACK
    assert results["bevel"] == WHITE and results["round"] != BLACK


def test_dash_leaves_gaps(canvas):
    thick_black()
    p.stroke_cap("butt")
    p.stroke_dash([10, 10])
    p.line(20, 50, 180, 50)
    assert px(canvas, 25, 50) == BLACK and px(canvas, 35, 50) == WHITE and px(canvas, 45, 50) == BLACK


def test_dash_offset_shifts_the_pattern(canvas):
    thick_black()
    p.stroke_cap("butt")
    p.stroke_dash([10, 10], offset=10)
    p.line(20, 50, 180, 50)
    assert px(canvas, 25, 50) == WHITE and px(canvas, 35, 50) == BLACK


def test_no_dash_and_single_length(sketch, canvas):
    p.stroke_dash(8)
    assert sketch.style.dash == (8.0,)
    p.no_dash()
    assert sketch.style.dash == () and sketch.style.dash_offset == 0.0


def test_stroke_style_applies_to_paths_and_is_carried_in_the_ir(sketch, canvas):
    p.stroke_cap("butt")
    p.stroke_join("bevel")
    p.stroke_dash([4, 2])
    p.begin_shape()
    p.vertex(0, 0)
    p.vertex(10, 10)
    p.end_shape()
    op = sketch.frame.ops[-1]
    assert isinstance(op, ir.StrokePath)
    assert (op.cap, op.join, op.dash) == ("butt", "bevel", (4.0, 2.0))


def test_stroke_style_is_restored_by_saved_state(sketch, canvas):
    with p.saved_state():
        p.stroke_cap("butt")
        p.stroke_dash([3, 3])
    assert sketch.style.stroke_cap == "round" and sketch.style.dash == ()


@pytest.mark.parametrize("call", [
    lambda: p.stroke_cap("project"), lambda: p.stroke_join("sharp"), lambda: p.miter_limit(0.5),
    lambda: p.stroke_dash([]), lambda: p.stroke_dash([-1, 2]), lambda: p.stroke_dash([0, 0]),
])
def test_bad_values_are_learner_readable_errors(canvas, call):
    with pytest.raises(ValueError):
        call()


def test_no_smooth_gives_hard_edges_until_smooth(canvas):
    def edge_values():
        p.background("white")
        p.no_stroke()
        p.fill("black")
        p.circle(100, 50, 61)
        return {px(canvas, x, 50) for x in range(60, 80)}
    assert len(edge_values() - {WHITE, BLACK}) > 0           # anti-aliased: greys on the edge
    p.no_smooth()
    assert edge_values() <= {WHITE, BLACK}                    # hard edge: only black and white
    p.smooth()
    assert len(edge_values() - {WHITE, BLACK}) > 0


def test_no_smooth_is_a_sketch_setting_that_survives_frames_and_pop():
    import pygame

    seen = []

    def setup():
        p.size(100, 100)
        p.no_smooth()

    def draw():
        with p.saved_state():
            pass
        seen.append(api.active_sketch().frame.ops[:1])

    pygame.init()
    api.active_sketch().run_namespace({"setup": setup, "draw": draw}, max_frames=3)
    assert all(ops and ops[0] == ir.SetAntialias(False) for ops in seen[1:])
