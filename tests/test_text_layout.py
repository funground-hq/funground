"""Text alignment and metrics (S-049, contract T7/T8)."""
from __future__ import annotations

import math

import pytest

import funground as p
from funground import api, ir
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


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


# ---- multi-line text and text boxes (S-053, contract T9/T10)

def test_newline_starts_a_new_line_one_leading_down():
    ops = text_ops(lambda: (p.text_size(20), p.text("one\ntwo\n\nfour", 10, 50)))
    assert [op.text for op in ops] == ["one", "two", "four"]       # empty lines draw nothing
    assert [op.y for op in ops] == pytest.approx([50, 75, 125])     # leading 1.25 x 20; the blank line keeps its place
    assert all(op.x == 10 for op in ops)


def test_text_leading_sets_the_line_distance_and_none_goes_back_to_automatic():
    def draw():
        p.text_size(20)
        p.text_leading(40)
        p.text("a\nb", 0, 0)
        p.text_leading(None)
        p.text("c\nd", 100, 0)

    ops = text_ops(draw)
    assert [op.y for op in ops] == pytest.approx([0, 40, 0, 25])


def test_multi_line_blocks_align_as_a_whole():
    def draw():
        p.text_size(20)
        draw.m = (p.text_ascent(), p.text_descent())
        p.text_align("center", "bottom")
        p.text("short\nmuch longer", 200, 100)
        draw.w = (p.text_width("short"), p.text_width("much longer"))

    ops = text_ops(draw)
    a, d = draw.m
    block = a + d + 25
    assert [op.y for op in ops] == pytest.approx([100 - block, 100 - block + 25])
    assert [op.x for op in ops] == pytest.approx([200 - draw.w[0] / 2, 200 - draw.w[1] / 2])   # each line centred


def test_text_width_of_several_lines_is_the_widest():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    assert p.text_width("ab\nabcd\na") == p.text_width("abcd")


def test_text_box_wraps_inside_the_width():
    def draw():
        p.text_size(16)
        draw.rest = p.text_box("the quick brown fox jumps over the lazy dog", 10, 20, 120)
        draw.widths = None

    ops = text_ops(draw)
    assert len(ops) > 1 and draw.rest == ""
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.text_size(16)
    assert all(p.text_width(op.text) <= 120 for op in ops)
    assert " ".join(op.text for op in ops) == "the quick brown fox jumps over the lazy dog"


def test_text_box_returns_what_did_not_fit_so_it_can_flow_on():
    words = " ".join(f"word{i}" for i in range(60))

    def draw():
        p.text_size(16)
        first = p.text_box(words, 0, 0, 150, 60)
        draw.first = first
        draw.second = p.text_box(first, 200, 0, 150, 1000)

    ops = text_ops(draw)
    assert draw.first and words.endswith(draw.first) and draw.second == ""
    shown = " ".join(op.text for op in ops)
    assert shown == words                                        # nothing lost, nothing repeated
    in_first = [op for op in ops if op.x < 200]
    assert all(op.y + 16 * 1.2 <= 60 for op in in_first)         # only whole lines in the box


def test_a_word_wider_than_the_box_is_broken():
    def draw():
        p.text_size(20)
        p.text_box("Supercalifragilisticexpialidocious", 0, 0, 80)

    ops = text_ops(draw)
    assert len(ops) > 2 and "".join(op.text for op in ops) == "Supercalifragilisticexpialidocious"


def test_text_box_alignment_is_inside_the_box():
    def draw():
        p.text_size(20)
        draw.m = (p.text_ascent(), p.text_descent(), p.text_width("hi"))
        p.text_align("right", "bottom")
        p.text_box("hi", 100, 50, 200, 300)
        p.text_align("center", "center")
        p.text_box("hi", 100, 50, 200, 300)

    right, centre = text_ops(draw)
    a, d, w = draw.m
    assert (right.x, right.y) == pytest.approx((300 - w, 350 - a - d))
    assert (centre.x, centre.y) == pytest.approx((200 - w / 2, 200 - (a + d) / 2))


def test_text_box_rejects_a_box_with_no_room():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with pytest.raises(ValueError, match="width above 0"):
        p.text_box("x", 0, 0, 0)
    with pytest.raises(ValueError, match="0 or more"):
        p.text_leading(-1)
    assert p.text_box("does not fit at all", 0, 0, 100, 5) == "does not fit at all"
