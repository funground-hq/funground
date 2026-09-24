"""Pinned v0.5 drawing/runtime semantics, verified pixel by pixel.

Each test documents one row of docs/Semantic_Contract.md. When v0.6 changes a
rule deliberately (e.g. stroke alignment), update the contract *and* the test
in the same commit.
"""
from __future__ import annotations

import pygame
import pytest

import playground as p
from playground import api
from playground.platform.pygame_platform import key_code

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)


def px(surface, x, y):
    return tuple(surface.get_at((x, y))[:3])


# ---------------------------------------------------------------- defaults
def test_default_style_and_state(sketch):
    assert (sketch.style.fill.rgb, sketch.style.stroke.rgb) == ((255, 255, 255), (0, 0, 0))
    assert sketch.style.stroke_width == 1
    assert sketch.style.text_size == 20
    assert (sketch.width, sketch.height) == (640, 480)
    assert sketch.fps == 60
    assert sketch.title == "playground"


def test_size_sets_live_values(canvas):
    assert (p.width, p.height) == (200, 100)


@pytest.mark.parametrize("args", [(0, 100), (100, 0), (-1, 100)])
def test_size_rejects_non_positive_dimensions(args):
    pygame.init()
    with pytest.raises(ValueError):
        p.size(*args)


def test_size_rejects_non_positive_fps():
    pygame.init()
    with pytest.raises(ValueError):
        p.size(100, 100, fps=0)


def test_drawing_before_size_is_a_clear_error():
    with pytest.raises(RuntimeError, match="p.size"):
        p.circle(0, 0, 10)


# ---------------------------------------------------------------- coordinates
def test_origin_is_top_left_y_down(canvas):
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.rect(0, 0, 10, 10)
    assert px(canvas, 0, 0) == RED
    assert px(canvas, 9, 9) == RED
    assert px(canvas, 10, 10) == WHITE
    assert px(canvas, 0, 99) == WHITE  # bottom-left is far from the origin


def test_rect_anchors_at_top_left(canvas):
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.rect(50, 20, 30, 10)
    assert px(canvas, 50, 20) == RED
    assert px(canvas, 79, 29) == RED
    assert px(canvas, 49, 20) == WHITE
    assert px(canvas, 80, 29) == WHITE
    assert px(canvas, 50, 30) == WHITE


def test_circle_is_centred_and_takes_a_diameter(canvas):
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.circle(100, 50, 40)  # radius 20
    assert px(canvas, 100, 50) == RED
    assert px(canvas, 82, 50) == RED
    assert px(canvas, 118, 50) == RED
    assert px(canvas, 100, 32) == RED
    assert px(canvas, 78, 50) == WHITE
    assert px(canvas, 122, 50) == WHITE


def test_ellipse_is_centred(canvas):
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.ellipse(100, 50, 80, 20)
    assert px(canvas, 100, 50) == RED
    assert px(canvas, 65, 50) == RED
    assert px(canvas, 135, 50) == RED
    assert px(canvas, 100, 42) == RED
    assert px(canvas, 100, 38) == WHITE
    assert px(canvas, 58, 50) == WHITE


def test_fractional_coordinates_are_honoured_with_antialiasing(canvas):
    """Contract C6 (D-005): v0.5 rounded to whole pixels; v0.6 keeps fractions and anti-aliases."""
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.rect(10.5, 10, 5, 5)
    assert px(canvas, 12, 12) == RED
    edge = px(canvas, 10, 12)               # half-covered column: a blend, not a hard edge
    assert edge != RED and edge != WHITE and edge[0] == 255


# ---------------------------------------------------------------- fill / stroke
def test_no_fill_and_no_stroke_draw_nothing(canvas):
    p.background("white")
    p.no_fill()
    p.no_stroke()
    p.rect(10, 10, 50, 50)
    p.circle(100, 50, 40)
    p.line(0, 0, 199, 99)
    p.point(150, 80)
    assert all(px(canvas, x, y) == WHITE for x, y in ((10, 10), (30, 30), (100, 50), (100, 50), (150, 80)))


def test_stroke_is_centred_on_the_edge(canvas):
    """Contract S4 (D-004): v0.5 grew strokes inward; v0.6 centres them on the geometric edge."""
    p.background("white")
    p.no_fill()
    p.stroke("black")
    p.stroke_width(6)
    p.rect(20, 20, 40, 40)
    assert px(canvas, 17, 40) == BLACK   # 3 px outside the edge
    assert px(canvas, 22, 40) == BLACK   # 3 px inside
    assert px(canvas, 16, 40) == WHITE
    assert px(canvas, 23, 40) == WHITE


