"""Pixel access (S-079, contract P7 and P8): get, set, load_pixels, pixels, update_pixels."""
from __future__ import annotations

import json
import time

import pytest

import funground as p
from funground import api, imaging, ir
from funground.capabilities import FungroundWarning
from funground.color import Color
from funground.picture import Picture
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def script(width=20, height=10) -> Sketch:
    """A script canvas (R14): a top-level size() with no window."""
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(width, height)
    return s


def run_draw(draw, size=(40, 30), frames=1) -> Sketch:
    """Run an animated sketch for *frames* frames; its last frame is in ``s.last_frame``."""
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(*size), "draw": draw}, max_frames=frames)
    return s


def final_px(s: Sketch, x: int, y: int) -> tuple[int, int, int]:
    (w, _h), rgb = s.last_frame
    i = (y * w + x) * 3
    return tuple(rgb[i:i + 3])


def rgba(c: Color) -> tuple[int, int, int, int]:
    return (c.red, c.green, c.blue, c.alpha)


# ---- P7: get ----------------------------------------------------------------------------------
def test_get_reads_this_frames_drawing_so_far():
    seen = []

    def draw():
        p.background(255, 0, 0)
        seen.append(rgba(p.get(5, 5)))
        p.no_stroke()
        p.fill(0, 0, 255)
        p.rect(0, 0, 10, 10)
        seen.append(rgba(p.get(5, 5)))
        p.fill(0, 255, 0)
        p.rect(0, 0, 10, 10)
        seen.append(rgba(p.get(5, 5)))

    run_draw(draw)
    assert seen == [(255, 0, 0, 255), (0, 0, 255, 255), (0, 255, 0, 255)]


def test_get_returns_a_colour_object():
    script()
    p.background("tomato")
    c = p.get(3, 3)
    assert isinstance(c, Color)
    assert (c.red, c.green, c.blue, c.alpha) == (255, 99, 71, 255)
    assert c.hue == pytest.approx(9.13, abs=0.1)
    p.fill(c)                                  # works wherever a colour does
    p.no_stroke()
    p.rect(0, 0, 2, 2)


def test_get_outside_the_canvas_is_transparent_black():
    script(10, 8)
    p.background("white")
    for x, y in [(-1, 0), (0, -1), (10, 0), (0, 8), (500, 500), (-100, -100)]:
        assert rgba(p.get(x, y)) == (0, 0, 0, 0), (x, y)


def test_coordinates_are_rounded_down():
    script(10, 10)
    p.set(2, 3, "red")
    assert rgba(p.get(2.9, 3.9)) == (255, 0, 0, 255)
    assert rgba(p.get(3.0, 3.0)) == (0, 0, 0, 0)
    assert rgba(p.get(-0.5, 3)) == (0, 0, 0, 0)          # rounds down to -1: outside
    p.set(5.9, 5.1, "blue")                              # writes pixel (5, 5)
    assert rgba(p.get(5, 5)) == (0, 0, 255, 255)


def test_get_region_returns_a_picture_of_that_region():
    script(20, 20)
    p.background("white")
    p.no_stroke()
    p.fill(255, 0, 0)
    p.rect(4, 4, 4, 4)
    g = p.get(2, 2, 8, 8)
    assert isinstance(g, Picture)
    assert (g.width, g.height) == (8, 8)
    assert rgba(g.get(0, 0)) == (255, 255, 255, 255)
    assert rgba(g.get(2, 2)) == (255, 0, 0, 255)         # canvas (4, 4)
    assert rgba(g.get(5, 5)) == (255, 0, 0, 255)
    assert rgba(g.get(6, 6)) == (255, 255, 255, 255)
    p.background("black")                                # the copy is independent of the canvas
    assert rgba(g.get(2, 2)) == (255, 0, 0, 255)


def test_get_region_partly_outside_is_transparent_there():
    script(10, 10)
    p.background("white")
    g = p.get(-2, -3, 6, 6)
    assert (g.width, g.height) == (6, 6)
    assert rgba(g.get(0, 0)) == (0, 0, 0, 0)
    assert rgba(g.get(1, 2)) == (0, 0, 0, 0)
    assert rgba(g.get(2, 3)) == (255, 255, 255, 255)
    assert rgba(g.get(5, 5)) == (255, 255, 255, 255)
    wholly_outside = p.get(100, 100, 3, 3)
    assert rgba(wholly_outside.get(1, 1)) == (0, 0, 0, 0)


