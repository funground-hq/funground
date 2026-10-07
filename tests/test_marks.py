"""Marks: a drawing kept as a value (S-132, contract K1-K3, decisions D-069 and D-070).

K1 recording, style, isolation and errors; K2 placement, anchors, transform order, fitting, the current
style, group opacity and nesting; K3 files (vector PDF and SVG, text, pictures). The maintainer's three
demonstrations are the tests named test_demo_*.
"""
from __future__ import annotations

import copy
import dataclasses
import importlib
import re
import time
import warnings

import pytest
from pypdf import PdfReader

import funground as f
from funground import api, ir
from funground.capabilities import FungroundWarning
from funground.marks import Mark
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

RED = (255, 0, 0)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)


def script(w=200, h=200) -> Sketch:
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    f.size(w, h)
    f.background("white")
    return s


def rgb(x, y) -> tuple[int, int, int]:
    c = f.get(x, y)
    return (c.red, c.green, c.blue)


def close(a, b, tol=40) -> bool:
    return all(abs(p - q) <= tol for p, q in zip(a, b))


def red_box(w=20, h=10) -> Mark:
    """A red rectangle from (0, 0) to (w, h) in the mark's own coordinates, no stroke."""
    with f.mark() as m:
        f.no_stroke()
        f.fill("red")
        f.rect(0, 0, w, h)
    return m


def flower() -> Mark:
    with f.mark() as m:
        f.stroke("black")
        for a in range(0, 360, 60):
            with f.saved_state():
                f.rotate(a)
                f.fill("tomato")
                f.ellipse(0, -30, 18, 40)
        f.fill("gold")
        f.circle(0, 0, 24)
    return m


def canvas_ops() -> tuple:
    return api.canvas_sketch().frame.ops


def pdf_objects(path):
    """(XObject subtypes, content streams) over the whole PDF, nested forms included."""
    reader = PdfReader(str(path))
    subtypes, streams, groups = [], [], []
    seen = set()

    def walk(res):
        if res is None:
            return
        res = res.get_object()
        for ref in (res.get("/XObject") or {}).values():
            key = getattr(ref, "idnum", id(ref))
            if key in seen:
                continue
            seen.add(key)
            obj = ref.get_object()
            subtypes.append(obj.get("/Subtype"))
            if obj.get("/Group") is not None:
                groups.append(obj["/Group"].get("/S"))
            if obj.get("/Subtype") == "/Form":
                streams.append(obj.get_data())
            walk(obj.get("/Resources"))

    for page in reader.pages:
        streams.append(page.get_contents().get_data())
        walk(page.get("/Resources"))
    return subtypes, b"\n".join(streams), groups


# ================================================================= K1: recording
def test_a_block_records_and_draws_nothing():
    script()
    canvas_frame = api.canvas_sketch().frame
    before = canvas_ops()
    with f.mark() as m:
        f.fill("red")
        f.rect(0, 0, 50, 50)
        assert canvas_frame.ops == before              # nothing reaches the canvas while recording
    assert api.canvas_sketch().frame is canvas_frame
    assert canvas_ops() == before
    assert rgb(10, 10) == WHITE
    assert isinstance(m, Mark) and not m.is_empty
    assert [type(op) for op in m._ops] == [ir.Rect]


def test_recording_inherits_the_current_style_and_starts_untransformed():
    script()
    f.fill("blue")
    f.stroke_width(4)
    f.stroke_cap("square")
    f.text_size(30)
    f.blend_mode("multiply")
    f.color_mode("hsb")
    f.translate(50, 50)
    with f.mark() as m:
        f.circle(0, 0, 10)
    (op,) = m._ops                                    # no Concat: the block starts at the identity
    assert op.style.fill == f.color("blue") or op.style.fill.rgba[:3] == (0, 0, 255)
    assert (op.style.stroke_width, op.style.stroke_cap, op.style.text_size) == (4, "square", 30)
    assert (op.style.blend_mode, op.style.color_mode) == ("multiply", "hsb")


