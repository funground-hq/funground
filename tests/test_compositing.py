"""Blend modes, opacity and shadow (S-051, contract S14)."""
from __future__ import annotations

import cairo
import pytest

import funground as p
from funground import api, ir
from funground.platform.headless import HeadlessPlatform
from funground.renderers.cairo2d import CairoRenderer
from funground.sketch import Sketch


def render(draw, size=(100, 100)):
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(*size), "draw": draw}, max_frames=1)
    (w, _h), rgb = s.last_frame

    def px(x, y):
        i = (y * w + x) * 3
        return tuple(rgb[i:i + 3])

    return px, s


def cairo_reference(dst, src, operator):
    """One pixel of *src* painted over *dst* with a Cairo operator: the pinned meaning of each mode."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(*(c / 255 for c in dst)); ctx.paint()
    ctx.set_operator(operator)
    ctx.set_source_rgb(*(c / 255 for c in src)); ctx.paint()
    surface.flush()
    b, g, r, _a = bytes(surface.get_data())[:4]
    return (r, g, b)


@pytest.mark.parametrize("mode", Sketch.BLEND_MODES)
def test_each_blend_mode_matches_the_cairo_operator_of_the_same_name(mode):
    dst, src = (200, 120, 40), (60, 140, 220)

    def draw():
        p.background(dst)
        p.no_stroke()
        p.blend_mode(mode)
        p.fill(src)
        p.rect(0, 0, 100, 100)

    px, _ = render(draw)
    assert px(50, 50) == cairo_reference(dst, src, CairoRenderer._BLENDS[mode])


def test_multiply_and_screen_do_what_their_names_say():
    def draw():
        p.background((128, 128, 128))
        p.no_stroke()
        p.blend_mode("multiply"); p.fill((128, 128, 128)); p.rect(0, 0, 50, 100)
        p.blend_mode("screen"); p.rect(50, 0, 50, 100)

    px, _ = render(draw)
    assert px(25, 50)[0] < 128 < px(75, 50)[0]


def test_opacity_multiplies_every_alpha_including_gradients_and_text():
    def draw():
        p.background("white")
        p.no_stroke()
        p.opacity(128)
        p.fill("black")
        p.rect(0, 0, 50, 50)
        p.fill(p.linear_gradient(50, 0, 100, 0, ["black", "black"]))
        p.rect(50, 0, 50, 50)
        p.opacity(255)
        p.fill("black")
        p.rect(0, 50, 50, 50)

    px, _ = render(draw)
    assert abs(px(25, 25)[0] - 127) <= 2 and abs(px(75, 25)[0] - 127) <= 2 and px(25, 75) == (0, 0, 0)


def test_opacity_applies_to_fill_and_stroke_separately_as_in_drawbot():
    def draw():
        p.background("white")
        p.opacity(128)
        p.fill("black")
        p.stroke("black")
        p.stroke_width(20)
        p.rect(20, 20, 60, 60)

    px, _ = render(draw)
    # where the stroke lies over the fill, two half-transparent layers make it darker
    assert px(50, 50)[0] > px(21, 50)[0]


def test_shadow_is_offset_soft_and_under_the_shape():
    def draw():
        p.background("white")
        p.no_stroke()
        p.shadow(20, 20, blur=6, color=(0, 0, 0, 255))
        p.fill("red")
        p.rect(20, 20, 40, 40)

    px, _ = render(draw)
    assert px(40, 40) == (255, 0, 0)                    # the shape covers its shadow
    assert px(70, 70) == (0, 0, 0)                      # the shadow, moved by (20, 20)
    edge = px(83, 70)                                   # 3 px outside the moved shape: partly shaded
    assert 0 < edge[0] < 255
    assert px(95, 95) == (255, 255, 255)                # beyond the blur: untouched


def test_shadow_offset_is_in_canvas_pixels_whatever_the_transform():
    def draw():
        p.background("white")
        p.no_stroke()
        p.translate(30, 30)
        p.rotate(90)
        p.scale(2)
        p.shadow(30, 0, blur=0, color="black")
        p.fill("red")
        p.rect(-5, -5, 10, 10)                          # a 20 x 20 square around (30, 30)

    px, _ = render(draw)
    assert px(30, 30) == (255, 0, 0) and px(60, 30) == (0, 0, 0) and px(30, 60) == (255, 255, 255)


def test_state_is_saved_restored_and_carried_into_the_ir():
    def draw():
        p.blend_mode("multiply")
        with p.saved_state():
            p.opacity(100)
            p.shadow(1, 2, 3, "navy")
            p.line(0, 0, 10, 10)
            p.begin_shape(); p.vertex(0, 0); p.vertex(10, 0); p.vertex(0, 10); p.end_shape(close=True)
        p.rect(0, 0, 5, 5)
        draw.style = api.active_sketch().style

    _, s = render(draw)
    assert (draw.style.blend_mode, draw.style.opacity, draw.style.shadow) == ("multiply", 255, None)
    fills = [op for op in s.last_ops if isinstance(op, ir.FillPath)]
    assert fills and fills[0].opacity == 100 and fills[0].shadow[:3] == (1.0, 2.0, 3.0)
    for op in s.last_ops:
        if isinstance(op, (ir.FillPath, ir.StrokePath, ir.Line, ir.Rect)):
            assert ir.op_from_jsonable(ir.op_to_jsonable(op)) == op


def test_defaults_leave_snapshots_unchanged():
    def draw():
        p.begin_shape(); p.vertex(0, 0); p.vertex(10, 0); p.vertex(0, 10); p.end_shape(close=True)

    _, s = render(draw)
    for op in s.last_ops:
        data = ir.op_to_jsonable(op)
        assert not {"blend_mode", "opacity", "shadow"} & set(data)
        assert not {"blend_mode", "opacity", "shadow"} & set(data.get("style", {}))


def test_learner_mistakes_are_explained():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with pytest.raises(ValueError, match="'multiply'"):
        p.blend_mode("mulitply")
    with pytest.raises(ValueError, match="0 .invisible. to 255"):
        p.opacity(300)
    with pytest.raises(ValueError, match="blur of 0 or more"):
        p.shadow(1, 1, -2)
