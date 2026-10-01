"""tint and part of a picture (S-078, contract P5, P6): pixel checks on small pictures."""
from __future__ import annotations

import inspect

import pytest

import funground as p
from funground import api, ir
from funground.picture import Picture
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def px(canvas, x, y):
    c = canvas.get_at((x, y))
    return (c.r, c.g, c.b, c.a)


def near(actual, expected, tol=1):
    return all(abs(a - e) <= tol for a, e in zip(actual, expected))


def solid(color, w=20, h=20):
    g = p.create_graphics(w, h)
    g.background(color)
    return g


def halves():
    """20 x 10: left half red, right half blue, opaque."""
    g = p.create_graphics(20, 10)
    g.no_stroke()
    g.fill("red")
    g.rect(0, 0, 10, 10)
    g.fill("blue")
    g.rect(10, 0, 10, 10)
    return g


def last(sketch):
    return sketch.frame.ops[-1]


# ---- P5: the colour -------------------------------------------------------------------------
def test_white_tint_leaves_the_picture_unchanged(canvas):
    g = solid((10, 100, 200))
    p.tint("white")
    p.image(g, 0, 0)
    assert px(canvas, 5, 5) == (10, 100, 200, 255)


def test_no_tint_is_a_plain_picture(canvas):
    g = solid((10, 100, 200))
    p.tint("red")
    p.no_tint()
    p.image(g, 0, 0)
    assert px(canvas, 5, 5) == (10, 100, 200, 255)


def test_red_tint_on_white_is_red(canvas):
    g = solid("white")
    p.tint("red")
    p.image(g, 0, 0)
    assert px(canvas, 5, 5) == (255, 0, 0, 255)


def test_tint_multiplies_each_channel(canvas):
    g = solid((200, 100, 50))
    p.tint(128, 255, 0)
    p.image(g, 0, 0)
    assert near(px(canvas, 5, 5), (100, 100, 0, 255))


def test_tint_alpha_makes_the_picture_see_through(canvas):
    p.background("white")
    g = solid("black")
    p.tint(255, 128)
    p.image(g, 0, 0)
    r, gr, b, a = px(canvas, 5, 5)
    assert a == 255 and near((r, gr, b), (127, 127, 127), 1)


def test_tint_alpha_on_a_transparent_canvas(canvas):
    g = solid("red")
    p.tint(255, 128)
    p.image(g, 0, 0)
    r, gr, b, a = px(canvas, 5, 5)
    assert abs(a - 128) <= 1 and abs(r - 128) <= 1 and (gr, b) == (0, 0)   # premultiplied bytes


def test_a_transparent_area_of_the_picture_stays_transparent(canvas):
    g = p.create_graphics(20, 20)            # transparent
    g.no_stroke()
    g.fill("white")
    g.rect(0, 0, 10, 20)                     # left half white, right half empty
    p.tint("red")
    p.image(g, 0, 0)
    assert px(canvas, 5, 5) == (255, 0, 0, 255)
    assert px(canvas, 15, 5) == (0, 0, 0, 0)


def test_tint_reads_every_colour_form_like_fill(canvas):
    g = solid("white")
    cases = [(("red",), (255, 0, 0)), (("#00ff00",), (0, 255, 0)), (((0, 0, 255),), (0, 0, 255)),
             ((255, 255, 0), (255, 255, 0)), ((p.hsb(0, 100, 100),), (255, 0, 0)),
             (("0x0000FF",), (0, 0, 255))]
    for args, expected in cases:
        p.tint(*args)
        p.image(g, 0, 0)
        assert px(canvas, 5, 5)[:3] == expected, args


def test_tint_grey_and_grey_with_alpha(canvas):
    p.background("white")
    g = solid("white")
    p.tint(128)
    p.image(g, 0, 0)
    assert near(px(canvas, 5, 5), (128, 128, 128, 255))
    p.tint(0, 0)                              # black, fully transparent: nothing is drawn
    p.image(g, 0, 0, 20, 20)
    assert near(px(canvas, 5, 5), (128, 128, 128, 255))