def test_the_surrounding_state_is_restored_exactly():
    s = script()
    f.fill("blue")
    f.push()
    f.translate(10, 10)
    f.clip(f.path().rect(0, 0, 100, 100))
    style, depth, ops = s.style, s._states.depth, canvas_ops()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with f.mark() as m:
            f.fill("red")
            f.stroke_width(7)
            f.translate(30, 0)
            f.rotate(45)
            f.clip(f.path().circle(0, 0, 10))
            f.no_smooth()
            f.push()                                   # left open: closed for the mark, with a warning
            f.circle(0, 0, 10)
    assert any(issubclass(w.category, FungroundWarning) and "f.mark()" in str(w.message) for w in caught)
    assert s.style is style and s._states.depth == depth and canvas_ops() == ops
    assert s._smooth is True
    saves = sum(isinstance(op, ir.Save) for op in m._ops)
    assert saves == sum(isinstance(op, ir.Restore) for op in m._ops)   # the mark is balanced
    f.pop()


def test_the_state_is_restored_after_an_error_and_the_mark_stays_unfinished():
    s = script()
    f.fill("blue")
    style, ops = s.style, canvas_ops()
    with pytest.raises(ZeroDivisionError):
        with f.mark() as m:
            f.fill("red")
            f.translate(5, 5)
            f.push()
            f.rect(0, 0, 10, 10)
            1 / 0
    assert s.style is style and s._states.depth == 0 and canvas_ops() == ops
    with pytest.raises(RuntimeError, match="unfinished"):
        m.place(10, 10)
    with pytest.raises(RuntimeError, match="unfinished"):
        m.bounds()
    f.rect(0, 0, 5, 5)                                 # drawing goes to the canvas again
    assert type(canvas_ops()[-1]) is ir.Rect


def test_placing_a_mark_inside_its_own_block_is_an_error():
    script()
    with f.mark() as m:
        f.rect(0, 0, 10, 10)
        with pytest.raises(RuntimeError, match="still being recorded"):
            m.place(10, 10)


def test_a_mark_that_was_never_recorded_cannot_be_placed_and_a_mark_is_recorded_once():
    script()
    m = f.mark()
    with pytest.raises(RuntimeError, match="never recorded"):
        m.place(0, 0)
    done = red_box()
    with pytest.raises(RuntimeError, match="recorded only once"):
        with done:
            pass


@pytest.mark.parametrize("call", [
    lambda tmp: f.layer("x"),
    lambda tmp: f.create_slider(0, 1),
    lambda tmp: f.create_checkbox("a"),
    lambda tmp: f.create_button("b"),
    lambda tmp: f.save(str(tmp / "a.png")),
    lambda tmp: f.save_frames(str(tmp / "####.png"), 2),
    lambda tmp: f.save_gif(str(tmp / "a.gif"), 1),
    lambda tmp: f.save_movie(str(tmp / "a.mp4"), 1),
    lambda tmp: f.show(),
    lambda tmp: f.new_page(),
    lambda tmp: f.get(0, 0),
    lambda tmp: f.set(0, 0, "red"),
    lambda tmp: f.load_pixels(),
    lambda tmp: f.update_pixels(),
    lambda tmp: f.filter("gray"),
    lambda tmp: f.background("white"),
    lambda tmp: f.clear(),
], ids=["layer", "slider", "checkbox", "button", "save", "save_frames", "save_gif", "save_movie", "show",
        "new_page", "get", "set", "load_pixels", "update_pixels", "filter", "background", "clear"])
def test_what_a_mark_block_refuses(call, tmp_path):
    s = script()
    ops = canvas_ops()
    with pytest.raises(RuntimeError, match=r"inside a `with f\.mark\(\)"):
        with f.mark():
            call(tmp_path)
    assert canvas_ops() == ops and s._layer_open is None and not s._layers
    assert not list(tmp_path.iterdir())


