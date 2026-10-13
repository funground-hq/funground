"""Type on a path (story S-161; contract row T24): f.text_on_path(message, path, offset=0)."""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET

import pytest
from pypdf import PdfReader

import funground as p
from funground import api, ir, typography
from funground.geometry import PathMeasure, Transform
from funground.web import Session

SVG = "{http://www.w3.org/2000/svg}"


def shot(canvas) -> bytes:
    return bytes(canvas._pixels().data)


def line(x1=20, y1=60, x2=180, y2=60):
    return p.path().move_to(x1, y1).line_to(x2, y2)


def style_for_text():
    p.fill("red")
    p.no_stroke()
    p.text_size(20)
    p.text_align("left", "baseline")


class Letter:
    """One letter that text_on_path drew, read back from the ops: the text of its Text op, where its middle
    is on its baseline, which way it turns (degrees), and where its advance starts and ends."""

    def __init__(self, op: ir.Text, frame: Transform) -> None:
        self.text = op.text
        self.op = op
        ascent = typography.text_metrics(op.style.text_size, typography.effective_font(op.style))[0]
        self.x, self.y = frame.apply(0, op.y + ascent)
        self.degrees = math.degrees(math.atan2(frame.b, frame.a))
        self.start = frame.apply(op.x, op.y + ascent)
        self.end = frame.apply(-op.x, op.y + ascent)


def letters() -> list[Letter]:
    frame, stack, out = Transform(), [], []
    for op in api.active_sketch().frame.ops:
        if isinstance(op, ir.Save):
            stack.append(frame)
        elif isinstance(op, ir.Restore):
            frame = stack.pop()
        elif isinstance(op, ir.Concat):
            frame = frame.concat(op.transform)
        elif isinstance(op, ir.Text):
            out.append(Letter(op, frame))
    return out


# ---- on a straight line it is f.text

@pytest.mark.parametrize("message", ["Hello, world", "office waffle", "fi fl ffi"])
def test_on_a_straight_line_it_draws_what_text_draws(canvas, message):
    p.background("white")
    style_for_text()
    p.text(message, 20, 60)
    plain = shot(canvas)
    p.background("white")
    assert p.text_on_path(message, line()) == ""
    assert any(v != 255 for v in plain)
    assert shot(canvas) == plain


@pytest.mark.parametrize("align", ["center", "right"])
def test_a_line_with_alignment_matches_text_with_the_same_alignment(canvas, align):
    p.background("white")
    style_for_text()
    p.text_align(align, "baseline")
    anchor = {"center": 100, "right": 180}[align]
    p.text("Aligned", anchor, 60)
    plain = shot(canvas)
    p.background("white")
    p.text_on_path("Aligned", line())
    assert shot(canvas) == plain


def test_a_ligature_is_one_letter_and_a_space_rides_with_the_letter_before(canvas):
    style_for_text()
    p.text_on_path("fine art", line())
    assert [letter.text for letter in letters()] == ["fi", "n", "e ", "a", "r", "t"]
    api.active_sketch().frame.clear()
    p.text_features(liga=False)
    p.text_on_path("fine", line())
    assert [letter.text for letter in letters()] == ["f", "i", "n", "e"]


def test_the_letters_keep_the_kerning_of_the_whole_text(canvas):
    style_for_text()
    p.text_on_path("AVA", line())
    a, v, _ = letters()
    shaped = typography.default_font().shape("AVA", 20)
    kerned = shaped.glyphs[0].x_advance * shaped.scale
    assert kerned < p.text_width("A")                    # AV is kerned in this font
    assert v.start[0] - a.start[0] == pytest.approx(kerned)


# ---- on a circle

def test_each_letter_stands_on_the_circle_and_turns_with_it(canvas):
    style_for_text()
    p.text_on_path("ROUND AND ROUND AND ROUND", p.path().circle(100, 100, 120))
    drawn = letters()
    assert len(drawn) >= 15
    for letter in drawn:
        assert math.hypot(letter.x - 100, letter.y - 100) == pytest.approx(60, abs=0.5)
        angle = math.degrees(math.atan2(letter.y - 100, letter.x - 100)) + 90      # the tangent, clockwise
        assert (letter.degrees - angle + 180) % 360 - 180 == pytest.approx(0, abs=0.5)


