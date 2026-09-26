"""Off-screen graphics (S-052, contract P1-P3): pictures, image() and the Image IR op."""
from __future__ import annotations

import json

import pytest

import funground as p
from funground import api, ir
from funground.picture import Picture
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def fresh(width=100, height=100):
    """A fresh headless sketch with a window already open, size (width, height)."""
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(width, height)
    return s


def run(s, draw, max_frames=1):
    s.run_namespace({"draw": draw}, max_frames=max_frames)
    return s.last_frame


def main_px(frame, x, y):
    (w, _h), rgb = frame
    i = (y * w + x) * 3
    return tuple(rgb[i:i + 3])


def picture_px(g: Picture, x: int, y: int) -> tuple[int, int, int, int]:
    """Flush *g* and read one pixel of its own persistent surface as (r, g, b, a)."""
    g._flush()
    surf = g._sketch._renderer.surface
    surf.flush()
    data = surf.get_data()
    stride = surf.get_stride()
    i = y * stride + x * 4
    b, gr, r, a = data[i], data[i + 1], data[i + 2], data[i + 3]
    return (r, gr, b, a)


# ---- P1: create_graphics ----------------------------------------------------------------
def test_new_picture_is_transparent():
    fresh(30, 30)
    g = p.create_graphics(10, 10)
    assert picture_px(g, 3, 3) == (0, 0, 0, 0)


def test_repr_and_size():
    fresh(30, 30)
    g = p.create_graphics(200, 100)
    assert repr(g) == "<Picture 200 x 100>"
    assert (g.width, g.height) == (200, 100)


def test_create_graphics_needs_the_window_first():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with pytest.raises(RuntimeError, match="f.size"):
        p.create_graphics(10, 10)


@pytest.mark.parametrize("w, h", [(0, 10), (-1, 10), (10, 0), (1.5, 10), (10, "10"), (True, 10)])
def test_create_graphics_needs_positive_whole_numbers(w, h):
    fresh(30, 30)
    with pytest.raises(ValueError):
        p.create_graphics(w, h)