def test_the_region_picture_can_be_drawn_and_drawn_on():
    script(20, 20)
    p.background("white")
    p.fill("navy")
    p.no_stroke()
    p.rect(0, 0, 5, 5)
    g = p.get(0, 0, 5, 5)
    p.image(g, 10, 10)
    assert rgba(p.get(12, 12)) == (0, 0, 128, 255)
    g.no_stroke()
    g.fill("red")
    g.rect(0, 0, 2, 2)
    assert rgba(g.get(1, 1)) == (255, 0, 0, 255)
    assert repr(g) == "<Picture 5 x 5>"


def test_get_argument_checks():
    script()
    with pytest.raises(ValueError):
        p.get(1, 1, 3)
    with pytest.raises(ValueError):
        p.get(1, 1, h=3)
    with pytest.raises(ValueError):
        p.get(1, 1, 0, 3)
    with pytest.raises(ValueError):
        p.get(1, 1, 3, -1)
    with pytest.raises(TypeError):
        p.get("1", 2)
    with pytest.raises(TypeError):
        p.get(True, 2)
    with pytest.raises(ValueError):
        p.get(float("nan"), 2)


def test_get_needs_a_window():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with pytest.raises(RuntimeError, match="f.size"):
        p.get(0, 0)
    with pytest.raises(RuntimeError, match="f.size"):
        p.set(0, 0, "red")


# ---- P7: set ----------------------------------------------------------------------------------
def test_set_makes_the_pixel_exactly_that_colour_whatever_the_state():
    script(20, 20)
    p.background("white")
    p.fill("red")
    p.stroke("blue")
    p.stroke_width(5)
    p.opacity(40)
    p.blend_mode("multiply")
    p.tint(10, 200, 10, 50)
    p.translate(7, 7)
    p.rotate(33)
    p.scale(3)
    p.clip(p.path().move_to(100, 100).line_to(105, 100).line_to(105, 105).close())               # a clip that excludes everything
    p.set(2, 3, (10, 20, 30))
    assert rgba(p.get(2, 3)) == (10, 20, 30, 255)       # not moved by the transform, not clipped, not faded
    p.set(4, 4, (200, 100, 50, 255))
    assert rgba(p.get(4, 4)) == (200, 100, 50, 255)


def test_set_replaces_what_was_there_including_alpha():
    script(10, 10)
    p.background("white")
    p.set(1, 1, (255, 0, 0, 255))
    p.set(1, 1, (0, 0, 255, 0))                         # fully transparent: replaces, does not blend
    assert rgba(p.get(1, 1)) == (0, 0, 0, 0)
    p.set(2, 2, (0, 0, 255, 128))
    c = p.get(2, 2)
    assert c.alpha == 128 and c.blue in (254, 255) and c.red == 0


@pytest.mark.parametrize("args, expected", [
    (("red",), (255, 0, 0, 255)),
    (("#336699",), (51, 102, 153, 255)),
    (("0x336699",), (51, 102, 153, 255)),
    (((10, 20, 30),), (10, 20, 30, 255)),
    (((10, 20, 30, 255),), (10, 20, 30, 255)),
    ((10, 20, 30), (10, 20, 30, 255)),
    ((128,), (128, 128, 128, 255)),
    ((200, 255), (200, 200, 200, 255)),
])
def test_set_takes_every_colour_form(args, expected):
    script(10, 10)
    p.set(1, 1, *args)
    assert rgba(p.get(1, 1)) == expected


def test_set_takes_a_colour_object():
    script(10, 10)
    p.set(1, 1, p.color(1, 2, 3))
    assert rgba(p.get(1, 1)) == (1, 2, 3, 255)


def test_set_reads_numbers_in_the_colour_mode():
    script(10, 10)
    p.color_mode("rgb", 1)
    p.set(1, 1, 1, 0, 0)
    p.set(2, 2, 0.5)
    assert rgba(p.get(1, 1)) == (255, 0, 0, 255)
    assert rgba(p.get(2, 2))[:3] in {(127, 127, 127), (128, 128, 128)}
    p.color_mode("hsb", 360, 100, 100, 1)
    p.set(3, 3, 0, 100, 100)
    assert rgba(p.get(3, 3)) == (255, 0, 0, 255)


