"""Transforms and the state stack (story S-027; contract rows F1, F2).

Pixel checks go through the `canvas` fixture (a live 200x100 window); op
checks read the sketch's Frame, which is the cross-backend contract.
"""
from __future__ import annotations

import math
import warnings

import pytest

import funground as p
from funground import ir
from funground.capabilities import FungroundWarning
from funground.geometry import Transform

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)


def px(surface, x, y):
    return tuple(surface.get_at((x, y))[:3])


def red_rects():
    p.background("white")
    p.no_stroke()
    p.fill("red")


# ---------------------------------------------------------------- F1: degrees, direction
def test_rotate_is_in_degrees_and_turns_x_into_y(canvas):
    red_rects()
    p.translate(100, 50)
    p.rotate(90)          # y-down: a quarter turn clockwise on screen
    p.rect(0, 0, 40, 10)  # local +x (40 long) now points down the screen
    assert px(canvas, 95, 70) == RED     # x 90..100, y 50..90
    assert px(canvas, 95, 55) == RED
    assert px(canvas, 105, 70) == WHITE  # not on the other side of the origin
    assert px(canvas, 120, 55) == WHITE  # where the unrotated rect would be
    assert px(canvas, 120, 45) == WHITE  # where a counter-clockwise turn would put it


def test_rotate_emits_concat_with_a_degree_rotation(sketch, canvas):
    p.translate(100, 50)
    p.rotate(30)
    p.rect(0, 0, 80, 40)
    ops = sketch.frame.ops
    assert ops[0] == ir.Concat(Transform.translation(100, 50))
    assert ops[1] == ir.Concat(Transform.rotation(30))
    assert isinstance(ops[2], ir.Rect)
    assert ops[1].transform.a == pytest.approx(math.cos(math.radians(30)))
    assert ops[1].transform.b == pytest.approx(math.sin(math.radians(30)))


def test_acceptance_translate_rotate_rect_lands_where_the_spike_drew_it(canvas):
    # sprint-04 acceptance line: translate(100, 50); rotate(30); rect(0, 0, 80, 40)
    red_rects()
    p.translate(100, 50)
    p.rotate(30)
    p.rect(0, 0, 80, 40)
    # local rect centre (40, 20) rotated 30 deg then shifted -> (124.6, 87.3)
    assert px(canvas, 124, 87) == RED
    assert px(canvas, 104, 64) == RED     # local (10, 10) rotated 30 deg then shifted -> (103.7, 63.7)
    assert px(canvas, 180, 52) == WHITE   # where the unrotated far corner would have been
    assert px(canvas, 95, 45) == WHITE


def test_radians_and_degrees_helpers():
    assert p.radians(180) == pytest.approx(math.pi)
    assert p.radians(90) == pytest.approx(math.pi / 2)
    assert p.degrees(math.pi) == pytest.approx(180)
    assert p.degrees(p.radians(37.5)) == pytest.approx(37.5)


# ---------------------------------------------------------------- F2: cumulative, order matters
def test_translate_then_scale_differs_from_scale_then_translate(canvas):
    red_rects()
    p.push()
    p.translate(20, 20)
    p.scale(2)
    p.rect(0, 0, 10, 10)     # -> x 20..40, y 20..40
    p.pop()
    p.fill("blue")
    p.scale(2)
    p.translate(20, 20)
    p.rect(0, 0, 10, 10)     # -> x 40..60, y 40..60
    assert px(canvas, 30, 30) == RED
    assert px(canvas, 50, 50) == BLUE
    assert px(canvas, 30, 50) == WHITE
    assert px(canvas, 50, 30) == WHITE


def test_translate_then_rotate_differs_from_rotate_then_translate(canvas):
    red_rects()
    p.push()
    p.translate(100, 50)
    p.rotate(90)
    p.rect(0, 0, 40, 10)     # x 90..100, y 50..90
    p.pop()
    assert px(canvas, 95, 70) == RED

    red_rects()
    p.rotate(90)
    p.translate(100, 50)     # the translation itself is rotated: lands off-canvas (x < 0)
    p.rect(0, 0, 40, 10)
    assert px(canvas, 95, 70) == WHITE
    assert all(px(canvas, x, y) == WHITE for x in range(0, 200, 7) for y in range(0, 100, 7))


def test_scale_takes_one_or_two_factors(canvas):
    red_rects()
    p.scale(2, 3)
    p.rect(10, 10, 10, 10)   # -> x 20..40, y 30..60
    assert px(canvas, 30, 45) == RED
    assert px(canvas, 30, 25) == WHITE
    assert px(canvas, 45, 45) == WHITE


def test_scale_of_zero_is_a_clear_error_at_the_call_site(canvas):
    with pytest.raises(ValueError, match="scale factor"):
        p.scale(0)
    with pytest.raises(ValueError, match="scale factor"):
        p.scale(2, 0)


