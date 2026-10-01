"""Text as a path (story S-088; contract row F13).

The main check: drawing f.text_path(...) with a fill and no stroke gives the same pixels as f.text(...).
"""
from __future__ import annotations

import os

import pygame
import pytest

import funground as p
from funground import api
from funground.paths import PathBuilder
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from test_path_booleans import fill_area

FONT = os.path.join(os.path.dirname(__file__), "..", "examples", "gallery", "text", "fonts", "DejaVuSansMono.ttf")


def shot(canvas) -> bytes:
    return bytes(canvas._pixels().data)


# The text op fills each glyph on its own; text_path joins the glyphs into one path that is filled once.
# Where two glyphs touch inside one edge pixel, the two ways of adding up the edge differ by a few
# levels (1 to 9 of 255 in these tests, in a dozen pixels). A single letter matches exactly.
CLOSE = 10


def worst(a: bytes, b: bytes) -> int:
    """The largest difference in any one colour channel of any pixel."""
    assert len(a) == len(b)
    return max((abs(i - j) for i, j in zip(a, b)), default=0)


def draw_both(canvas, message, x, y, setup=lambda: None):
    """Pixels of f.text and of draw_path(text_path), with the same fill and no stroke."""
    out = []
    for how in ("text", "path"):
        p.background("white")
        p.fill("red")
        p.no_stroke()
        setup()
        if how == "text":
            p.text(message, x, y)
        else:
            p.draw_path(p.text_path(message, x, y))
        out.append(shot(canvas))
    return out


def assert_same(canvas, message, x, y, setup=lambda: None):
    a, b = draw_both(canvas, message, x, y, setup)
    assert any(v != 255 for v in a), "the text drew nothing, so the comparison proves nothing"
    assert worst(a, b) <= CLOSE


# ---------------------------------------------------------------- same pixels as text()
def test_default_settings_match_text(canvas):
    assert_same(canvas, "Hello, fun!", 10, 20)


def test_a_single_letter_matches_text_exactly(canvas):
    a, b = draw_both(canvas, "g", 20, 10, lambda: p.text_size(60))
    assert any(v != 255 for v in a)
    assert a == b


def test_centre_baseline_alignment_matches_text(canvas):
    def setup():
        p.text_align("center", "baseline")
        p.text_size(24)
    assert_same(canvas, "Centred", 100, 60, setup)


def test_right_bottom_alignment_matches_text(canvas):
    def setup():
        p.text_align("right", "bottom")
    assert_same(canvas, "Right", 190, 90, setup)


def test_two_lines_with_leading_match_text(canvas):
    def setup():
        p.text_size(16)
        p.text_leading(30)
    assert_same(canvas, "one\ntwo", 10, 10, setup)


def test_blank_line_between_lines_matches_text(canvas):
    def setup():
        p.text_size(14)
    assert_same(canvas, "top\n\nbottom", 10, 5, setup)


def test_bold_style_matches_text(canvas):
    def setup():
        p.text_style("bold")
        p.text_size(22)
    assert_same(canvas, "Bold", 10, 20, setup)


def test_loaded_font_matches_text(canvas):
    def setup():
        p.text_font(p.load_font(FONT))
        p.text_size(18)
    assert_same(canvas, "mono 123", 10, 30, setup)


# ---------------------------------------------------------------- what the path is
def test_returns_a_new_builder_each_time():
    a, b = p.text_path("A", 0, 0), p.text_path("A", 0, 0)
    assert isinstance(a, PathBuilder) and a is not b
    assert not a.is_empty and a.is_closed
    assert a.geometry == b.geometry


def test_path_is_not_transformed(canvas):
    plain = p.text_path("Hi", 10, 10).geometry
    p.push()
    p.translate(50, 30)
    p.rotate(20)
    moved = p.text_path("Hi", 10, 10).geometry
    p.pop()
    assert moved == plain


def test_drawing_the_path_applies_the_current_transform(canvas):
    path = p.text_path("Hi", 0, 0)
    p.background("white")
    p.fill("red")
    p.no_stroke()
    p.push()
    p.translate(30, 40)
    p.draw_path(path)
    p.pop()
    moved = shot(canvas)
    p.background("white")
    p.text("Hi", 30, 40)
    assert worst(moved, shot(canvas)) == 0


def test_the_colour_is_not_part_of_the_path(canvas):
    p.fill("red")
    path = p.text_path("Hi", 10, 10)
    p.background("white")
    p.fill("blue")
    p.no_stroke()
    p.draw_path(path)
    data = shot(canvas)
    assert any(data[i] == 255 and data[i + 1] == 0 and data[i + 2] == 0 for i in range(0, len(data), 4))  # blue (BGRA)
    assert not any(data[i + 2] == 255 and data[i] == 0 for i in range(0, len(data), 4))                   # no red