def test_stroke_draws_over_fill(canvas):
    p.background("white")
    p.fill("red")
    p.stroke("black")
    p.stroke_width(2)
    p.rect(20, 20, 40, 40)
    assert px(canvas, 20, 40) == BLACK
    assert px(canvas, 40, 40) == RED


def test_stroke_width_minimum_is_one():
    with pytest.raises(ValueError):
        p.stroke_width(0)
    p.stroke_width(1)
    assert api.active_sketch().style.stroke_width == 1


def test_point_size_follows_stroke_width(canvas):
    """Contract S7: a dot of diameter ~stroke_width in the stroke colour (anti-aliased since v0.6)."""
    p.background("white")
    p.stroke("black")
    p.stroke_width(1)
    p.point(50, 50)
    assert px(canvas, 50, 50) != WHITE      # a 1-px dot lands on its pixel
    assert px(canvas, 53, 50) == WHITE
    p.stroke_width(8)  # radius 4
    p.point(120, 50)
    assert px(canvas, 120, 50) == BLACK
    assert px(canvas, 122, 50) == BLACK
    assert px(canvas, 126, 50) == WHITE


def test_line_uses_stroke_only(canvas):
    p.background("white")
    p.fill("red")
    p.stroke("black")
    p.stroke_width(2)                       # a 2-px line centred on y=50 covers rows 49 and 50 fully
    p.line(0, 50, 199, 50)
    assert px(canvas, 100, 50) == BLACK and px(canvas, 100, 49) == BLACK
    assert px(canvas, 100, 52) == WHITE
    p.no_stroke()
    p.line(0, 20, 199, 20)
    assert px(canvas, 100, 20) == WHITE


# ---------------------------------------------------------------- colour
def test_colour_forms_are_passed_through(canvas):
    p.no_stroke()
    for value, expected in (("red", RED), ((0, 180, 100), (0, 180, 100)), ("#F05A45", (0xF0, 0x5A, 0x45))):
        p.background("white")
        p.fill(value)
        p.rect(0, 0, 10, 10)
        assert px(canvas, 5, 5) == expected


def test_alpha_is_honoured(canvas):
    """Contract S2 (D-003): v0.5 dropped alpha on the window; v0.6 composites it."""
    p.background("white")
    p.no_stroke()
    p.fill((0, 0, 255, 128))
    p.rect(0, 0, 10, 10)
    r, g, b = px(canvas, 5, 5)
    assert b == 255 and 120 <= r <= 135 and 120 <= g <= 135   # half blue over white


def test_background_fills_everything(canvas):
    p.background("navy")
    assert px(canvas, 0, 0) == px(canvas, 199, 99) == (0, 0, 128)


# ---------------------------------------------------------------- text
def _ink_bbox(surface, bg):
    xs, ys = [], []
    w, h = surface.get_size()
    for y in range(h):
        for x in range(w):
            if tuple(surface.get_at((x, y))[:3]) != bg:
                xs.append(x)
                ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def test_text_anchors_at_top_left(canvas):
    p.background("white")
    p.fill("black")
    p.text_size(30)
    p.text("H", 40, 20)
    x0, y0, x1, y1 = _ink_bbox(canvas, WHITE)
    assert x0 >= 40 and y0 >= 20
    assert x0 - 40 < 6 and y0 - 20 < 8  # ink starts near the anchor, not centred on it


def test_text_colour_falls_back_from_fill_to_stroke_to_white(canvas):
    p.text_size(30)
    p.background("white")
    p.fill("red")
    p.stroke("black")
    p.text("H", 10, 10)
    assert RED in {tuple(canvas.get_at((x, y))[:3]) for x in range(10, 40) for y in range(10, 40)}

    p.background("white")
    p.no_fill()
    p.text("H", 10, 10)
    inks = {tuple(canvas.get_at((x, y))[:3]) for x in range(10, 40) for y in range(10, 40)}
    assert BLACK in inks and RED not in inks

    p.background("navy")
    p.no_stroke()
    p.text("H", 10, 10)
    assert WHITE in {tuple(canvas.get_at((x, y))[:3]) for x in range(10, 40) for y in range(10, 40)}


def test_text_explicit_colour_wins(canvas):
    p.background("white")
    p.fill("red")
    p.text_size(30)
    p.text("H", 10, 10, color="navy")
    inks = {tuple(canvas.get_at((x, y))[:3]) for x in range(10, 40) for y in range(10, 40)}
    assert (0, 0, 128) in inks and RED not in inks


