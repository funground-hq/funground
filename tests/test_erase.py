"""erase() and no_erase() (S-107, contract F15)."""
from __future__ import annotations

import json

import cairo
import pytest

import funground as p
from funground import api, ir
from funground.color import Color
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

ORANGE = (200, 100, 50)


def run(draw, size=(100, 100), frames=1):
    """Run *draw* once on a headless sketch; return the sketch."""
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(*size), "draw": draw}, max_frames=frames)
    return s


def alpha_at(x, y):
    return p.get(x, y).a


# ---- strengths ----------------------------------------------------------------------------
def test_full_strength_makes_pixels_fully_transparent():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.no_stroke()
        p.erase()
        p.rect(20, 20, 40, 40)
        p.no_erase()
        seen["hole"], seen["outside"] = p.get(40, 40), p.get(80, 80)

    run(draw)
    assert seen["hole"] == Color(0, 0, 0, 0)
    assert seen["outside"] == Color(*ORANGE, 255)


def test_half_strength_takes_away_about_half_the_alpha():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.no_stroke()
        p.erase(128)
        p.rect(0, 0, 50, 50)
        seen["a"] = alpha_at(25, 25)

    run(draw)
    assert abs(seen["a"] - 127) <= 2


def test_zero_strength_changes_nothing():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.no_stroke()
        p.erase(0, 0)
        p.rect(0, 0, 50, 50)
        seen["a"] = alpha_at(25, 25)

    run(draw)
    assert seen["a"] == 255


def test_colour_is_ignored_while_erasing():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.no_stroke()
        p.fill(0, 255, 0)
        p.erase()
        p.circle(30, 30, 30)       # the green fill does not matter
        p.fill(255, 0, 255)
        p.rect(60, 60, 20, 20)
        seen["a"] = (p.get(30, 30), p.get(70, 70))

    run(draw)
    assert seen["a"] == (Color(0, 0, 0, 0), Color(0, 0, 0, 0))


def test_fill_and_stroke_have_their_own_strengths():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.stroke_width(6)
        p.erase(100, 255)
        p.rect(20, 20, 60, 60)
        seen["inside"] = alpha_at(50, 50)
        seen["edge"] = alpha_at(20, 50)        # the middle of the outline
        seen["fill_only"] = alpha_at(30, 50)

    run(draw)
    assert seen["edge"] == 0
    assert abs(seen["inside"] - (255 - 100)) <= 2
    assert abs(seen["fill_only"] - (255 - 100)) <= 2


def test_no_fill_and_no_stroke_are_respected():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.no_fill()
        p.stroke_width(4)
        p.erase()
        p.rect(20, 20, 60, 60)
        seen["inside"] = alpha_at(50, 50)
        seen["edge"] = alpha_at(20, 50)

    run(draw)
    assert seen["inside"] == 255 and seen["edge"] == 0


@pytest.mark.parametrize("bad", [-1, 256, 300.5, "255", None, True])
def test_strengths_outside_0_to_255_are_errors(bad):
    run(lambda: None)
    with pytest.raises(ValueError, match="erase"):
        p.erase(bad)
    with pytest.raises(ValueError, match="erase"):
        p.erase(255, bad)


def test_a_bad_call_leaves_the_state_alone():
    run(lambda: None)
    with pytest.raises(ValueError):
        p.erase(999)
    assert api.active_sketch().style.erasing is None


# ---- no_erase, push and pop ----------------------------------------------------------------
def test_no_erase_paints_again():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.no_stroke()
        p.erase()
        p.rect(0, 0, 40, 100)
        p.no_erase()
        p.fill(0, 0, 255)
        p.rect(40, 0, 40, 100)
        seen["erased"], seen["painted"] = p.get(20, 50), p.get(60, 50)

    run(draw)
    assert seen["erased"] == Color(0, 0, 0, 0)
    assert seen["painted"] == Color(0, 0, 255, 255)