def test_set_with_a_bad_colour_is_an_error_even_off_the_canvas():
    script(10, 10)
    with pytest.raises(ValueError):
        p.set(1, 1, "no-such-colour")
    with pytest.raises(ValueError):
        p.set(-5, -5, "no-such-colour")


def test_set_outside_the_canvas_does_nothing():
    s = script(10, 10)
    p.background("white")
    for x, y in [(-1, 0), (0, -1), (10, 0), (0, 10), (99, 99)]:
        p.set(x, y, "red")
    s._flush_pixel_patch()
    assert not any(isinstance(op, ir.Pixels) for op in s.frame.ops)
    assert rgba(p.get(0, 0)) == (255, 255, 255, 255)


def test_later_drawing_covers_a_set_pixel_and_a_later_set_covers_drawing():
    script(10, 10)
    p.background("white")
    p.set(5, 5, "red")
    p.no_stroke()
    p.fill("blue")
    p.circle(5, 5, 6)
    assert rgba(p.get(5, 5)) == (0, 0, 255, 255)
    p.set(5, 5, (0, 200, 0))
    assert rgba(p.get(5, 5)) == (0, 200, 0, 255)


def test_set_does_not_change_its_neighbours_in_a_patch():
    script(10, 10)
    p.background("white")
    p.no_stroke()
    p.fill(0, 0, 255, 100)                              # a soft colour the patch must leave alone
    p.rect(0, 0, 10, 10)
    before = [rgba(p.get(x, y)) for x in range(10) for y in range(10)]
    p.set(0, 0, "red")
    p.set(9, 9, "green")                                # far apart: one op covers the gap between them
    after = [rgba(p.get(x, y)) for x in range(10) for y in range(10)]
    changed = [i for i, (b, a) in enumerate(zip(before, after)) if b != a]
    assert changed == [0, 99]


