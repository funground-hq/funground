"""CMYK colour (story S-170, contract rows S17, D4 and D5): f.cmyk(), exact inks in a PDF, sRGB for the rest.

The PDF is read back with pypdf (``pdfcolour.scan`` looks at every object, not only the ones a walk
from the page reaches) and, for what it looks like, drawn by pdfium.
"""
from __future__ import annotations

import math

import cairo
import pytest
from fontTools.ttLib.tables import _h_e_a_d as head_table
from pdfcolour import scan
from pypdf import PdfReader

import funground as f
from funground import api, ir
from funground.color import Color, cmyk_to_rgb
from funground.export import cmyk as standins_module
from funground.export import pdf_colour
from funground.export.cmyk import CmykStandins
from funground.export.pdf_colour import ColourError
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def script(width=200, height=120) -> Sketch:
    sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    sketch.size(width, height)
    return sketch


def close(got, want, places=5) -> bool:
    return all(abs(a - b) < 10 ** -places for a, b in zip(got, want)) and len(got) == len(want)


def has(operations, want, places=5) -> bool:
    return any(close(found, want, places) for found in operations)


# ---------------------------------------------------------------- the constructor (S17)
def test_cmyk_makes_a_colour_that_remembers_its_inks():
    c = f.cmyk(10, 20, 30, 40)
    assert isinstance(c, Color)
    assert c.cmyk == (10.0, 20.0, 30.0, 40.0)
    assert c.alpha == 255


@pytest.mark.parametrize("inks, rgb", [
    ((0, 0, 0, 0), (255, 255, 255)),
    ((0, 0, 0, 100), (0, 0, 0)),
    ((100, 100, 100, 100), (0, 0, 0)),
    ((100, 0, 0, 0), (0, 255, 255)),
    ((0, 100, 100, 0), (255, 0, 0)),
    ((0, 0, 0, 50), (128, 128, 128)),
    ((20, 40, 60, 10), (184, 138, 92)),
])
def test_screen_colour_is_the_simple_formula(inks, rgb):
    assert f.cmyk(*inks).rgb == rgb == cmyk_to_rgb(*inks)


def test_alpha_is_0_to_255_as_for_hsb():
    assert f.cmyk(0, 0, 0, 100, 128).alpha == 128
    assert f.cmyk(0, 0, 0, 100, 128.9).alpha == 128          # truncated, as colour numbers are (S1)
    with pytest.raises(ValueError):
        f.cmyk(0, 0, 0, 100, 256)
    with pytest.raises(ValueError):
        f.cmyk(0, 0, 0, 100, -1)


@pytest.mark.parametrize("bad", [-1, 100.5, 101, float("nan"), float("inf"), True, "50", None])
def test_a_bad_ink_is_a_clear_error(bad):
    for place in range(4):
        inks = [0, 0, 0, 0]
        inks[place] = bad
        with pytest.raises(ValueError, match=r"ink .* must be"):
            f.cmyk(*inks)


def test_inks_ignore_the_colour_mode():
    f.color_mode("hsb", 1)
    assert f.cmyk(100, 0, 0, 0).rgb == (0, 255, 255)
    assert f.cmyk(0, 0, 0, 0, 255).alpha == 255


def test_colours_with_the_same_rgb_but_different_inks_differ():
    assert f.cmyk(0, 0, 0, 100) != f.cmyk(100, 100, 100, 100) and f.cmyk(0, 0, 0, 100).rgb == f.cmyk(100, 100, 100, 100).rgb
    assert f.cmyk(1, 2, 3, 4) == f.cmyk(1, 2, 3, 4)
    assert f.cmyk(0, 0, 0, 100) != Color(0, 0, 0)
    assert f.hsb(10, 20, 30).cmyk is None and f.color("tomato").cmyk is None


def test_lerp_of_two_inked_colours_mixes_the_inks():
    mid = f.lerp_color(f.cmyk(0, 0, 0, 0, 0), f.cmyk(100, 50, 0, 20, 255), 0.5)
    assert mid.cmyk == (50.0, 25.0, 0.0, 10.0) and mid.alpha == 128
    assert f.lerp_color(f.cmyk(0, 0, 0, 0), "red", 0.5).cmyk is None