def test_tint_follows_the_colour_mode(canvas):
    g = solid("white")
    p.color_mode("hsb", 360, 100, 100, 1)
    p.tint(0, 100, 100)                       # red in hsb
    p.image(g, 0, 0)
    assert px(canvas, 5, 5)[:3] == (255, 0, 0)
    p.color_mode("rgb", 1)
    p.tint(0, 1, 0)
    p.image(g, 0, 0)
    assert px(canvas, 5, 5)[:3] == (0, 255, 0)


def test_a_gradient_is_not_a_tint(canvas):
    with pytest.raises(ValueError, match="gradient"):
        p.tint(p.linear_gradient(0, 0, 10, 0, ["red", "blue"]))


def test_bad_tint_values(canvas):
    with pytest.raises(ValueError):
        p.tint("red", 100)
    with pytest.raises(TypeError):
        p.tint(True, 1, 2)


def test_tint_does_not_touch_shapes_or_text(canvas):
    p.tint("red")
    p.no_stroke()
    p.fill("white")
    p.rect(0, 0, 10, 10)
    p.text_size(30)
    p.text("W", 40, 0)
    assert px(canvas, 5, 5) == (255, 255, 255, 255)
    seen = {px(canvas, x, y)[:3] for x in range(40, 70) for y in range(0, 35)}
    assert (255, 255, 255) in seen                       # solid white text, not red
    assert not any(c[1] == 0 and c[2] == 0 and c[0] > 0 for c in seen)


def test_tint_combines_with_opacity_by_multiplying(canvas):
    p.background("white")
    g = solid("black")
    p.tint(255, 128)
    p.opacity(128)
    p.image(g, 0, 0)
    assert near(px(canvas, 5, 5), (191, 191, 191, 255), 1)


def test_tint_combines_with_blend_mode(canvas):
    p.background((200, 200, 200))
    g = solid((100, 100, 100))
    p.blend_mode("multiply")
    p.tint(128, 255, 255)
    p.image(g, 0, 0)
    # the tinted picture (50, 100, 100) multiplied with the background (200, 200, 200)
    assert near(px(canvas, 5, 5), (39, 78, 78, 255), 1)


# ---- P5: saved state, pictures, frames -------------------------------------------------------
def test_tint_is_saved_by_push_and_pop(canvas, sketch):
    p.tint("red")
    p.push()
    p.tint("blue")
    assert sketch.style.tint.rgba == (0, 0, 255, 255)
    p.pop()
    assert sketch.style.tint.rgba == (255, 0, 0, 255)
    with p.saved_state():
        p.no_tint()
        assert sketch.style.tint is None
    assert sketch.style.tint is not None


def test_a_picture_has_its_own_tint(canvas):
    g = solid("white")
    h = p.create_graphics(20, 20)
    p.tint("red")                              # the window's tint is not h's
    assert h._sketch.style.tint is None
    h.tint("blue")
    h.image(g, 0, 0)
    p.no_tint()
    p.image(h, 0, 0)
    assert px(canvas, 5, 5) == (0, 0, 255, 255)
    assert "tint" in p.picture.ALLOWED_METHODS and "no_tint" in p.picture.ALLOWED_METHODS


def test_a_pictures_tint_persists_between_flushes():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(40, 40)
    h = p.create_graphics(20, 20)
    h.tint("green")
    h._flush()
    assert h._sketch.style.tint.rgba == (0, 255, 0, 255)


def test_tint_persists_across_frames_like_fill():
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    seen = []

    def setup():
        p.size(40, 40)
        p.tint("red")

    def draw():
        seen.append(s.style.tint)

    s.run_namespace({"setup": setup, "draw": draw}, max_frames=3)
    assert len(seen) == 3 and all(t is not None and t.rgba == (255, 0, 0, 255) for t in seen)


