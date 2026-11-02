"""Tidy a cut-out and give its outline (S-245, D-115, contract P12 and P13)."""
from __future__ import annotations

import math
import statistics

import pygame
import pytest

import funground as f
from funground import api
from funground.picture import Picture
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from conftest import ROOT

DATA = ROOT / "tests" / "data" / "cutout"      # two of the scenes of spike S-227: drawn for the spike, original, CC0


@pytest.fixture(autouse=True)
def sketch():
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    f.size(100, 100)
    return s


def scene():
    """An 80 x 60 lime picture: a red body (10..49 x 10..49) with a lime hole, and a red speck far away."""
    g = f.create_graphics(80, 60)
    g.background("lime")
    g.no_stroke()
    g.fill("red")
    g.rect(10, 10, 40, 40)
    g.fill("lime")
    g.rect(25, 25, 8, 8)                 # a hole: it looks like the background
    g.fill("red")
    g.rect(65, 5, 4, 4)                  # a speck: it looks like the body but is not joined to it
    return g


def pixel(g, x, y):
    g.load_pixels()
    i = (y * g.width + x) * 4
    return tuple(g.pixels[i:i + 4])


def visible(g):
    g.load_pixels()
    return {(i // 4 % g.width, i // 4 // g.width) for i in range(3, len(g.pixels), 4) if g.pixels[i]}


# ------------------------------------------------------------------ tidy
def test_defaults_are_unchanged():
    plain, explicit = scene(), scene()
    plain.remove_color("lime")
    explicit.remove_color("lime", tidy=False, at=None)
    assert bytes(plain._snapshot().pixels) == bytes(explicit._snapshot().pixels)
    assert pixel(plain, 66, 6)[3] == 255 and pixel(plain, 28, 28)[3] == 0      # the speck stays, the hole stays open


def test_tidy_drops_specks_and_fills_holes_with_the_original_colour():
    original, g = scene(), scene()
    g.remove_color("lime", tidy=True)
    assert pixel(g, 66, 6) == (0, 0, 0, 0)                          # the speck is gone
    assert pixel(g, 28, 28) == pixel(original, 28, 28) == (0, 255, 0, 255)      # the hole has its own lime back
    assert pixel(g, 0, 0) == (0, 0, 0, 0)                           # the outside is still see-through
    for x, y in ((10, 10), (49, 49), (30, 12), (25, 25), (32, 32)):
        assert pixel(g, x, y) == pixel(original, x, y)              # every kept pixel is exactly the original
    assert len(visible(g)) == 40 * 40


def test_tidy_keeps_the_original_colours_of_a_textured_hole():
    g = f.create_graphics(30, 30)
    g.background("lime")
    g.no_stroke()
    g.fill("red")
    g.rect(5, 5, 20, 20)
    g.fill(0, 255, 0)
    g.rect(12, 12, 6, 6)
    g.fill(0, 250, 3)
    g.rect(14, 14, 2, 2)
    original = g.copy()
    g.remove_color("lime", tolerance=10, tidy=True)
    for x in range(30):
        for y in range(30):
            if 5 <= x < 25 and 5 <= y < 25:
                assert pixel(g, x, y) == pixel(original, x, y)
            else:
                assert pixel(g, x, y)[3] == 0


def test_tidy_works_with_remove_background():
    empty = f.create_graphics(60, 40)
    empty.background("navy")
    now = empty.copy()
    now.no_stroke()
    now.fill("gold")
    now.rect(10, 10, 30, 20)
    now.rect(50, 2, 3, 3)                                           # a speck
    now.remove_background(empty, tidy=True)
    assert pixel(now, 51, 3)[3] == 0 and pixel(now, 20, 20)[3] == 255
    assert len(visible(now)) == 30 * 20


def test_at_chooses_the_part():
    g = f.create_graphics(80, 60)
    g.background("lime")
    g.no_stroke()
    g.fill("red")
    g.rect(5, 5, 40, 40)                                            # the larger part
    g.rect(60, 10, 10, 10)                                          # the smaller part
    largest, chosen = g.copy(), g.copy()
    largest.remove_color("lime", tidy=True)
    chosen.remove_color("lime", at=(65, 15))                         # at= implies tidy
    assert pixel(largest, 10, 10)[3] == 255 and pixel(largest, 65, 15)[3] == 0
    assert pixel(chosen, 10, 10)[3] == 0 and pixel(chosen, 65, 15)[3] == 255
    assert len(visible(chosen)) == 100


def test_at_in_a_hole_is_on_a_see_through_pixel_and_the_picture_is_not_changed():
    g = scene()
    before = bytes(g._snapshot().pixels)
    with pytest.raises(ValueError, match="see-through"):
        g.remove_color("lime", at=(28, 28))
    with pytest.raises(ValueError, match="see-through"):
        g.remove_color("lime", at=(0, 0))
    assert bytes(g._snapshot().pixels) == before


@pytest.mark.parametrize("bad", [(-1, 5), (80, 5), (5, 60), (5.0, 60.0), (float("inf"), 1)])
def test_at_outside_the_picture_is_a_plain_error(bad):
    g = scene()
    with pytest.raises(ValueError, match="outside the picture"):
        g.remove_color("lime", at=bad)
    with pytest.raises(ValueError, match="outside the picture"):
        g.remove_background(scene(), at=bad)


@pytest.mark.parametrize("bad", [5, "x", (1,), (1, 2, 3), ("a", "b"), (True, 3), (float("nan"), 1)])
def test_at_that_is_not_a_point_is_a_value_error(bad):
    with pytest.raises(ValueError, match="at must be a point"):
        scene().remove_color("lime", at=bad)


def test_tidy_must_be_true_or_false():
    with pytest.raises(TypeError, match="tidy"):
        scene().remove_color("lime", tidy=1)


def test_tidy_with_everything_removed_gives_a_see_through_picture():
    g = scene()
    g.remove_color("lime", tolerance=255, tidy=True)
    assert visible(g) == set()


def test_at_uses_logical_pixels_on_a_dense_picture():
    g = Picture(40, 30, 2.0, "dense")                               # 80 x 60 real pixels
    g._write_pixels(bytes([0, 0, 255, 255]) * 80 * 60)               # all red
    g.remove_color("lime", at=(39.9, 29.9))                          # the last logical pixel: fine
    assert g._snapshot().pixels[3] == 255 and g.outline(20)


# ------------------------------------------------------------------ the acceptance numbers
def cut(name, **options):
    empty = f.load_image(str(DATA / f"{name}_empty.jpg"))
    shot = f.load_image(str(DATA / f"{name}_person.jpg"))
    shot.remove_background(empty, tolerance=30, **options)
    return shot


def iou(picture, name):
    truth = pygame.mask.from_threshold(pygame.image.load(str(DATA / f"{name}_truth.png")), (255, 255, 255),
                                       (127, 127, 127, 255))
    picture.load_pixels()
    kept = pygame.mask.from_surface(pygame.image.frombytes(bytes(picture.pixels), (picture.width, picture.height),
                                                           "RGBA"), 127)
    inside = kept.overlap_area(truth, (0, 0))
    return inside / (kept.count() + truth.count() - inside)


def test_the_busy_scene_reaches_096_with_tidy():
    assert iou(cut("busy_background"), "busy_background") < 0.9           # without tidy
    assert iou(cut("busy_background", tidy=True), "busy_background") >= 0.96


def test_the_striped_scene_reaches_055_with_a_point_on_the_person():
    assert iou(cut("striped_wall"), "striped_wall") < 0.5
    assert iou(cut("striped_wall", at=(275, 250)), "striped_wall") >= 0.55


# ------------------------------------------------------------------ outline
def disc(radius=30, size=100):
    g = f.create_graphics(size, size)
    g.no_stroke()
    g.fill("tomato")
    g.circle(size / 2, size / 2, radius * 2)
    return g


def gaps(points):
    return [math.dist(points[i], points[(i + 1) % len(points)]) for i in range(len(points))]


def test_outline_has_at_most_the_points_asked_for_and_80_at_first():
    g = disc()
    assert len(g.outline()) == 80
    assert len(g.outline(points=12)) == 12
    assert len(g.outline(points=3)) == 3
    assert all(isinstance(p, tuple) and len(p) == 2 for p in g.outline(10))


def test_outline_of_a_small_shape_has_fewer_points_than_asked_for():
    g = f.create_graphics(20, 20)
    g.no_stroke()
    g.fill("red")
    g.rect(5, 5, 4, 4)
    assert 3 <= len(g.outline(80)) <= 12


def test_outline_points_are_evenly_spread_round_a_circle():
    points = disc(30).outline(60)
    d = gaps(points)
    assert statistics.pstdev(d) / statistics.mean(d) < 0.05
    assert max(d) < 1.15 * min(d)
    assert all(29 <= math.dist(p, (50, 50)) <= 31 for p in points)    # on the border


def test_outline_is_a_closed_border_round_a_known_shape():
    g = f.create_graphics(100, 80)
    g.no_stroke()
    g.fill("red")
    g.rect(20, 10, 50, 40)                                             # pixels 20..69 x 10..49
    points = g.outline(40)
    d = gaps(points)
    assert len(points) == 40 and max(d) < 1.5 * min(d) + 1               # evenly spread, and no gap at the close
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    assert (min(xs), max(xs), min(ys), max(ys)) == (20.5, 69.5, 10.5, 49.5)     # the centres of the border pixels
    for x, y in points:                                                 # every point is on the border
        assert x in (20.5, 69.5) or y in (10.5, 49.5)
    for corner in ((20.5, 10.5), (69.5, 10.5), (69.5, 49.5), (20.5, 49.5)):
        assert min(math.dist(p, corner) for p in points) < 10          # the corners are covered
    assert abs(sum(d) - 2 * (49 + 39)) < 12                             # it goes all the way round


def test_outline_is_the_border_of_the_largest_part_only():
    g = scene()
    g.remove_color("lime")                                              # the hole and a speck are left
    xs = [p[0] for p in g.outline(80)]
    assert max(xs) < 51 and min(xs) > 9                                 # not the speck at x = 65, nor the hole


def test_outline_of_a_picture_with_nothing_to_see_is_an_empty_list():
    assert f.create_graphics(20, 20).outline() == []
    g = scene()
    g.remove_color("lime", tolerance=255)
    assert g.outline(5) == []


def test_outline_does_not_change_the_picture():
    g = disc()
    before = bytes(g._snapshot().pixels)
    g.outline()
    assert bytes(g._snapshot().pixels) == before


@pytest.mark.parametrize("bad", [2, 0, -5, 80.0, 3.5, "80", None, True])
def test_outline_points_must_be_a_whole_number_of_three_or_more(bad):
    with pytest.raises(ValueError, match="points"):
        disc().outline(points=bad)


def test_outline_feeds_a_path_and_a_clip():
    points = disc().outline(30)
    path = f.path().polygon(points)
    stencil = f.create_graphics(100, 100)
    stencil.no_stroke()
    stencil.fill("white")
    stencil.draw_path(path)
    assert pixel(stencil, 50, 50)[3] == 255 and pixel(stencil, 5, 5)[3] == 0
    with f.saved_state():
        f.clip(path)


def test_outline_is_in_logical_pixels_on_a_dense_picture():
    g = Picture(50, 50, 2.0, "dense")                                   # 100 x 100 real pixels
    rows = bytearray(100 * 100 * 4)
    for y in range(20, 80):
        for x in range(20, 80):
            i = (y * 100 + x) * 4
            rows[i:i + 4] = bytes([0, 0, 255, 255])
    g._write_pixels(bytes(rows))
    xs = [p[0] for p in g.outline(16)]
    assert min(xs) == pytest.approx(10.25) and max(xs) == pytest.approx(39.75)