# ---------------------------------------------------------------- usable wherever a colour is
def test_every_colour_slot_takes_it_and_the_ops_keep_the_inks():
    s = script()
    ink = f.cmyk(0, 80, 100, 0)
    f.background(ink)
    f.fill(ink)
    f.stroke(f.cmyk(100, 0, 0, 0))
    f.shadow(2, 2, 3, f.cmyk(0, 0, 0, 100, 128))
    f.rect(1, 1, 5, 5)
    f.text("Hi", 10, 50)
    f.fill(f.linear_gradient(0, 0, 100, 0, [f.cmyk(100, 0, 0, 0), f.cmyk(0, 100, 0, 0)]))
    f.rect(1, 1, 5, 5)
    f.tint(f.cmyk(0, 50, 50, 0))
    g = f.create_graphics(4, 4)
    f.image(g, 0, 0)
    ops = list(s.frame)
    assert ops[0].color.cmyk == (0.0, 80.0, 100.0, 0.0)                     # background
    assert ops[1].style.fill == ink and ops[1].style.stroke.cmyk == (100.0, 0.0, 0.0, 0.0)
    assert ops[1].style.shadow[3].cmyk == (0.0, 0.0, 0.0, 100.0)
    assert ops[2].color.cmyk == (0.0, 80.0, 100.0, 0.0)                     # the text colour
    assert [stop.cmyk for _, stop in ops[3].style.fill.stops] == [(100.0, 0.0, 0.0, 0.0), (0.0, 100.0, 0.0, 0.0)]
    assert ops[-1].tint.cmyk == (0.0, 50.0, 50.0, 0.0)


def test_ir_snapshots_keep_the_inks_and_leave_rgb_alone():
    s = script()
    f.background(f.cmyk(0, 80, 100, 0, 200))
    f.fill(f.linear_gradient(0, 0, 100, 0, [f.cmyk(100, 0, 0, 0), "red"]))
    f.shadow(2, 2, 3, f.cmyk(0, 0, 0, 100))
    f.rect(1, 1, 5, 5)
    f.fill("tomato")
    f.rect(1, 1, 5, 5)
    data = s.frame.to_jsonable()
    assert data[0]["color"] == {"cmyk": [0.0, 80.0, 100.0, 0.0], "alpha": 200}
    assert data[-1]["style"]["fill"] == [255, 99, 71, 255]             # an RGB colour is as it was
    again = ir.Frame.from_jsonable(data)
    assert list(again) == list(s.frame)
    assert again.to_jsonable() == data


def test_png_shows_the_approximation(tmp_path):
    from PIL import Image
    script(20, 20)
    f.background(f.cmyk(0, 100, 100, 0))
    f.save(str(tmp_path / "a.png"))
    assert Image.open(tmp_path / "a.png").convert("RGB").getpixel((10, 10)) == (255, 0, 0)


def test_svg_shows_the_approximation(tmp_path):
    script(20, 20)
    f.background(f.cmyk(0, 100, 100, 0))
    f.save(str(tmp_path / "a.svg"))
    assert "rgb(100%, 0%, 0%)" in (tmp_path / "a.svg").read_text(encoding="utf-8")


# ---------------------------------------------------------------- the stand-ins
def test_a_standin_is_never_a_real_colour():
    """Real colours are n/255 = 257n/65535 to Cairo's 16 bits; a stand-in is k/65535 with k from 1 to 255."""
    palette = CmykStandins()
    for n in range(0, 2000, 7):
        rgb = palette.rgb_for((n % 100, (n * 3) % 100, (n * 7) % 100, 0.5 * (n % 200)))
        codes = [round(v * standins_module.SCALE) for v in rgb]
        assert all(1 <= code <= 255 for code in codes) and codes[2] >= 251 > max(codes[:2])
    for r in range(0, 256, 5):
        for g in range(0, 256, 17):
            for b in range(0, 256, 17):
                assert palette.inks_for(r / 255, g / 255, b / 255) is None


def test_the_same_inks_get_the_same_standin_and_read_back():
    palette = CmykStandins()
    first = palette.rgb_for((1.0, 2.0, 3.0, 4.0))
    other = palette.rgb_for((4.0, 3.0, 2.0, 1.0))
    assert palette.rgb_for((1.0, 2.0, 3.0, 4.0)) == first != other
    printed = tuple(float(f"{v:.9g}") for v in first)               # as Cairo writes it
    assert palette.inks_for(*printed) == (1.0, 2.0, 3.0, 4.0)
    assert len(palette) == 2


