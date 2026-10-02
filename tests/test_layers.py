"""Layers (S-095, contract F16, D-053): `with f.layer(name):` draws on a named picture over the canvas.

The picture part: redirection, stacking, persistence, hide and show, errors, pages, size(), and the
composite in PNG, get() and last_frame. PDF and SVG draw each layer as a picture is drawn (vector).
"""
from __future__ import annotations

import re
import zlib

import pygame
import pytest

import funground as f
from funground import api, ir
from funground.picture import ALLOWED_METHODS, Picture
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def script(w=40, h=30) -> Sketch:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.size(w, h)
    return s


def rgb(c):
    return (c.r, c.g, c.b, c.a)


def px(path, x, y):
    return tuple(pygame.image.load(str(path)).get_at((x, y)))


def last_pixel(s, x, y):
    (w, _), data = s.last_frame
    i = (y * w + x) * 3
    return tuple(data[i:i + 3])


# ---------------------------------------------------------------- redirection
def test_drawing_goes_to_the_layer_not_the_canvas():
    script()
    f.background(255, 255, 255)
    with f.layer("dots"):
        f.no_stroke()
        f.fill(255, 0, 0)
        f.rect(0, 0, 10, 10)
    frame_ops = api.active_sketch().frame.ops
    assert not any(isinstance(op, ir.Rect) for op in frame_ops)       # the canvas recorded no rect
    assert rgb(f.get(5, 5)) == (255, 0, 0, 255)                        # but the layer is over it
    assert rgb(f.get(20, 20)) == (255, 255, 255, 255)


def test_style_set_inside_the_layer_stays_inside():
    script()
    f.fill(0, 0, 255)
    with f.layer("a"):
        f.fill(255, 0, 0)
    assert api.active_sketch().style.fill.rgba == (0, 0, 255, 255)


def test_every_picture_drawing_method_and_image_are_redirected():
    """Drawing functions in api.py talk to active_sketch() (the open layer's); nothing else does."""
    import inspect

    for name in ALLOWED_METHODS | {"image"}:
        fn = getattr(api, name, None)
        if callable(fn):
            source = inspect.getsource(fn)
            assert "active_sketch()" in source and "canvas_sketch()" not in source, name
    for name in ("size", "save", "random", "noise", "millis", "new_page", "create_graphics", "layer"):
        assert "canvas_sketch()" in inspect.getsource(getattr(api, name)), name


def test_image_inside_a_layer_draws_onto_the_layer():
    script()
    g = f.create_graphics(10, 10)
    g.background(0, 255, 0)
    with f.layer("pics"):
        f.image(g, 0, 0)
    assert not any(isinstance(op, ir.Image) for op in api.active_sketch().frame.ops)
    assert rgb(f.get(5, 5)) == (0, 255, 0, 255)


def test_queries_keep_their_canvas_meaning():
    s = script(40, 30)
    s.mouse_x, s.mouse_y = 7, 9
    s.frame_count = 12
    with f.layer("q"):
        assert f.width == 40 and f.height == 30
        assert f.mouse_x == 7 and f.mouse_y == 9
        assert f.frame_count == 12
        f.random_seed(5)
        a = f.random(10)
    f.random_seed(5)
    assert f.random(10) == a                 # the canvas's own random generator
    assert api._active is s


def test_load_pixels_inside_a_layer_reads_the_layer():
    script(4, 4)
    f.background(255, 255, 255)
    with f.layer("p"):
        f.background(10, 20, 30)
        f.load_pixels()
        assert list(f.pixels[:4]) == [10, 20, 30, 255]


# ---------------------------------------------------------------- return value
def test_layer_returns_its_picture_and_the_with_value():
    script()
    g = f.layer("sky")
    assert isinstance(g, Picture)
    with f.layer("sky") as inner:
        assert inner is g
    assert f.layer("sky") is g
    assert (g.width, g.height) == (40, 30)


def test_returned_picture_works_with_get_filters_and_save(tmp_path):
    script()
    with f.layer("sky") as sky:
        f.background(200, 100, 50)
    assert rgb(sky.get(3, 3)) == (200, 100, 50, 255)
    sky.filter("invert")
    assert rgb(sky.get(3, 3)) == (55, 155, 205, 255)
    sky.save(str(tmp_path / "sky.png"))
    assert px(tmp_path / "sky.png", 3, 3)[:3] == (55, 155, 205)
    sky.circle(20, 15, 10)                       # drawing straight on the picture works too
    assert isinstance(sky.get(0, 0, 5, 5), Picture)


