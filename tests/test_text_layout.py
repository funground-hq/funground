"""Text alignment and metrics (S-049, contract T7/T8)."""
from __future__ import annotations

import math

import pytest

import playground as p
from playground import api, ir
from playground.platform.headless import HeadlessPlatform
from playground.sketch import Sketch


def text_ops(draw) -> list[ir.Text]:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(400, 200), "draw": draw}, max_frames=1)
    return [op for op in s.last_ops if isinstance(op, ir.Text)]


def test_default_is_top_left_as_in_v05():
    [op] = text_ops(lambda: p.text("Hello", 50, 60))
    assert (op.x, op.y) == (50, 60)
    assert "text_align" not in ir.op_to_jsonable(op)["style"]       # snapshots stay identical


def test_horizontal_alignment_moves_by_the_measured_width():
    def draw():
        p.text_size(30)
        width = p.text_width("Hello")
        for h in ("left", "center", "right"):
            p.text_align(h)
            p.text("Hello", 200, 100)
        draw.width = width

    ops = text_ops(draw)
    w = draw.width
    assert [op.x for op in ops] == pytest.approx([200, 200 - w / 2, 200 - w])
    assert all(op.y == 100 for op in ops)


def test_vertical_alignment_uses_ascent_and_descent():
    def draw():
        p.text_size(40)
        draw.metrics = (p.text_ascent(), p.text_descent())
        for v in ("top", "center", "baseline", "bottom"):
            p.text_align("left", v)
            p.text("Ag", 10, 100)

    ops = text_ops(draw)
    a, d = draw.metrics
    assert [op.y for op in ops] == pytest.approx([100, 100 - (a + d) / 2, 100 - a, 100 - a - d])


def test_vertical_is_kept_when_only_horizontal_is_given_as_in_p5():
    def draw():
        p.text_align("left", "baseline")
        p.text_align("right")
        draw.style = api.active_sketch().style

    text_ops(draw)
    assert (draw.style.text_align, draw.style.text_valign) == ("right", "baseline")


def test_alignment_is_saved_and_restored_with_the_state():
    def draw():
        p.text_align("center", "center")
        with p.saved_state():
            p.text_align("right", "bottom")
        p.text("x", 0, 0)
        draw.style = api.active_sketch().style

    text_ops(draw)
    assert (draw.style.text_align, draw.style.text_valign) == ("center", "center")


def test_metrics_scale_with_text_size():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.text_size(100)
    a100, d100 = p.text_ascent(), p.text_descent()
    p.text_size(50)
    assert math.isclose(p.text_ascent(), a100 / 2) and math.isclose(p.text_descent(), d100 / 2)
    assert 0 < d100 < a100 < 100 + d100                     # DejaVu: about 0.93 em up, 0.24 em down


def test_unknown_names_are_explained():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with pytest.raises(ValueError, match="'left', 'center', 'right'"):
        p.text_align("middle")
    with pytest.raises(ValueError, match="'baseline'"):
        p.text_align("left", "centre")


def test_aligned_text_round_trips_through_the_snapshot_format():
    def draw():
        p.text_align("center", "baseline")
        p.text("Hi", 100, 100)

    [op] = text_ops(draw)
    again = ir.op_from_jsonable(ir.op_to_jsonable(op))
    assert again == op