def test_transforms_apply_to_text_too(sketch, canvas):
    p.background("white")
    p.translate(50, 20)
    p.text("Hi", 0, 0, "red")
    ops = sketch.frame.ops
    assert isinstance(ops[1], ir.Concat) and isinstance(ops[2], ir.Text)
    # Rendered under the transform: the glyphs sit near (50, 20), not at the origin.
    assert any(px(canvas, x, y) != WHITE for x in range(50, 80) for y in range(20, 45))
    assert all(px(canvas, x, y) == WHITE for x in range(0, 40) for y in range(0, 15))


# ---------------------------------------------------------------- push / pop
def test_nested_push_pop_restores_transforms_level_by_level(sketch, canvas):
    red_rects()
    p.push()
    p.translate(50, 0)
    p.push()
    p.translate(0, 50)
    p.rect(0, 0, 10, 10)     # at (50, 50)
    p.pop()
    p.rect(0, 0, 10, 10)     # at (50, 0)
    p.pop()
    p.rect(0, 0, 10, 10)     # at (0, 0)
    kinds = [type(op).__name__ for op in sketch.frame.ops[1:]]  # after the Clear
    assert kinds == ["Save", "Concat", "Save", "Concat", "Rect", "Restore", "Rect", "Restore", "Rect"]
    assert px(canvas, 55, 55) == RED
    assert px(canvas, 55, 5) == RED
    assert px(canvas, 5, 5) == RED
    assert px(canvas, 5, 55) == WHITE


def test_pop_restores_the_style_as_well_as_the_transform(sketch, canvas):
    red_rects()
    p.stroke_width(1)
    p.text_size(20)
    p.push()
    p.fill("blue")
    p.stroke("green")
    p.stroke_width(7)
    p.text_size(40)
    p.translate(100, 0)
    p.pop()
    assert sketch.style.fill.rgb == RED
    assert sketch.style.stroke is None
    assert sketch.style.stroke_width == 1
    assert sketch.style.text_size == 20
    p.rect(0, 0, 10, 10)
    assert px(canvas, 5, 5) == RED       # red again, and back at the origin
    assert px(canvas, 105, 5) == WHITE


def test_pop_without_push_warns_and_is_ignored(sketch, canvas):
    with pytest.warns(FungroundWarning, match="without a matching"):
        p.pop()
    assert not any(isinstance(op, ir.Restore) for op in sketch.frame.ops)


# ---------------------------------------------------------------- with p.saved_state()
def test_state_context_manager_pushes_and_pops(sketch, canvas):
    red_rects()
    with p.saved_state():
        p.fill("blue")
        p.translate(50, 50)
        p.rect(0, 0, 10, 10)
    p.rect(0, 0, 10, 10)
    kinds = [type(op).__name__ for op in sketch.frame.ops[1:]]
    assert kinds == ["Save", "Concat", "Rect", "Restore", "Rect"]
    assert sketch.style.fill.rgb == RED
    assert px(canvas, 55, 55) == BLUE
    assert px(canvas, 5, 5) == RED


def test_state_context_manager_restores_when_the_body_raises(sketch, canvas):
    red_rects()
    with pytest.raises(KeyError):
        with p.saved_state():
            p.fill("blue")
            p.translate(50, 50)
            raise KeyError("learner bug")
    assert sketch.style.fill.rgb == RED
    assert sketch._states.depth == 0
    assert isinstance(sketch.frame.ops[-1], ir.Restore)
    p.rect(0, 0, 10, 10)
    assert px(canvas, 5, 5) == RED
    assert px(canvas, 55, 55) == WHITE


def test_state_blocks_nest(sketch, canvas):
    with p.saved_state():
        p.translate(10, 0)
        with p.saved_state():
            p.translate(0, 10)
            assert sketch._states.depth == 2
        assert sketch._states.depth == 1
    assert sketch._states.depth == 0


# ---------------------------------------------------------------- end-of-frame safety
def test_unbalanced_push_warns_naming_the_count_and_does_not_leak(sketch, frame_canvas):
    canvas = frame_canvas      # a running sketch's frames; a script keeps its pushes open (R14)
    red_rects()
    p.push()
    p.push()
    p.fill("blue")
    p.translate(50, 0)
    p.rect(0, 0, 10, 10)     # blue, at (50, 0)
    with pytest.warns(FungroundWarning, match=r"2 f\.push\(\)"):
        assert px(canvas, 55, 5) == BLUE   # rendering ends the frame
    # Next frame: style and transform are back to what they were before the pushes.
    assert sketch._states.depth == 0
    assert sketch.style.fill.rgb == RED
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        p.rect(0, 0, 10, 10)
        assert px(canvas, 5, 5) == RED
    assert px(canvas, 55, 5) == BLUE       # the earlier frame's pixels are still there, unshifted