def test_a_plain_picture_is_not_a_context_manager():
    script()
    g = f.create_graphics(5, 5)
    with pytest.raises(TypeError):
        with g:
            pass


# ---------------------------------------------------------------- stacking
def test_layers_stack_in_first_use_order():
    script()
    with f.layer("first"):
        f.background(255, 0, 0)
    with f.layer("second"):
        f.background(0, 0, 255)
    assert rgb(f.get(1, 1)) == (0, 0, 255, 255)           # the later layer is on top
    with f.layer("first"):                                 # using the first again does not move it
        f.circle(20, 15, 5)
    assert rgb(f.get(1, 1)) == (0, 0, 255, 255)


def test_layers_are_over_the_canvas_even_when_the_canvas_draws_later():
    script()
    with f.layer("top"):
        f.no_stroke()
        f.fill(255, 0, 0)
        f.rect(0, 0, 20, 30)
    f.no_stroke()
    f.fill(0, 255, 0)
    f.rect(0, 0, 40, 30)                                   # drawn after the layer, still underneath
    assert rgb(f.get(5, 5)) == (255, 0, 0, 255)
    assert rgb(f.get(30, 5)) == (0, 255, 0, 255)


def test_layer_ops_are_tagged_for_files():
    s = script()
    with f.layer("a"):
        f.background(1, 2, 3)
    with f.layer("b"):
        f.circle(5, 5, 5)
    ops = s._layer_ops()
    assert [op.layer for op in ops] == ["a", "b"]
    assert all(isinstance(op, ir.Image) for op in ops)
    assert not any(getattr(op, "layer", None) for op in s.frame.ops)    # the canvas frame is untouched


# ---------------------------------------------------------------- persistence
def test_a_layer_keeps_its_pixels_across_frames():
    s = Sketch(platform=HeadlessPlatform())
    api.use_sketch(s)

    def setup():
        f.size(60, 20)

    def draw():
        f.background(255, 255, 255)                        # the canvas is redrawn every frame
        with f.layer("trail"):
            f.no_stroke()
            f.fill(255, 0, 0)
            f.rect(f.frame_count * 10, 5, 5, 5)           # one square a frame
        f.fill(0, 0, 255)

    s.run_namespace({"setup": setup, "draw": draw}, max_frames=4)
    for n in range(4):
        assert last_pixel(s, n * 10 + 2, 7) == (255, 0, 0), n
    assert last_pixel(s, 50, 7) == (255, 255, 255)


def test_background_and_clear_inside_a_layer_reset_it():
    script()
    with f.layer("x"):
        f.fill(255, 0, 0)
        f.circle(20, 15, 20)
    assert rgb(f.get(20, 15)) == (255, 0, 0, 255)
    with f.layer("x"):
        f.clear()
    assert rgb(f.get(20, 15))[3] == 0
    with f.layer("x"):
        f.fill(255, 0, 0)
        f.circle(20, 15, 20)
        f.background(0, 255, 0)
    assert rgb(f.get(20, 15)) == (0, 255, 0, 255)


def test_the_canvas_drawing_is_unaffected_by_a_layer_clear():
    script()
    f.background(9, 9, 9)
    with f.layer("x"):
        f.clear()
    assert rgb(f.get(1, 1)) == (9, 9, 9, 255)


# ---------------------------------------------------------------- hide and show
def test_hide_and_show():
    script()
    f.background(255, 255, 255)
    with f.layer("red"):
        f.background(255, 0, 0)
    assert rgb(f.get(1, 1)) == (255, 0, 0, 255)
    f.hide_layer("red")
    assert rgb(f.get(1, 1)) == (255, 255, 255, 255)
    with f.layer("red"):                                    # a hidden layer can still be drawn on
        f.circle(20, 15, 4)
    f.show_layer("red")
    assert rgb(f.get(1, 1)) == (255, 0, 0, 255)


def test_unknown_layer_names_are_value_errors():
    script()
    f.layer("real")
    with pytest.raises(ValueError, match="nope"):
        f.hide_layer("nope")
    with pytest.raises(ValueError, match="nope"):
        f.show_layer("nope")