# ---- P5: IR ----------------------------------------------------------------------------------
def test_image_op_records_tint_only_when_set(canvas, sketch):
    g = solid("white")
    p.image(g, 0, 0)
    d = ir.op_to_jsonable(last(sketch))
    assert "tint" not in d and not {"sx", "sy", "sw", "sh"} & set(d)
    p.tint(255, 0, 0, 128)
    p.image(g, 0, 0)
    d = ir.op_to_jsonable(last(sketch))
    assert d["tint"] == [255, 0, 0, 128]


def test_tint_and_part_round_trip_through_json(canvas, sketch):
    g = solid("white")
    p.tint(10, 20, 30, 40)
    p.image(g, 1, 2, 3, 4, 5, 6, 7, 8)
    p.rect(0, 0, 5, 5)
    ops = sketch.frame.ops
    again = ir.Frame.from_jsonable(ir.Frame(list(ops)).to_jsonable()).ops
    assert again[-2].tint == ops[-2].tint
    assert (again[-2].sx, again[-2].sy, again[-2].sw, again[-2].sh) == (5, 6, 7, 8)
    assert again[-1].style.tint.rgba == (10, 20, 30, 40)


def test_default_state_does_not_serialise_tint(canvas, sketch):
    p.rect(0, 0, 5, 5)
    assert "tint" not in ir.op_to_jsonable(last(sketch))["style"]


# ---- P5: PDF and SVG -------------------------------------------------------------------------
def test_pdf_with_a_tinted_image_is_written(tmp_path):
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(60, 60)
    g = solid("white", 30, 30)
    plain, tinted = tmp_path / "plain.pdf", tmp_path / "tinted.pdf"

    def draw():                                # saving happens at the end of each frame
        p.background("white")
        if s.frame_count == 0:
            p.image(g, 0, 0, 30, 30)
            p.save(str(plain))
        else:
            p.tint(255, 0, 0, 100)
            p.image(g, 0, 0, 30, 30)
            p.save(str(tinted))

    s.run_namespace({"draw": draw}, max_frames=2)
    assert tinted.read_bytes()[:5] == b"%PDF-"
    assert tinted.stat().st_size > 0 and tinted.read_bytes() != plain.read_bytes()


def test_svg_with_a_tinted_part_is_written(tmp_path):
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(60, 60)
    g = halves()
    out = tmp_path / "t.svg"

    def draw():
        p.tint("green")
        p.image(g, 0, 0, 40, 20, 5, 0, 10, 10)
        p.save(str(out))

    s.run_namespace({"draw": draw}, max_frames=1)
    assert b"<svg" in out.read_bytes()


def test_pdf_part_of_a_picture_replays_its_drawing(tmp_path):
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(60, 60)
    g = halves()
    out = tmp_path / "part.pdf"

    def draw():
        p.image(g, 0, 0, 40, 20, 0, 0, 10, 10)
        p.save(str(out))

    s.run_namespace({"draw": draw}, max_frames=1)
    data = out.read_bytes()
    assert data[:5] == b"%PDF-" and b"/Subtype /Image" not in data


# ---- P6: part of a picture ------------------------------------------------------------------
def test_a_part_without_a_size_is_drawn_at_its_own_size(canvas, sketch):
    g = halves()
    p.image(g, 50, 10, None, None, 10, 0, 10, 10)        # the blue half
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (50, 10, 10, 10)
    assert (op.sx, op.sy, op.sw, op.sh) == (10, 0, 10, 10)
    assert px(canvas, 55, 15) == (0, 0, 255, 255)
    assert px(canvas, 49, 15) == (0, 0, 0, 0) and px(canvas, 61, 15) == (0, 0, 0, 0)