def test_unbalanced_push_is_closed_in_the_frame_itself(sketch, canvas):
    p.push()
    p.translate(5, 5)
    p.push()
    with pytest.warns(FungroundWarning):
        sketch._end_draw()
    kinds = [type(op).__name__ for op in sketch.frame.ops]
    assert kinds == ["Save", "Concat", "Save", "Restore", "Restore"]
    assert sketch._states.depth == 0


def test_top_level_transform_resets_at_the_start_of_the_next_frame(frame_canvas):
    canvas = frame_canvas      # a running sketch's frames; a script's transform carries on (R14)
    red_rects()
    p.translate(50, 0)
    p.rect(0, 0, 10, 10)
    assert px(canvas, 55, 5) == RED
    assert px(canvas, 5, 5) == WHITE
    p.rect(0, 0, 10, 10)     # a new frame: no translate in effect any more
    assert px(canvas, 5, 5) == RED


def test_unbalanced_push_in_a_run_loop_does_not_leak_between_frames():
    """A learner's draw() that forgets pop() still gets a stable picture every frame."""
    from funground import api

    seen = []

    def draw():
        seen.append(api.active_sketch()._states.depth)
        p.push()
        p.fill("blue")
        p.translate(30, 0)

    import pygame

    pygame.init()
    with pytest.warns(FungroundWarning, match=r"1 f\.push\(\)"):
        api.active_sketch().run_namespace({"draw": draw}, fps=1000, max_frames=3)
    assert seen == [0, 0, 0]
    assert api.active_sketch().style.fill.rgb == WHITE


def test_style_set_without_push_carries_into_the_next_frame_like_p5():
    """Contract F2 (S-067 wording): transforms reset every frame; unpushed style does not."""
    from funground import api

    seen = []

    def draw():
        seen.append(api.active_sketch().style.fill.rgb)
        p.fill("blue")

    import pygame

    pygame.init()
    api.active_sketch().run_namespace({"draw": draw}, fps=1000, max_frames=3)
    assert seen == [WHITE, BLUE, BLUE]


# ---------------------------------------------------------------- S-043: shear and matrices
def test_apply_matrix_with_a_rotation_equals_rotate(canvas):
    import math

    def draw(use_matrix):
        red_rects()
        with p.saved_state():
            p.translate(100, 50)
            if use_matrix:
                a = math.radians(30)
                p.apply_matrix(math.cos(a), math.sin(a), -math.sin(a), math.cos(a), 0, 0)
            else:
                p.rotate(30)
            p.rect(-30, -10, 60, 20)
        return [px(canvas, x, y) for x in range(60, 140, 3) for y in range(20, 80, 3)]

    assert draw(True) == draw(False)


def test_shear_x_slants_sideways(canvas):
    red_rects()
    p.shear_x(45)                     # x moves by y
    p.rect(10, 40, 20, 20)            # covers x 50..90 at y 40..60 roughly
    assert px(canvas, 70, 50) == RED
    assert px(canvas, 20, 50) == WHITE


def test_shear_y_slants_up_and_down(canvas):
    red_rects()
    p.shear_y(45)                     # y moves by x
    p.rect(40, 0, 20, 20)             # at x ~50 the rect sits at y ~50..70
    assert px(canvas, 50, 60) == RED
    assert px(canvas, 50, 10) == WHITE


def test_ninety_degree_shear_and_flat_matrix_are_errors(canvas):
    with pytest.raises(ValueError):
        p.shear_x(90)
    with pytest.raises(ValueError):
        p.apply_matrix(1, 2, 2, 4, 0, 0)


def test_reset_matrix_forgets_transforms_until_pop(canvas):
    red_rects()
    with p.saved_state():
        p.translate(150, 0)
        with p.saved_state():
            p.reset_matrix()
            p.rect(0, 0, 10, 10)          # at the real origin
        p.rect(0, 20, 10, 10)             # translate is back: x 150..160
    assert px(canvas, 5, 5) == RED
    assert px(canvas, 155, 25) == RED and px(canvas, 5, 25) == WHITE


def test_reset_matrix_keeps_the_hidpi_scale(monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    from funground import api
    from funground.sketch import Sketch

    api.use_sketch(Sketch())
    from conftest import open_frame_window

    open_frame_window(100, 50)          # a running sketch's window (a top-level size() has none, R14)
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.translate(40, 0)
    p.reset_matrix()
    p.rect(0, 0, 10, 10)
    s = api.active_sketch()
    s._render()
    surf = s._platform.target
    assert tuple(surf.get_at((19, 19))[:3]) == RED        # 10 logical px == 20 physical
    assert tuple(surf.get_at((21, 5))[:3]) == WHITE