# ---- HiDPI (scale 2) --------------------------------------------------------------------------
def test_hidpi_get_reads_the_top_left_physical_pixel(monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    seen = []

    def draw():
        p.background("white")
        p.no_stroke()
        p.fill(255, 0, 0)
        p.rect(0.5, 0, 10, 10)             # covers physical columns 1 to 20: not column 0
        seen.append(rgba(p.get(0, 0)))     # logical pixel 0 = physical columns 0 and 1: reads column 0
        seen.append(rgba(p.get(1, 0)))     # physical columns 2 and 3: red
        seen.append(rgba(p.get(10, 0)))    # physical columns 20 and 21: reads column 20, red
        seen.append(rgba(p.get(11, 0)))

    run_draw(draw, (30, 20))
    assert seen == [(255, 255, 255, 255), (255, 0, 0, 255), (255, 0, 0, 255), (255, 255, 255, 255)]


def test_hidpi_set_paints_the_whole_block(monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")

    def draw():
        p.background("white")
        p.set(3, 2, "blue")

    s = run_draw(draw, (10, 10))
    assert s.last_frame[0] == (20, 20)
    for px, py in [(6, 4), (7, 4), (6, 5), (7, 5)]:
        assert final_px(s, px, py) == (0, 0, 255)
    for px, py in [(5, 4), (8, 4), (6, 3), (6, 6), (0, 0)]:
        assert final_px(s, px, py) == (255, 255, 255)


def test_hidpi_set_is_not_blurred_by_a_neighbouring_gap(monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")

    def draw():
        p.background("white")
        p.no_stroke()
        p.fill(0, 0, 0)
        p.circle(5, 5, 7)                  # soft edges at physical resolution
        p.set(0, 0, "red")
        p.set(9, 9, "red")                 # one op; its gap must keep the soft edges exactly

    plain = run_draw(lambda: (p.background("white"), p.no_stroke(), p.fill(0, 0, 0), p.circle(5, 5, 7)), (10, 10))
    with_sets = run_draw(draw, (10, 10))
    (w, _), a = plain.last_frame
    _, b = with_sets.last_frame
    differing = {i // 3 for i in range(len(a)) if a[i] != b[i]}
    blocks = {(0, 0), (0, 1), (1, 0), (1, 1), (18, 18), (19, 18), (18, 19), (19, 19)}
    assert {(i % w, i // w) for i in differing} <= blocks


def test_hidpi_load_pixels_has_one_value_per_logical_pixel(monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    seen = {}

    def draw():
        p.background("white")
        p.no_stroke()
        p.fill(255, 0, 0)
        p.rect(0.5, 0, 4, 4)
        p.load_pixels()
        seen["len"] = len(p.pixels)
        seen["px"] = tuple(p.pixels[0:4])          # logical (0, 0): physical column 0, not covered
        seen["px1"] = tuple(p.pixels[4:8])         # logical (1, 0): physical column 2, covered

    run_draw(draw, (10, 6))
    assert seen["len"] == 10 * 6 * 4
    assert seen["px"] == (255, 255, 255, 255)
    assert seen["px1"] == (255, 0, 0, 255)


def test_hidpi_update_pixels_fills_blocks(monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")

    def draw():
        p.background("white")
        p.load_pixels()
        i = (2 * 10 + 3) * 4
        p.pixels[i:i + 4] = bytes((0, 255, 0, 255))
        p.update_pixels()

    s = run_draw(draw, (10, 10))
    for px, py in [(6, 4), (7, 4), (6, 5), (7, 5)]:
        assert final_px(s, px, py) == (0, 255, 0)
    assert final_px(s, 8, 4) == (255, 255, 255)


# ---- P8: the pixels buffer --------------------------------------------------------------------
def test_pixels_is_none_before_load_pixels():
    script()
    assert p.pixels is None
    p.load_pixels()
    assert p.pixels is not None


def test_update_pixels_before_load_pixels_is_an_error():
    script()
    with pytest.raises(RuntimeError, match="load_pixels"):
        p.update_pixels()


def test_buffer_layout_and_index_formula():
    script(5, 4)
    p.background(0, 0, 0)
    p.set(1, 0, (10, 20, 30))
    p.set(4, 3, (40, 50, 60, 255))
    p.set(2, 2, (70, 80, 90))
    p.load_pixels()
    pixels = p.pixels
    assert isinstance(pixels, bytearray)
    assert len(pixels) == 5 * 4 * 4
    for (x, y), want in {(1, 0): (10, 20, 30, 255), (4, 3): (40, 50, 60, 255), (2, 2): (70, 80, 90, 255),
                         (0, 0): (0, 0, 0, 255)}.items():
        i = (y * 5 + x) * 4
        assert tuple(pixels[i:i + 4]) == want


def test_pixels_hold_straight_not_premultiplied_colour():
    script(4, 1)
    p.set(0, 0, (200, 100, 50, 128))
    p.load_pixels()
    r, g, b, a = p.pixels[0:4]
    assert a == 128
    assert (r, g, b) == pytest.approx((200, 100, 50), abs=2)       # 8-bit premultiplied storage: close, not exact
    assert tuple(p.pixels[4:8]) == (0, 0, 0, 0)


def test_changing_pixels_changes_nothing_until_update_pixels():
    script(6, 6)
    p.background("white")
    p.load_pixels()
    p.pixels[0:4] = bytes((255, 0, 0, 255))
    assert rgba(p.get(0, 0)) == (255, 255, 255, 255)
    p.update_pixels()
    assert rgba(p.get(0, 0)) == (255, 0, 0, 255)


def test_load_pixels_sees_this_frames_drawing():
    seen = []

    def draw():
        p.background(10, 20, 30)
        p.load_pixels()
        seen.append(tuple(p.pixels[0:4]))

    run_draw(draw)
    assert seen == [(10, 20, 30, 255)]


def test_update_pixels_is_a_set_of_every_pixel():
    script(8, 8)
    p.background("white")
    p.fill("red")
    p.opacity(30)
    p.translate(3, 3)
    p.load_pixels()
    for i in range(0, len(p.pixels), 4):
        p.pixels[i:i + 4] = bytes((1, 2, 3, 255))
    p.update_pixels()
    assert all(rgba(p.get(x, y)) == (1, 2, 3, 255) for x in range(8) for y in range(8))


def test_update_pixels_writes_transparent_pixels_as_transparent():
    script(4, 4)
    p.background("white")
    p.load_pixels()
    p.pixels[0:4] = bytes((200, 100, 50, 0))               # colour with no alpha: just transparent
    p.update_pixels()
    assert rgba(p.get(0, 0)) == (0, 0, 0, 0)


def test_update_pixels_checks_the_buffer():
    script(4, 4)
    p.load_pixels()
    p.pixels.append(0)
    with pytest.raises(ValueError, match="values"):
        p.update_pixels()
    p.pixels.pop()                                          # back to the right size
    p.pixels[0:4] = bytes((255, 0, 0, 255))
    p.update_pixels()
    assert rgba(p.get(0, 0)) == (255, 0, 0, 255)
    api.active_sketch().pixels = [1, 2, 300] + [0] * 61     # not bytes
    with pytest.raises(ValueError):
        p.update_pixels()


def test_pixels_is_a_live_value():
    script()
    assert "pixels" in p.__all__
    assert "pixels" not in vars(p)
    p.load_pixels()
    first = p.pixels
    p.load_pixels()
    assert p.pixels is not first and len(p.pixels) == len(first)


def test_load_pixels_then_update_pixels_changes_nothing():
    """The round trip is exact, soft edges included (premultiplied Cairo values and back)."""
    s = script(60, 40)
    p.background(255, 255, 255, 0)
    p.no_stroke()
    p.fill(255, 0, 0, 100)
    p.circle(20, 20, 31.3)
    p.fill(0, 120, 255, 77)
    p.circle(33, 22, 25.7)
    p.stroke(10, 200, 90, 130)
    p.stroke_width(3.3)
    p.no_fill()
    p.line(2, 3, 57, 38)
    s._sync_canvas()
    before = bytes(s._renderer.pixels().data)
    p.load_pixels()
    p.update_pixels()
    s._sync_canvas()
    after = bytes(s._renderer.pixels().data)
    assert after == before
    assert any(0 < before[i] < 255 for i in range(3, len(before), 4))     # there really were soft edges


def test_every_premultiplied_value_survives_the_conversion():
    data = bytearray()
    for a in range(256):
        for c in range(a + 1):
            data += bytes((c, c, c, a))
    n = len(data) // 4
    rgba_bytes = imaging.bgra_to_rgba(bytes(data), n, 1)
    assert imaging.rgba_to_bgra(bytes(rgba_bytes), n, 1) == bytes(data)


def test_roundtrip_speed_of_a_full_canvas():
    s = script(640, 400)
    p.background("white")
    p.fill("tomato")
    p.circle(300, 200, 250)
    s._sync_canvas()
    started = time.perf_counter()
    p.load_pixels()
    p.update_pixels()
    p.get(0, 0)                                  # forces the write onto the canvas
    elapsed = time.perf_counter() - started
    # generous: CI machines are slower than a desk machine (about 0.01 s here); this only catches a
    # per-pixel Python loop sneaking into the whole-image path, which would take seconds
    assert elapsed < 2.0, f"load + update of 640 x 400 took {elapsed:.3f} s"


# ---- IR ---------------------------------------------------------------------------------------
def pixel_ops(s: Sketch) -> list[ir.Pixels]:
    return [op for op in s.frame.ops if isinstance(op, ir.Pixels)]


def test_many_sets_in_a_row_are_one_pixels_op():
    s = script(50, 50)
    for y in range(30):
        for x in range(30):
            p.set(x, y, (x * 8, y * 8, 0))
    s._flush_pixel_patch()
    ops = pixel_ops(s)
    assert len(ops) == 1
    op = ops[0]
    assert (op.x, op.y, op.width, op.height) == (0, 0, 30, 30)
    assert isinstance(op.checksum, int)


def test_a_set_run_is_split_by_other_ops_and_by_reads():
    s = script(20, 20)
    p.set(1, 1, "red")
    p.set(2, 2, "red")
    p.circle(10, 10, 4)
    p.set(3, 3, "red")
    p.get(0, 0)                                  # a read ends the run
    p.set(4, 4, "red")
    s._flush_pixel_patch()
    kinds = [type(op).__name__ for op in s.frame.ops]
    assert kinds == ["Pixels", "Circle", "Pixels", "Pixels"]
    first, _, second, third = s.frame.ops
    assert (first.x, first.y, first.width, first.height) == (1, 1, 2, 2)
    assert (second.x, second.width) == (3, 1) and (third.x, third.width) == (4, 1)


def test_the_pixels_op_serialises_without_bytes():
    s = script(20, 20)
    p.set(2, 3, (1, 2, 3))
    p.set(4, 6, (4, 5, 6))
    s._flush_pixel_patch()
    (op,) = pixel_ops(s)
    assert op.data is not None
    d = ir.op_to_jsonable(op)
    assert set(d) == {"op", "x", "y", "width", "height", "checksum"}
    assert (d["x"], d["y"], d["width"], d["height"]) == (2, 3, 3, 4)
    text = json.dumps(d)
    back = ir.op_from_jsonable(json.loads(text))
    assert back == op and back.data is None
    with pytest.raises(RuntimeError, match="no pixels"):
        s._renderer._draw_pixels(s._renderer._ctx, back)


def test_the_checksum_follows_the_pixels():
    def checksum_of(colour):
        s = script(10, 10)
        p.set(1, 1, colour)
        s._flush_pixel_patch()
        return pixel_ops(s)[0].checksum

    assert checksum_of("red") == checksum_of((255, 0, 0))
    assert checksum_of("red") != checksum_of("blue")


def test_update_pixels_is_one_op_over_the_whole_canvas():
    s = script(12, 7)
    p.load_pixels()
    p.update_pixels()
    (op,) = pixel_ops(s)
    assert (op.x, op.y, op.width, op.height) == (0, 0, 12, 7)
    assert "data" not in ir.op_to_jsonable(op)


def test_the_ops_of_an_animated_frame_include_pixels():
    def draw():
        p.background("white")
        p.set(1, 1, "red")
        p.set(2, 2, "red")

    s = run_draw(draw)
    assert [type(op).__name__ for op in s.last_ops] == ["Clear", "Pixels"]
    assert final_px(s, 1, 1) == (255, 0, 0)


# ---- PDF and SVG ------------------------------------------------------------------------------
@pytest.mark.parametrize("ext", ["pdf", "svg"])
def test_a_script_with_pixel_writes_saves_as_pdf_and_svg(tmp_path, ext):
    script(30, 20)
    p.background("white")
    p.fill("red")
    p.circle(15, 10, 10)
    for x in range(10):
        p.set(x, 1, (x * 20, 0, 255))
    out = tmp_path / f"frame.{ext}"
    p.save(str(out))
    data = out.read_bytes()
    assert len(data) > 200
    assert (b"/Subtype /Image" in data) if ext == "pdf" else (b"<image" in data)


def test_an_animated_frame_with_pixel_writes_saves_as_pdf(tmp_path):
    out = tmp_path / "frame.pdf"

    def draw():
        p.background("white")
        p.set(3, 3, "red")
        p.save(str(out))

    run_draw(draw)
    data = out.read_bytes()
    assert data.startswith(b"%PDF") and b"/Subtype /Image" in data


# ---- pictures ---------------------------------------------------------------------------------
def test_a_picture_has_get_set_and_pixels():
    script(30, 30)
    g = p.create_graphics(10, 8)
    assert g.pixels is None
    g.set(2, 3, "red")
    assert rgba(g.get(2, 3)) == (255, 0, 0, 255)
    assert rgba(g.get(0, 0)) == (0, 0, 0, 0)               # transparent to start
    assert rgba(g.get(50, 50)) == (0, 0, 0, 0)
    g.load_pixels()
    assert len(g.pixels) == 10 * 8 * 4
    i = (3 * 10 + 2) * 4
    assert tuple(g.pixels[i:i + 4]) == (255, 0, 0, 255)
    g.pixels[i:i + 4] = bytes((0, 255, 0, 255))
    g.update_pixels()
    assert rgba(g.get(2, 3)) == (0, 255, 0, 255)
    with pytest.raises(RuntimeError):
        p.create_graphics(3, 3).update_pixels()


def test_a_pictures_pixels_can_be_replaced_by_assignment():
    script(30, 30)
    g = p.create_graphics(2, 2)
    g.load_pixels()
    g.pixels = bytearray(bytes((255, 0, 0, 255)) * 4)
    g.update_pixels()
    assert rgba(g.get(1, 1)) == (255, 0, 0, 255)


def test_a_picture_reads_its_own_drawing_and_state_is_its_own():
    script(30, 30)
    g = p.create_graphics(10, 10)
    g.background("white")
    g.no_stroke()
    g.fill(255, 0, 0)
    g.rect(0, 0, 5, 5)
    assert rgba(g.get(2, 2)) == (255, 0, 0, 255)
    g.translate(5, 5)
    g.rect(0, 0, 3, 3)                                      # later drawing still uses the picture's transform
    assert rgba(g.get(6, 6)) == (255, 0, 0, 255)
    assert rgba(g.get(4, 6)) == (255, 255, 255, 255)


def test_a_picture_with_pixel_writes_loses_its_history():
    script(30, 30)
    g = p.create_graphics(10, 10)
    g.background("white")
    g.rect(0, 0, 3, 3)
    assert g._snapshot().history is not None
    g.set(5, 5, "red")
    assert g._snapshot().history is None
    g.circle(2, 2, 2)                                       # still none: nothing has started a new history
    assert g._snapshot().history is None
    g.background("white")                                   # an opaque background starts one again (P3)
    assert g._snapshot().history is not None
    assert rgba(g.get(5, 5)) == (255, 255, 255, 255)


def test_update_pixels_on_a_picture_drops_its_history_too():
    script(30, 30)
    g = p.create_graphics(10, 10)
    g.background("white")
    g.load_pixels()
    g.update_pixels()
    assert g._snapshot().history is None


def test_a_picture_with_pixel_writes_embeds_its_pixels_in_pdf(tmp_path):
    script(30, 30)
    g = p.create_graphics(10, 10)
    g.background("white")
    g.set(5, 5, "red")
    p.image(g, 5, 5)
    out = tmp_path / "x.pdf"
    p.save(str(out))
    assert b"/Subtype /Image" in out.read_bytes()
    single = tmp_path / "g.pdf"
    g.save(str(single))
    assert b"/Subtype /Image" in single.read_bytes()


def test_a_picture_with_pixel_writes_draws_on_the_canvas():
    script(30, 30)
    p.background("white")
    g = p.create_graphics(10, 10)
    g.set(1, 1, (0, 0, 255))
    p.image(g, 10, 10)
    assert rgba(p.get(11, 11)) == (0, 0, 255, 255)
    assert rgba(p.get(12, 12)) == (255, 255, 255, 255)      # the picture is transparent elsewhere


def test_a_picture_made_by_get_is_named_after_the_windows_count():
    script(30, 30)
    a = p.create_graphics(5, 5)
    b = p.get(0, 0, 4, 4)
    c = a.get(0, 0, 2, 2)
    names = {a.name, b.name, c.name}
    assert len(names) == 3 and names == {"graphics-1", "graphics-2", "graphics-3"}


def test_many_sets_on_a_picture_are_one_op():
    script(30, 30)
    g = p.create_graphics(20, 20)
    for y in range(20):
        for x in range(20):
            g.set(x, y, (x, y, 0))
    g._sketch._flush_pixel_patch()
    assert sum(isinstance(op, ir.Pixels) for op in g._sketch.frame.ops) == 1
    assert rgba(g.get(7, 9)) == (7, 9, 0, 255)


# ---- scripts ----------------------------------------------------------------------------------
def test_pixel_functions_work_in_a_script_and_in_a_saved_png(tmp_path):
    script(16, 16)
    p.background("white")
    p.set(4, 4, "red")
    assert rgba(p.get(4, 4)) == (255, 0, 0, 255)
    p.load_pixels()
    p.pixels[0:4] = bytes((0, 0, 255, 255))
    p.update_pixels()
    out = tmp_path / "s.png"
    p.save(str(out))                                          # a waiting write is flushed by the save
    p.set(8, 8, (0, 255, 0))
    p.save(str(tmp_path / "t.png"))
    import pygame
    img = pygame.image.load(str(out))
    assert tuple(img.get_at((0, 0)))[:3] == (0, 0, 255)
    assert tuple(img.get_at((4, 4)))[:3] == (255, 0, 0)
    assert tuple(pygame.image.load(str(tmp_path / "t.png")).get_at((8, 8)))[:3] == (0, 255, 0)


def test_a_new_script_canvas_forgets_pixels_and_waiting_writes():
    script(10, 10)
    p.set(1, 1, "red")
    p.load_pixels()
    p.size(12, 12)
    assert p.pixels is None
    assert rgba(p.get(1, 1)) == (0, 0, 0, 0)


# ---- end of the frame is not drawn twice ------------------------------------------------------
def final_frame(draw, size=(30, 20)):
    return run_draw(draw, size).last_frame[1]


def test_reading_mid_frame_does_not_draw_the_frame_twice():
    def scene():
        p.background(255, 255, 255)
        p.no_stroke()
        p.fill(255, 0, 0, 90)                       # translucent: drawing it twice would show
        p.circle(10, 10, 14)
        p.fill(0, 0, 255, 90)
        p.rect(5, 5, 14, 10)

    def reading():
        p.background(255, 255, 255)
        p.no_stroke()
        p.fill(255, 0, 0, 90)
        p.circle(10, 10, 14)
        p.get(10, 10)                               # a read in the middle of the frame
        p.fill(0, 0, 255, 90)
        p.rect(5, 5, 14, 10)

    assert final_frame(reading) == final_frame(scene)


def test_every_kind_of_read_leaves_the_final_frame_unchanged():
    def scene():
        p.background(240, 240, 200)
        p.no_stroke()
        p.fill(255, 0, 0, 90)
        p.circle(10, 10, 14)
        p.push()
        p.translate(5, 3)
        p.rotate(20)
        p.fill(0, 0, 255, 90)
        p.rect(2, 2, 12, 8)
        p.pop()
        p.stroke(0, 90)
        p.line(0, 0, 29, 19)

    def reading():
        p.background(240, 240, 200)
        p.no_stroke()
        p.fill(255, 0, 0, 90)
        p.circle(10, 10, 14)
        p.get(1, 1)
        p.push()
        p.get(1, 1, 5, 5)
        p.translate(5, 3)                           # a read inside an open push, state carried across it
        p.rotate(20)
        p.load_pixels()
        p.fill(0, 0, 255, 90)
        p.rect(2, 2, 12, 8)
        p.get(10, 10)
        p.pop()
        p.stroke(0, 90)
        p.line(0, 0, 29, 19)
        p.get(0, 0)

    assert final_frame(reading) == final_frame(scene)


def test_a_read_inside_an_open_push_and_a_clip_keeps_both_for_later_drawing():
    def scene():
        p.background(255, 255, 255)
        p.no_stroke()
        p.push()
        p.translate(10, 5)
        p.clip(p.path().move_to(0, 0).line_to(8, 0).line_to(8, 8).line_to(0, 8).close())
        p.fill(255, 0, 0)
        p.rect(-5, -5, 40, 40)
        p.pop()
        p.fill(0, 0, 255, 80)
        p.rect(0, 0, 4, 4)

    def reading():
        p.background(255, 255, 255)
        p.no_stroke()
        p.push()
        p.translate(10, 5)
        p.clip(p.path().move_to(0, 0).line_to(8, 0).line_to(8, 8).line_to(0, 8).close())
        p.get(12, 7)
        p.fill(255, 0, 0)
        p.rect(-5, -5, 40, 40)
        p.pop()
        p.get(12, 7)
        p.fill(0, 0, 255, 80)
        p.rect(0, 0, 4, 4)

    assert final_frame(reading) == final_frame(scene)


def test_a_read_after_an_unbalanced_push_still_unwinds_at_the_end_of_the_frame():
    def draw():
        p.background(255, 255, 255)
        p.push()
        p.translate(5, 5)
        p.get(0, 0)

    with pytest.warns(FungroundWarning, match="push"):
        s = run_draw(draw, frames=3)           # would raise if a Save leaked into the next frame
    assert s.last_frame is not None


def test_a_waiting_set_at_the_end_of_the_frame_is_drawn_once():
    def draw():
        p.background(255, 255, 255)
        p.no_stroke()
        p.fill(255, 0, 0, 90)
        p.circle(10, 10, 14)
        p.set(3, 3, (0, 0, 255, 128))

    def other():
        p.background(255, 255, 255)
        p.no_stroke()
        p.fill(255, 0, 0, 90)
        p.circle(10, 10, 14)
        p.get(0, 0)
        p.set(3, 3, (0, 0, 255, 128))

    assert final_frame(draw) == final_frame(other)


def test_reads_work_on_every_frame_of_a_running_sketch():
    values = []

    def draw():
        p.background(10 * (p.frame_count + 1), 0, 0)
        values.append(p.get(0, 0).red)

    run_draw(draw, frames=4)
    assert values == [10, 20, 30, 40]


def test_a_read_after_the_canvas_is_resized_sees_the_new_blank_canvas():
    seen = []

    def draw():
        if p.frame_count == 0:
            p.background(255, 0, 0)
        else:
            p.resize_canvas(10, 10)
            seen.append((p.width, rgba(p.get(2, 2))))
            p.background(0, 255, 0)
            seen.append((p.width, rgba(p.get(2, 2))))

    run_draw(draw, (20, 20), frames=2)
    assert seen == [(10, (0, 0, 0, 0)), (10, (0, 255, 0, 255))]