def test_a_part_is_enlarged_into_the_destination_size(canvas):
    g = halves()
    p.image(g, 0, 0, 40, 40, 5, 0, 10, 10)               # half red, half blue, 4 times larger
    assert px(canvas, 10, 20) == (255, 0, 0, 255)
    assert px(canvas, 30, 20) == (0, 0, 255, 255)
    assert px(canvas, 41, 20) == (0, 0, 0, 0)            # clipped to the box


def test_a_part_stays_inside_its_box(canvas):
    g = halves()
    p.image(g, 100, 50, 20, 20, 0, 0, 5, 5)              # only red
    assert px(canvas, 110, 60) == (255, 0, 0, 255)
    assert px(canvas, 125, 60) == (0, 0, 0, 0) and px(canvas, 99, 60) == (0, 0, 0, 0)


def test_a_source_reaching_outside_is_clipped_and_keeps_its_place(canvas, sketch):
    g = halves()                                          # 20 x 10
    p.image(g, 100, 50, 80, 80, -5, -5, 10, 10)          # scale 8: only (0..5, 0..5) exists
    op = last(sketch)
    assert (op.sx, op.sy, op.sw, op.sh) == (0, 0, 5, 5)
    assert (op.x, op.y, op.width, op.height) == (140, 90, 40, 40)
    assert px(canvas, 145, 95) == (255, 0, 0, 255)
    assert px(canvas, 120, 70) == (0, 0, 0, 0)            # where the missing part would have been


def test_a_source_past_the_far_edge_is_clipped(canvas, sketch):
    g = halves()
    p.image(g, 0, 0, 60, 30, 15, 5, 10, 10)               # scale 6; only 5 x 5 exist
    op = last(sketch)
    assert (op.sx, op.sy, op.sw, op.sh) == (15, 5, 5, 5)
    assert (op.x, op.y, op.width, op.height) == (0, 0, 30, 15)
    assert px(canvas, 10, 10) == (0, 0, 255, 255)
    assert px(canvas, 40, 10) == (0, 0, 0, 0)


def test_a_source_wholly_outside_draws_nothing(canvas, sketch):
    g = halves()
    n = len(sketch.frame)
    p.image(g, 0, 0, 20, 20, 100, 100, 10, 10)
    assert len(sketch.frame) == n


@pytest.mark.parametrize("mode, args, expected_box", [
    ("corner", (30, 20, 40, 20), (30, 20, 40, 20)),
    ("center", (50, 30, 40, 20), (30, 20, 40, 20)),
    ("corners", (30, 20, 70, 40), (30, 20, 40, 20)),
])
def test_part_under_each_image_mode(canvas, sketch, mode, args, expected_box):
    g = halves()
    p.image_mode(mode)
    p.image(g, *args, 0, 0, 20, 10)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == expected_box
    assert (op.sx, op.sy, op.sw, op.sh) == (0, 0, 20, 10)


def test_part_without_a_destination_size_under_center(canvas, sketch):
    g = halves()
    p.image_mode("center")
    p.image(g, 50, 50, None, None, 10, 0, 10, 10)         # the box is sw x sh, centred on (50, 50)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (45, 45, 10, 10)


def test_part_without_a_destination_size_under_corners_is_an_error(canvas):
    g = halves()
    p.image_mode("corners")
    with pytest.raises(ValueError, match="corners"):
        p.image(g, 0, 0, None, None, 0, 0, 5, 5)


def test_clipping_under_center_keeps_the_place(canvas, sketch):
    g = halves()                                           # 20 x 10
    p.image_mode("center")
    p.image(g, 50, 50, 20, 20, 15, 0, 10, 10)             # box (40, 40, 20, 20), scale 2; 5 px visible
    op = last(sketch)
    assert (op.sx, op.sw) == (15, 5) and (op.x, op.width) == (40, 10)


def test_source_numbers_are_all_or_nothing(canvas):
    g = halves()
    with pytest.raises(ValueError, match="all four"):
        p.image(g, 0, 0, 10, 10, 1, 2)
    with pytest.raises(ValueError, match="all four"):
        p.image(g, 0, 0, 10, 10, sx=1, sy=2, sw=3)