def test_a_look_alike_that_is_not_ours_is_an_error():
    palette = CmykStandins()
    palette.rgb_for((1.0, 2.0, 3.0, 4.0))
    with pytest.raises(ValueError, match="stand-in"):
        palette.inks_for(9 / 65535, 1 / 65535, 251 / 65535)           # a number this document never made
    with pytest.raises(ValueError, match="stand-in"):
        palette.inks_for(1 / 65535, 0.5, 0.5)                          # part stand-in


def test_one_document_has_room_for_many_inks_and_then_says_so(monkeypatch):
    palette = CmykStandins()
    monkeypatch.setattr(standins_module, "ROOM", 3)
    for i in range(3):
        palette.rgb_for((i, 0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="different cmyk"):
        palette.rgb_for((50.0, 0.0, 0.0, 0.0))


def test_many_distinct_inks_in_one_pdf_all_read_back(tmp_path):
    script(100, 100)
    f.no_stroke()
    wanted = [(i % 101, (i * 7) % 101, (i * 13) % 101, (i * 3) % 101) for i in range(700)]
    for inks in wanted:
        f.fill(f.cmyk(*inks))
        f.rect(1, 1, 5, 5)
    f.save(str(tmp_path / "many.pdf"))
    found = scan(tmp_path / "many.pdf")
    assert len({tuple(round(v, 4) for v in op) for op in found.ops["k"]}) == len(set(wanted))
    for inks in wanted[::50]:
        assert has(found.ops["k"], tuple(v / 100 for v in inks)), inks
    assert found.rgb == []


# ---------------------------------------------------------------- the PDF (D4)
def poster(path):
    """CMYK fills, a stroke, text and a gradient: the story's acceptance drawing."""
    script(300, 200)
    f.background(f.cmyk(0, 0, 0, 5))
    f.no_stroke()
    f.fill(f.cmyk(100, 20, 0, 5))
    f.rect(10, 10, 100, 80)
    f.fill(f.cmyk(0, 100, 100, 0, 128))                                 # opacity stays alpha
    f.rect(60, 50, 100, 80)
    f.fill(f.linear_gradient(0, 150, 300, 150, [f.cmyk(100, 0, 0, 0), f.cmyk(0, 100, 0, 0), f.cmyk(0, 0, 100, 0)]))
    f.rect(0, 150, 300, 40)
    f.stroke(f.cmyk(0, 0, 0, 100))
    f.stroke_width(3)
    f.no_fill()
    f.circle(250, 70, 40)
    f.no_stroke()
    f.fill(f.cmyk(0, 0, 0, 100))
    f.text_size(30)
    f.text("Ink", 20, 130)
    f.save(str(path))


def test_a_pdf_of_cmyk_fills_text_and_a_gradient_holds_exactly_those_inks(tmp_path):
    poster(tmp_path / "a.pdf")
    found = scan(tmp_path / "a.pdf")
    assert has(found.ops["k"], (0, 0, 0, 0.05))                          # background
    assert has(found.ops["k"], (1.0, 0.2, 0, 0.05))                      # fill
    assert has(found.ops["k"], (0, 1.0, 1.0, 0))                         # the translucent fill
    assert has(found.ops["k"], (0, 0, 0, 1.0))                           # the text: live text, so its fill is in a form
    assert has(found.ops["K"], (0, 0, 0, 1.0))                           # the stroke
    (space, colours), = [s for s in found.shadings if s[0] == "DeviceCMYK"]
    assert [tuple(round(v, 6) for v in c) for c in colours] == [(1, 0, 0, 0), (0, 1, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)]
    # no unintended RGB: no operator, no space, no stand-in left over
    assert found.rgb == [] and found.ops["rg"] == found.ops["RG"] == []
    assert "DeviceRGB" not in found.spaces and "ICCBased" not in found.spaces
    assert not found.has_output_intent


def test_opacity_is_still_an_alpha_in_the_file(tmp_path):
    poster(tmp_path / "a.pdf")
    reader = PdfReader(tmp_path / "a.pdf")
    states = reader.pages[0]["/Resources"]["/ExtGState"]
    alphas = {round(float(state.get_object().get("/ca", 1)), 2) for state in states.values()}
    assert 0.5 in alphas


def test_a_cmyk_only_pdf_has_cmyk_groups(tmp_path):
    poster(tmp_path / "a.pdf")
    reader = PdfReader(tmp_path / "a.pdf")
    groups = [reader.get_object(n).get("/Group") for n in sorted(k for g in reader.xref.values() for k in g)
              if hasattr(reader.get_object(n), "get")]
    spaces = {str(g.get_object().get("/CS")) for g in groups if g is not None} | {
        str(reader.pages[0]["/Group"].get("/CS"))}
    assert spaces <= {"/DeviceCMYK", "/DeviceGray"} and "/DeviceCMYK" in spaces


def test_shadows_and_blend_modes_in_cmyk_leave_no_rgb(tmp_path):
    script(120, 100)
    f.no_stroke()
    f.fill(f.cmyk(100, 0, 0, 0))
    f.circle(40, 50, 60)
    f.fill(f.cmyk(0, 100, 100, 0))
    f.blend_mode("multiply")
    f.opacity(128)
    f.shadow(4, 4, 5, f.cmyk(0, 0, 0, 100, 128))
    f.rect(40, 20, 60, 60)
    f.save(str(tmp_path / "a.pdf"))
    found = scan(tmp_path / "a.pdf")
    assert found.rgb == [] and has(found.ops["k"], (0, 1.0, 1.0, 0))
    assert has(found.ops["k"] + found.ops["K"], (0, 0, 0, 1.0))           # the shadow's ink


def test_text_in_a_gradient_and_text_as_shapes_are_cmyk(tmp_path):
    script(200, 80)
    f.text_size(40)
    f.fill(f.linear_gradient(0, 0, 200, 0, [f.cmyk(100, 0, 100, 0), f.cmyk(0, 100, 100, 0)]))
    f.text("Live", 5, 50)
    f.save(str(tmp_path / "live.pdf"))
    f.save(str(tmp_path / "shapes.pdf"), text="shapes")
    for name in ("live", "shapes"):
        found = scan(tmp_path / f"{name}.pdf")
        assert found.rgb == [], name
        assert any(s[0] == "DeviceCMYK" for s in found.shadings), name


def test_a_multi_page_document_and_a_picture_save_are_cmyk_too(tmp_path):
    script(100, 80)
    f.background(f.cmyk(0, 100, 0, 0))
    f.new_page(100, 80)
    f.background(f.cmyk(0, 0, 100, 0))
    f.save(str(tmp_path / "two.pdf"))
    found = scan(tmp_path / "two.pdf")
    assert has(found.ops["k"], (0, 1.0, 0, 0)) and has(found.ops["k"], (0, 0, 1.0, 0)) and found.rgb == []
    g = f.create_graphics(40, 40)
    g.background(f.cmyk(100, 0, 100, 0))
    g.save(str(tmp_path / "g.pdf"))
    found = scan(tmp_path / "g.pdf")
    assert has(found.ops["k"], (1.0, 0, 1.0, 0)) and found.rgb == []


def test_pdf_looks_right_in_pdfium(tmp_path):
    pdfium = pytest.importorskip("pypdfium2")
    script(40, 40)
    f.background(f.cmyk(0, 0, 0, 100))
    f.fill(f.cmyk(0, 0, 0, 0))
    f.no_stroke()
    f.rect(20, 20, 20, 20)
    f.save(str(tmp_path / "a.pdf"))
    page = pdfium.PdfDocument(str(tmp_path / "a.pdf"))[0].render(scale=1).to_pil().convert("RGB")
    assert sum(page.getpixel((5, 5))) < 150 and page.getpixel((30, 30)) == (255, 255, 255)     # pdfium's K is a deep grey


# ---------------------------------------------------------------- RGB is tagged as sRGB (D4)
def rgb_poster(path, **options):
    script(200, 120)
    f.background("white")
    f.no_stroke()
    f.fill(f.linear_gradient(0, 0, 200, 0, ["red", "blue"]))
    f.rect(0, 0, 200, 40)
    f.fill(255, 0, 0)
    f.rect(10, 50, 60, 40)
    f.stroke(0, 0, 255)
    f.circle(150, 80, 40)
    f.fill(0)
    f.text("Hi", 10, 110)
    f.save(str(path), **options)


def test_rgb_in_a_pdf_is_tagged_as_srgb(tmp_path):
    rgb_poster(tmp_path / "a.pdf")
    found = scan(tmp_path / "a.pdf")
    assert found.rgb == [] and found.ops["rg"] == found.ops["RG"] == []
    assert has(found.ops["sc"], (1, 0, 0))
    assert has(found.ops["SC"], (0, 0, 1))
    assert "ICCBased" in found.spaces and "DeviceRGB" not in found.spaces
    assert [s[0] for s in found.shadings] == ["ICCBased"]
    reader = PdfReader(tmp_path / "a.pdf")
    intent = reader.trailer["/Root"]["/OutputIntents"][0]
    assert intent["/OutputConditionIdentifier"] == "sRGB IEC61966-2.1"
    profile = intent["/DestOutputProfile"].get_data()
    assert profile[36:40] == b"acsp" and profile[12:16] == b"mntr" and profile[16:20] == b"RGB "
    assert intent["/DestOutputProfile"]["/N"] == 3
    assert "GTS_PDFXVersion" not in (reader.metadata or {})              # nothing is claimed


def test_the_srgb_profile_is_the_one_in_the_package():
    data = pdf_colour.PROFILE.read_bytes()
    assert len(data) == 588 and data[36:40] == b"acsp"
    assert "No copyright, use freely".encode("utf-16-be") in data or b"No copyright, use freely" in data


def test_a_pdf_keeps_its_header_version(tmp_path):
    rgb_poster(tmp_path / "a.pdf")
    poster(tmp_path / "b.pdf")
    rgb_poster(tmp_path / "c.pdf", bleed=f.mm(3), marks=True)
    for name in "abc":
        assert PdfReader(str(tmp_path / f"{name}.pdf")).pdf_header >= "%PDF-1.4", name


def test_a_pdf_without_cmyk_is_the_same_bytes_every_time(tmp_path, monkeypatch):
    real = cairo.PDFSurface

    def surface(*args):
        s = real(*args)
        s.set_metadata(cairo.PDFMetadata.CREATE_DATE, "2026-01-01T00:00:00")
        return s

    monkeypatch.setattr(cairo, "PDFSurface", surface)
    monkeypatch.setattr(head_table, "timestampNow", lambda: 0)
    rgb_poster(tmp_path / "a.pdf")
    rgb_poster(tmp_path / "b.pdf")
    assert (tmp_path / "a.pdf").read_bytes() == (tmp_path / "b.pdf").read_bytes()
    poster(tmp_path / "c.pdf")
    poster(tmp_path / "d.pdf")
    assert (tmp_path / "c.pdf").read_bytes() == (tmp_path / "d.pdf").read_bytes()


def test_pdfium_draws_the_tagged_colours_as_before(tmp_path):
    pdfium = pytest.importorskip("pypdfium2")
    rgb_poster(tmp_path / "a.pdf")
    page = pdfium.PdfDocument(str(tmp_path / "a.pdf"))[0].render(scale=1).to_pil().convert("RGB")
    assert all(abs(got - want) <= 2 for got, want in zip(page.getpixel((30, 70)), (255, 0, 0)))


def test_a_picture_stays_rgb_and_makes_the_file_a_mixed_one(tmp_path):
    script(100, 80)
    f.background(f.cmyk(0, 0, 0, 10))
    g = f.create_graphics(20, 20)
    g.background(0, 0, 255)
    f.tint(f.cmyk(0, 50, 50, 0))
    f.image(g, 10, 10)
    f.no_tint()
    f.save(str(tmp_path / "a.pdf"))
    found = scan(tmp_path / "a.pdf")
    assert has(found.ops["k"], (0, 0, 0, 0.1))
    assert "ICCBased" in found.spaces and found.rgb == []                 # the picture is tagged, never DeviceRGB
    assert found.has_output_intent                                       # the file has RGB, so it says what it is


def test_a_mixed_drawing_keeps_each_colour_in_its_own_kind(tmp_path):
    script(100, 80)
    f.no_stroke()
    f.fill(f.cmyk(0, 100, 100, 0))
    f.rect(0, 0, 40, 40)
    f.fill(255, 0, 0)
    f.rect(50, 0, 40, 40)
    f.save(str(tmp_path / "a.pdf"))
    found = scan(tmp_path / "a.pdf")
    assert has(found.ops["k"], (0, 1.0, 1.0, 0)) and has(found.ops["sc"], (1, 0, 0))
    assert found.rgb == [] and found.has_output_intent


def test_a_mixed_gradient_turns_its_rgb_stops_into_inks(tmp_path):
    script(100, 40)
    f.no_stroke()
    f.fill(f.linear_gradient(0, 0, 100, 0, [f.cmyk(0, 0, 0, 100), "red"]))
    f.rect(0, 0, 100, 40)
    f.save(str(tmp_path / "a.pdf"))
    (space, colours), = scan(tmp_path / "a.pdf").shadings
    assert space == "DeviceCMYK" and close(colours[0], (0, 0, 0, 1)) and close(colours[1], (0, 1, 1, 0))


# ---------------------------------------------------------------- crop marks in registration (D5)
def test_crop_marks_are_registration_colour(tmp_path):
    script(100, 80)
    f.background(f.cmyk(0, 100, 0, 0))
    f.save(str(tmp_path / "a.pdf"), bleed=f.mm(3), marks=True)
    found = scan(tmp_path / "a.pdf")
    assert has(found.ops["K"], (1, 1, 1, 1))
    assert found.rgb == [] and not found.has_output_intent


def test_crop_marks_on_an_rgb_drawing_are_still_registration(tmp_path):
    rgb_poster(tmp_path / "a.pdf", bleed=f.mm(3), marks=True)
    found = scan(tmp_path / "a.pdf")
    assert has(found.ops["K"], (1, 1, 1, 1)) and has(found.ops["sc"], (1, 0, 0))
    assert found.rgb == []
    page = PdfReader(tmp_path / "a.pdf").pages[0]
    assert page.trimbox is not None and page.bleedbox is not None          # the boxes step still runs last


# ---------------------------------------------------------------- failing safe
def test_if_the_colour_step_fails_for_a_cmyk_file_there_is_no_file(tmp_path, monkeypatch):
    def boom(self):
        raise RuntimeError("broken")

    monkeypatch.setattr(pdf_colour._Rewriter, "run", boom)
    with pytest.raises(ColourError, match="no file was left"):
        poster(tmp_path / "a.pdf")
    assert not (tmp_path / "a.pdf").exists()


def test_a_form_the_walk_missed_is_caught_by_the_scan_and_the_file_removed(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_colour._Rewriter, "_form", lambda self, form: None)
    with pytest.raises(ColourError, match="did not reach"):
        poster(tmp_path / "a.pdf")
    assert not (tmp_path / "a.pdf").exists()


def test_an_unknown_gradient_function_is_an_error_not_a_guess(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_colour._Rewriter, "_leaves", lambda self, function: (_ for _ in ()).throw(ColourError("type 4")))
    with pytest.raises(ColourError):
        poster(tmp_path / "a.pdf")
    assert not (tmp_path / "a.pdf").exists()


def test_if_the_colour_step_fails_without_cmyk_the_file_is_left_as_drawn(tmp_path, monkeypatch):
    def boom(self):
        raise RuntimeError("broken")

    monkeypatch.setattr(pdf_colour._Rewriter, "run", boom)
    rgb_poster(tmp_path / "a.pdf")                                         # a save never fails for the tagging
    found = scan(tmp_path / "a.pdf")
    assert found.rgb and not found.has_output_intent


def test_the_pdf_leaves_no_temporary_state_for_the_next_save(tmp_path):
    poster(tmp_path / "a.pdf")
    poster(tmp_path / "b.pdf")
    assert scan(tmp_path / "a.pdf").ops["k"] == scan(tmp_path / "b.pdf").ops["k"]


def test_inks_are_floats_not_rounded(tmp_path):
    script(40, 40)
    f.background(f.cmyk(12.5, 0.25, 99.99, 3.3333))
    f.save(str(tmp_path / "a.pdf"))
    assert has(scan(tmp_path / "a.pdf").ops["k"], (0.125, 0.0025, 0.9999, 0.033333), places=6)
    assert math.isclose(f.cmyk(12.5, 0, 0, 0).cmyk[0], 12.5)


# ---------------------------------------------------------------- the gallery example
def test_the_gallery_poster_saves_a_pdf_of_exact_inks(tmp_path, monkeypatch):
    from conftest import ROOT, run_sketch
    monkeypatch.chdir(tmp_path)
    run_sketch(ROOT / "examples" / "gallery" / "colour" / "05_cmyk_poster.py", frames=2)
    found = scan(tmp_path / "cmyk_poster.pdf")
    assert has(found.ops["k"], (0, 0.85, 1.0, 0)) and has(found.ops["k"], (1.0, 0.75, 0, 0.2))
    assert has(found.ops["k"], (0, 0, 0, 1.0)) and has(found.ops["K"], (1, 1, 1, 1))     # the headline; the marks
    assert any(s[0] == "DeviceCMYK" for s in found.shadings)
    assert found.rgb == [] and "ICCBased" not in found.spaces and not found.has_output_intent
