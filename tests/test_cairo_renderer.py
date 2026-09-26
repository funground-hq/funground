"""CairoRenderer (S-023): the v0.6 vector semantics, pixel by pixel, without a window."""
from __future__ import annotations

import cairo
import pytest

from funground import ir
from funground.capabilities import Capability
from funground.color import Color
from funground.geometry import Path, Transform
from funground.renderers.cairo2d import CairoRenderer
from funground.state import GraphicsState

WHITE, BLACK, RED = Color(255, 255, 255), Color(0, 0, 0), Color(255, 0, 0)


def draw(ops, w=100, h=100):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    r = CairoRenderer()
    r.draw(r.context_for(surf), ir.Frame(ops))
    surf.flush()
    data, stride = surf.get_data(), surf.get_stride()

    def px(x, y):
        i = y * stride + x * 4
        return (data[i + 2], data[i + 1], data[i])  # BGRA -> RGB (opaque frames)
    return px


def test_capabilities_cover_the_vector_contract():
    assert {Capability.RASTER_2D, Capability.ALPHA, Capability.ANTIALIAS, Capability.TRANSFORMS,
            Capability.VECTOR_PATHS, Capability.CLIP_PATH, Capability.PDF_EXPORT} <= CairoRenderer.capabilities


def test_rect_top_left_and_fill(canvas=None):
    px = draw([ir.Clear(WHITE), ir.Rect(10, 20, 30, 10, GraphicsState(fill=RED, stroke=None))])
    assert px(10, 20) == (255, 0, 0) and px(39, 29) == (255, 0, 0)
    assert px(9, 20) == (255, 255, 255) and px(40, 29) == (255, 255, 255)


def test_alpha_is_honoured_d003():
    px = draw([ir.Clear(WHITE), ir.Rect(0, 0, 50, 50, GraphicsState(fill=Color(0, 0, 255, 128), stroke=None))])
    r, g, b = px(25, 25)
    assert b == 255 and 120 <= r <= 135 and 120 <= g <= 135   # half blue over white


def test_stroke_is_centred_on_the_edge_d004():
    px = draw([ir.Clear(WHITE), ir.Rect(20, 20, 40, 40, GraphicsState(fill=None, stroke=BLACK, stroke_width=6))])
    assert px(17, 40) == (0, 0, 0)     # 3 px outside the edge
    assert px(22, 40) == (0, 0, 0)     # 3 px inside
    assert px(16, 40) == (255, 255, 255) and px(23, 40) == (255, 255, 255)


def test_fractional_coordinates_are_anti_aliased_d005():
    px = draw([ir.Clear(WHITE), ir.Rect(10.5, 10, 10, 10, GraphicsState(fill=BLACK, stroke=None))])
    assert px(10, 15) not in ((0, 0, 0), (255, 255, 255))   # a grey edge pixel
    assert px(15, 15) == (0, 0, 0)


def test_circle_is_centred_and_takes_a_diameter():
    px = draw([ir.Clear(WHITE), ir.Circle(50, 50, 40, GraphicsState(fill=RED, stroke=None))])
    assert px(50, 50) == (255, 0, 0) and px(32, 50) == (255, 0, 0) and px(28, 50) == (255, 255, 255)


def test_transform_clip_and_paths():
    tri = Path().move_to(0, 0).line_to(40, 0).line_to(0, 40).close()
    ops = [ir.Clear(WHITE), ir.Save(), ir.Concat(Transform.translation(50, 50)),
           ir.ClipPath(Path.rect(0, 0, 20, 40)), ir.FillPath(tri, BLACK), ir.Restore(),
           ir.StrokePath(Path().move_to(0, 90).line_to(99, 90), RED, 2)]
    px = draw(ops)
    assert px(55, 55) == (0, 0, 0)          # inside triangle and clip
    assert px(75, 55) == (255, 255, 255)    # inside triangle, outside clip (x >= 70)
    assert px(50, 90) == (255, 0, 0)        # stroke drawn after restore, unclipped


def test_unbalanced_restore_is_an_error():
    with pytest.raises(RuntimeError):
        draw([ir.Restore()])


def test_text_op_is_drawn_via_outlines():
    px = draw([ir.Clear(WHITE), ir.Text("H", 10, 10, BLACK, GraphicsState(text_size=40))])
    inks = [(x, y) for y in range(100) for x in range(100) if px(x, y) != (255, 255, 255)]
    assert inks and min(x for x, _ in inks) >= 10 and min(y for _, y in inks) >= 10


def test_point_uses_stroke_and_dot_size():
    px = draw([ir.Clear(WHITE), ir.Point(50, 50, GraphicsState(stroke=BLACK, stroke_width=8))])
    assert px(50, 50) == (0, 0, 0) and px(56, 50) == (255, 255, 255)