@pytest.mark.parametrize("sw, sh", [(0, 5), (5, 0), (-1, 5), (5, -2)])
def test_source_size_must_be_above_zero(canvas, sw, sh):
    g = halves()
    with pytest.raises(ValueError, match="above 0"):
        p.image(g, 0, 0, 10, 10, 0, 0, sw, sh)


def test_source_numbers_must_be_numbers(canvas):
    g = halves()
    with pytest.raises(TypeError):
        p.image(g, 0, 0, 10, 10, "a", 0, 5, 5)


def test_a_whole_picture_keeps_its_old_numbers(canvas, sketch):
    g = halves()
    p.image(g, 3, 4)
    op = last(sketch)
    assert (op.x, op.y, op.width, op.height) == (3.0, 4.0, 20, 10)
    assert op.sx is None and op.tint is None


def test_part_works_with_transform_opacity_and_tint(canvas):
    p.background("white")
    g = halves()
    p.translate(100, 0)
    p.opacity(128)
    p.tint("red")
    p.image(g, 0, 0, 20, 20, 0, 0, 10, 10)                 # the red half, red tint, half see-through
    r, gr, b, a = px(canvas, 110, 10)
    assert a == 255 and r == 255 and abs(gr - 127) <= 1
    assert px(canvas, 90, 10) == (255, 255, 255, 255)      # nothing leaked left of the box


def test_part_follows_a_clip(canvas):
    g = halves()
    clip_area = p.path().move_to(0, 0).line_to(20, 0).line_to(20, 40).line_to(0, 40).close()
    p.push()
    p.clip(clip_area)
    p.image(g, 0, 0, 40, 40, 0, 0, 20, 10)                 # the whole picture, 2 times larger
    p.pop()
    assert px(canvas, 10, 10) == (255, 0, 0, 255)
    assert px(canvas, 30, 10) == (0, 0, 0, 0)


def test_g_image_with_parts_and_tint(canvas):
    src = halves()
    dst = p.create_graphics(40, 40)
    dst.tint("lime")
    dst.image(src, 0, 0, 40, 40, 10, 0, 10, 10)            # the blue half, tinted lime: black
    p.image(dst, 0, 0)
    assert px(canvas, 10, 10) == (0, 0, 0, 255)
    dst2 = p.create_graphics(40, 40)
    dst2.image(src, 0, 0, 40, 40, 10, 0, 10, 10)
    p.image(dst2, 100, 0)
    assert px(canvas, 110, 10) == (0, 0, 255, 255)


def test_picture_image_signature_accepts_parts():
    names = list(inspect.signature(Picture.image).parameters)
    assert names[-4:] == ["sx", "sy", "sw", "sh"]


def test_replayed_drawing_of_a_part_lands_in_the_same_place(canvas, sketch):
    """What a PDF/SVG target replays must match the raster picture: the part fills its box."""
    import cairo
    from funground.renderers.cairo2d import CairoRenderer

    g = halves()
    p.image(g, 50, 10, 40, 40, 5, 0, 10, 10)               # half red, half blue, 4 times larger
    op = last(sketch)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
    ctx = cairo.Context(surface)
    renderer = CairoRenderer()
    renderer._base_matrix = ctx.get_matrix()
    renderer._replay_image_history(ctx, op, op.snapshot, 1.0)
    surface.flush()
    data = bytes(surface.get_data())

    def at(x, y):
        b, gr, r, a = data[(y * 100 + x) * 4:(y * 100 + x) * 4 + 4]
        return (r, gr, b, a)

    assert at(60, 30) == (255, 0, 0, 255) and at(80, 30) == (0, 0, 255, 255)
    assert at(95, 30) == (0, 0, 0, 0) and at(45, 30) == (0, 0, 0, 0)
