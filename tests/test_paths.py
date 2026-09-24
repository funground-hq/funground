"""Shapes, paths and clipping (story S-028; contract row F3).

Pixel checks go through the `canvas` fixture (a live 200x100 window); op
checks read the sketch's Frame, which is the cross-backend contract.
"""
from __future__ import annotations

import math

import pytest

import playground as p
from playground import api, ir
from playground.capabilities import PlaygroundWarning
from playground.geometry import Path
from playground.paths import PathBuilder
from playground.platform.headless import HeadlessPlatform
from playground.sketch import Sketch

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)


def px(surface, x, y):
    return tuple(surface.get_at((x, y))[:3])


def kinds(sketch, skip=1):
    return [type(op).__name__ for op in sketch.frame.ops[skip:]]  # skip the Clear


def star_points(cx=100, cy=50, r=45):
    """Every second corner of a pentagon: a pentagram, which crosses itself."""
    return [(cx + r * math.cos(math.radians(-90 + i * 144)), cy + r * math.sin(math.radians(-90 + i * 144)))
            for i in range(5)]


# ---------------------------------------------------------------- begin_shape / vertex / end_shape
def test_star_polygon_is_filled_including_its_centre_non_zero_rule(sketch, canvas):
    p.background("white")
    p.fill("red")
    p.no_stroke()
    p.begin_shape()
    for x, y in star_points():
        p.vertex(x, y)
    p.end_shape(close=True)
    assert kinds(sketch) == ["FillPath"]
    assert sketch.frame.ops[1].path.is_closed
    assert px(canvas, 100, 50) == RED     # the inner pentagon has winding number 2: filled (F3), not a hole
    assert px(canvas, 100, 10) == RED     # the top tip
    assert px(canvas, 100, 95) == WHITE   # below the star
    assert px(canvas, 15, 15) == WHITE


def test_closed_shape_is_filled_then_stroked(sketch, canvas):
    p.background("white")
    p.fill("red")
    p.stroke("blue")
    p.stroke_width(3)
    p.begin_shape()
    p.vertex(20, 20)
    p.vertex(100, 80)
    p.vertex(180, 20)
    p.end_shape(close=True)
    assert kinds(sketch) == ["FillPath", "StrokePath"]          # S5: fill first, stroke on top
    fill, stroke = sketch.frame.ops[1:]
    assert fill.color.rgb == RED and stroke.color.rgb == BLUE and stroke.width == 3.0
    assert px(canvas, 100, 40) == RED     # inside
    assert px(canvas, 100, 20) == BLUE    # the closing edge is stroked
    assert px(canvas, 60, 50) == BLUE     # on the first edge


def test_open_polyline_is_stroked_only(sketch, canvas):
    p.background("white")
    p.fill("red")
    p.stroke("blue")
    p.stroke_width(3)
    p.begin_shape()
    p.vertex(20, 20)
    p.vertex(100, 80)
    p.vertex(180, 20)
    p.end_shape()
    assert kinds(sketch) == ["StrokePath"]  # no FillPath even though a fill is set (F3)
    assert not sketch.frame.ops[1].path.is_closed
    assert px(canvas, 60, 50) == BLUE     # on the line from (20, 20) to (100, 80)
    assert px(canvas, 100, 40) == WHITE   # would be inside if it were filled
    assert px(canvas, 100, 20) == WHITE   # no closing edge


def test_vertices_become_a_move_then_lines(sketch, canvas):
    p.no_fill()
    p.begin_shape()
    p.vertex(1, 2)
    p.vertex(3, 4)
    p.vertex(5, 6)
    p.end_shape()
    assert sketch.frame.ops[0].path.segments == (("move", (1, 2)), ("line", (3, 4)), ("line", (5, 6)))


def test_bezier_curve_vertex_is_stroked_through_its_midpoint(sketch, canvas):
    p.background("white")
    p.no_fill()
    p.stroke("blue")
    p.stroke_width(3)
    p.begin_shape()
    p.vertex(20, 80)
    p.curve_vertex(20, 0, 180, 0, 180, 80)   # cubic: the midpoint (t = 0.5) is at (100, 20)
    p.end_shape()
    (op,) = sketch.frame.ops[1:]
    assert isinstance(op, ir.StrokePath)
    assert op.path.segments[1] == ("cubic", (20, 0), (180, 0), (180, 80))
    assert px(canvas, 100, 20) == BLUE
    assert px(canvas, 100, 60) == WHITE   # under the arch
    assert px(canvas, 20, 5) == WHITE     # the control point itself is not on the curve


