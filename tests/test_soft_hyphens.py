"""Hyphenation by soft hyphens (story S-160, contract row T23, decision D-085 = a).

A soft hyphen (U+00AD) marks a place where a word may break. It is never drawn and has no width, except
at the end of a line that breaks there: then the line ends with a hyphen.
"""
from __future__ import annotations

import pytest

import funground as p
from funground import api, ir, typography
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

SHY = "\N{SOFT HYPHEN}"
COOP = f"co{SHY}op{SHY}er{SHY}a{SHY}tion"
INTERNATIONAL = f"in{SHY}ter{SHY}na{SHY}tion{SHY}al"


def text_ops(draw) -> list[ir.Text]:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(400, 300), "draw": draw}, max_frames=1)
    return [op for op in s.last_ops if isinstance(op, ir.Text)]


def box(message, width, size=20, align="left", height=None):
    """The lines text_box draws (as in the ops) and what it returns."""
    def draw():
        p.text_size(size)
        p.text_align(align)
        draw.rest = p.text_box(message, 10, 10, width, height)

    return [op.text for op in text_ops(draw)], draw.rest


def drawn(line: str) -> str:
    """What can be seen of a line: the soft hyphens that were not used for a break are not there."""
    return line.replace(SHY, "")


def width_of(text: str, size=20) -> float:
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(100, 100)
    p.text_size(size)
    return p.text_width(text)


# ---------------------------------------------------------------- invisible and without width
def test_a_soft_hyphen_has_no_width():
    assert width_of(COOP) == width_of("cooperation")
    assert width_of(f"co{SHY}op{SHY}eration") == width_of("cooperation")


def test_the_shapes_have_no_soft_hyphen_glyph():
    font = typography.default_font()
    run = font.shape(COOP, 20)
    assert run.text == "cooperation"
    assert [g.gid for g in run.glyphs] == [g.gid for g in font.shape("cooperation", 20).glyphs]


def test_text_outside_a_box_draws_no_soft_hyphen():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(300, 100)
    p.text_size(30)
    assert p.text_path(COOP, 10, 10).geometry == p.text_path("cooperation", 10, 10).geometry
    assert p.text_to_points(COOP, 10, 10) == p.text_to_points("cooperation", 10, 10)


def test_alignment_measures_without_the_soft_hyphens():
    def draw():
        p.text_size(30)
        p.text_align("right")
        p.text(COOP, 300, 10)
        draw.width = p.text_width("cooperation")

    [op] = text_ops(draw)
    assert op.x == pytest.approx(300 - draw.width)


def test_a_line_of_only_soft_hyphens_is_harmless():
    def draw():
        p.text(SHY, 10, 10)
        p.text(SHY + SHY, 10, 40)
        p.text_box(SHY, 10, 70, 100)
        draw.width = p.text_width(SHY)

    text_ops(draw)
    assert draw.width == 0


# ---------------------------------------------------------------- breaking
def test_a_narrow_box_breaks_long_words_at_the_soft_hyphens_and_only_there():
    lines, rest = box(f"{COOP} {INTERNATIONAL}", 90)
    assert rest == ""
    assert [drawn(line) for line in lines] == ["coopera-", "tion in-", "terna-", "tional"]


def test_a_hyphen_is_drawn_only_where_a_line_breaks():
    lines, _ = box(f"{COOP} {INTERNATIONAL} {COOP}", 80)
    for line in lines:
        assert "-" not in drawn(line).removesuffix("-")
    assert sum(line.endswith("-") for line in lines) >= 3
    assert not lines[-1].endswith("-")


def test_what_is_left_of_the_words_after_the_hyphens_is_all_of_them():
    lines, _ = box(f"{COOP} {INTERNATIONAL} {COOP}", 80)
    text = "".join(drawn(line).removesuffix("-") if line.endswith("-") else drawn(line) + " " for line in lines)
    assert text.strip() == "cooperation international cooperation"


@pytest.mark.parametrize("width", [60, 75, 90, 130])
def test_every_line_fits_the_box_with_its_hyphen(width):
    lines, _ = box(f"{COOP} {INTERNATIONAL} {COOP}", width)
    assert all(width_of(line) <= width for line in lines)


def test_a_line_breaks_at_the_last_soft_hyphen_that_fits():
    lines, _ = box(COOP, width_of("coop-") + 0.5)
    assert lines[0] == f"co{SHY}op-"
    lines, _ = box(COOP, width_of("coopera-") + 0.5)
    assert lines[0] == f"co{SHY}op{SHY}er{SHY}a-"


def test_a_word_that_fits_the_rest_of_the_line_is_not_broken():
    lines, _ = box(f"one two {COOP}", 400)
    assert [drawn(line) for line in lines] == ["one two cooperation"]


def test_a_word_that_does_not_fit_the_rest_of_the_line_fills_it_with_its_first_part():
    lines, _ = box(f"a {COOP}", width_of("a coop-") + 1)
    assert lines[0] == f"a co{SHY}op-"
    assert [drawn(line) for line in lines[1:]] == ["eration"]


