"""Font collections, .ttc and .otc (story S-119; contract T11 and T18).

A collection holds several fonts in one file. `f.load_font(path, face=...)` picks one by number or
by style name, `f.system_font()` looks inside collections, and PDF and SVG text embed the face that
was used as a single font. Tests build a collection from two generated fonts; the one test that uses
a real system font is skipped when Nirmala.ttc is not there.
"""
from __future__ import annotations

import base64
import io
import os
import re
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

import funground as f
from funground import api, typography
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from fontmaker import make_collection, make_static_font


@pytest.fixture(autouse=True)
def _isolated_font_registry():
    saved, saved_paths = dict(typography._registry), dict(typography._path_to_key)
    yield
    typography._registry.clear()
    typography._registry.update(saved)
    typography._path_to_key.clear()
    typography._path_to_key.update(saved_paths)


def script(width=240, height=80):
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    f.size(width, height)
    f.background("white")
    f.fill("black")
    f.text_size(20)


def advance(font) -> int:
    """The width of the letter A in the font, in font units."""
    resource = font._resource()
    return resource.shape("A", 1000).glyphs[0].x_advance


def test_load_font_reads_the_first_face_of_a_collection(tmp_path):
    path = make_collection(tmp_path)
    font = f.load_font(path)
    assert font.style() == "Regular" and font.family() == "TestColl"
    assert advance(font) == 600
    assert f.load_font(path) == font                    # the same face again is the same font


def test_face_by_number_and_by_style_name(tmp_path):
    path = make_collection(tmp_path)
    second = f.load_font(path, face=1)
    assert second.style() == "Bold" and advance(second) == 700
    assert f.load_font(path, face="Bold") == second
    assert f.load_font(path, face="bold") == second
    assert f.load_font(path, face="TestColl Bold") == second
    assert f.load_font(path, face="Regular") == f.load_font(path, face=0)
    assert second != f.load_font(path)                  # two faces of one file are two fonts
    assert second.name != f.load_font(path).name


def test_a_bad_face_is_a_clear_error(tmp_path):
    path = make_collection(tmp_path)
    for bad in (2, -1):
        with pytest.raises(ValueError, match="2 faces"):
            f.load_font(path, face=bad)
    with pytest.raises(ValueError, match="no face called 'Italic'"):
        f.load_font(path, face="Italic")
    with pytest.raises(ValueError, match="face must be"):
        f.load_font(path, face=1.5)
    plain = make_static_font(tmp_path, "Plain")
    assert f.load_font(plain, face=0).style() == "Regular"
    with pytest.raises(ValueError, match="1 face"):
        f.load_font(plain, face=1)


def test_otc_files_load_too(tmp_path):
    path = make_collection(tmp_path, extension="otc")
    assert f.load_font(path, face=1).style() == "Bold"


def test_text_in_the_second_face_renders(tmp_path):
    path = make_collection(tmp_path)
    script()
    f.text_font(f.load_font(path, face=1), 30)
    run = typography.effective_font(api.active_sketch().style).shape("ABC", 30)
    assert [g.x_advance for g in run.glyphs] == [700, 700, 700]
    f.text("ABC", 10, 10)
    out = tmp_path / "second.png"
    f.save(str(out))
    from PIL import Image

    box = Image.open(out).convert("L").point(lambda v: 255 if v < 128 else 0).getbbox()
    assert box is not None
    assert box[2] > 10 + 2 * 30 * 0.7 * 0.8             # three wide letters: the second face's width


def test_system_font_finds_a_face_inside_a_collection(tmp_path, monkeypatch):
    make_collection(tmp_path, "Group Family")
    make_static_font(tmp_path, "Other")
    monkeypatch.setattr(typography, "_system_font_dirs", lambda: [str(tmp_path)])
    regular = f.system_font("group family")
    assert regular.style() == "Regular" and regular._resource().face == 0
    bold = f.system_font("Group Family Bold")
    assert bold.style() == "Bold" and bold._resource().face == 1
    assert bold._resource().path.endswith("Group Family.ttc")
    with pytest.raises(FileNotFoundError, match="Group Family Italic"):
        f.system_font("Group Family Italic")


def test_system_font_prefers_regular_even_when_it_is_the_later_face(tmp_path, monkeypatch):
    make_collection(tmp_path, "Backwards", styles=("Bold", "Regular"))
    monkeypatch.setattr(typography, "_system_font_dirs", lambda: [str(tmp_path)])
    font = f.system_font("Backwards")
    assert font.style() == "Regular" and font._resource().face == 1


def test_a_collection_face_goes_into_the_pdf_as_one_font(tmp_path):
    pytest.importorskip("pypdfium2")
    from pypdf import PdfReader
    from test_pdf_text import fonts, texts, words

    path = make_collection(tmp_path)
    script()
    f.text_font(f.load_font(path, face="Bold"), 30)
    f.text("ABC DE", 10, 10)
    out = tmp_path / "coll.pdf"
    f.save(str(out))
    (font,) = fonts(out)
    assert "TestColl" in str(font["/BaseFont"])
    descriptor = font["/DescendantFonts"][0].get_object()["/FontDescriptor"].get_object()
    data = descriptor["/FontFile2"].get_object().get_data()
    assert data[:4] != b"ttcf"                            # one font, not the collection
    embedded = TTFont(io.BytesIO(data))
    assert embedded["name"].getDebugName(2) == "Bold"    # the face that was used
    for engine in texts(out):
        assert words(engine[0]) == "ABC DE"
    assert len(PdfReader(str(out)).pages) == 1


def test_a_collection_face_goes_into_the_svg_as_a_font_face(tmp_path):
    path = make_collection(tmp_path)
    script()
    f.text_font(f.load_font(path, face=1), 30)
    f.text("ABC", 10, 10)
    out = tmp_path / "coll.svg"
    f.save(str(out))
    css = out.read_text(encoding="utf-8")
    found = re.findall(r"font-family: '([^']*)'; font-weight: (\w+);[^}]*?base64,([A-Za-z0-9+/=]+)", css)
    assert [(fam, weight) for fam, weight, _ in found] == [("TestColl", "normal")]
    data = base64.b64decode(found[0][2])
    assert data[:4] != b"ttcf"
    embedded = TTFont(io.BytesIO(data))
    assert embedded["name"].getDebugName(2) == "Bold"
    assert embedded["hmtx"]["A"][0] == 700                 # the second face's own tables


NIRMALA = "C:/Windows/Fonts/Nirmala.ttc"


@pytest.mark.skipif(not Path(NIRMALA).exists(), reason="Nirmala.ttc is not on this computer")
def test_nirmala_ui_shapes_telugu():
    font = f.system_font("Nirmala UI")
    assert font.family() == "Nirmala UI" and font.contains("నమస్తే")
    run = font._resource().shape("నమస్తే", 20)
    assert 0 < len(run.glyphs) < len("నమస్తే") and all(g.gid != 0 for g in run.glyphs)
    assert os.path.normcase(font._resource().path) == os.path.normcase(os.path.normpath(NIRMALA))