def test_text_size_must_be_positive():
    with pytest.raises(ValueError):
        p.text_size(0)


def test_text_converts_any_object(canvas):
    p.background("white")
    p.fill("black")
    p.text(3.5, 0, 0)
    p.text(p.frame_count, 0, 40)
    assert _ink_bbox(canvas, WHITE) is not None


# ---------------------------------------------------------------- input
def test_key_names():
    pygame.init()
    assert key_code("left") == pygame.K_LEFT
    assert key_code("SPACE") == pygame.K_SPACE
    assert key_code("enter") == pygame.K_RETURN
    assert key_code("escape") == pygame.K_ESCAPE
    assert key_code("a") == pygame.K_a
    assert key_code("7") == pygame.K_7
    assert key_code(pygame.K_x) == pygame.K_x


def test_unknown_key_name_is_an_error():
    with pytest.raises(ValueError):
        key_code("banana")


def test_key_down_is_false_when_nothing_is_pressed(canvas):
    assert p.key_down("left") is False


# ---------------------------------------------------------------- helpers
def test_random_forms():
    for _ in range(200):
        assert 0.0 <= p.random(10) <= 10.0
        assert 5.0 <= p.random(5, 10) <= 10.0


def test_random_seed_makes_random_repeatable():
    p.random_seed(42)
    first = [p.random(100) for _ in range(5)]
    p.random_seed(42)
    assert [p.random(100) for _ in range(5)] == first


def test_random_seed_does_not_touch_the_stdlib_generator():
    import random

    random.seed(1)
    before = random.random()
    random.seed(1)
    p.random_seed(99)
    assert random.random() == before


def test_constrain_and_distance():
    assert p.constrain(5, 0, 10) == 5
    assert p.constrain(-1, 0, 10) == 0
    assert p.constrain(11, 0, 10) == 10
    assert p.distance(0, 0, 3, 4) == 5.0


# ---------------------------------------------------------------- runtime
def test_run_requires_draw_and_optional_setup():
    with pytest.raises(RuntimeError, match="draw"):
        api.active_sketch().run_namespace({}, max_frames=1)
    with pytest.raises(TypeError):
        api.active_sketch().run_namespace({"draw": lambda: None, "setup": 3}, max_frames=1)
    with pytest.raises(TypeError):
        api.active_sketch().run_namespace({"draw": "nope"}, max_frames=1)


def test_run_without_size_creates_the_default_window():
    seen = {}

    def draw():
        seen["size"] = (p.width, p.height)

    api.active_sketch().run_namespace({"draw": draw}, max_frames=1)
    assert seen["size"] == (640, 480)


def test_frame_count_starts_at_zero_and_counts_completed_frames():
    seen = []

    def draw():
        seen.append(p.frame_count)

    api.active_sketch().run_namespace({"draw": draw}, max_frames=3)
    assert seen == [0, 1, 2]
    assert p.frame_count == 3


def test_setup_runs_once_before_draw():
    calls = []
    ns = {"setup": lambda: calls.append("setup"), "draw": lambda: calls.append("draw")}
    api.active_sketch().run_namespace(ns, max_frames=2)
    assert calls == ["setup", "draw", "draw"]


def test_stop_ends_the_loop():
    n = []

    def draw():
        n.append(1)
        if len(n) == 4:
            p.stop()

    api.active_sketch().run_namespace({"draw": draw}, max_frames=100)
    assert len(n) == 4


def test_run_fps_argument_validation():
    with pytest.raises(ValueError):
        api.active_sketch().run_namespace({"draw": lambda: None}, fps=0, max_frames=1)
    with pytest.raises(ValueError):
        api.active_sketch().run_namespace({"draw": lambda: None}, max_frames=0)


def test_delta_time_is_seconds_and_updates():
    seen = []

    def draw():
        seen.append(p.delta_time)

    api.active_sketch().run_namespace({"draw": draw}, fps=1000, max_frames=3)
    assert seen[0] == 0.0
    assert all(0.0 <= d < 1.0 for d in seen[1:])


def test_a_second_run_in_the_same_process_works():
    api.active_sketch().run_namespace({"draw": lambda: None}, max_frames=1)
    api.active_sketch().run_namespace({"draw": lambda: None}, max_frames=2)
    assert p.frame_count == 2


def test_max_frames_captures_the_final_frame():
    def draw():
        p.background("navy")

    api.active_sketch().run_namespace({"draw": draw}, max_frames=1)
    (w, h), data = api.active_sketch().last_frame
    assert (w, h) == (640, 480)
    assert data[:3] == bytes((0, 0, 128))