def test_push_and_pop_save_and_restore_erasing():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.no_stroke()
        p.push()
        p.erase()
        p.rect(0, 0, 30, 100)
        p.pop()
        p.fill(0, 0, 255)
        p.rect(30, 0, 30, 100)
        p.erase()
        p.push()
        p.no_erase()
        p.fill(0, 255, 0)
        p.rect(60, 0, 20, 100)
        p.pop()
        p.rect(80, 0, 20, 100)         # erasing again after the pop
        seen["a"] = [p.get(x, 50) for x in (10, 40, 70, 90)]

    run(draw)
    assert seen["a"] == [Color(0, 0, 0, 0), Color(0, 0, 255, 255), Color(0, 255, 0, 255), Color(0, 0, 0, 0)]


def test_erasing_stays_on_across_frames_like_any_style_setting():
    states = []

    def draw():
        states.append(api.active_sketch().style.erasing)
        p.erase(10)

    run(draw, frames=2)
    assert states == [None, (10, 255)]


# ---- interactions ----------------------------------------------------------------------------
def test_blend_mode_opacity_and_shadow_are_ignored_while_erasing():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.no_stroke()
        p.blend_mode("multiply")
        p.opacity(30)
        p.shadow(8, 8, 4)
        p.erase()
        p.rect(10, 10, 30, 30)
        seen["hole"] = p.get(20, 20)
        seen["where_a_shadow_would_be"] = p.get(48, 48)

    run(draw)
    assert seen["hole"] == Color(0, 0, 0, 0)               # opacity 30 would have erased almost nothing
    assert seen["where_a_shadow_would_be"] == Color(*ORANGE, 255)


def test_gradient_and_tint_are_ignored():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.no_stroke()
        p.fill(p.linear_gradient(0, 0, 100, 0, ["red", (0, 0, 255, 10)]))
        p.tint(255, 10)
        p.erase()
        p.rect(0, 0, 100, 100)
        seen["a"] = (alpha_at(5, 5), alpha_at(95, 95))

    run(draw)
    assert seen["a"] == (0, 0)


# ---- text and images -----------------------------------------------------------------------
def test_text_erases_its_glyph_shapes():
    seen = {}

    def draw():
        p.background(*ORANGE)
        p.text_size(80)
        p.erase()
        p.text("I", 20, 5)
        p.no_erase()
        holes = sum(1 for x in range(100) for y in range(100) if alpha_at(x, y) == 0)
        seen["holes"] = holes
        seen["corner"] = alpha_at(99, 99)

    run(draw)
    assert 100 < seen["holes"] < 4000       # some glyph pixels, nowhere near the whole canvas
    assert seen["corner"] == 255


def test_an_image_erases_by_its_own_alpha_times_the_strength():
    seen = {}

    def draw():
        g = p.create_graphics(40, 40)
        g.no_stroke()
        g.fill(255, 0, 0)
        g.rect(0, 0, 20, 40)           # the left half is opaque, the right half stays transparent
        p.background(*ORANGE)
        p.erase(128)
        p.image(g, 0, 0)
        p.no_erase()
        seen["a"] = (alpha_at(10, 10), alpha_at(30, 10), alpha_at(60, 60))

    run(draw)
    under_picture, beside_it, away = seen["a"]
    assert abs(under_picture - 127) <= 2
    assert beside_it == 255 and away == 255


# ---- pictures --------------------------------------------------------------------------------
def test_cutting_a_hole_in_an_overlay_picture_shows_the_background():
    seen = {}

    def draw():
        overlay = p.create_graphics(100, 100)
        overlay.background(0, 0, 255)
        overlay.no_stroke()
        overlay.erase()
        overlay.circle(50, 50, 40)
        overlay.no_erase()
        p.background(255, 255, 0)
        p.image(overlay, 0, 0)
        seen["hole"], seen["around"] = p.get(50, 50), p.get(5, 5)
        seen["state_off"] = overlay._sketch.style.erasing

    run(draw)
    assert seen["hole"] == Color(255, 255, 0, 255)
    assert seen["around"] == Color(0, 0, 255, 255)
    assert seen["state_off"] is None


def test_a_picture_keeps_its_own_erasing_state():
    seen = {}

    def draw():
        g = p.create_graphics(20, 20)
        g.erase(77, 33)
        seen["picture"] = g._sketch.style.erasing
        seen["window"] = api.active_sketch().style.erasing

    run(draw)
    assert seen["picture"] == (77, 33) and seen["window"] is None


