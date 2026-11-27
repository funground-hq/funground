"""p.save() and export replay (S-034)."""
from __future__ import annotations

import re

import cairo
import pygame
import pytest

import funground as p
from funground import api, ir
from funground.color import Color
from funground.export import format_of, save_frame
from funground.geometry import Path
from funground.state import GraphicsState


def test_format_validation_names_the_choices():
    assert format_of("x.PNG") == "png" and format_of("a/b.pdf") == "pdf" and format_of("c.svg") == "svg"
    with pytest.raises(ValueError, match=r"\.png, \.pdf, \.svg"):
        format_of("frame.jpg")


def test_save_frame_writes_valid_files(tmp_path):
    frame = ir.Frame([
        ir.Clear(Color(255, 255, 255)),
        ir.Save(), ir.ClipPath(Path.rect(0, 0, 40, 40)),
        ir.Circle(20, 20, 30, GraphicsState(fill=Color(255, 0, 0, 128))),
        ir.Restore(),
        ir.Text("Hi", 5, 45, Color(0, 0, 0), GraphicsState(text_size=14)),
    ])
    png, pdf, svg = (tmp_path / f"f.{e}" for e in ("png", "pdf", "svg"))
    for path in (png, pdf, svg):
        save_frame(frame, str(path), 80, 60)
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert pdf.read_bytes()[:5] == b"%PDF-"
    text = svg.read_text(encoding="utf-8")
    assert "<svg" in text and re.search(r'viewBox="0 0 80 60"|width="80(pt|px)?"', text)
    surf = cairo.ImageSurface.create_from_png(str(png))
    assert (surf.get_width(), surf.get_height()) == (80, 60)


def test_png_export_honours_backing_scale(tmp_path):
    frame = ir.Frame([ir.Clear(Color(0, 0, 255))])
    out = tmp_path / "s.png"
    save_frame(frame, str(out), 10, 10, scale=3)
    surf = cairo.ImageSurface.create_from_png(str(out))
    assert (surf.get_width(), surf.get_height()) == (30, 30)


def test_p_save_writes_the_frame_that_was_on_screen(tmp_path):
    out = tmp_path / "frame.png"

    def draw():
        p.background("navy")
        p.fill("gold")
        p.circle(50, 50, 40)
        if p.frame_count == 2:
            p.save(str(out))

    api.active_sketch().run_namespace({"draw": draw}, max_frames=4)
    assert out.exists()
    surf = cairo.ImageSurface.create_from_png(str(out))
    data, stride = surf.get_data(), surf.get_stride()
    i = 50 * stride + 50 * 4
    assert (data[i + 2], data[i + 1], data[i]) == (255, 215, 0)      # gold at the centre
    j = 5 * stride + 5 * 4
    assert (data[j + 2], data[j + 1], data[j]) == (0, 0, 128)        # navy background


def test_p_save_rejects_bad_extension_at_the_call_site(canvas):
    with pytest.raises(ValueError):
        p.save("frame.bmp")


def test_pdf_export_from_a_session1_sketch(tmp_path):
    from conftest import EXAMPLES, run_sketch

    out = tmp_path / "shapes.pdf"
    src = (EXAMPLES / "02_shapes.py").read_text(encoding="utf-8")
    src = src.replace("    f.background(\"white\")\n", f"    f.background(\"white\")\n    f.save(r'{out}')\n", 1)
    patched = tmp_path / "02_shapes_save.py"
    patched.write_text(src, encoding="utf-8")
    run_sketch(patched, frames=2)
    assert out.read_bytes()[:5] == b"%PDF-" and out.stat().st_size > 1000


def test_png_saves_what_is_on_screen_including_earlier_frames(tmp_path):
    """A sketch that paints without clearing: the PNG holds every frame's drawing."""
    import cairo

    from funground import api
    from funground.platform.headless import HeadlessPlatform
    from funground.sketch import Sketch

    out = tmp_path / "painting.png"
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))

    def setup():
        p.size(100, 50)
        p.background("white")

    def draw():
        p.no_stroke()
        p.fill("red")
        p.rect(p.frame_count * 30, 10, 20, 20)        # a new square each frame, nothing cleared
        if p.frame_count == 2:
            p.save(str(out))

    s.run_namespace({"setup": setup, "draw": draw}, max_frames=3)
    surf = cairo.ImageSurface.create_from_png(str(out))
    data, stride = surf.get_data(), surf.get_stride()

    def rgb(x, y):
        i = y * stride + x * 4
        return (data[i + 2], data[i + 1], data[i])

    assert rgb(10, 20) == (255, 0, 0) and rgb(40, 20) == (255, 0, 0) and rgb(70, 20) == (255, 0, 0)
    assert rgb(25, 20) == (255, 255, 255)


def test_svg_keeps_an_opaque_background_as_a_plain_fill(tmp_path):
    """S-249: background() was written as a mask and filter group, which load_svg drops (a black square)."""
    frame = ir.Frame([ir.Clear(Color(253, 245, 230)), ir.Circle(20, 20, 10, GraphicsState(fill=Color(255, 0, 0)))])
    svg = tmp_path / "f.svg"
    save_frame(frame, str(svg), 40, 40)
    text = svg.read_text(encoding="utf-8")
    assert "<filter" not in text and "<mask" not in text
    picture = p.load_svg(str(svg))
    assert picture.get(1, 1) == Color(253, 245, 230)


