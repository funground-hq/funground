"""Colour constructors and colour objects (S-044, D-017 = C, contract S12)."""
from __future__ import annotations

import pytest

import playground as p
from playground.color import Color

WHITE, RED = (255, 255, 255), (255, 0, 0)


def test_there_is_no_color_mode():
    assert not hasattr(p, "color_mode")


@pytest.mark.parametrize("h, s, b, expected", [
    (0, 100, 100, (255, 0, 0)), (120, 100, 100, (0, 255, 0)), (240, 100, 100, (0, 0, 255)),
    (60, 100, 100, (255, 255, 0)), (0, 0, 100, (255, 255, 255)), (0, 0, 0, (0, 0, 0)),
    (360, 100, 100, (255, 0, 0)), (480, 100, 100, (0, 255, 0)),          # hue wraps
    (0, 150, 100, (255, 0, 0)), (0, 100, -5, (0, 0, 0)),                 # s/b clamp
])
def test_hsb(h, s, b, expected):
    assert p.hsb(h, s, b).rgb == expected


@pytest.mark.parametrize("h, s, l, expected", [
    (0, 100, 50, (255, 0, 0)), (240, 100, 50, (0, 0, 255)), (0, 0, 100, (255, 255, 255)),
    (120, 100, 25, (0, 128, 0)),
])
def test_hsl(h, s, l, expected):
    assert p.hsl(h, s, l).rgb == expected


def test_alpha_in_hsb_and_hsl():
    assert p.hsb(0, 100, 100, 128).a == 128 and p.hsl(0, 100, 50, 64).a == 64


def test_color_accepts_every_form_and_reads_back():
    for value in ("tomato", (255, 99, 71), "#FF6347", [255, 99, 71], Color(255, 99, 71)):
        assert p.color(value).rgb == (255, 99, 71)
    c = p.color(255, 99, 71, 200)
    assert (c.red, c.green, c.blue, c.alpha) == (255, 99, 71, 200)
    assert c.hue == pytest.approx(9.13, abs=0.01)
    assert c.saturation == pytest.approx(72.16, abs=0.01)
    assert c.brightness == pytest.approx(100.0)
    assert p.color("gray50").lightness == pytest.approx(49.8, abs=0.1)
    with pytest.raises(ValueError):
        p.color(1, 2)


def test_hsb_round_trips_through_the_getters():
    c = p.hsb(200, 60, 80)
    assert c.hue == pytest.approx(200, abs=1) and c.saturation == pytest.approx(60, abs=1) and c.brightness == pytest.approx(80, abs=1)


def test_lerp_color():
    assert p.lerp_color("black", "white", 0.5).rgb == (128, 128, 128)
    assert p.lerp_color((255, 0, 0, 0), (0, 0, 255, 255), 0.25).rgba == (191, 0, 64, 64)
    assert p.lerp_color("red", "blue", 2).rgb == (0, 0, 255)            # amount clamped


def test_colour_objects_work_wherever_a_colour_does(canvas):
    p.background(p.hsb(0, 0, 100))
    p.no_stroke()
    p.fill(p.hsb(0, 100, 100))
    p.rect(0, 0, 10, 10)
    assert tuple(canvas.get_at((5, 5))[:3]) == RED
    assert tuple(canvas.get_at((50, 50))[:3]) == WHITE


@pytest.mark.parametrize("bad", [("a", 50, 50), (0, None, 50), (float("nan"), 50, 50)])
def test_bad_hsb_values_are_errors(bad):
    with pytest.raises(ValueError):
        p.hsb(*bad)


def test_public_color_function_and_internal_color_module_coexist():
    """p.color is the learner-facing function; the colour module stays importable by path."""
    import importlib

    import playground

    assert callable(playground.color) and playground.color("red").rgb == (255, 0, 0)
    module = importlib.import_module("playground.color")
    assert module.Color is Color