def test_bad_names():
    script()
    with pytest.raises(TypeError):
        f.layer(3)
    with pytest.raises(ValueError):
        f.layer("")


# ---------------------------------------------------------------- errors
def test_nested_layers_are_a_runtime_error():
    s = script()
    with f.layer("outer"):
        with pytest.raises(RuntimeError, match="nest"):
            f.layer("inner")
        with pytest.raises(RuntimeError, match="nest"):
            f.layer("outer")
    assert s._layer_open is None


def test_an_exception_in_the_block_restores_the_canvas():
    s = script()
    with pytest.raises(KeyError):
        with f.layer("boom"):
            f.circle(5, 5, 5)
            raise KeyError("x")
    assert s._layer_open is None
    f.rect(0, 0, 5, 5)
    assert any(isinstance(op, ir.Rect) for op in s.frame.ops)    # back on the canvas
    with f.layer("boom"):                                         # and layers still work
        pass


def test_a_layer_needs_a_window():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with pytest.raises(RuntimeError):
        f.layer("x")


# ---------------------------------------------------------------- pages and size()
def test_each_page_has_its_own_layers_and_keeps_its_look(tmp_path):
    s = script(20, 20)
    f.background(255, 255, 255)
    with f.layer("a"):
        f.background(255, 0, 0)
    f.new_page()
    assert s._layers == {}                                  # the new page has no layers
    f.background(255, 255, 255)
    with f.layer("a"):
        f.background(0, 0, 255)
    f.save(str(tmp_path / "doc.png"))
    assert px(tmp_path / "doc_1.png", 5, 5)[:3] == (255, 0, 0)
    assert px(tmp_path / "doc_2.png", 5, 5)[:3] == (0, 0, 255)


def test_size_drops_the_layers():
    s = script()
    old = f.layer("a")
    with old:
        f.background(255, 0, 0)
    f.size(50, 50)
    assert s._layers == {}
    new = f.layer("a")
    assert new is not old and (new.width, new.height) == (50, 50)
    with pytest.raises(RuntimeError, match="earlier canvas"):
        with old:
            pass


def test_layers_are_dropped_when_a_run_ends():
    s = Sketch(platform=HeadlessPlatform())
    api.use_sketch(s)

    def draw():
        with f.layer("x"):
            f.circle(5, 5, 5)

    s.run_namespace({"setup": lambda: f.size(20, 20), "draw": draw}, max_frames=2)
    assert s._layers == {}


# ---------------------------------------------------------------- PNG, get() and last_frame
def test_png_get_and_last_frame_include_layers(tmp_path):
    s = Sketch(platform=HeadlessPlatform())
    api.use_sketch(s)
    seen = {}

    def draw():
        f.background(255, 255, 255)
        with f.layer("a"):
            f.background(255, 0, 0)
        seen["get"] = rgb(f.get(1, 1))
        f.save(str(tmp_path / "frame.png"))

    s.run_namespace({"setup": lambda: f.size(20, 20), "draw": draw}, max_frames=1)
    assert seen["get"] == (255, 0, 0, 255)
    assert px(tmp_path / "frame.png", 1, 1)[:3] == (255, 0, 0)
    assert last_pixel(s, 1, 1) == (255, 0, 0)


def test_script_png_includes_layers(tmp_path):
    script(20, 20)
    f.background(255, 255, 255)
    with f.layer("a"):
        f.no_stroke()
        f.fill(0, 128, 0)
        f.rect(0, 0, 10, 10)
    f.save(str(tmp_path / "s.png"))
    assert px(tmp_path / "s.png", 2, 2)[:3] == (0, 128, 0)
    assert px(tmp_path / "s.png", 15, 15)[:3] == (255, 255, 255)
    f.save(str(tmp_path / "again.png"))                      # saving twice does not stack anything
    assert px(tmp_path / "again.png", 15, 15)[:3] == (255, 255, 255)


# ---------------------------------------------------------------- PDF and SVG: vector, not images
def pdf_text(path) -> bytes:
    data = path.read_bytes()
    parts = [data]
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        try:
            parts.append(zlib.decompressobj().decompress(m.group(1)))
        except zlib.error:
            pass
    return b"\n".join(parts)


