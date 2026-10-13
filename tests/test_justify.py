"""Justified text (story S-159, contract row T22): f.text_align("justify") in f.text_box()."""
from __future__ import annotations

import pytest

import funground as p
from funground import api, ir, typography
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

STORY = ("Posters are read from far away, so the words must be easy to find. A justified column has two "
         "straight edges.\nA second paragraph starts here, and it ends with a short last line.")


def text_ops(draw) -> list[ir.Text]:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(400, 300), "draw": draw}, max_frames=1)
    return [op for op in s.last_ops if isinstance(op, ir.Text)]


def right_edge(op: ir.Text) -> float:
    """Where the line of *op* ends: its start plus its advance, with the stretched spaces."""
    font = typography.effective_font(op.style)
    run = font.shape(op.text, op.style.text_size, word_spacing=op.word_spacing, **typography.text_settings(op.style))
    return op.x + run.advance


def justified_box(message=STORY, width=170, size=16, **settings):
    def draw():
        p.text_size(size)
        p.text_align("justify")
        draw.rest = p.text_box(message, 30, 10, width, **settings)

    ops = text_ops(draw)
    return ops, draw.rest


def test_justify_is_a_horizontal_alignment():
    def draw():
        p.text_align("justify", "bottom")
        draw.style = api.active_sketch().style

    text_ops(draw)
    assert (draw.style.text_align, draw.style.text_valign) == ("justify", "bottom")


def test_a_bad_alignment_names_justify_among_the_choices():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with pytest.raises(ValueError, match="'justify'"):
        p.text_align("full")


def test_every_line_but_the_last_of_a_paragraph_ends_at_the_right_edge():
    ops, _ = justified_box()
    lines, rests = typography.wrap_lines(STORY, 170, 16)
    ends = typography.paragraph_ends(STORY, [len(STORY) - len(rest) for rest in rests])
    assert len(ops) == len(lines) > 6 and any(ends) and not all(ends)
    stretched = 0
    for op, last in zip(ops, ends):
        assert op.x == 30
        if not last and " " in op.text:
            assert right_edge(op) == pytest.approx(30 + 170, abs=0.01)
            assert op.word_spacing > 0
            stretched += 1
    assert stretched >= 4


def test_the_last_line_of_each_paragraph_is_set_left():
    ops, _ = justified_box()
    first_last = next(op for op in ops if op.text.endswith("edges."))
    for op in (first_last, ops[-1]):
        assert op.word_spacing == 0
        assert right_edge(op) < 30 + 170


def test_a_line_of_one_word_is_set_left():
    ops, _ = justified_box("Extraordinarily wonderful typography", width=100)
    assert all(op.word_spacing == 0 for op in ops if " " not in op.text)


def test_only_the_spaces_grow_the_letters_and_tracking_do_not():
    ops, _ = justified_box()
    op = next(op for op in ops if op.word_spacing)
    font = typography.default_font()
    plain = font.shape(op.text, 16).placements(0, 0)
    stretched = font.shape(op.text, 16, word_spacing=op.word_spacing).placements(0, 0)
    assert len(plain) == len(stretched)
    spaces_before = 0
    for (glyph, x, _), (_, stretched_x, _) in zip(plain, stretched):
        assert stretched_x == pytest.approx(x + spaces_before * op.word_spacing)
        spaces_before += op.text[glyph.cluster] == " "


def test_tracking_is_kept_and_the_line_still_ends_at_the_edge():
    def draw():
        p.text_size(16)
        p.text_tracking(2)
        p.text_align("justify")
        p.text_box(STORY, 30, 10, 190)

    ops = text_ops(draw)
    stretched = [op for op in ops if op.word_spacing]
    assert stretched and all(right_edge(op) == pytest.approx(220, abs=0.01) for op in stretched)


def test_the_overflow_is_the_same_as_for_a_left_box():
    def run(align):
        def draw():
            p.text_size(16)
            p.text_align(align)
            draw.rest = p.text_box(STORY, 30, 10, 170, 60)

        text_ops(draw)
        return draw.rest

    assert run("justify") == run("left") != ""


def test_the_last_line_shown_in_a_short_box_is_still_stretched_when_the_paragraph_goes_on():
    ops, rest = justified_box(height=60)
    assert rest and len(ops) == 3
    assert right_edge(ops[-1]) == pytest.approx(30 + 170, abs=0.01)


def test_blank_lines_keep_their_place():
    ops, _ = justified_box("One short line\n\nAnother short line", width=300)
    assert [op.text for op in ops] == ["One short line", "Another short line"]
    assert all(op.word_spacing == 0 for op in ops)


def test_text_without_a_box_sets_justify_as_left():
    def draw():
        p.text_align("justify")
        p.text("Left as usual\nand again", 50, 20)

    ops = text_ops(draw)
    assert [(op.x, op.word_spacing) for op in ops] == [(50, 0), (50, 0)]


def test_text_width_is_unchanged_and_the_box_width_is_what_the_line_measures():
    def draw():
        p.text_size(16)
        draw.plain = p.text_width("Posters are read")
        p.text_align("justify")
        p.text_box("Posters are read from far", 30, 10, 150)
        draw.after = p.text_width("Posters are read")

    ops = text_ops(draw)
    assert draw.plain == draw.after                           # measuring is not changed by the alignment
    assert right_edge(ops[0]) - ops[0].x == pytest.approx(150, abs=0.01)


def test_it_is_not_written_to_the_snapshot_when_there_is_no_spacing():
    [op] = text_ops(lambda: p.text("Hello", 10, 10))
    assert "word_spacing" not in ir.op_to_jsonable(op)


def test_the_spacing_round_trips_through_the_snapshot_format():
    ops, _ = justified_box()
    stretched = next(op for op in ops if op.word_spacing)
    assert ir.op_to_jsonable(stretched)["word_spacing"] == stretched.word_spacing
    assert ir.op_from_jsonable(ir.op_to_jsonable(stretched)) == stretched


# ---------------------------------------------------------------- FormattedString
def formatted() -> p.FormattedString:
    return (p.FormattedString().append("Posters are read from ", size=16)
            .append("far away", style="bold", size=16).append(", so the words must be easy to find. ", size=16)
            .append("A justified column", style="italic", size=16).append(" has two straight edges.", size=16))


def test_a_formatted_string_is_stretched_to_the_box_width_across_its_runs():
    def draw():
        p.text_align("justify")
        draw.rest = p.text_box(formatted(), 30, 10, 200)

    ops = text_ops(draw)
    by_top: dict[float, list[ir.Text]] = {}
    for op in ops:
        by_top.setdefault(op.y, []).append(op)
    assert len(by_top) >= 3
    *body, last = by_top.values()
    for pieces in body:
        edge = 0.0
        for op in pieces:
            run = typography.effective_font(op.style).shape(op.text, op.style.text_size,
                                                            word_spacing=op.word_spacing)
            edge = max(edge, op.x + run.advance)
        assert edge == pytest.approx(230, abs=0.01)
    assert all(op.word_spacing == 0 for op in last)


def test_a_formatted_string_keeps_its_pieces_in_order_without_gaps():
    def draw():
        p.text_align("justify")
        p.text_box(formatted(), 30, 10, 200)

    ops = text_ops(draw)
    line = [op for op in ops if op.y == ops[0].y]
    for left, right in zip(line, line[1:]):
        run = typography.effective_font(left.style).shape(left.text, left.style.text_size,
                                                          word_spacing=left.word_spacing)
        assert right.x == pytest.approx(left.x + run.advance, abs=0.01)