def test_direct_construction_from_a_path():
    script()
    f.stroke("blue")
    f.stroke_width(3)
    m = f.mark(f.path().rect(0, 0, 10, 10), fill="red")
    fill, stroke = m._ops
    assert type(fill) is ir.FillPath and fill.color.rgba[:3] == RED
    assert type(stroke) is ir.StrokePath and stroke.color.rgba[:3] == (0, 0, 255) and stroke.width == 3
    only = f.mark(f.path().rect(0, 0, 10, 10), fill="red", stroke=None)
    assert [type(op) for op in only._ops] == [ir.FillPath]
    outline = f.mark(f.path().circle(0, 0, 10), fill=None, stroke_width=2)
    assert [type(op) for op in outline._ops] == [ir.StrokePath] and outline._ops[0].width == 2
    assert api.canvas_sketch().style.stroke_width == 3       # the current style is unchanged
    with pytest.raises(TypeError):
        f.mark(fill="red")
    with pytest.raises(TypeError):
        f.mark(42)
    with pytest.raises(ValueError, match=".svg"):
        f.mark("leaf.png")


def test_a_mark_can_be_recorded_before_the_window_opens():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with f.mark() as dot:                              # at the top of a sketch, before f.run()
        f.no_stroke()
        f.fill("red")
        f.circle(0, 0, 20)
    sketch = api.active_sketch()
    assert not sketch._has_window and not sketch.frame

    def setup():
        f.size(100, 100)

    def draw():
        f.background("white")
        dot.place(50, 50)

    sketch.run_namespace({"setup": setup, "draw": draw}, fps=1000, max_frames=2)
    (w, h), data = sketch.last_frame
    i = (50 * w + 50) * 3
    assert tuple(data[i:i + 3]) == RED


# ================================================================= immutability
def test_a_finished_mark_cannot_be_changed_and_placing_never_changes_it():
    script()
    m = flower()
    ops, bounds = m._ops, m.bounds()
    with pytest.raises(AttributeError):
        m._ops = ()
    with pytest.raises(AttributeError):
        m.anything = 1
    with pytest.raises(AttributeError):
        del m._ops
    with pytest.raises(dataclasses.FrozenInstanceError):
        ops[0].x = 5
    assert isinstance(ops, tuple)
    for i in range(5):
        m.place(20 * i, 30, scale=i + 1, rotate=10 * i, opacity=0.5, anchor="center")
        f.fill("black")
        m.place(10, 10, style="current", width=30)
    assert m._ops is ops and m.bounds() == bounds
    assert copy.copy(m) is m and copy.deepcopy(m) is m
    public = {n for n in dir(m) if not n.startswith("_")}
    assert public == {"place", "bounds", "is_empty", "width", "height"}


# ================================================================= K2: placement
def test_place_moves_the_origin_to_x_y():
    script()
    red_box().place(50, 50)
    assert rgb(60, 55) == RED and rgb(45, 55) == WHITE and rgb(72, 55) == WHITE


def test_rotate_turns_clockwise_about_the_placed_origin():
    script()
    red_box().place(50, 50, rotate=90)             # (x, y) -> (-y, x): the box now spans x 40..50, y 50..70
    assert rgb(45, 60) == RED and rgb(60, 55) == WHITE


@pytest.mark.parametrize("scale, inside, outside", [
    (2, (85, 65), (95, 65)),
    ((1, 3), (60, 75), (75, 60)),
    (-1, (40, 45), (60, 45)),
])
def test_scale(scale, inside, outside):
    script()
    red_box().place(50, 50, scale=scale)
    assert rgb(*inside) == RED and rgb(*outside) == WHITE


def test_transform_order_is_translate_then_rotate_then_scale():
    script()
    red_box().place(50, 50, scale=2, rotate=90)    # local (20, 10) -> (40, 20) -> (-20, 40) -> (30, 90)
    assert rgb(35, 85) == RED and rgb(55, 60) == WHITE and rgb(85, 65) == WHITE


