"""p.save() and export replay (S-034)."""
from __future__ import annotations

import re

import cairo
import pygame
import pytest

import playground as p
from playground import api, ir
from playground.color import Color
from playground.export import format_of, save_frame
from playground.geometry import Path
from playground.state import GraphicsState


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
    src = src.replace("    p.background(\"white\")\n", f"    p.background(\"white\")\n    p.save(r'{out}')\n", 1)
    patched = tmp_path / "02_shapes_save.py"
    patched.write_text(src, encoding="utf-8")
    run_sketch(patched, frames=2)
    assert out.read_bytes()[:5] == b"%PDF-" and out.stat().st_size > 1000