def test_curve_vertex_needs_a_starting_vertex(canvas):
    p.begin_shape()
    with pytest.raises(RuntimeError, match=r"p\.vertex"):
        p.curve_vertex(0, 0, 10, 10, 20, 20)
    p.end_shape()


def test_vertex_and_end_shape_outside_a_shape_name_begin_shape(canvas):
    with pytest.raises(RuntimeError, match=r"p\.begin_shape"):
        p.vertex(1, 1)
    with pytest.raises(RuntimeError, match=r"p\.begin_shape"):
        p.end_shape()
    p.begin_shape()
    with pytest.raises(RuntimeError, match=r"p\.end_shape"):
        p.begin_shape()


def test_empty_shape_draws_nothing(sketch, canvas):
    p.begin_shape()
    p.end_shape(close=True)
    assert sketch.frame.ops == ()


def test_shape_left_open_at_frame_end_is_dropped_with_a_warning(sketch, canvas):
    p.background("white")
    p.fill("red")
    p.begin_shape()
    p.vertex(0, 0)
    p.vertex(50, 0)
    p.vertex(50, 50)
    with pytest.warns(PlaygroundWarning, match=r"p\.end_shape"):
        assert px(canvas, 10, 10) == WHITE       # rendering ends the frame; the shape never drew
    assert sketch._shape is None
    p.begin_shape()                              # the next frame can start a fresh shape
    p.vertex(0, 0)
    p.end_shape()


def test_shape_uses_the_style_current_at_end_shape(sketch, canvas):
    p.fill("red")
    p.begin_shape()
    p.vertex(0, 0)
    p.vertex(10, 0)
    p.vertex(10, 10)
    p.fill("blue")
    p.end_shape(close=True)
    assert sketch.frame.ops[0].color.rgb == BLUE


# ---------------------------------------------------------------- p.path() / draw_path
def test_path_builder_chains_and_returns_itself():
    path = p.path()
    assert isinstance(path, PathBuilder) and path.is_empty
    assert path.move_to(0, 0).line_to(10, 0).curve_to(10, 5, 5, 10, 0, 10).quad_to(0, 5, 0, 0).close() is path
    assert path.is_closed and len(path) == 5
    assert path.geometry.segments[3][0] == "cubic"   # quad_to is stored as its cubic equivalent
    assert "closed" in repr(path)


def test_path_builder_needs_move_to_first():
    with pytest.raises(ValueError, match="move_to"):
        p.path().line_to(1, 1)
    with pytest.raises(ValueError, match="move_to"):
        p.path().close()


def test_path_is_reusable_under_translate(sketch, canvas):
    p.background("white")
    p.fill("red")
    p.no_stroke()
    square = p.path().move_to(0, 0).line_to(20, 0).line_to(20, 20).line_to(0, 20).close()
    before = square.geometry
    with p.state():
        p.translate(30, 30)
        p.draw_path(square)
    with p.state():
        p.translate(120, 60)
        p.draw_path(square)
    assert square.geometry == before                 # drawing never changes the path
    assert kinds(sketch) == ["Save", "Concat", "FillPath", "Restore", "Save", "Concat", "FillPath", "Restore"]
    assert sketch.frame.ops[3].path == sketch.frame.ops[7].path
    assert px(canvas, 40, 40) == RED
    assert px(canvas, 130, 70) == RED
    assert px(canvas, 40, 70) == WHITE
    assert px(canvas, 10, 10) == WHITE               # not at the origin


def test_draw_path_open_path_is_stroked_not_filled(sketch, canvas):
    p.background("white")
    p.fill("red")
    p.stroke("blue")
    p.stroke_width(3)
    p.draw_path(p.path().move_to(20, 20).line_to(100, 80).line_to(180, 20))
    assert kinds(sketch) == ["StrokePath"]
    assert px(canvas, 100, 40) == WHITE
    assert px(canvas, 60, 50) == BLUE