@pytest.mark.parametrize("anchor, fx, fy", [
    ("center", 0.5, 0.5), ("top-left", 0, 0), ("top", 0.5, 0), ("top-right", 1, 0), ("left", 0, 0.5),
    ("right", 1, 0.5), ("bottom-left", 0, 1), ("bottom", 0.5, 1), ("bottom-right", 1, 1),
])
def test_every_anchor(anchor, fx, fy):
    script()
    with f.mark() as m:                                 # a box away from the origin, so "origin" differs
        f.no_stroke()
        f.fill("red")
        f.rect(30, 30, 40, 20)
    m.place(100, 100, anchor=anchor)
    left, top = 100 - 40 * fx, 100 - 20 * fy
    assert rgb(int(left + 20), int(top + 10)) == RED
    assert rgb(int(left) + 1, int(top) + 1) == RED and rgb(int(left) + 38, int(top) + 18) == RED
    assert rgb(int(left) - 2, int(top) - 2) == WHITE and rgb(int(left) + 42, int(top) + 22) == WHITE


def test_origin_anchor_and_the_centre_stays_put_when_rotated():
    script()
    with f.mark() as m:
        f.no_stroke()
        f.fill("red")
        f.rect(30, 30, 40, 20)
    m.place(0, 0)                                       # origin: the box keeps its place
    assert rgb(50, 40) == RED
    m.place(150, 150, anchor="center", rotate=90)       # spans x 140..160, y 130..170
    assert rgb(150, 132) == RED and rgb(150, 168) == RED and rgb(135, 150) == WHITE


def test_place_checks_its_arguments():
    script()
    m = red_box()
    with pytest.raises(ValueError, match="anchor"):
        m.place(0, 0, anchor="middle")
    with pytest.raises(ValueError, match="opacity"):
        m.place(0, 0, opacity=1.5)
    with pytest.raises(ValueError, match="scale"):
        m.place(0, 0, scale=0)
    with pytest.raises(TypeError):
        m.place(0, 0, rotate="a")
    with pytest.raises(ValueError, match="style"):
        m.place(0, 0, style="mine")
    with pytest.raises(ValueError, match="not both"):
        m.place(0, 0, scale=2, width=10)
    with pytest.raises(ValueError, match="above 0"):
        m.place(0, 0, width=0)


def test_a_mark_follows_the_current_transform():
    script()
    with f.saved_state():
        f.translate(100, 100)
        red_box().place(0, 0)
    assert rgb(110, 105) == RED and rgb(10, 5) == WHITE


# ---- group opacity
def test_opacity_fades_the_mark_as_one_piece():
    script()
    with f.mark() as m:
        f.no_stroke()
        f.fill("red")
        f.rect(0, 0, 40, 40)
        f.rect(20, 0, 40, 40)                           # overlaps the first from x 20 to 40
    m.place(50, 50, opacity=0.5)
    alone, overlap = rgb(60, 70), rgb(80, 70)
    assert close(alone, (255, 128, 128), 3) and alone == overlap   # the overlap does not show through
    # drawn directly with the same opacity, the overlap would be darker
    f.opacity(128)
    f.no_stroke()
    f.fill("red")
    f.rect(50, 120, 40, 40)
    f.rect(70, 120, 40, 40)
    assert rgb(80, 140) != rgb(60, 140)


def test_groups_are_emitted_only_when_needed():
    script()
    m = red_box()
    m.place(10, 10)
    m.place(10, 10, opacity=1)
    assert not any(isinstance(op, (ir.BeginGroup, ir.EndGroup)) for op in canvas_ops())
    m.place(10, 10, opacity=0.3)
    groups = [op for op in canvas_ops() if isinstance(op, ir.BeginGroup)]
    assert len(groups) == 1 and groups[0].opacity == 0.3 and groups[0].bounds


def test_placing_ignores_the_current_style_and_opacity_by_default():
    script()
    m = red_box()
    f.fill("blue")
    f.opacity(50)
    m.place(50, 50)
    assert rgb(60, 55) == RED


def test_reset_matrix_in_a_mark_returns_to_the_marks_own_origin():
    script()
    with f.mark() as m:
        f.no_stroke()
        f.fill("red")
        f.translate(30, 0)
        f.rotate(20)
        f.reset_matrix()
        f.rect(0, 0, 10, 10)
    m.place(50, 50)
    assert rgb(55, 55) == RED and rgb(5, 5) == WHITE and rgb(85, 55) == WHITE


