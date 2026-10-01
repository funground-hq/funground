"""Mixed styles in one text (story S-091; contract row T14).

A FormattedString is runs of text, each with the settings it was given. Settings left out follow the
drawing state at draw time. These tests read the IR: one Text op per run segment.
"""
from __future__ import annotations

import pytest

import funground as p
from funground import api, ir
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch
from funground.typography import effective_font, text_metrics


def run(draw, size=(400, 300)):
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(*size), "draw": draw}, max_frames=1)
    return [op for op in s.last_ops if isinstance(op, ir.Text)]


def baseline(op: ir.Text) -> float:
    return op.y + effective_font(op.style).ascent * op.style.text_size / effective_font(op.style).units_per_em


# ---------------------------------------------------------------- building (the first sentences of T14)
def test_append_returns_the_same_object_so_calls_chain():
    fs = p.FormattedString()
    assert fs.append("a") is fs
    assert fs.append("b", size=30).append("c") is fs


def test_str_len_and_plus():
    a = p.FormattedString().append("Hello ", size=30)
    b = p.FormattedString().append("world", style="bold")
    both = a + b
    assert str(both) == "Hello world" and len(both) == 11
    assert str(a) == "Hello " and str(b) == "world"        # neither is changed by +
    assert len(p.FormattedString()) == 0 and str(p.FormattedString()) == ""
    assert str(a + "!") == "Hello !" and str("> " + b) == "> world"


def test_repr_names_the_runs_and_text():
    r = repr(p.FormattedString().append("ab").append("cd", size=9))
    assert "2 runs" in r and "'abcd'" in r


def test_append_applies_str_to_anything():
    assert str(p.FormattedString().append(42).append(None)) == "42None"


def test_an_empty_run_adds_nothing():
    assert len(p.FormattedString().append("").runs) == 0


def test_runs_keep_only_the_settings_given():
    fs = p.FormattedString().append("a").append("b", size=30, style="bold")
    plain, own = fs.runs
    assert (plain.size, plain.style, plain.color, plain.tracking, plain.features, plain.variations, plain.font) == (
        None, None, None, None, None, None, None)
    assert (own.size, own.style) == (30, "bold") and own.color is None


# ---------------------------------------------------------------- settings: own and following
def test_every_setting_a_run_gives_reaches_its_op():
    def draw():
        p.fill("red")
        p.text(p.FormattedString().append(
            "ab", size=33, style="bold", color="blue", tracking=2.5,
            features={"liga": False}, variations={"wght": 700}), 10, 10)

    [op] = run(draw)
    assert op.text == "ab"
    st = op.style
    assert (st.text_size, st.text_style, st.text_tracking) == (33, "bold", 2.5)
    assert st.text_features == (("liga", False),) and st.font_variations == (("wght", 700.0),)
    assert op.color.rgba == (0, 0, 255, 255)


def test_unset_settings_follow_the_drawing_state_when_drawn_not_when_appended():
    fs = p.FormattedString().append("ab")

    def draw():
        p.fill(10, 20, 30)
        p.text_size(40)
        p.text_style("italic")
        p.text_tracking(3)
        p.text(fs, 0, 0)
        p.fill(200, 100, 50)
        p.text_size(12)
        p.text_style("bold")
        p.text_tracking(0)
        p.text(fs, 0, 50)

    first, second = run(draw)
    assert (first.style.text_size, first.style.text_style, first.style.text_tracking) == (40, "italic", 3.0)
    assert first.color.rgba == (10, 20, 30, 255)
    assert (second.style.text_size, second.style.text_style, second.style.text_tracking) == (12, "bold", 0.0)
    assert second.color.rgba == (200, 100, 50, 255)


def test_colour_falls_back_as_t4_does():
    fs = p.FormattedString().append("ab")

    def draw():
        p.no_fill()
        p.stroke("green")
        p.text(fs, 0, 0)
        p.text(fs, 0, 30, "purple")            # the colour argument is for runs with no colour of their own

    first, second = run(draw)
    assert first.color == p.color("green")
    assert second.color == p.color("purple")