def test_a_see_through_background_still_replaces(tmp_path):
    """A background with alpha below 255 replaces what was there; it does not blend with it."""
    frame = ir.Frame([ir.Clear(Color(255, 0, 0)), ir.Clear(Color(0, 0, 255, 0))])
    png = tmp_path / "f.png"
    save_frame(frame, str(png), 10, 10)
    surf = cairo.ImageSurface.create_from_png(str(png))
    assert bytes(surf.get_data()[:4]) == b"\x00\x00\x00\x00"


def test_a_saved_svg_keeps_the_bare_size_so_it_matches_the_window(tmp_path):
    """Contract R20, D-132: a screen sketch shows in a browser at the size of its window."""
    path = tmp_path / "screen.svg"
    save_frame(ir.Frame([ir.Clear(Color(255, 255, 255))]), str(path), 640, 400)
    head = re.search(r"<svg[^>]*>", path.read_text(encoding="utf-8")).group(0)
    assert 'width="640"' in head and 'height="400"' in head and 'viewBox="0 0 640 400"' in head
    picture = p.load_svg(str(path))
    assert (picture.width, picture.height) == (640, 400)


def test_a_saved_pdf_keeps_the_real_size(tmp_path):
    """Contract R20, D-132: a PDF is the true-size file. The canvas is in whole units, hence the tolerance."""
    from pypdf import PdfReader

    side = int(p.mm(100))
    path = tmp_path / "real.pdf"
    save_frame(ir.Frame([ir.Clear(Color(255, 255, 255))]), str(path), side, side)
    page = PdfReader(str(path)).pages[0].mediabox
    assert float(page.width) * 25.4 / 72 == pytest.approx(100, abs=0.5)
    assert float(page.height) * 25.4 / 72 == pytest.approx(100, abs=0.5)


def _images_in(pdf_path) -> int:
    """How many pictures the PDF stores (a picture with see-through parts is stored with its mask: two objects)."""
    return pdf_path.read_bytes().count(b"/Subtype /Image")


def test_a_picture_drawn_many_times_is_stored_once_in_a_pdf(tmp_path, caplog):
    """S-321: a cut-out puppet draws one drawing again and again, each time clipped to one piece. The PDF stores the
    drawing once, not once per piece (a flipbook page was 2.5 MB, 48 KB after), and saving says nothing about it."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 60, 40)          # the drawing: a red dot on white
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(1, 1, 1)
    ctx.paint()
    ctx.set_source_rgb(1, 0.4, 0.3)
    ctx.arc(30, 20, 15, 0, 6.3)
    ctx.fill()
    surface.write_to_png(str(tmp_path / "drawing.png"))
    once, many, two = (tmp_path / f"{name}.pdf" for name in ("once", "many", "two"))

    pictures = {}

    def draw():                                                     # each file is the frame it is saved in
        if not pictures:
            pictures["drawing"] = p.load_image(str(tmp_path / "drawing.png"))
            pictures["other"] = p.load_image(str(tmp_path / "drawing.png"))
            pictures["other"].remove_color("white")                  # different pixels: a picture of its own
            p.size(400, 300)
        p.background("white")
        p.image(pictures["drawing"], 0, 0)
        if p.frame_count == 1:
            p.save(str(once))
            return
        for n in range(80):                                         # a flipbook page: 8 puppets of 10 pieces
            with p.saved_state():
                p.clip(p.path().rect(n * 20, 0, 20, 300))
                p.image(pictures["drawing"], n * 18, n * 12)
        if p.frame_count == 2:
            p.save(str(many))
            return
        p.image(pictures["other"], 300, 200)
        p.save(str(two))

    with caplog.at_level("WARNING"):
        api.active_sketch().run_namespace({"draw": draw}, max_frames=3)
    assert _images_in(many) == _images_in(once) >= 1
    assert many.stat().st_size < 2 * once.stat().st_size
    assert _images_in(two) > _images_in(many)                       # a different picture is kept as well
    assert not [r for r in caplog.records if "Multiple definitions" in r.getMessage()]


def test_pictures_on_a_pdf_share_one_surface_with_no_mime_data(monkeypatch):
    """S-339 (D-173): the same pixels are painted from one surface, which carries no mime data (pycairo's mime-data
    clean-up wrote to freed memory once a PDF's copy outlived the surface: Python crashed in the browser). The cache
    keeps the newest pictures within its bound, and always the one just drawn."""
    from funground.renderers import cairo2d
    renderer = cairo2d.CairoRenderer()
    blank, red = bytes(20 * 20 * 4), bytes([0, 0, 255, 255]) * (20 * 20)
    surface = cairo.PDFSurface(None, 200, 200)
    ctx = cairo.Context(surface)
    for _ in range(40):
        renderer._paint_picture(ctx, blank, 20, 20, 0, 0, 20, 20, 1.0, False)
    assert len(renderer._picture_surfaces) == 1
    (img,) = renderer._picture_surfaces.values()
    assert img.get_mime_data(cairo.MIME_TYPE_UNIQUE_ID) is None
    monkeypatch.setattr(cairo2d, "PICTURE_SURFACE_CACHE_BYTES", 20 * 20 * 4)     # room for one picture
    renderer._paint_picture(ctx, red, 20, 20, 0, 0, 20, 20, 1.0, False)
    assert len(renderer._picture_surfaces) == 1 and renderer._picture_bytes == 20 * 20 * 4
    surface.finish()
    image = cairo.ImageSurface(cairo.FORMAT_ARGB32, 20, 20)                     # a raster target keeps nothing
    renderer._paint_picture(cairo.Context(image), blank, 20, 20, 0, 0, 20, 20, 1.0, False)
    assert len(renderer._picture_surfaces) == 1