def test_no_clip_in_a_mark_does_not_lift_the_clip_around_it():
    script()
    with f.mark() as m:
        f.no_clip()
        f.no_stroke()
        f.fill("red")
        f.rect(0, 0, 180, 40)
    with f.saved_state():
        f.clip(f.path().rect(0, 0, 100, 200))
        m.place(10, 10)
    assert rgb(50, 20) == RED and rgb(150, 20) == WHITE


def test_erasing_in_a_mark_cuts_the_mark_not_the_canvas():
    script()
    f.background("blue")
    with f.mark() as m:
        f.no_stroke()
        f.fill("red")
        f.rect(0, 0, 60, 60)
        f.erase()
        f.circle(30, 30, 20)
    m.place(50, 50)
    assert rgb(80, 80) == (0, 0, 255)                   # the hole shows the canvas, which is not erased
    assert f.get(80, 80).alpha == 255
    assert rgb(55, 55) == RED


# ---- nesting
def test_nesting_a_border_of_flowers():
    script(600, 200)
    bloom = flower()
    with f.mark() as border:
        for i in range(8):
            bloom.place(i * 70, 0, scale=0.4)
    bx, by, bw, bh = border.bounds()
    fx, fy, fw, fh = bloom.bounds()
    assert bw == pytest.approx(7 * 70 + fw * 0.4, abs=0.2) and bh == pytest.approx(fh * 0.4, abs=0.2)
    assert all(isinstance(op, ir.Op) for op in border._ops)          # flattened: plain ops
    border.place(20, 190, anchor="bottom-left")
    for i in range(8):
        cx, cy = 20 - bx + i * 70, 190 - (by + bh)
        assert close(rgb(round(cx), round(cy)), GOLD), i
    assert rgb(5, 100) == WHITE


# ---- fitting: width and height
def test_width_alone_scales_uniformly():
    script()
    m = red_box(20, 10)
    m.place(10, 10, width=100, anchor="top-left")       # 100 x 50
    assert rgb(105, 55) == RED and rgb(105, 65) == WHITE and rgb(115, 30) == WHITE


def test_height_alone_scales_uniformly():
    script()
    red_box(20, 10).place(10, 10, height=40, anchor="top-left")    # 80 x 40
    assert rgb(85, 45) == RED and rgb(95, 30) == WHITE


def test_both_fit_inside_the_box_and_centre_in_it():
    script()
    m = red_box(20, 10)
    m.place(10, 10, width=100, height=100, anchor="top-left")       # 100 x 50, centred: y 35..85
    assert rgb(60, 37) == RED and rgb(60, 83) == RED and rgb(60, 32) == WHITE and rgb(60, 88) == WHITE
    m.place(150, 150, width=40, height=40, anchor="center")         # 40 x 20 centred on (150, 150)
    assert rgb(132, 142) == RED and rgb(150, 135) == WHITE


def test_fit_happens_before_rotate_and_an_empty_mark_cannot_be_fitted():
    script()
    red_box(20, 10).place(100, 100, width=80, anchor="center", rotate=90)   # 80 x 40, turned: 40 x 80
    assert rgb(100, 65) == RED and rgb(70, 100) == WHITE
    with f.mark() as empty:
        pass
    with pytest.raises(ValueError, match="empty"):
        empty.place(0, 0, width=10)


# ---- the current style
def test_style_current_makes_a_black_silhouette():
    script()
    bloom = flower()
    f.fill("black")
    f.no_stroke()
    bloom.place(100, 100, style="current")
    assert rgb(100, 100) == (0, 0, 0)                   # was gold
    assert rgb(100, 70) == (0, 0, 0)                    # was a tomato petal
    bloom.place(40, 40)                                 # its own style is untouched
    assert close(rgb(40, 40), GOLD)


def test_style_current_with_no_fill_gives_an_outline():
    script()
    m = red_box(60, 60)
    f.no_fill()
    f.stroke("blue")
    f.stroke_width(4)
    m.place(50, 50, style="current")
    assert rgb(80, 80) == WHITE and rgb(50, 80) == (0, 0, 255)