def test_hidpi_picture_is_physically_larger_and_placed_sharp(monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    s = fresh(40, 40)
    g = p.create_graphics(10, 10)
    assert (g._sketch._renderer.surface.get_width(), g._sketch._renderer.surface.get_height()) == (20, 20)
    g.no_stroke()
    g.fill("red")
    g.rect(0, 0, 10, 10)

    def draw():
        p.background("white")
        p.image(g, 0, 0)

    (w, h), rgb = run(s, draw)
    assert (w, h) == (80, 80)               # 40 logical x scale 2
    frame = ((w, h), rgb)
    assert main_px(frame, 10, 10) == (255, 0, 0)
    assert main_px(frame, 79, 79) == (255, 255, 255)


# ---- P2: drawing on a picture -------------------------------------------------------------
def test_picture_has_its_own_state_and_transform_starting_at_defaults():
    fresh(30, 30)
    p.translate(10, 10)
    p.fill("red")
    g = p.create_graphics(20, 20)
    assert g._sketch.style.fill.rgba == (255, 255, 255, 255)     # white, not the main sketch's red
    assert g._sketch.style.stroke.rgba == (0, 0, 0, 255)
    g.no_stroke()
    g.fill("blue")
    g.rect(0, 0, 5, 5)                                    # unaffected by the main sketch's translate
    assert picture_px(g, 2, 2) == (0, 0, 255, 255)


def test_pixels_state_and_transform_persist_across_frames_and_flushes():
    s = fresh(30, 30)
    g = p.create_graphics(20, 20)
    g.no_stroke()
    g.translate(5, 5)
    g.fill("red")
    g.rect(0, 0, 5, 5)                     # lands at (5, 5) .. (10, 10)

    def draw_once():
        p.background("white")
        p.image(g, 0, 0)                   # flush #1: captures the red square, translate carries on

    run(s, draw_once)
    assert picture_px(g, 7, 7) == (255, 0, 0, 255)

    # No f.size()/setup() in between; draw again without re-translating: still translated.
    g.fill("blue")
    g.rect(0, 0, 2, 2)                     # should land at (5, 5) .. (7, 7), inside the red square

    def draw_again():
        p.background("white")
        p.image(g, 0, 0)                   # flush #2

    run(s, draw_again)
    assert picture_px(g, 6, 6) == (0, 0, 255, 255)          # the new blue square
    assert picture_px(g, 9, 9) == (255, 0, 0, 255)          # the old red square, untouched


def test_image_captures_content_at_the_call_not_later_drawing():
    s = fresh(60, 30)
    g = p.create_graphics(20, 20)
    g.no_stroke()
    g.fill("red")
    g.rect(0, 0, 20, 20)

    def draw():
        p.background("white")
        p.image(g, 0, 0)              # captures red
        g.fill("blue")
        g.rect(0, 0, 20, 20)          # changes g after the first call, in the same frame
        p.image(g, 20, 0)             # captures blue (a new call is a new snapshot)

    frame = run(s, draw)
    assert main_px(frame, 5, 5) == (255, 0, 0)
    assert main_px(frame, 25, 5) == (0, 0, 255)


def test_image_scales_to_width_and_height():
    s = fresh(80, 80)
    g = p.create_graphics(10, 10)
    g.no_stroke()
    g.fill("lime")
    g.rect(0, 0, 10, 10)

    def draw():
        p.background("white")
        p.image(g, 0, 0, 40, 40)

    frame = run(s, draw)
    assert main_px(frame, 20, 20) == (0, 255, 0)
    assert main_px(frame, 60, 60) == (255, 255, 255)


def test_targets_transform_and_clip_apply_to_image():
    s = fresh(80, 80)
    g = p.create_graphics(10, 10)
    g.no_stroke()
    g.fill("red")
    g.rect(0, 0, 10, 10)

    def draw():
        p.background("white")
        with p.saved_state():
            p.translate(30, 30)
            window = p.path().move_to(0, 0).line_to(5, 0).line_to(5, 5).line_to(0, 5).close()
            p.clip(window)
            p.image(g, 0, 0)

    frame = run(s, draw)
    assert main_px(frame, 32, 32) == (255, 0, 0)     # inside both the translate and the clip
    assert main_px(frame, 37, 37) == (255, 255, 255)  # outside the clip


def test_targets_blend_mode_and_opacity_apply_to_image():
    s = fresh(40, 40)
    g = p.create_graphics(40, 40)
    g.no_stroke()
    g.fill((128, 128, 128))
    g.rect(0, 0, 40, 40)

    def draw():
        p.background((128, 128, 128))
        p.blend_mode("multiply")
        p.image(g, 0, 0)

    frame = run(s, draw)
    assert main_px(frame, 20, 20)[0] < 128           # multiply(128, 128) darkens

    s2 = fresh(40, 40)
    g2 = p.create_graphics(40, 40)
    g2.no_stroke()
    g2.fill("black")
    g2.rect(0, 0, 40, 40)

    def draw2():
        p.background("white")
        p.opacity(128)
        p.image(g2, 0, 0)

    frame2 = run(s2, draw2)
    r, gr, b = main_px(frame2, 20, 20)
    assert abs(r - 127) <= 3 and r == gr == b


def test_pictures_inside_pictures_and_self_draw_is_an_error():
    fresh(60, 60)
    inner = p.create_graphics(10, 10)
    inner.no_stroke()
    inner.fill("red")
    inner.rect(0, 0, 10, 10)
    outer = p.create_graphics(30, 30)
    outer.background("white")
    outer.image(inner, 5, 5)
    assert picture_px(outer, 8, 8)[:3] == (255, 0, 0)

    with pytest.raises(ValueError, match="cannot be drawn onto itself"):
        outer.image(outer, 0, 0)


def test_a_non_picture_raises_type_error():
    fresh(20, 20)
    with pytest.raises(TypeError, match="later release"):
        p.image("not a picture", 0, 0)


def test_unknown_attributes_raise_attribute_error():
    fresh(20, 20)
    g = p.create_graphics(10, 10)
    for name in ("size", "run", "random", "noise", "lerp", "cursor", "frame_count", "no_such_thing"):
        with pytest.raises(AttributeError):
            getattr(g, name)


# ---- P3: history for vector export --------------------------------------------------------
def test_opaque_background_drops_the_history():
    fresh(30, 30)
    g = p.create_graphics(10, 10)
    g.no_stroke()
    g.fill("red")
    g.rect(0, 0, 10, 10)
    snap1 = g._snapshot()
    assert snap1.history is not None and len(snap1.history) == 1

    g.background("white")            # opaque: drops everything before it
    g.fill("blue")
    g.rect(0, 0, 5, 5)
    snap2 = g._snapshot()
    assert snap2.history is not None
    assert len(snap2.history) == 2
    assert isinstance(snap2.history[0], ir.Clear) and snap2.history[0].color.rgba == (255, 255, 255, 255)


def test_clear_also_drops_the_history():
    fresh(30, 30)
    g = p.create_graphics(10, 10)
    g.no_stroke()
    g.fill("red")
    g.rect(0, 0, 10, 10)
    g.clear()
    g.fill("blue")
    g.rect(0, 0, 5, 5)
    snap = g._snapshot()
    assert len(snap.history) == 2
    assert isinstance(snap.history[0], ir.Clear) and snap.history[0].color.rgba == (0, 0, 0, 0)


def test_history_becomes_unavailable_past_ten_thousand_ops_and_resumes_after_a_reset():
    fresh(30, 30)
    g = p.create_graphics(20, 20)
    g.background("white")
    g.no_stroke()
    for i in range(10005):
        g.fill((i % 255, 0, 0))
        g.point(i % 20, (i // 20) % 20)
    assert g._snapshot().history is None

    g.background("white")            # resumes collecting
    g.fill("blue")
    g.rect(0, 0, 5, 5)
    snap = g._snapshot()
    assert snap.history is not None
    assert len(snap.history) == 2


def test_pdf_export_of_a_picture_with_history_is_vector(tmp_path):
    s = fresh(60, 60)
    g = p.create_graphics(20, 20)
    g.no_stroke()
    g.fill("red")
    g.rect(0, 0, 20, 20)
    out = tmp_path / "frame.pdf"

    def draw():
        p.background("white")
        p.image(g, 0, 0)
        p.save(str(out))

    run(s, draw)
    data = out.read_bytes()
    assert b"/Subtype /Image" not in data


def test_pdf_export_falls_back_to_pixels_past_the_history_limit(tmp_path):
    s = fresh(60, 60)
    g = p.create_graphics(20, 20)
    g.background("white")
    g.no_stroke()
    for i in range(10005):
        g.fill((i % 255, 0, 0))
        g.point(i % 20, (i // 20) % 20)
    out = tmp_path / "frame.pdf"

    def draw():
        p.background("white")
        p.image(g, 0, 0)
        p.save(str(out))

    run(s, draw)
    data = out.read_bytes()
    assert b"/Subtype /Image" in data


# ---- IR: the Image op -----------------------------------------------------------------
def test_image_op_serialises_without_pixels_and_round_trips():
    s = fresh(30, 30)
    g = p.create_graphics(10, 10)

    def draw():
        p.background("white")
        p.image(g, 1, 2)

    run(s, draw)
    img_op = next(op for op in s.last_ops if isinstance(op, ir.Image))
    assert img_op.source == "graphics-1"
    assert isinstance(img_op.version, int) and img_op.version >= 0

    data = ir.op_to_jsonable(img_op)
    assert "snapshot" not in data
    assert "pixels" not in json.dumps(data)
    assert "blend_mode" not in data and "opacity" not in data     # defaults omitted

    back = ir.op_from_jsonable(data)
    assert back.snapshot is None
    assert back == img_op                  # snapshot is excluded from equality


def test_image_op_records_non_default_blend_and_opacity():
    s = fresh(30, 30)
    g = p.create_graphics(10, 10)

    def draw():
        p.background("white")
        p.push()
        p.opacity(100)
        p.blend_mode("multiply")
        p.image(g, 0, 0)
        p.pop()

    run(s, draw)
    img_op = next(op for op in s.last_ops if isinstance(op, ir.Image))
    data = ir.op_to_jsonable(img_op)
    assert data["blend_mode"] == "multiply" and data["opacity"] == 100


# ---- g.save() -----------------------------------------------------------------------
def test_save_writes_png_and_pdf_immediately(tmp_path):
    fresh(20, 20)
    g = p.create_graphics(10, 10)
    g.no_stroke()
    g.fill("red")
    g.rect(0, 0, 10, 10)
    png_path = tmp_path / "g.png"
    pdf_path = tmp_path / "g.pdf"

    g.save(str(png_path))
    g.save(str(pdf_path))

    assert png_path.exists() and png_path.stat().st_size > 0
    data = pdf_path.read_bytes()
    assert data.startswith(b"%PDF")
    assert b"/Subtype /Image" not in data       # a history is available here: stays vector