def test_a_clockwise_circle_has_its_text_on_the_outside_and_a_flipped_one_on_the_inside(canvas):
    style_for_text()
    outside = p.path().circle(100, 100, 100)
    p.text_on_path("OUT", outside, offset=0.785 * 100 - 12)          # starts near the top
    top = letters()
    api.active_sketch().frame.clear()
    # "up" for a letter is its local -y; for a clockwise circle that points away from the centre
    for letter in top:
        up = (math.sin(math.radians(letter.degrees)), -math.cos(math.radians(letter.degrees)))
        assert up[0] * (letter.x - 100) + up[1] * (letter.y - 100) > 0
    inside = p.path().circle(100, 100, 100).scale(-1, 1).translate(200, 0)
    p.text_on_path("IN", inside)
    for letter in letters():
        up = (math.sin(math.radians(letter.degrees)), -math.cos(math.radians(letter.degrees)))
        assert up[0] * (letter.x - 100) + up[1] * (letter.y - 100) < 0


def test_the_angle_follows_a_curve_smoothly(canvas):
    style_for_text()
    arc = p.path().move_to(10, 90).curve_to(10, 10, 190, 10, 190, 90)
    p.text_on_path("a smooth arch of letters", arc)
    drawn = letters()
    turns = [b.degrees - a.degrees for a, b in zip(drawn, drawn[1:])]
    assert all(0 < turn < 25 for turn in turns)      # the letters turn a little more each, with no jump
    assert drawn[0].degrees < -60 and drawn[-1].degrees > 60


def test_a_closed_path_carries_on_past_its_start(canvas):
    style_for_text()
    ring = p.path().circle(100, 100, 120)
    length = PathMeasure(ring.geometry).length
    message = "AROUND" * 4
    assert p.text_width(message) < length
    assert p.text_on_path(message, ring, offset=0.75 * length) == ""
    assert len(letters()) == len(message)
    first = letters()[0]
    assert first.start == pytest.approx((100, 40), abs=1)                     # the text starts at the top: it wrapped
    assert first.degrees == pytest.approx(0, abs=7)       # and its first letter is upright there
    api.active_sketch().frame.clear()
    too_long = "AROUND" * 40
    rest = p.text_on_path(too_long, ring)
    assert 0 < len(rest) < len(too_long) and too_long.endswith(rest)
    drawn = "".join(letter.text for letter in letters())
    assert drawn + rest == too_long
    assert p.text_width(drawn) <= length + 1e-6 < p.text_width(drawn + rest[0])


# ---- overflow, alignment and offset

def test_text_that_does_not_fit_is_not_drawn_and_is_returned(canvas):
    style_for_text()
    width = p.text_width("Hello")
    rest = p.text_on_path("Hello World", line(0, 50, width + 1, 50))
    assert rest == " World"
    assert "".join(letter.text for letter in letters()) == "Hello"
    api.active_sketch().frame.clear()
    assert p.text_on_path("Hello", line(0, 50, width, 50)) == ""             # exactly the length fits
    assert len(letters()) == 5
    api.active_sketch().frame.clear()
    assert p.text_on_path("Hello", line(0, 50, width - 0.5, 50)) == "o"


def test_an_empty_message_draws_nothing_and_returns_nothing(canvas):
    assert p.text_on_path("", line()) == ""
    assert p.text_on_path("   ", line()) == ""
    assert letters() == []


def test_alignment_along_the_path(canvas):
    style_for_text()
    width = p.text_width("Middle")
    for align, start in (("left", 0), ("center", (160 - width) / 2), ("right", 160 - width), ("justify", 0)):
        p.text_align(align, "baseline")
        api.active_sketch().frame.clear()
        p.text_on_path("Middle", line())
        drawn = letters()
        assert drawn[0].start[0] == pytest.approx(20 + start, abs=1e-6), align
        assert drawn[-1].end[0] == pytest.approx(20 + start + width, abs=1e-6), align


def test_the_offset_moves_the_text_along_the_path_after_alignment(canvas):
    style_for_text()
    width = p.text_width("Move")
    p.text_on_path("Move", line(), offset=30)
    assert letters()[0].start[0] == pytest.approx(50)
    api.active_sketch().frame.clear()
    p.text_align("center", "baseline")
    p.text_on_path("Move", line(), offset=-10)
    assert letters()[0].start[0] == pytest.approx(20 + (160 - width) / 2 - 10)
    api.active_sketch().frame.clear()
    p.text_align("right", "baseline")
    assert p.text_on_path("Move", line(), offset=10) == "e"           # pushed past the end: the last letter is cut
    assert "".join(letter.text for letter in letters()) == "Mov"


