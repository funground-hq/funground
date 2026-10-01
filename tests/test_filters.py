"""Copy, resize, mask and filters (S-080, contract P9 and P10), plus pictures under no_smooth (P3)."""
from __future__ import annotations

import math
import random

import pytest

import funground as p
from funground import api, imaging, ir
from funground.color import Color
from funground.picture import Picture
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def script(width=20, height=10) -> Sketch:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(width, height)
    return s


def run_draw(draw, size=(40, 30)) -> Sketch:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(*size), "draw": draw}, max_frames=1)
    return s


def final_px(s: Sketch, x: int, y: int) -> tuple[int, int, int]:
    (w, _h), rgb = s.last_frame
    i = (y * w + x) * 3
    return tuple(rgb[i:i + 3])


def rgba(c: Color) -> tuple[int, int, int, int]:
    return (c.red, c.green, c.blue, c.alpha)


def make(width, height, pixels) -> Picture:
    """A picture whose pixel i is pixels[i] (an (r, g, b) or (r, g, b, a) tuple)."""
    g = p.create_graphics(width, height)
    for i, c in enumerate(pixels):
        g.set(i % width, i // width, *c)
    return g


def read(g: Picture) -> list[tuple[int, int, int, int]]:
    return [rgba(g.get(x, y)) for y in range(g.height) for x in range(g.width)]


def apply(kind, value, pixels, width=None):
    """Run a filter on unpremultiplied RGBA tuples; give the tuples back."""
    width = width or len(pixels)
    height = len(pixels) // width
    flat = bytes(v for c in pixels for v in (tuple(c) + (255,) * (4 - len(c))))
    out = imaging.bgra_to_rgba(imaging.filter_bgra(imaging.rgba_to_bgra(flat, width, height), width, height, kind, value),
                               width, height)
    return [tuple(out[i:i + 4]) for i in range(0, len(out), 4)]


# ---- P9: copy -----------------------------------------------------------------------------------
def test_copy_has_the_same_pixels_and_is_independent():
    script()
    g = p.create_graphics(8, 6)
    g.background(10, 20, 30)
    c = g.copy()
    assert isinstance(c, Picture) and c is not g and c.name != g.name
    assert (c.width, c.height) == (8, 6)
    assert read(c) == read(g)
    c.set(1, 1, 255, 0, 0)
    g.set(2, 2, 0, 255, 0)
    assert rgba(g.get(1, 1)) == (10, 20, 30, 255)
    assert rgba(c.get(2, 2)) == (10, 20, 30, 255)
    assert rgba(c.get(1, 1)) == (255, 0, 0, 255)


def test_copy_carries_the_drawing_history_and_pixels_only_pictures():
    script()
    g = p.create_graphics(8, 6)
    g.background("white")
    g.circle(4, 3, 4)
    g.load_pixels()                         # flushes; history is still a list
    c = g.copy()
    assert c._history == g._history and c._history is not g._history
    g.set(0, 0, 1, 2, 3)
    g.copy()._snapshot()
    assert g._history is None               # a pixel write dropped it (P7) ...
    assert g.copy()._history is None        # ... and the copy has none either


def test_copy_of_a_filtered_picture_and_filtering_a_copy_leaves_the_original():
    script()
    g = make(2, 1, [(200, 100, 50), (0, 0, 0)])
    c = g.copy()
    c.filter("invert")
    assert read(g)[0] == (200, 100, 50, 255)
    assert read(c)[0] == (55, 155, 205, 255)


# ---- P9: resize ---------------------------------------------------------------------------------
def test_resize_sets_the_size_in_place():
    script()
    g = p.create_graphics(20, 10)
    g.background("red")
    assert g.resize(40, 30) is None
    assert (g.width, g.height) == (40, 30)
    assert rgba(g.get(39, 29)) == (255, 0, 0, 255)
    assert g.get(40, 0).alpha == 0          # outside the new size


def test_resize_with_a_zero_keeps_the_aspect_ratio():
    script()
    g = p.create_graphics(20, 10)
    g.resize(40, 0)
    assert (g.width, g.height) == (40, 20)
    g.resize(0, 5)
    assert (g.width, g.height) == (10, 5)
    h = p.create_graphics(30, 10)
    h.resize(10, 0)                         # 3.33 rounds to 3
    assert (h.width, h.height) == (10, 3)


@pytest.mark.parametrize("w, h", [(0, 0), (-1, 5), (5, -1), (-3, 0), (0, -3)])
def test_resize_errors(w, h):
    script()
    g = p.create_graphics(20, 10)
    with pytest.raises(ValueError):
        g.resize(w, h)
    assert (g.width, g.height) == (20, 10)


def test_resize_scales_smoothly():
    script()
    g = make(2, 1, [(0, 0, 0), (255, 255, 255)])
    g.resize(8, 4)
    greys = [g.get(x, 1).red for x in range(8)]
    assert greys == sorted(greys) and len(set(greys)) == 8     # a ramp, step by step
    assert 0 < greys[3] < 255 and 0 < greys[4] < 255


def test_resize_drops_the_history_and_the_picture_can_be_drawn_on_after():
    script()
    g = p.create_graphics(10, 10)
    g.background("white")
    g.circle(5, 5, 6)
    g.load_pixels()
    assert g._history is not None
    g.resize(20, 20)
    assert g._history is None
    g.fill("blue")
    g.no_stroke()
    g.rect(0, 0, 4, 4)
    assert rgba(g.get(1, 1)) == (0, 0, 255, 255)


def test_resize_does_not_touch_the_canvas():
    s = script()
    p.background(5, 6, 7)
    g = p.create_graphics(10, 10)
    g.resize(30, 30)
    assert rgba(p.get(3, 3)) == (5, 6, 7, 255)
    assert (s.width, s.height) == (20, 10)


def test_resize_on_a_hidpi_picture_keeps_the_logical_size():
    script()
    g = Picture(10, 10, 2.0, "graphics-900")
    g.background("red")
    g.resize(20, 0)
    assert (g.width, g.height) == (20, 20)
    snap = g._snapshot()
    assert (snap.phys_width, snap.phys_height) == (40, 40)
    assert rgba(g.get(19, 19)) == (255, 0, 0, 255)


# ---- P9: mask -----------------------------------------------------------------------------------
def test_mask_multiplies_alpha_by_the_masks_alpha():
    script()
    g = make(2, 1, [(255, 0, 0), (0, 0, 255)])
    m = make(2, 1, [(0, 0, 0, 255), (0, 0, 0, 0)])
    assert g.mask(m) is None
    assert read(g) == [(255, 0, 0, 255), (0, 0, 0, 0)]
    half = make(1, 1, [(0, 255, 0, 200)])
    half.mask(make(1, 1, [(1, 1, 1, 128)]))
    assert half.get(0, 0).alpha == round(200 * 128 / 255)
    assert half.get(0, 0).green == 255                       # the colour itself is kept


def test_mask_scales_a_mask_of_another_size():
    script()
    g = make(4, 2, [(9, 9, 9)] * 8)
    m = make(2, 1, [(0, 0, 0, 255), (0, 0, 0, 0)])           # left half opaque
    g.mask(m)
    top = [g.get(x, 0).alpha for x in range(4)]
    assert top[0] == 255 and top == sorted(top, reverse=True) and top[-1] < 128    # the mask was stretched (smoothly)
    assert [g.get(x, 1).alpha for x in range(4)] == top


def test_mask_drops_the_history_and_leaves_the_mask_and_canvas_alone():
    script()
    p.background(1, 2, 3)
    g = p.create_graphics(6, 6)
    g.background("white")
    g.load_pixels()
    m = p.create_graphics(6, 6)
    m.background(0, 0, 0, 255)
    before = read(m)
    g.mask(m)
    assert g._history is None
    assert read(m) == before
    assert rgba(p.get(0, 0)) == (1, 2, 3, 255)


def test_mask_needs_a_picture():
    script()
    g = p.create_graphics(4, 4)
    with pytest.raises(TypeError):
        g.mask("not a picture")


# ---- P10: formulas ------------------------------------------------------------------------------
def test_threshold_uses_luminance():
    red, green, blue, white, black = (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255), (0, 0, 0)
    px = [red, green, blue, white, black]
    # luminance: red 76, green 150, blue 29 (of 255)
    assert [c[0] for c in apply("threshold", None, px)] == [0, 255, 0, 255, 0]       # default 0.5
    assert [c[0] for c in apply("threshold", 0.29, px)] == [255, 255, 0, 255, 0]
    assert [c[0] for c in apply("threshold", 0.1, px)] == [255, 255, 255, 255, 0]
    assert [c[0] for c in apply("threshold", 0.6, px)] == [0, 0, 0, 255, 0]
    assert [c[0] for c in apply("threshold", 1, px)] == [0, 0, 0, 0, 0]
    out = apply("threshold", 0.5, [(200, 200, 200, 90)])[0]
    assert out == (255, 255, 255, 90)                                                # alpha kept


def test_gray_is_the_luminance_and_keeps_alpha():
    rng = random.Random(3)
    px = [(rng.randrange(256), rng.randrange(256), rng.randrange(256)) for _ in range(300)]
    for (r, g, b), (r2, g2, b2, a) in zip(px, apply("gray", None, px)):
        expected = math.floor(0.299 * r + 0.587 * g + 0.114 * b + 0.5)
        assert abs(r2 - (299 * r + 587 * g + 114 * b) / 1000) <= 0.5 + 1e-9
        assert r2 == g2 == b2 == expected and a == 255
    assert apply("gray", None, [(100, 150, 200, 77)])[0][3] == 77


def test_opaque_sets_alpha_to_255_and_keeps_colour():
    out = apply("opaque", None, [(10, 20, 30, 0), (40, 50, 60, 128), (70, 80, 90, 255)])
    assert out == [(0, 0, 0, 255), (40, 50, 60, 255), (70, 80, 90, 255)]


def test_invert_flips_colour_and_keeps_alpha():
    assert apply("invert", None, [(0, 100, 255, 255)]) == [(255, 155, 0, 255)]
    assert apply("invert", None, [(0, 100, 255, 0)])[0][3] == 0
    px = apply("invert", None, [(10, 20, 30, 128)])[0]
    assert px[3] == 128 and abs(px[0] - 245) <= 1


@pytest.mark.parametrize("levels", [2, 3, 4, 8, 255])
def test_posterize_formula(levels):
    px = [(v, v, v) for v in range(256)]
    for v, (r, g, b, a) in enumerate(apply("posterize", levels, px, width=16)):
        q = math.floor(v * (levels - 1) / 255 + 0.5)
        want = math.floor(q * 255 / (levels - 1) + 0.5)
        assert r == g == b == want and a == 255
    assert apply("posterize", 2, [(100, 200, 130, 90)])[0] == (0, 255, 255, 90)


def test_posterize_needs_a_value():
    with pytest.raises(ValueError):
        apply("posterize", None, [(1, 2, 3)])


def _grid(width, height, base, pos, bright):
    pixels = [base] * (width * height)
    pixels[pos[1] * width + pos[0]] = bright
    return pixels


@pytest.mark.parametrize("pos", [(1, 1), (0, 0), (2, 2), (0, 2)])
def test_dilate_and_erode_on_a_small_picture(pos):
    black, white = (0, 0, 0), (255, 255, 255)
    grid = _grid(3, 3, black, pos, white)
    dilated = apply("dilate", None, grid, width=3)
    for y in range(3):
        for x in range(3):
            near = abs(x - pos[0]) <= 1 and abs(y - pos[1]) <= 1
            assert dilated[y * 3 + x][:3] == (white if near else black)
    inverse = _grid(3, 3, white, pos, black)
    eroded = apply("erode", None, inverse, width=3)
    for y in range(3):
        for x in range(3):
            near = abs(x - pos[0]) <= 1 and abs(y - pos[1]) <= 1
            assert eroded[y * 3 + x][:3] == (black if near else white)


def test_erode_edges_repeat_the_border_pixel():
    # A 3x1 strip: with the border repeated, the left pixel's neighbourhood is (a, a, b), not (0, a, b).
    # (a zero border would make the left green 0, not 100)
    out = apply("erode", None, [(200, 100, 50), (150, 120, 60), (180, 90, 70)], width=3)
    assert [c[:3] for c in out] == [(150, 100, 50), (150, 90, 50), (150, 90, 60)]
    out = apply("dilate", None, [(200, 100, 50), (150, 120, 60), (180, 90, 70)], width=3)
    assert [c[:3] for c in out] == [(200, 120, 60), (200, 120, 70), (180, 120, 70)]


def test_erode_and_dilate_work_per_channel_and_keep_alpha():
    out = apply("dilate", None, [(255, 0, 0, 40), (0, 0, 0, 200), (0, 0, 255, 99)], width=3)
    assert [c[3] for c in out] == [40, 200, 99]
    assert out[1][:3] == (255, 0, 255)


# ---- P10: blur ----------------------------------------------------------------------------------
def _dot_picture(scale, size=21):
    g = Picture(size, size, scale, "graphics-901")
    g.background("white")
    g.no_stroke()
    g.fill("black")
    g.rect(size // 2, size // 2, 1, 1)
    return g


@pytest.mark.parametrize("scale", [1.0, 2.0])
def test_blur_spreads_a_dot_by_the_radius_in_logical_pixels(scale):
    script()
    g = _dot_picture(scale)
    centre = 10
    g.filter("blur", 3)
    row = [g.get(x, centre).red for x in range(21)]
    assert row[centre] > 0 and row[centre] < 255             # the dot has spread out
    assert row[centre] == min(row)                           # darkest in the middle
    assert row[centre - 3] < 255 and row[centre + 3] < 255   # it reaches 3 logical pixels out ...
    assert row[0] == 255 and row[20] == 255                  # ... and no further than the radius allows


def test_blur_at_scale_1_and_2_looks_the_same():
    script()
    a, b = _dot_picture(1.0), _dot_picture(2.0)
    a.filter("blur", 2)
    b.filter("blur", 2)
    assert read(a) == read(b)


def test_blur_radius_zero_changes_nothing_and_default_is_one():
    script()
    g = _dot_picture(1.0)
    before = read(g)
    g.filter("blur", 0)
    assert read(g) == before
    g.filter("blur")
    assert read(g) != before
    h = _dot_picture(1.0)
    h.filter("blur", 1)
    assert read(g) == read(h)


def test_blur_keeps_opaque_pixels_opaque_and_does_not_darken_edges():
    script()
    g = p.create_graphics(10, 10)
    g.background("red")
    g.filter("blur", 3)
    assert {(c.red, c.alpha) for c in (g.get(x, y) for x in (0, 5, 9) for y in (0, 5, 9))} <= {(255, 255), (255, 254)}


# ---- P10: errors, raster ------------------------------------------------------------------------
@pytest.mark.parametrize("kind, value", [
    ("sepia", None), ("", None), (3, None), ("THRESHOLD", None),
    ("threshold", -0.1), ("threshold", 1.5),
    ("blur", -1),
    ("posterize", 1), ("posterize", 256), ("posterize", 2.5), ("posterize", 0),
])
def test_unknown_kind_or_value_out_of_range(kind, value):
    script()
    g = p.create_graphics(4, 4)
    with pytest.raises(ValueError):
        g.filter(kind, value)
    with pytest.raises(ValueError):
        p.filter(kind, value)


def test_unknown_kind_lists_the_choices():
    script()
    with pytest.raises(ValueError, match="threshold.*gray.*opaque.*invert.*blur.*posterize.*erode.*dilate"):
        p.filter("sepia")


def test_a_value_that_is_not_a_number_is_a_type_error():
    script()
    with pytest.raises(TypeError):
        p.filter("blur", "big")
    with pytest.raises(TypeError):
        p.filter("posterize", True)


def test_a_bad_filter_changes_nothing():
    script()
    p.background(10, 20, 30)
    with pytest.raises(ValueError):
        p.filter("posterize")
    assert rgba(p.get(0, 0)) == (10, 20, 30, 255)


def test_filter_on_the_canvas_applies_to_what_was_drawn_this_frame():
    seen = []

    def draw():
        p.background(255, 0, 0)
        p.no_stroke()
        p.fill(0, 0, 255)
        p.rect(0, 0, 20, 30)
        p.filter("invert")
        p.fill(0, 255, 0)                    # drawn after the filter: not inverted
        p.rect(30, 0, 10, 30)
        seen.append(rgba(p.get(5, 5)))

    s = run_draw(draw)
    assert seen == [(255, 255, 0, 255)]
    assert final_px(s, 5, 5) == (255, 255, 0)      # blue inverted
    assert final_px(s, 25, 5) == (0, 255, 255)     # red inverted
    assert final_px(s, 35, 5) == (0, 255, 0)


def test_filter_is_a_pixels_op_in_the_ir_and_drops_a_pictures_history():
    s = script(8, 8)
    p.background("white")
    p.filter("gray")
    kinds = [type(op) for op in s.frame.ops]
    assert kinds.count(ir.Pixels) == 1
    g = p.create_graphics(6, 6)
    g.background("white")
    g.load_pixels()
    assert g._history is not None
    g.filter("invert")
    g._snapshot()
    assert g._history is None
    assert rgba(g.get(0, 0)) == (0, 0, 0, 255)


def test_filter_is_a_public_name_and_a_picture_method():
    assert "filter" in p.__all__
    from funground.picture import ALLOWED_METHODS
    assert "filter" in ALLOWED_METHODS
    assert all(hasattr(Picture, m) for m in ("copy", "resize", "mask"))


# ---- P10: Pillow and plain Python give the same bytes -----------------------------------------
def _random_bgra(width, height, seed):
    rng = random.Random(seed)
    flat = bytearray()
    for _ in range(width * height):
        flat += bytes((rng.randrange(256), rng.randrange(256), rng.randrange(256), rng.choice((255, 255, 255, 0, rng.randrange(256)))))
    return imaging.rgba_to_bgra(bytes(flat), width, height)


@pytest.mark.parametrize("kind, value", [("posterize", 2), ("posterize", 3), ("posterize", 5), ("posterize", 64),
                                          ("erode", None), ("dilate", None)])
def test_pillow_and_plain_python_give_identical_bytes(monkeypatch, kind, value):
    pytest.importorskip("PIL")
    for width, height in ((37, 23), (1, 9), (9, 1), (2, 2)):
        bgra = _random_bgra(width, height, seed=width * 100 + height)
        with_pillow = imaging.filter_bgra(bgra, width, height, kind, value)
        monkeypatch.setattr(imaging, "_pillow", lambda: None)
        plain = imaging.filter_bgra(bgra, width, height, kind, value)
        monkeypatch.undo()
        assert plain == with_pillow, (kind, value, width, height)


def test_plain_python_erode_matches_a_brute_force_reference(monkeypatch):
    monkeypatch.setattr(imaging, "_pillow", lambda: None)
    width, height = 11, 7
    rng = random.Random(5)
    flat = bytes(rng.randrange(256) if i % 4 != 3 else 255 for i in range(width * height * 4))
    for kind, pick in (("erode", min), ("dilate", max)):
        out = bytes(imaging.bgra_to_rgba(imaging.filter_bgra(imaging.rgba_to_bgra(flat, width, height),
                                                              width, height, kind), width, height))
        for y in range(height):
            for x in range(width):
                for c in range(3):
                    want = pick(flat[(min(max(y + dy, 0), height - 1) * width + min(max(x + dx, 0), width - 1)) * 4 + c]
                                for dy in (-1, 0, 1) for dx in (-1, 0, 1))
                    assert out[(y * width + x) * 4 + c] == want


def test_the_plain_path_runs_without_pillow(monkeypatch):
    monkeypatch.setattr(imaging, "_pillow", lambda: None)
    assert apply("posterize", 2, [(100, 200, 130)])[0] == (0, 255, 255, 255)
    assert apply("dilate", None, [(0, 0, 0), (255, 255, 255)])[0] == (255, 255, 255, 255)


# ---- P3: pictures under no_smooth ---------------------------------------------------------------
def _strip_draw(smooth_on):
    def draw():
        p.background("white")
        g = p.create_graphics(2, 1)
        g.set(0, 0, 255, 0, 0)
        g.set(1, 0, 0, 0, 255)
        if not smooth_on:
            p.no_smooth()
        p.image(g, 0, 0, 40, 20)
        p.smooth()
    return draw


def test_no_smooth_scales_pictures_with_the_nearest_pixel():
    s = run_draw(_strip_draw(False))
    row = [final_px(s, x, 10) for x in range(40)]
    assert set(row) == {(255, 0, 0), (0, 0, 255)}            # crisp: no mixed colours at all
    assert row[19] == (255, 0, 0) and row[20] == (0, 0, 255)


def test_smooth_scaling_still_blends_pictures():
    s = run_draw(_strip_draw(True))
    row = [final_px(s, x, 10) for x in range(40)]
    assert set(row) - {(255, 0, 0), (0, 0, 255)}             # some in-between colours