def test_a_word_that_does_not_fit_even_in_its_first_part_goes_to_the_next_line():
    lines, _ = box(f"A longer line {COOP}", width_of("A longer line co-") - 1)
    assert [drawn(line) for line in lines] == ["A longer line", "cooperation"]


def test_a_long_word_without_a_soft_hyphen_still_breaks_between_letters():
    lines, _ = box("Extraordinarily", 100)
    assert len(lines) > 1 and "".join(lines) == "Extraordinarily"


def test_a_soft_hyphen_is_used_before_breaking_between_letters():
    lines, _ = box(f"ab{SHY}cdefghijklmnopqrstuvwxyz", 90)
    assert lines[0] == f"ab-"
    assert drawn("".join(lines)).replace("-", "") == "abcdefghijklmnopqrstuvwxyz"
    assert not any(line.endswith("-") for line in lines[1:])


def test_a_soft_hyphen_at_the_start_or_end_of_a_word_is_never_a_break():
    lines, _ = box(f"{SHY}Extraordinarily{SHY}", 100)
    assert "-" not in "".join(lines)


def test_two_soft_hyphens_in_a_row_are_one_place_to_break():
    lines, _ = box(f"extra{SHY}{SHY}ordinary", 80)
    assert [drawn(line) for line in lines][0] == "extra-"
    assert drawn("".join(lines)).replace("-", "") == "extraordinary"


def test_paragraphs_are_wrapped_each_on_their_own():
    lines, _ = box(f"{COOP}\n{COOP}", 80)
    assert [drawn(line) for line in lines] == ["cooper-", "ation", "cooper-", "ation"]


def test_tracking_counts_in_the_fit():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(100, 100)
    p.text_size(20)
    p.text_tracking(3)
    room = p.text_width("coop-")
    p.text_tracking(0)

    def draw():
        p.text_size(20)
        p.text_tracking(3)
        draw.rest = p.text_box(COOP, 10, 10, room + 0.5)

    [first, *_] = text_ops(draw)
    assert first.text == f"co{SHY}op-"


# ---------------------------------------------------------------- the overflow
def test_the_overflow_goes_on_after_the_soft_hyphen_that_was_used():
    lines, rest = box(f"{COOP} {COOP}", 100, height=30)        # one line fits
    assert lines == [f"co{SHY}op{SHY}er{SHY}a-"]
    assert rest == f"tion {COOP}"


def test_the_overflow_is_the_start_of_the_next_box():
    rest, seen = f"{COOP} {INTERNATIONAL}", []
    while rest:
        lines, rest = box(rest, 90, height=30)
        seen += [drawn(line) for line in lines]
    assert seen == ["coopera-", "tion in-", "terna-", "tional"]


# ---------------------------------------------------------------- with justify
def test_a_line_that_ends_in_a_hyphen_is_justified_like_any_other():
    def draw():
        p.text_size(20)
        p.text_align("justify")
        p.text_box(f"Wonderful {COOP} and {INTERNATIONAL} posters", 10, 10, 190)

    hyphenated = [op for op in text_ops(draw) if op.text.endswith("-") and " " in op.text]
    assert hyphenated
    for op in hyphenated:
        run = typography.default_font().shape(op.text, 20, word_spacing=op.word_spacing)
        assert op.x + run.advance == pytest.approx(200, abs=0.01)


# ---------------------------------------------------------------- FormattedString
def formatted() -> p.FormattedString:
    return (p.FormattedString().append("A word ", size=20)
            .append(f"co{SHY}op{SHY}er", size=20, style="bold").append(f"a{SHY}tion", size=20, style="italic")
            .append(" and more", size=20))


def test_a_formatted_string_breaks_at_a_soft_hyphen_inside_a_run():
    def draw():
        draw.rest = p.text_box(formatted(), 10, 10, 120)

    ops = text_ops(draw)
    rows = [[drawn(op.text) for op in ops if op.y == top] for top in dict.fromkeys(op.y for op in ops)]
    assert rows == [["A word ", "co-"], ["oper", "ation"], ["and more"]]
    assert draw.rest.runs == ()


def test_the_hyphen_is_in_the_look_of_the_run_it_ends():
    def draw():
        p.text_box(formatted(), 10, 10, 120)

    ops = text_ops(draw)
    hyphenated = next(op for op in ops if op.text.endswith("-"))
    assert hyphenated.style.text_style == "bold"
    assert drawn(hyphenated.text) == "co-"


def test_the_overflow_of_a_formatted_string_goes_on_after_the_soft_hyphen():
    def draw():
        draw.rest = p.text_box(formatted(), 10, 10, 120, 25)        # one line fits

    ops = text_ops(draw)
    assert [op.text for op in ops][-1].endswith("-")
    assert isinstance(draw.rest, p.FormattedString)
    assert drawn(str(draw.rest)) == "operation and more"
    assert not str(draw.rest).startswith(SHY)


def test_the_width_of_a_formatted_string_ignores_soft_hyphens():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(100, 100)
    with_shy = p.FormattedString().append(COOP, size=20)
    without = p.FormattedString().append("cooperation", size=20)
    assert p.text_width(with_shy) == pytest.approx(p.text_width(without))