def test_pdf_and_svg_show_the_layer_as_vectors(tmp_path):
    script(60, 40)
    f.background(255, 255, 255)
    with f.layer("shapes"):
        f.no_stroke()
        f.fill(255, 0, 0)
        f.circle(30, 20, 20)
    f.save(str(tmp_path / "a.pdf"))
    f.save(str(tmp_path / "a.svg"))
    pdf = pdf_text(tmp_path / "a.pdf")
    assert pdf.startswith(b"%PDF")
    assert b"/Subtype /Image" not in pdf and b"/Subtype/Image" not in pdf
    svg = (tmp_path / "a.svg").read_text()
    assert "<svg" in svg and "<image" not in svg
    assert re.search(r"<path[^>]*fill=\"rgb\(100%, 0%, 0%\)\"", svg) or "rgb(100%, 0%, 0%)" in svg


def test_a_hidden_layer_is_not_in_the_files(tmp_path):
    script(60, 40)
    with f.layer("shapes"):
        f.no_stroke()
        f.fill(255, 0, 0)
        f.circle(30, 20, 20)
    f.hide_layer("shapes")
    f.save(str(tmp_path / "h.svg"))
    assert "rgb(100%, 0%, 0%)" not in (tmp_path / "h.svg").read_text()


def test_animated_pdf_save_includes_layers(tmp_path):
    s = Sketch(platform=HeadlessPlatform())
    api.use_sketch(s)

    def draw():
        f.background(255, 255, 255)
        with f.layer("a"):
            f.no_stroke()
            f.fill(255, 0, 0)
            f.circle(10, 10, 8)
        f.save(str(tmp_path / "anim.svg"))

    s.run_namespace({"setup": lambda: f.size(20, 20), "draw": draw}, max_frames=1)
    assert "rgb(100%, 0%, 0%)" in (tmp_path / "anim.svg").read_text()


# ---------------------------------------------------------------- no layers: nothing changes
def test_a_sketch_without_layers_is_unchanged():
    s = script()
    f.background(255, 255, 255)
    f.circle(10, 10, 5)
    assert s._layers == {}
    assert s._view() is s._renderer
    assert s._with_layers(s.frame) is s.frame
    ops = s.frame.ops
    assert not any(isinstance(op, ir.Image) for op in ops)
    # the new Image field is left out of serialised ops when it is None
    image = ir.Image("graphics-1", 1, 0, 0, 1, 1)
    assert "layer" not in ir.op_to_jsonable(image)
    assert ir.op_from_jsonable(ir.op_to_jsonable(image)) == image
    tagged = ir.Image("graphics-1", 1, 0, 0, 1, 1, layer="sky")
    assert ir.op_to_jsonable(tagged)["layer"] == "sky"
    assert ir.op_from_jsonable(ir.op_to_jsonable(tagged)) == tagged


# ---------------------------------------------------------------- review fixes (Sprint 12)
def test_each_layer_block_starts_from_a_fresh_transform_and_leaves_no_state():
    """F16 pinned in review: a block is an implicit push()/reset_matrix() ... pop(), so a translate()
    in a layer every frame does not pile up, and a fill set inside does not leak into the next block."""
    script()
    f.background(255, 255, 255)
    for _ in range(3):
        with f.layer("a"):
            f.translate(10, 0)
            f.no_stroke()
            f.fill(255, 0, 0)
            f.rect(0, 0, 5, 5)
    assert rgb(f.get(12, 2)) == (255, 0, 0, 255)          # always drawn at x = 10..15
    assert rgb(f.get(22, 2)) == (255, 255, 255, 255)      # never moved on to 20 or 30


def test_push_background_pop_in_a_picture_still_saves_as_pdf(tmp_path):
    """Review fix: a reset inside an open push() no longer leaves an unmatched restore in the history."""
    script(30, 30)
    g = f.create_graphics(20, 20)
    g.push()
    g.translate(5, 5)
    g.background(255, 255, 255)
    g.fill(0, 0, 255)
    g.rect(0, 0, 5, 5)
    g.pop()
    g.save(str(tmp_path / "g.pdf"))                       # used to raise "restore() without matching save()"
    g.save(str(tmp_path / "g.svg"))
    assert (tmp_path / "g.pdf").stat().st_size > 0 and (tmp_path / "g.svg").stat().st_size > 0