def test_draw_path_with_no_fill_and_no_stroke_emits_nothing(sketch, canvas):
    p.no_fill()
    p.no_stroke()
    p.draw_path(p.path().move_to(0, 0).line_to(10, 10).close())
    assert sketch.frame.ops == ()


def test_draw_path_rejects_things_that_are_not_paths(canvas):
    with pytest.raises(TypeError, match=r"p\.path\(\)"):
        p.draw_path([(0, 0), (10, 10)])  # type: ignore[arg-type]


def test_draw_path_accepts_a_raw_geometry_path(sketch, canvas):
    p.draw_path(Path.rect(0, 0, 10, 10))
    assert kinds(sketch, 0) == ["FillPath", "StrokePath"]


# ---------------------------------------------------------------- clip
def clip_window():
    return p.path().move_to(50, 25).line_to(100, 25).line_to(100, 75).line_to(50, 75).close()


def test_clip_limits_drawing_to_the_path(sketch, canvas):
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.push()
    p.clip(clip_window())
    p.rect(0, 0, 200, 100)                            # covers the canvas; only the window shows
    p.pop()
    assert kinds(sketch) == ["Save", "ClipPath", "Rect", "Restore"]
    assert px(canvas, 75, 50) == RED
    assert px(canvas, 25, 50) == WHITE
    assert px(canvas, 150, 50) == WHITE
    assert px(canvas, 75, 10) == WHITE
    assert px(canvas, 75, 90) == WHITE


def test_clip_is_undone_by_pop(sketch, canvas):
    p.background("white")
    p.no_stroke()
    p.fill("red")
    with p.state():
        p.clip(clip_window())
        p.rect(0, 0, 200, 100)
    p.fill("blue")
    p.rect(150, 0, 50, 100)                           # after pop(): drawn outside the old window
    assert px(canvas, 75, 50) == RED
    assert px(canvas, 175, 50) == BLUE
    assert px(canvas, 25, 50) == WHITE


def test_clip_follows_the_current_transform(canvas):
    p.background("white")
    p.no_stroke()
    p.fill("red")
    with p.state():
        p.translate(100, 0)
        p.clip(clip_window())                         # window now spans x 150..200
        p.rect(-100, 0, 200, 100)
    assert px(canvas, 175, 50) == RED
    assert px(canvas, 75, 50) == WHITE


def test_background_is_not_limited_by_a_clip(canvas):
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.rect(0, 0, 200, 100)
    with p.state():
        p.clip(clip_window())
        p.background("blue")                          # S9: background paints the whole canvas
    assert px(canvas, 10, 10) == BLUE
    assert px(canvas, 75, 50) == BLUE


def test_clip_persists_only_for_the_frame_when_used_without_push(canvas):
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.clip(clip_window())
    p.rect(0, 0, 200, 100)
    assert px(canvas, 25, 50) == WHITE
    p.rect(0, 0, 200, 100)                            # a new frame: no clip in effect any more (F2)
    assert px(canvas, 25, 50) == RED


# ---------------------------------------------------------------- the sample sketch exports
def test_sample_sketch_exports_to_pdf_headless(tmp_path, monkeypatch):
    """S-028 acceptance: a star, a Bezier curve and a clipped pattern export to PDF."""
    from conftest import EXAMPLES, run_sketch

    monkeypatch.setenv("PLAYGROUND_HEADLESS", "1")
    sketch = api.use_sketch(Sketch())                 # picks the headless platform from the environment
    assert isinstance(sketch._platform, HeadlessPlatform)
    out = tmp_path / "paths.pdf"
    src = (EXAMPLES / "14_paths.py").read_text(encoding="utf-8")
    assert 'p.background("white")' in src
    src = src.replace('    p.background("white")\n', f'    p.background("white")\n    p.save(r"{out}")\n', 1)
    patched = tmp_path / "14_paths_save.py"
    patched.write_text(src, encoding="utf-8")
    run_sketch(patched, frames=2)
    ops = api.active_sketch().last_ops
    assert any(isinstance(op, ir.ClipPath) for op in ops)
    assert any(isinstance(op, ir.FillPath) for op in ops)
    assert any(isinstance(op, ir.StrokePath) and any(s[0] == "cubic" for s in op.path) for op in ops)
    assert out.read_bytes()[:5] == b"%PDF-" and out.stat().st_size > 1000