def test_position_moves_the_path():
    a = p.text_path("Hi", 10, 10).bounds()
    b = p.text_path("Hi", 40, 25).bounds()
    assert b[0] - a[0] == pytest.approx(30) and b[1] - a[1] == pytest.approx(15)


def test_empty_message_gives_an_empty_path():
    assert p.text_path("", 10, 10).is_empty
    assert p.text_path("\n\n", 10, 10).is_empty


def test_numbers_are_turned_into_text_like_text_does():
    assert p.text_path(42, 0, 0).geometry == p.text_path("42", 0, 0).geometry


def test_spaces_alone_give_an_empty_path():
    assert p.text_path("   ", 0, 0).is_empty


def test_size_scales_the_path():
    p.text_size(20)
    small = p.text_path("W", 0, 0).bounds()
    p.text_size(40)
    big = p.text_path("W", 0, 0).bounds()
    assert (big[2] - big[0]) == pytest.approx(2 * (small[2] - small[0]), rel=0.01)


# ---------------------------------------------------------------- works with the path tools
def test_difference_cuts_the_letters_out(canvas):
    p.text_size(60)
    letters = p.text_path("O", 20, 10)
    panel = p.path().rect(10, 5, 100, 80)
    cut = panel.difference(letters)
    assert fill_area(canvas, cut) < fill_area(canvas, panel) - 300
    assert fill_area(canvas, cut) + fill_area(canvas, letters) == pytest.approx(fill_area(canvas, panel), abs=40)


def test_expand_stroke_gives_an_outline(canvas):
    p.text_size(50)
    ring = p.text_path("I", 20, 10).expand_stroke(3)
    assert isinstance(ring, PathBuilder) and not ring.is_empty
    assert fill_area(canvas, ring) > 0


def test_clip_to_letters(canvas):
    p.text_size(80)
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.push()
    p.clip(p.text_path("I", 20, 0))
    p.rect(0, 0, 200, 100)
    p.pop()
    clipped = shot(canvas)
    drawn = fill_area(canvas, p.text_path("I", 20, 0))
    area = sum((255 - clipped[i]) / 255 for i in range(0, len(clipped), 4))
    assert drawn > 100
    assert area == pytest.approx(drawn, abs=2)


def test_path_methods_work_on_it():
    path = p.text_path("Hi", 10, 10)
    assert path.translate(5, 5).bounds()[0] == pytest.approx(path.bounds()[0] + 5)


# ---------------------------------------------------------------- pictures and scripts
def test_picture_has_text_path(canvas):
    from funground.picture import ALLOWED_METHODS
    assert "text_path" in ALLOWED_METHODS
    g = p.create_graphics(100, 50)
    g.text_size(20)
    path = g.text_path("Hi", 5, 5)
    assert isinstance(path, PathBuilder) and not path.is_empty


def test_picture_uses_its_own_text_settings(canvas):
    g = p.create_graphics(100, 50)
    g.text_size(10)
    small = g.text_path("W", 0, 0).bounds()
    g.text_size(30)
    big = g.text_path("W", 0, 0).bounds()
    assert big[2] > small[2] * 2
    p.text_size(50)                      # the window's own size does not matter to the picture
    assert g.text_path("W", 0, 0).bounds() == big


def test_picture_path_matches_picture_text(canvas, tmp_path):
    files = []
    for how in ("text", "path"):
        g = p.create_graphics(120, 50)
        g.background("white")
        g.fill("red")
        g.no_stroke()
        g.text_size(24)
        if how == "text":
            g.text("Pic", 10, 10)
        else:
            g.draw_path(g.text_path("Pic", 10, 10))
        files.append(tmp_path / (how + ".png"))
        g.save(str(files[-1]))
    a, b = (pygame.image.load(str(f)) for f in files)
    assert worst(pygame.image.tobytes(a, "RGBA"), pygame.image.tobytes(b, "RGBA")) <= CLOSE


def test_works_in_a_script(tmp_path):
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(120, 60)
    p.background("white")
    p.fill("black")
    p.no_stroke()
    p.draw_path(p.text_path("Go", 10, 10))
    p.save(str(tmp_path / "a.png"))
    image = pygame.image.load(str(tmp_path / "a.png"))
    assert any(tuple(image.get_at((x, y)))[:3] != (255, 255, 255) for x in range(10, 40) for y in range(10, 40))