def test_style_current_recolours_text_and_paths_but_not_pictures():
    script()
    pic = f.create_graphics(20, 20)
    pic.background("green")
    with f.mark() as m:
        f.fill("red")
        f.text_size(40)
        f.text("H", 0, 0)
        f.draw_path(f.path().rect(60, 0, 20, 20))
        f.image(pic, 100, 0)
    f.fill("blue")
    f.no_stroke()
    m.place(10, 10, style="current")
    ops = canvas_ops()
    texts = [op for op in ops if isinstance(op, ir.Text)]
    assert texts and texts[-1].color.rgba[:3] == (0, 0, 255)
    assert texts[-1].style.text_size == 40              # font and size stay
    assert rgb(80, 20) == (0, 0, 255)
    assert rgb(120, 20) == (0, 255, 0)                  # the picture keeps its pixels


def test_style_current_reaches_nested_marks():
    script()
    inner = red_box(20, 20)
    with f.mark() as outer:
        inner.place(0, 0)
        inner.place(40, 0)
    f.fill("blue")
    f.no_stroke()
    outer.place(10, 10, style="current")
    assert rgb(20, 20) == (0, 0, 255) and rgb(60, 20) == (0, 0, 255)


def test_style_current_ignores_the_current_opacity_and_blend():
    script()
    m = red_box(20, 20)
    f.fill("blue")
    f.no_stroke()
    f.opacity(50)
    f.blend_mode("multiply")
    m.place(10, 10, style="current")
    assert rgb(20, 20) == (0, 0, 255)


# ================================================================= bounds
def test_bounds_of_a_plain_rectangle_are_tight_and_conservative():
    script()
    x, y, w, h = red_box(40, 20).bounds()
    assert -1 / 32 <= -x <= 1 / 32 + 1e-9 and x <= 0 and y <= 0
    assert 40 <= w <= 40 + 1 / 16 and 20 <= h <= 20 + 1 / 16


def test_bounds_include_the_stroke():
    script()
    with f.mark() as m:
        f.stroke("black")
        f.stroke_width(10)
        f.no_fill()
        f.rect(0, 0, 40, 20)
    x, y, w, h = m.bounds()
    assert x <= -5 and y <= -5 and x + w >= 45 and y + h >= 25
    assert x > -5.1 and x + w < 45.1


def test_bounds_include_text():
    script()
    f.text_size(40)
    with f.mark() as m:
        f.fill("black")
        f.text("Hello", 0, 0)
    x, y, w, h = m.bounds()
    assert w > 0.8 * f.text_width("Hello") and 20 < h < 60 and m.width == w and m.height == h


def test_bounds_are_never_smaller_than_the_ink():
    script()
    bloom = flower()
    bx, by, bw, bh = bloom.bounds()
    bloom.place(100, 100)
    f.load_pixels()
    data = f.pixels
    for yy in range(200):
        for xx in range(200):
            i = (yy * 200 + xx) * 4
            if data[i:i + 3] != b"\xff\xff\xff":
                assert 100 + bx - 1 <= xx <= 100 + bx + bw + 1 and 100 + by - 1 <= yy <= 100 + by + bh + 1


def test_an_empty_mark():
    script()
    with f.mark() as e:
        pass
    with f.mark() as invisible:
        f.no_fill()
        f.no_stroke()
        f.circle(0, 0, 10)
    for m in (e, invisible):
        assert m.bounds() is None and m.is_empty and m.width == 0 and m.height == 0
    ops = canvas_ops()
    e.place(10, 10)
    assert canvas_ops() == ops                          # draws nothing
    with pytest.raises(ValueError, match="the mark is empty"):
        e.place(10, 10, anchor="center")
    assert f.mark(f.path()).is_empty


# ================================================================= layers
def test_a_mark_placed_inside_a_layer_goes_to_the_layer():
    script()
    m = red_box()
    with f.layer("top"):
        m.place(50, 50)
        with f.mark() as inner:                         # recording inside a layer block is fine too
            f.no_stroke()
            f.fill("blue")
            f.rect(0, 0, 10, 10)
    inner.place(150, 150)
    assert not any(isinstance(op, ir.Rect) and op.style.fill.rgba[:3] == RED for op in canvas_ops())
    assert rgb(60, 55) == RED and rgb(155, 155) == (0, 0, 255)


