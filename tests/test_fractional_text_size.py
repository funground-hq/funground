"""Fractional text sizes (story S-171, contract row T3): f.text_size(143.7) keeps the fraction."""
from __future__ import annotations

import pytest

import funground as p
from funground import api, ir


def size_now() -> float:
    return api.active_sketch().style.text_size


def test_a_fraction_is_kept(canvas):
    p.text_size(20.5)
    assert size_now() == 20.5


def test_a_fraction_below_one_is_valid(canvas):
    p.text_size(0.5)
    assert size_now() == 0.5


def test_a_whole_size_stays_a_whole_number(canvas):
    p.text_size(24.0)
    assert size_now() == 24 and isinstance(size_now(), int)


def test_text_font_keeps_a_fractional_size(canvas):
    p.text_font(None, 13.25)
    assert size_now() == 13.25


def test_a_formatted_run_keeps_a_fractional_size(canvas):
    line = p.FormattedString().append("Big", size=33.3)
    assert line.runs[0].size == 33.3


@pytest.mark.parametrize("size", [0, -1, -0.5, float("nan"), float("inf")])
def test_a_size_that_is_not_above_zero_is_an_error(canvas, size):
    with pytest.raises(ValueError, match="above 0"):
        p.text_size(size)


@pytest.mark.parametrize("size", ["20", None, True])
def test_a_size_that_is_not_a_number_is_an_error(canvas, size):
    with pytest.raises(TypeError, match="number"):
        p.text_size(size)


def test_a_bad_size_leaves_the_size_alone(canvas):
    p.text_size(30)
    with pytest.raises(ValueError):
        p.text_size(0)
    assert size_now() == 30


def test_a_fractional_size_measures_between_its_neighbours(canvas):
    widths = []
    for size in (20, 20.5, 21):
        p.text_size(size)
        widths.append(p.text_width("Fractions"))
    assert widths[0] < widths[1] < widths[2]


def test_a_fractional_size_is_drawn_between_its_neighbours(canvas):
    ink = []
    for size in (20, 20.5, 21):
        p.text_size(size)
        p.background("white")
        p.fill("black")
        p.text("HHHHHHHH", 0, 0)
        row = canvas.get_size()[0]
        ink.append(sum(255 - canvas.get_at((x, y))[0] for x in range(row) for y in range(40)))
    assert ink[0] < ink[1] < ink[2]


def test_the_state_is_the_same_for_the_same_fraction(canvas):
    p.text_size(17.5)
    a = api.active_sketch().style
    p.text_size(17.5)
    assert a == api.active_sketch().style and hash(a) == hash(api.active_sketch().style)


@pytest.mark.parametrize("size", [18.75, 18])
def test_the_text_op_carries_the_size_through_the_ir_json(canvas, size):
    p.text_size(size)
    p.text("x", 0, 0)
    op = [op for op in api.active_sketch().frame.ops if isinstance(op, ir.Text)][-1]
    data = ir.op_to_jsonable(op)
    assert data["style"]["text_size"] == size
    assert repr(data["style"]["text_size"]) == repr(size)                # a whole size still prints as 18, not 18.0
    assert ir.op_from_jsonable(data) == op


@pytest.mark.parametrize("target", [37, 143.7, 480.25])
def test_fitting_a_headline_is_exact_to_half_a_pixel(canvas, target):
    p.text_size(p.fit_text_size("Spring Fair", target))
    assert abs(p.text_width("Spring Fair") - target) < 0.5


def test_many_distinct_sizes_each_measure_and_draw_their_own(canvas):
    widths = []
    for i in range(300):
        p.text_size(5 + i * 0.173)
        p.text("Hamburgefonts", 0, 0)
        widths.append(p.text_width("Hamburgefonts"))
    assert widths == sorted(widths) and len(set(widths)) == 300
    p.text_size(5)
    assert p.text_width("Hamburgefonts") == pytest.approx(widths[0], rel=1e-9)