def test_letters_before_the_start_of_an_open_path_are_left_out_and_not_returned(canvas):
    style_for_text()
    first = p.text_width("H")
    assert p.text_on_path("Hello", line(), offset=-first - 1) == ""
    assert "".join(letter.text for letter in letters()) == "llo"          # the "e" starts before the path too


def test_the_vertical_alignment_moves_the_letters_off_the_path_along_the_normal(canvas):
    style_for_text()
    ascent, descent = p.text_ascent(), p.text_descent()
    expected = {"baseline": -ascent, "top": 0, "center": -(ascent + descent) / 2, "bottom": -(ascent + descent)}
    for vertical, top in expected.items():
        p.text_align("left", vertical)
        api.active_sketch().frame.clear()
        p.text_on_path("Ab", p.path().circle(100, 100, 120))
        for letter in letters():
            assert letter.op.y == pytest.approx(top), vertical
    p.text_align("left", "bottom")
    api.active_sketch().frame.clear()
    p.text_on_path("Ab", line())
    assert all(l.y == pytest.approx(60 - descent) for l in letters())      # the bottom of the letters is on the path


# ---- the drawing state

def test_it_follows_the_current_transform_and_leaves_it_alone(canvas):
    p.background("white")
    style_for_text()
    p.text_on_path("Moved", line(50, 60, 190, 60))
    expected = shot(canvas)
    p.background("white")
    p.push()
    p.translate(30, 0)
    p.text_on_path("Moved", line(20, 60, 160, 60))
    assert api.active_sketch()._transform_now() == Transform.translation(30, 0)
    p.pop()
    assert api.active_sketch()._transform_now().is_identity
    assert shot(canvas) == expected


def test_a_gradient_fill_stays_where_the_sketch_put_it(canvas):
    p.background("white")
    style_for_text()
    p.fill(p.linear_gradient(20, 0, 180, 0, ["red", "blue"]))
    p.text("Gradient text", 20, 60)
    plain = shot(canvas)
    p.background("white")
    p.text_on_path("Gradient text", line())
    assert shot(canvas) == plain


def test_it_uses_the_fill_and_the_current_font_settings(canvas):
    p.background("white")
    p.fill("red")
    p.text_size(24)
    p.text_style("bold")
    p.text_tracking(3)
    p.text_align("left", "baseline")
    p.text("Bold", 20, 60)
    plain = shot(canvas)
    p.background("white")
    p.text_on_path("Bold", line())
    assert shot(canvas) == plain


def test_it_works_in_a_running_frame(frame_canvas):
    p.background("white")
    p.fill("black")
    p.text_size(24)
    p.text_align("left", "baseline")
    assert p.text_on_path("Frame", line(10, 60, 190, 60)) == ""
    assert any(frame_canvas.get_at((x, y)).r < 128 for x in range(10, 100) for y in range(40, 62))


def test_it_works_on_a_picture(canvas):
    g = p.create_graphics(200, 100)
    g.fill("black")
    g.text_size(20)
    g.text_align("left", "baseline")
    assert g.text_on_path("Picture", g.path().move_to(10, 60).line_to(190, 60)) == ""
    p.background("white")
    p.image(g, 0, 0)
    assert any(v != 255 for v in shot(canvas))


def test_it_works_with_a_font_that_needs_fallback(canvas):
    style_for_text()
    assert p.text_on_path("a\U0001F600b", line()) == ""
    assert [letter.text for letter in letters()] == ["a", "\U0001F600", "b"]


# ---- what it refuses

def test_a_path_with_no_length_is_a_value_error(canvas):
    with pytest.raises(ValueError, match="some length"):
        p.text_on_path("Hi", p.path())
    with pytest.raises(ValueError, match="some length"):
        p.text_on_path("Hi", p.path().move_to(10, 10))
    with pytest.raises(ValueError, match="some length"):
        p.text_on_path("Hi", p.path().move_to(10, 10).line_to(10, 10))


def test_wrong_arguments_have_plain_errors(canvas):
    with pytest.raises(TypeError, match="needs a path"):
        p.text_on_path("Hi", "not a path")
    with pytest.raises(TypeError, match="FormattedString"):
        p.text_on_path(p.FormattedString().append("Hi"), line())
    with pytest.raises(TypeError, match="offset"):
        p.text_on_path("Hi", line(), "far")
    with pytest.raises(TypeError, match="offset"):
        p.text_on_path("Hi", line(), True)
    with pytest.raises(ValueError, match="finite"):
        p.text_on_path("Hi", line(), float("nan"))
    with pytest.raises(ValueError, match="new line"):
        p.text_on_path("Two\nlines", line())