# ---- the IR ----------------------------------------------------------------------------------
def test_the_ir_records_erasing_only_while_it_is_on():
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))

    def draw():
        p.rect(0, 0, 10, 10)
        p.erase(200, 50)
        p.rect(0, 0, 10, 10)
        p.no_erase()
        p.rect(0, 0, 10, 10)

    s.run_namespace({"setup": lambda: p.size(20, 20), "draw": draw}, max_frames=1)
    rects = [op for op in s.last_ops if type(op) is ir.Rect]
    texts = [json.dumps(ir.op_to_jsonable(op)) for op in rects]
    assert "erasing" not in texts[0] and "erasing" not in texts[2]
    assert '"erasing": [200, 50]' in texts[1]
    assert ir.op_from_jsonable(json.loads(texts[1])) == rects[1]


def test_path_ops_record_the_strength_only_when_erasing():
    from funground.geometry import Path
    from funground.state import GraphicsState
    from funground.sketch import Sketch as S

    path = Path.rect(0, 0, 10, 10)
    plain = S._fill_op(path, GraphicsState())
    erasing = S._fill_op(path, GraphicsState(erasing=(90, 30)))
    stroking = S._stroke_op(path, GraphicsState(erasing=(90, 30)))
    assert "erase" not in ir.op_to_jsonable(plain)
    assert ir.op_to_jsonable(erasing)["erase"] == 90
    assert ir.op_to_jsonable(stroking)["erase"] == 30
    for op in (plain, erasing, stroking):
        assert ir.op_from_jsonable(json.loads(json.dumps(ir.op_to_jsonable(op)))) == op


# ---- export ----------------------------------------------------------------------------------
def test_png_keeps_the_transparency(tmp_path):
    out = tmp_path / "hole.png"

    def draw():
        p.background(*ORANGE)
        p.no_stroke()
        p.erase()
        p.circle(50, 50, 40)
        p.save(str(out))

    run(draw)
    surf = cairo.ImageSurface.create_from_png(str(out))
    data, stride = surf.get_data(), surf.get_stride()
    assert data[50 * stride + 50 * 4 + 3] == 0
    assert data[5 * stride + 5 * 4 + 3] == 255


@pytest.mark.parametrize("ext", ["pdf", "svg"])
def test_pdf_and_svg_are_written_without_error(tmp_path, ext):
    """Cairo expresses DEST_OUT in PDF as raster fallback and in SVG as filters; we only
    promise a valid file here (see the guide for what a viewer shows)."""
    out = tmp_path / f"hole.{ext}"

    def draw():
        p.background(*ORANGE)
        p.no_stroke()
        p.erase(200)
        p.circle(50, 50, 40)
        p.text("hi", 10, 10)
        p.save(str(out))

    run(draw)
    head = out.read_bytes()[:5]
    assert out.stat().st_size > 500
    assert head == b"%PDF-" if ext == "pdf" else b"<?xml" == head


def test_an_erasing_overlay_picture_leaves_a_hole_in_the_pdf(tmp_path):
    """PDF replays a picture's drawing as vectors, so a hole cut in an overlay does show the background."""
    pdfium = pytest.importorskip("pypdfium2")
    out = tmp_path / "overlay.pdf"

    def draw():
        overlay = p.create_graphics(100, 100)
        overlay.background(0, 0, 255)
        overlay.no_stroke()
        overlay.erase()
        overlay.circle(50, 50, 40)
        p.background(255, 255, 0)
        p.image(overlay, 0, 0)
        p.save(str(out))

    run(draw)
    img = pdfium.PdfDocument(str(out))[0].render(scale=1).to_pil().convert("RGB")
    assert img.getpixel((50, 50)) == (255, 255, 0)
    assert img.getpixel((5, 5)) == (0, 0, 255)


# ---- the window ------------------------------------------------------------------------------
def test_erased_pixels_present_exactly_like_clear():
    """The window shows what is under the canvas for transparent pixels; erase and clear leave the same pixels."""
    def erased():
        p.background(*ORANGE)
        p.erase()
        p.rect(0, 0, 100, 100)

    def cleared():
        p.background(*ORANGE)
        p.clear()

    a, b = run(erased), run(cleared)
    assert a.last_frame == b.last_frame