# ================================================================= K3: files
def test_pdf_and_svg_stay_vector_with_text_and_an_opacity_group(tmp_path):
    script(300, 200)
    with f.mark() as m:
        f.fill(f.linear_gradient(-30, 0, 30, 0, ["red", "blue"]))
        f.circle(0, 0, 60)
        f.fill("black")
        f.text_size(16)
        f.text("Marked", -25, 35)
    m.place(80, 80)
    m.place(220, 80, opacity=0.5, rotate=20)
    f.save(str(tmp_path / "a.pdf"))
    f.save(str(tmp_path / "a.svg"))
    subtypes, content, groups = pdf_objects(tmp_path / "a.pdf")
    assert "/Image" not in subtypes                     # no picture of the mark: shapes
    assert re.search(rb" c\b", content) and re.search(rb"\b(f|B|b|f\*)\n", content)
    assert "/Transparency" in groups                    # the faded placement is a transparency group
    text = " ".join(page.extract_text() for page in PdfReader(str(tmp_path / "a.pdf")).pages)
    assert text.count("Marked") == 2                    # real text, in both placements (T15)
    svg = (tmp_path / "a.svg").read_text(encoding="utf-8")
    assert "<image" not in svg and "<path" in svg and "Gradient" in svg
    assert len(re.findall(r"<text [^>]*>Marked</text>", svg)) == 2   # live SVG text (T19)


def test_a_picture_inside_a_mark_keeps_its_p3_behaviour(tmp_path):
    script()
    pic = f.create_graphics(40, 40)
    pic.fill("green")
    pic.circle(20, 20, 30)
    with f.mark() as m:
        f.image(pic, 0, 0)
    m.place(50, 50)
    assert rgb(70, 70) == (0, 255, 0)
    f.save(str(tmp_path / "a.pdf"))
    subtypes, _, _ = pdf_objects(tmp_path / "a.pdf")
    assert "/Image" not in subtypes                     # the picture's history replays as vectors (P3)


def test_screen_rendering_is_crisp_when_scaled_up():
    script()
    with f.mark() as dot:
        f.no_stroke()
        f.fill("black")
        f.circle(0, 0, 4)
    dot.place(100, 100, scale=40)                       # a 160-pixel disc from a 4-pixel one
    row = [rgb(x, 100)[0] for x in range(10, 40)]       # across the left edge at x = 20
    partial = [v for v in row if 0 < v < 255]
    assert len(partial) <= 2                            # one anti-aliased pixel, not a blurred bitmap edge
    assert rgb(25, 100) == (0, 0, 0) and rgb(15, 100) == WHITE