def test_it_accepts_a_path_geometry_as_well_as_a_builder(canvas):
    style_for_text()
    assert p.text_on_path("Hi", line().geometry) == ""
    assert [letter.text for letter in letters()] == ["H", "i"]


def test_only_the_first_part_of_a_path_is_followed(canvas):
    style_for_text()
    two = p.path().move_to(0, 10).line_to(100, 10).move_to(0, 80).line_to(100, 80)
    p.text_on_path("Hi", two)
    assert {round(letter.y) for letter in letters()} == {10}


# ---- measuring

def test_path_measure_follows_lines_curves_and_closed_shapes():
    straight = PathMeasure(line(0, 0, 30, 40).geometry)
    assert straight.length == pytest.approx(50)
    assert not straight.closed
    assert straight.point_at(25) == pytest.approx((15, 20, math.degrees(math.atan2(40, 30))))
    assert straight.point_at(-5)[:2] == pytest.approx((0, 0))
    assert straight.point_at(500)[:2] == pytest.approx((30, 40))
    circle = PathMeasure(p.path().circle(0, 0, 200).geometry)
    assert circle.closed
    assert circle.length == pytest.approx(math.pi * 200, rel=1e-3)
    x, y, degrees = circle.point_at(circle.length / 4)                    # a quarter of the way: the bottom
    assert (x, y) == pytest.approx((0, 100), abs=0.2)
    assert degrees == pytest.approx(180, abs=0.1)
    assert circle.point_at(circle.length + 1)[:2] == pytest.approx(circle.point_at(1)[:2])    # it wraps
    assert PathMeasure(p.path().geometry).length == 0


def test_a_measured_curve_is_close_to_the_curve():
    square = p.path().rect(0, 0, 40, 40)
    box = PathMeasure(square.geometry)
    assert box.closed and box.length == pytest.approx(160)
    assert box.point_at(50)[:2] == pytest.approx((40, 10))


# ---- files

def test_the_pdf_holds_each_letter_as_selectable_text(canvas, tmp_path):
    p.background("white")
    style_for_text()
    message = "FUNGROUND POSTER PRINT"
    assert p.text_on_path(message, p.path().circle(100, 100, 120)) == ""
    path = tmp_path / "ring.pdf"
    p.save(str(path))
    extracted = PdfReader(str(path)).pages[0].extract_text()
    assert extracted.replace("\n", "") == message       # pypdf puts a line break between letters that turn


def test_the_pdf_with_text_as_shapes_has_no_text_and_the_same_picture(canvas, tmp_path):
    p.background("white")
    style_for_text()
    p.text_on_path("Shapes", line())
    path = tmp_path / "shapes.pdf"
    p.save(str(path), text="shapes")
    assert PdfReader(str(path)).pages[0].extract_text().strip() == ""


def test_the_svg_holds_each_letter_as_live_text_in_order(canvas, tmp_path):
    style_for_text()
    message = "Round the ring we go"
    p.text_on_path(message, p.path().circle(100, 100, 120))
    path = tmp_path / "ring.svg"
    p.save(str(path))
    texts = list(ET.parse(path).getroot().iter(SVG + "text"))
    assert "".join(t.text for t in texts) == message
    assert len(texts) == len(message.replace(" ", ""))
    assert all("matrix(" in t.get("transform", "") for t in texts[1:])       # each turned to the path


def test_it_works_under_a_web_session(tmp_path):
    p.size(300, 100)
    p.text_size(20)
    expected = p.text_on_path("Hello World", line(10, 50, 60, 50))          # the answer outside a Session
    assert 0 < len(expected) < len("Hello World")
    answer = tmp_path / "rest.txt"
    source = f"""
import funground as f
f.size(300, 100)
f.fill("black")
f.text_size(20)
rest = f.text_on_path("Hello World", f.path().move_to(10, 50).line_to(60, 50))
open({str(answer)!r}, "w", encoding="utf-8").write(rest)
f.show()
"""
    session = Session(300, 100)
    try:
        session.start(source, "sketch.py")
    finally:
        session.stop()
    assert answer.read_text(encoding="utf-8") == expected