def test_a_runs_own_colour_beats_the_colour_argument():
    fs = p.FormattedString().append("a", color="red").append("b")

    def draw():
        p.text(fs, 0, 0, "blue")

    a, b = run(draw)
    assert a.color == p.color("red") and b.color == p.color("blue")


def test_colour_is_read_in_the_colour_mode_of_append_time():
    p.color_mode("hsb", 360, 100, 100)
    fs = p.FormattedString().append("a", color=(0, 100, 100))      # hsb: red
    p.color_mode("rgb", 255)

    def draw():
        p.color_mode("rgb", 255)
        p.text(fs, 0, 0)

    [op] = run(draw)
    assert op.color.rgba == (255, 0, 0, 255)


def test_a_run_font_from_load_font_or_a_path():
    from funground.typography import DEFAULT_FONT
    mono = p.load_font(DEFAULT_FONT.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"))
    by_object = p.FormattedString().append("a", font=mono)
    by_path = p.FormattedString().append("a", font=DEFAULT_FONT.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"))
    assert by_object.runs[0].font == by_path.runs[0].font == mono.name

    [op] = run(lambda: p.text(by_object, 0, 0))
    assert op.style.font == mono.name


def test_a_run_with_a_missing_font_names_the_places():
    with pytest.raises(FileNotFoundError):
        p.FormattedString().append("a", font="no-such-font.ttf")


# ---------------------------------------------------------------- errors
@pytest.mark.parametrize("kwargs, error", [
    ({"size": 0}, ValueError),
    ({"size": -3}, ValueError),
    ({"size": "big"}, TypeError),
    ({"size": True}, TypeError),
    ({"style": "heavy"}, ValueError),
    ({"color": "not-a-colour"}, ValueError),
    ({"tracking": "wide"}, TypeError),
    ({"tracking": True}, TypeError),
    ({"features": {"liga": 1}}, TypeError),
    ({"features": ["liga"]}, TypeError),
    ({"features": {"toolongtag": True}}, ValueError),
    ({"variations": {"wght": "bold"}}, TypeError),
    ({"variations": {"": 1}}, ValueError),
    ({"font": 3}, TypeError),
])
def test_bad_settings_are_errors(kwargs, error):
    with pytest.raises(error):
        p.FormattedString().append("a", **kwargs)


def test_a_failed_append_adds_nothing():
    fs = p.FormattedString().append("a")
    with pytest.raises(ValueError):
        fs.append("b", size=-1)
    assert str(fs) == "a"


# ---------------------------------------------------------------- layout: one baseline, tallest line
def test_each_run_segment_is_its_own_text_op_in_order():
    fs = p.FormattedString().append("ab", size=20).append("cd", size=40).append("ef", size=20)
    ops = run(lambda: p.text(fs, 10, 10))
    assert [o.text for o in ops] == ["ab", "cd", "ef"]
    assert [o.style.text_size for o in ops] == [20, 40, 20]
    assert ops[0].x == 10
    assert ops[1].x == pytest.approx(10 + p.text_width(p.FormattedString().append("ab", size=20)))


def test_runs_on_a_line_share_one_baseline_from_the_tallest_ascent():
    fs = p.FormattedString().append("small ", size=16).append("Big", size=60).append(" small", size=16)
    ops = run(lambda: p.text(fs, 10, 20))
    assert {round(baseline(o), 6) for o in ops} == {round(baseline(ops[1]), 6)}
    assert ops[1].y == 20                          # the tallest run sits at the top, as plain text does
    assert ops[0].y > 20


def test_the_second_line_is_one_tallest_leading_below():
    fs = p.FormattedString().append("a ", size=20).append("B", size=60).append("\nsecond", size=20)
    ops = run(lambda: p.text(fs, 0, 0))
    first_baseline = baseline(ops[0])
    assert ops[-1].text == "second"
    assert baseline(ops[-1]) - first_baseline == pytest.approx(25.0)     # 1.25 x 20: its own tallest run


def test_the_line_leading_comes_from_the_tallest_run_on_that_line():
    fs = (p.FormattedString().append("one\n", size=20).append("two ", size=20).append("TWO\n", size=80)
          .append("three", size=20))
    ops = run(lambda: p.text(fs, 0, 0))
    by_text = {o.text: o for o in ops}
    assert baseline(by_text["two "]) - baseline(by_text["one"]) == pytest.approx(80 * 1.25)
    assert baseline(by_text["three"]) - baseline(by_text["TWO\n".strip()]) == pytest.approx(25.0)


def test_text_leading_overrides_the_automatic_leading_for_every_line():
    fs = p.FormattedString().append("a\n", size=20).append("b", size=70)

    def draw():
        p.text_leading(40)
        p.text(fs, 0, 0)

    a, b = run(draw)
    assert baseline(b) - baseline(a) == pytest.approx(40)


def test_a_newline_breaks_the_line_in_any_run_and_blank_lines_emit_nothing():
    fs = p.FormattedString().append("a\n\nb", size=20).append("c\nd", style="bold")
    ops = run(lambda: p.text(fs, 0, 0))
    assert [o.text for o in ops] == ["a", "b", "c", "d"]
    assert baseline(ops[1]) - baseline(ops[0]) == pytest.approx(50)         # a blank line keeps its place
    assert ops[2].y == ops[1].y and ops[3].y > ops[2].y


def test_a_newline_at_the_end_of_a_run_starts_the_next_run_on_a_new_line():
    fs = p.FormattedString().append("top\n", size=30).append("under", size=10)
    a, b = run(lambda: p.text(fs, 0, 0))
    assert a.y == 0
    assert baseline(b) - baseline(a) == pytest.approx(12.5)               # the second line is only size 10


# ---------------------------------------------------------------- alignment
def test_horizontal_alignment_uses_the_width_of_the_whole_mixed_line():
    fs = p.FormattedString().append("Hi ", size=20).append("there", size=50, style="bold")
    whole = p.text_width(fs)

    def draw():
        p.text_align("center")
        p.text(fs, 200, 0)
        p.text_align("right")
        p.text(fs, 200, 100)

    c1, c2, r1, r2 = run(draw)
    assert c1.x == pytest.approx(200 - whole / 2)
    assert r1.x == pytest.approx(200 - whole)
    assert c2.x == pytest.approx(c1.x + p.text_width(p.FormattedString().append("Hi ", size=20)))


def test_vertical_alignment_uses_the_tallest_ascent_and_descent():
    fs = p.FormattedString().append("a", size=20).append("B", size=60)
    big_ascent, big_descent = text_metrics(60, effective_font(api.active_sketch().style))

    def draw():
        p.text_align("left", "baseline")
        p.text(fs, 0, 100)

    small, big = run(draw)
    assert baseline(big) == pytest.approx(100) and baseline(small) == pytest.approx(100)
    assert big.y == pytest.approx(100 - big_ascent)


def test_a_single_run_without_settings_is_exactly_the_plain_text_ops():
    def draw_plain():
        p.text_size(24)
        p.text_align("center", "center")
        p.text_leading(31.7)
        p.text("one\ntwo words\n\nfour", 200, 150)
        p.text_align("right")
        p.text_leading(None)
        p.text("a\nbc", 380, 10, "red")

    def draw_formatted():
        p.text_size(24)
        p.text_align("center", "center")
        p.text_leading(31.7)
        p.text(p.FormattedString().append("one\ntwo words\n\nfour"), 200, 150)
        p.text_align("right")
        p.text_leading(None)
        p.text(p.FormattedString().append("a\nbc"), 380, 10, "red")

    assert run(draw_plain) == run(draw_formatted)


# ---------------------------------------------------------------- text_box and wrapping
def test_a_single_run_text_box_is_exactly_the_plain_text_box():
    message = "The quick brown fox jumps over the lazy dog and keeps running far away"

    def draw(m):
        def go():
            p.text_size(18)
            draw.rest = p.text_box(m, 10, 10, 150, 90)
        return go

    plain = run(draw(message))
    plain_rest = draw.rest
    formatted = run(draw(p.FormattedString().append(message)))
    assert plain == formatted
    assert str(draw.rest) == plain_rest and isinstance(draw.rest, p.FormattedString)


def test_wrapping_breaks_at_spaces_across_runs():
    fs = p.FormattedString().append("alpha beta ").append("gamma delta", style="bold")

    def draw():
        p.text_size(20)
        p.text_box(fs, 0, 0, p.text_width("alpha beta gamma") - 1, None)

    ops = run(draw)
    lines = {}
    for o in ops:
        lines.setdefault(o.y, []).append(o.text)
    assert [" ".join(v).replace("  ", " ") for _, v in sorted(lines.items())] == ["alpha beta", "gamma delta"]


def test_wrapping_measures_each_run_with_its_own_settings():
    narrow = p.FormattedString().append("aaaa bbbb", size=10)
    wide = p.FormattedString().append("aaaa ", size=10).append("bbbb", size=40)

    def draw(fs):
        def go():
            p.text_size(10)
            go.rest = p.text_box(fs, 0, 0, 150, None)
        return go

    d1 = draw(narrow)
    assert len({o.y for o in run(d1)}) == 1          # fits on one line at size 10
    d2 = draw(wide)
    assert len({o.y for o in run(d2)}) == 2          # "bbbb" at size 40 does not


def test_a_word_split_across_runs_stays_one_word():
    fs = p.FormattedString().append("some wor").append("ds together here", style="bold")
    first_two = p.FormattedString().append("some wor").append("ds", style="bold")
    ops = run(lambda: p.text_box(fs, 0, 0, p.text_width(first_two) + 2, None))
    first_line = "".join(o.text for o in ops if o.y == ops[0].y)
    assert first_line == "some words"                 # "words" was never cut at the run boundary
    assert "".join(o.text for o in ops).replace(" ", "") == "somewordstogetherhere"


def test_a_word_wider_than_the_box_is_broken_between_letters_with_its_runs():
    fs = p.FormattedString().append("ab", size=20).append("cdefgh", size=20, style="bold")
    ops = run(lambda: p.text_box(fs, 0, 0, p.text_width("abcd") + 1, None))
    assert len({o.y for o in ops}) >= 2
    assert "".join(o.text for o in ops) == "abcdefgh"
    assert ops[0].style.text_style == "normal" and ops[-1].style.text_style == "bold"


def test_the_box_height_shows_only_whole_lines_and_returns_the_rest_with_its_runs():
    fs = (p.FormattedString().append("one two ", size=20).append("three four ", size=20, style="bold", color="red")
          .append("five six", size=20, style="italic"))

    def draw():
        draw.rest = p.text_box(fs, 0, 0, p.text_width("one two") + 2, 2 * 25 + 1)

    ops = run(draw)
    rest = draw.rest
    assert isinstance(rest, p.FormattedString)
    shown = "".join(o.text for o in ops)
    assert (shown + str(rest)).replace(" ", "") == str(fs).replace(" ", "")
    assert len(rest) > 0
    assert any(r.style == "italic" for r in rest.runs)
    assert all(r.text for r in rest.runs)


def test_a_rest_keeps_run_settings_and_can_flow_into_a_second_box():
    fs = (p.FormattedString().append("aaaa bbbb ", color="red").append("cccc dddd", style="bold", size=30))

    def draw():
        draw.rest = p.text_box(fs, 0, 0, 150, 30)
        draw.again = p.text_box(draw.rest, 200, 0, 150, 200)

    ops = run(draw)
    assert isinstance(draw.again, p.FormattedString) and len(draw.again) == 0
    assert "".join(o.text for o in ops).replace(" ", "") == "aaaabbbbccccdddd"
    assert any(o.x >= 200 and o.style.text_size == 30 for o in ops)


def test_all_fitting_returns_an_empty_formatted_string():
    fs = p.FormattedString().append("hi", size=10)
    run(lambda: setattr(run, "rest", p.text_box(fs, 0, 0, 200, 100)))
    assert isinstance(run.rest, p.FormattedString) and len(run.rest) == 0 and str(run.rest) == ""


def test_text_box_alignment_uses_each_lines_own_mixed_width():
    fs = p.FormattedString().append("ab ", size=20).append("cd", size=40).append(" ef", size=20)

    def draw():
        p.text_align("right")
        p.text_box(fs, 0, 0, 300, None)

    ops = run(draw)
    assert ops[-1].x + p.text_width(p.FormattedString().append(" ef", size=20)) == pytest.approx(300)


def test_text_box_errors_are_the_same():
    fs = p.FormattedString().append("a")
    with pytest.raises(ValueError):
        p.text_box(fs, 0, 0, 0)
    with pytest.raises(ValueError):
        p.text_box(fs, 0, 0, 10, -1)


# ---------------------------------------------------------------- text_width and text_path
def test_text_width_adds_each_runs_own_advance_and_takes_the_widest_line():
    a = p.FormattedString().append("Hello ", size=20)
    b = p.FormattedString().append("world", size=50, style="bold")
    assert p.text_width(a + b) == pytest.approx(p.text_width(a) + p.text_width(b))
    two = p.FormattedString().append("short\n", size=20).append("a longer line", size=20)
    assert p.text_width(two) == pytest.approx(p.text_width(p.FormattedString().append("a longer line", size=20)))
    assert p.text_width(p.FormattedString()) == 0.0


def test_text_width_follows_the_drawing_state_for_unset_settings():
    fs = p.FormattedString().append("Hello")
    p.text_size(20)
    small = p.text_width(fs)
    p.text_size(40)
    assert p.text_width(fs) == pytest.approx(small * 2)
    assert p.text_width(fs) == pytest.approx(p.text_width("Hello"))


def test_text_width_is_the_same_for_a_single_plain_run():
    p.text_size(27)
    assert p.text_width(p.FormattedString().append("Kerning AV")) == p.text_width("Kerning AV")


def test_text_path_of_a_mixed_text_holds_each_runs_outlines():
    small = p.FormattedString().append("Ab", size=20)
    mixed = p.FormattedString().append("Ab", size=20).append("Ab", size=60)
    one = p.text_path(small, 0, 0).bounds()
    both = p.text_path(mixed, 0, 0).bounds()
    assert both[2] > one[2] * 2 and both[3] > one[3] * 2          # wider, and taller from the large run


def test_text_path_of_a_single_run_is_the_plain_path():
    p.text_size(30)
    p.text_align("center", "baseline")
    plain = p.text_path("Hi\nthere", 100, 100)
    formatted = p.text_path(p.FormattedString().append("Hi\nthere"), 100, 100)
    assert plain.bounds() == formatted.bounds()


# ---------------------------------------------------------------- pictures, scripts
def test_a_picture_draws_a_formatted_string_with_its_own_state(canvas):
    fs = p.FormattedString().append("ab", size=30, color="red").append("cd")
    g = p.create_graphics(200, 80)
    g.text_size(14)
    g.fill("blue")
    g.text(fs, 5, 5)
    ops = [op for op in g._sketch.frame.ops if isinstance(op, ir.Text)]
    assert [o.text for o in ops] == ["ab", "cd"]
    assert ops[0].style.text_size == 30 and ops[1].style.text_size == 14
    assert ops[0].color == p.color("red") and ops[1].color == p.color("blue")


def test_a_picture_has_text_box_text_width_and_text_path_for_it(canvas):
    fs = p.FormattedString().append("hello ", size=20).append("big world", size=40)
    g = p.create_graphics(300, 200)
    assert g.text_width(fs) == pytest.approx(p.text_width(fs))
    assert not g.text_path(fs, 0, 0).is_empty
    rest = g.text_box(fs, 0, 0, 200, 30)
    assert isinstance(rest, p.FormattedString) and len(rest) > 0


def test_it_draws_pixels(canvas):
    p.background("white")
    p.fill("black")
    p.text(p.FormattedString().append("Hi", size=40, color="red"), 10, 10)
    seen = {canvas.get_at((x, y))[:3] for x in range(10, 50) for y in range(10, 50)}
    assert (255, 0, 0) in seen


def test_the_formatted_string_is_public_and_state_is_untouched():
    assert "FormattedString" in p.__all__ and p.FormattedString is api.FormattedString
    before = api.active_sketch().style
    p.FormattedString().append("a", size=99, style="bold", color="red", tracking=9)
    assert api.active_sketch().style == before