# ================================================================= animated sketches
def test_record_in_setup_place_in_draw_and_placing_is_quick():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    state = {}
    timings = []

    def setup():
        f.size(400, 300)
        with f.mark() as m:
            f.no_stroke()
            for i in range(50):
                f.fill("red")
                f.circle(i % 10, i // 10, 4)
        state["m"] = m

    def draw():
        f.background("white")
        t0 = time.perf_counter()
        for i in range(200):
            state["m"].place(20 + (i % 20) * 19, 20 + (i // 20) * 28, rotate=i)
        timings.append(time.perf_counter() - t0)

    sketch = api.active_sketch()
    sketch.run_namespace({"setup": setup, "draw": draw}, fps=1000, max_frames=3)
    (w, h), data = sketch.last_frame
    i = (22 * w + 22) * 3
    assert tuple(data[i:i + 3]) == RED
    assert min(timings) < 0.25                          # measured about 2.5 ms for 200 placements


# ================================================================= the naming trap
def test_the_module_never_hides_the_function():
    marks_module = importlib.import_module("funground.marks")
    import funground.marks  # noqa: F401
    assert callable(f.mark) and f.mark is api.mark
    assert marks_module is not f.mark and f.marks is marks_module
    assert "marks" not in f.__all__ and "mark" in f.__all__


# ================================================================= IR
def test_group_ops_round_trip_through_json():
    group = ir.BeginGroup(0.25, "normal", (1.0, 2.0, 3.0, 4.0))
    frame = ir.Frame([ir.Save(), group, ir.EndGroup(), ir.Restore()])
    data = frame.to_jsonable()
    assert data[1] == {"op": "BeginGroup", "opacity": 0.25, "bounds": [1.0, 2.0, 3.0, 4.0]}
    assert data[2] == {"op": "EndGroup"}
    assert ir.Frame.from_jsonable(data).ops == frame.ops
    assert ir.op_to_jsonable(ir.BeginGroup()) == {"op": "BeginGroup"}
    assert "BeginGroup" in ir.OP_TYPES and "EndGroup" in ir.OP_TYPES


# ================================================================= SVG files
SVG_LEAF = ('<svg xmlns="http://www.w3.org/2000/svg" width="60" height="40" viewBox="0 0 60 40">'
            '<rect x="10" y="10" width="40" height="20" fill="#00ff00"/></svg>')


def test_a_mark_from_an_svg_file(tmp_path):
    script()
    path = tmp_path / "leaf.svg"
    path.write_text(SVG_LEAF, encoding="utf-8")
    leaf = f.mark(str(path))
    x, y, w, h = leaf.bounds()                          # the origin is the file's top-left
    assert x == pytest.approx(10, abs=0.1) and y == pytest.approx(10, abs=0.1) and w == pytest.approx(40, abs=0.1)
    leaf.place(100, 100)
    assert rgb(130, 120) == (0, 255, 0)
    f.fill("blue")
    f.no_stroke()
    leaf.place(0, 0, style="current")                   # recoloured
    assert rgb(30, 20) == (0, 0, 255)
    f.save(str(tmp_path / "a.pdf"))
    subtypes, content, _ = pdf_objects(tmp_path / "a.pdf")
    assert "/Image" not in subtypes
    assert re.search(rb" (re|l|c)\b", content)                 # path operators: the shapes are vector
    with pytest.raises(FileNotFoundError):
        f.mark(str(tmp_path / "missing.svg"))
    with pytest.raises(TypeError):
        f.mark(str(path), fill="red")


# ================================================================= the maintainer's three demonstrations
def test_demo_1_a_simple_mark_from_a_path():
    script()
    leaf = f.mark(f.path().ellipse(0, 0, 40, 16), fill="olive", stroke=None)
    assert leaf.bounds() == pytest.approx((-20, -8, 40, 16), abs=1 / 16)
    leaf.place(100, 100)
    leaf.place(100, 150, rotate=90, scale=0.5)
    assert rgb(100, 100) == (128, 128, 0) and rgb(100, 150) == (128, 128, 0) and rgb(115, 150) == WHITE


def test_demo_2_a_composite_flower():
    script()
    bloom = flower()
    kinds = {type(op) for op in bloom._ops}
    assert kinds >= {ir.Ellipse, ir.Circle, ir.Save, ir.Restore, ir.Concat}
    bloom.place(100, 100)
    assert close(rgb(100, 100), GOLD) and close(rgb(100, 70), (255, 99, 71)) and rgb(160, 160) == WHITE


def test_demo_3_repeated_placements_and_a_nested_border_saved_as_vector_pdf(tmp_path):
    script(600, 400)
    bloom = flower()
    for i in range(5):
        bloom.place(60 + i * 110, 120, scale=0.6 + 0.15 * i, rotate=12 * i, opacity=1 - 0.15 * i)
    with f.mark() as border:
        for i in range(8):
            bloom.place(i * 70, 0, scale=0.4)
    border.place(20, 390, anchor="bottom-left")
    border.place(580, 10, anchor="top-right", rotate=180)
    f.save(str(tmp_path / "flowers.pdf"))
    subtypes, content, groups = pdf_objects(tmp_path / "flowers.pdf")
    assert "/Image" not in subtypes
    assert content.count(b" c ") + content.count(b" c\n") > 100      # many curve segments: real shapes
    assert "/Transparency" in groups
