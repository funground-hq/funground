"""Real text in PDFs (S-094, contract T15, decision D-043).

Every PDF funground writes carries its text as real PDF text with an embedded font subset, so it
can be selected, searched and copied, and it looks the same as the glyph outlines it replaces.
Text is read back with two independent engines: pypdf and pdfium (pypdfium2, the engine inside
Chrome and Edge). Looks are checked by rendering the PDF with pdfium at 4x and comparing it with
the same frame written the old way, as outlines (the exporter with real text switched off).
"""
from __future__ import annotations

import re
from contextlib import contextmanager

import pytest

pypdfium2 = pytest.importorskip("pypdfium2")
from PIL import Image, ImageChops, ImageStat  # noqa: E402
from pypdf import PdfReader  # noqa: E402

import funground as f  # noqa: E402
from funground import api, export  # noqa: E402
from funground.export import pdf_text  # noqa: E402
from funground.platform.headless import HeadlessPlatform  # noqa: E402
from funground.renderers.cairo2d import CairoRenderer  # noqa: E402
from funground.sketch import Sketch  # noqa: E402

from conftest import ROOT  # noqa: E402
from fontmaker import make_static_font, make_variable_font  # noqa: E402

MONO = ROOT / "examples" / "gallery" / "text" / "fonts" / "DejaVuSansMono.ttf"
HEBREW = "שלום עולם"        # "hello world"
ARABIC = "مرحبا"                            # "welcome"

# Looks: the PDF with real text against the same frame as outlines, both drawn by pdfium at 4x.
# MEAN_LIMIT bounds the mean difference over the whole page (0-255 per channel); CELL_LIMIT bounds
# the worst difference after shrinking both pictures back to 1x (each 4x4 block averaged), so
# anti-aliasing noise averages out but a missing, extra or shifted glyph does not.
# Measured (Windows 11, pypdfium2 5.x): text in the right place gives a mean of at most 0.11 and a
# worst cell of at most 2, except where a glyph is a plain rectangle ("l", "I"): pdfium snaps the
# *outline* PDF's rectangular fill paths outward to whole device pixels (the reference here), which
# moves a stem edge by up to one 4x pixel and gives cells up to 70 ("lll" at size 30). Against
# Cairo's own drawing the real-text PDF matches (S-109, PDF_Text_Note.md). Text moved by half a pixel gives a mean of at
# least 0.66 and a worst cell of at least 128; a missing glyph gives a worst cell of 255.
SCALE = 4
MEAN_LIMIT = 0.3
CELL_LIMIT = 96


def script(width=240, height=120):
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    f.size(width, height)
    f.background("white")
    f.fill("black")
    f.text_size(20)


def texts(path) -> tuple[list[str], list[str]]:
    """The text of each page as pypdf and as pdfium read it."""
    by_pypdf = [page.extract_text() for page in PdfReader(str(path)).pages]
    doc = pypdfium2.PdfDocument(str(path))
    by_pdfium = [doc[i].get_textpage().get_text_range() for i in range(len(doc))]
    doc.close()
    return by_pypdf, by_pdfium


def words(s: str) -> str:
    return " ".join(s.split())


def fonts(path) -> list:
    """Every embedded font (Type0 font object), once each, over all pages and nested XObjects."""
    reader = PdfReader(str(path))
    found: dict = {}
    seen: set = set()

    def walk(resources):
        if resources is None:
            return
        res = resources.get_object()
        for ref in (res.get("/Font") or {}).values():
            font = ref.get_object()
            found[ref.idnum if hasattr(ref, "idnum") else id(font)] = font
        for ref in (res.get("/XObject") or {}).values():
            key = ref.idnum if hasattr(ref, "idnum") else id(ref)
            if key not in seen:
                seen.add(key)
                walk(ref.get_object().get("/Resources"))

    for page in reader.pages:
        walk(page.get("/Resources"))
    return list(found.values())


class _OutlinesOnly(pdf_text.PdfTextCollector):
    """A collector that never takes a run: every run is drawn as outlines, as before T15."""

    def add(self, run, x, y, matrix):
        return None


@contextmanager
def outlines_only(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(export, "PdfTextCollector", _OutlinesOnly)
        yield


def render(path, page=0) -> Image.Image:
    doc = pypdfium2.PdfDocument(str(path))
    image = doc[page].render(scale=SCALE).to_pil().convert("RGB")
    doc.close()
    return image


def difference(a: Image.Image, b: Image.Image) -> tuple[float, int]:
    """(mean difference over the page, worst difference of a 1x pixel after averaging 4x4 blocks)."""
    diff = ImageChops.difference(a, b)
    mean = sum(ImageStat.Stat(diff).mean) / 3
    small = ImageChops.difference(a.reduce(SCALE), b.reduce(SCALE))
    worst = max(hi for _, hi in small.getextrema())
    return mean, worst


def save_both(tmp_path, monkeypatch, name="page"):
    """Save the current script as real text and as outlines; return both paths."""
    real, outline = tmp_path / f"{name}.pdf", tmp_path / f"{name}_outlines.pdf"
    f.save(str(real))
    with outlines_only(monkeypatch):
        f.save(str(outline))
    return real, outline


# ---------------------------------------------------------------- the text copies out
def test_plain_text_extracts(tmp_path):
    script()
    f.text("Hello, PDF world", 10, 10)
    f.save(str(tmp_path / "a.pdf"))
    by_pypdf, by_pdfium = texts(tmp_path / "a.pdf")
    assert words(by_pypdf[0]) == "Hello, PDF world"
    assert words(by_pdfium[0]) == "Hello, PDF world"
    assert [str(font["/BaseFont"]).split("+")[1] for font in fonts(tmp_path / "a.pdf")] == ["DejaVuSans"]


def test_ligatures_copy_as_letters(tmp_path):
    from funground import typography

    run = typography.default_font().shape("fi office", 20)
    assert len(run.glyphs) < len("fi office")           # DejaVu really made the fi and ffi ligatures
    script()
    f.text("fi office", 10, 10)
    f.save(str(tmp_path / "a.pdf"))
    for engine in texts(tmp_path / "a.pdf"):
        assert words(engine[0]) == "fi office"


def test_an_accent_and_the_same_letter_alone_both_copy_right(tmp_path):
    from funground import typography

    run = typography.default_font().shape("x́", 20)
    assert len(run.glyphs) == 2 and {g.cluster for g in run.glyphs} == {0}    # one cluster, two glyphs
    script()
    f.text("x́ x", 10, 10)
    f.save(str(tmp_path / "a.pdf"))
    for engine in texts(tmp_path / "a.pdf"):
        assert words(engine[0]) == "x́ x"


def test_tracking(tmp_path, monkeypatch):
    script(300, 60)
    f.text_tracking(3)
    f.text("Spread out", 10, 10)
    real, outline = save_both(tmp_path, monkeypatch)
    for engine in texts(real):
        assert words(engine[0]) == "Spread out"
    mean, worst = difference(render(real), render(outline))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


def test_text_box_wrapping(tmp_path, monkeypatch):
    script(200, 160)
    message = "A text box wraps its words onto several lines when they do not fit"
    f.text_box(message, 10, 10, 180, 140)
    real, outline = save_both(tmp_path, monkeypatch)
    for engine in texts(real):
        assert words(engine[0]) == message
    mean, worst = difference(render(real), render(outline))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


def test_formatted_string_with_two_fonts(tmp_path, monkeypatch):
    script(300, 60)
    fs = f.FormattedString()
    fs.append("Plain and ")
    fs.append("mono", font=str(MONO), color="red")
    f.text(fs, 10, 10)
    real, outline = save_both(tmp_path, monkeypatch)
    for engine in texts(real):
        assert words(engine[0]) == "Plain and mono"
    names = sorted(str(font["/BaseFont"]).split("+")[1] for font in fonts(real))
    assert names == ["DejaVuSans", "DejaVuSansMono"]
    mean, worst = difference(render(real), render(outline))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


def test_a_loaded_font(tmp_path):
    script()
    f.text_font(f.load_font(str(MONO)))
    f.text("Loaded font", 10, 10)
    f.save(str(tmp_path / "a.pdf"))
    for engine in texts(tmp_path / "a.pdf"):
        assert words(engine[0]) == "Loaded font"
    assert [str(font["/BaseFont"]).split("+")[1] for font in fonts(tmp_path / "a.pdf")] == ["DejaVuSansMono"]


def test_a_variable_font_at_two_settings(tmp_path, monkeypatch):
    font = f.load_font(make_variable_font(tmp_path))
    script(300, 100)
    f.text_font(font, 40)
    f.text("AAA", 10, 5)
    f.font_variations(wght=900)
    f.text("AA", 10, 50)
    real, outline = save_both(tmp_path, monkeypatch)
    for engine in texts(real):
        assert words(engine[0]) == "AAA AA"
    embedded = fonts(real)
    assert len(embedded) == 2                       # one instance per axis setting
    assert any("wght900" in str(font["/BaseFont"]) for font in embedded)
    mean, worst = difference(render(real), render(outline))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


def test_right_to_left_text_reads_in_order_with_pdfium(tmp_path, monkeypatch):
    script(300, 100)
    f.text(HEBREW, 10, 10)
    f.text(ARABIC, 10, 50)
    real, outline = save_both(tmp_path, monkeypatch)
    by_pdfium = texts(real)[1][0]
    assert HEBREW in by_pdfium and ARABIC in by_pdfium
    mean, worst = difference(render(real), render(outline))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


def test_a_cff_font_embeds(tmp_path, monkeypatch):
    script(300, 60)
    f.text_font(f.load_font(make_static_font(tmp_path, cff=True)), 30)
    f.text("ABC DE", 10, 10)
    real, outline = save_both(tmp_path, monkeypatch)
    (font,) = fonts(real)
    descendant = font["/DescendantFonts"][0].get_object()
    assert descendant["/Subtype"] == "/CIDFontType0"
    assert descendant["/FontDescriptor"].get_object()["/FontFile3"].get_object()["/Subtype"] == "/OpenType"
    for engine in texts(real):
        assert words(engine[0]) == "ABC DE"
    mean, worst = difference(render(real), render(outline))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


# ---------------------------------------------------------------- it looks the same
def _rotated_and_scaled():
    f.translate(120, 60)
    f.rotate(30)
    f.scale(1.5, 0.8)
    f.text("Turned", -40, -10)


def _skewed():
    f.translate(30, 30)
    f.shear_x(20)
    f.text("Leaning", 0, 0)


def _clipped():
    f.clip(f.path().move_to(0, 0).line_to(200, 0).line_to(0, 120).close())
    f.text_size(40)
    f.text("Clipped", 10, 30)


def _opacity_and_blend():
    f.no_stroke()
    f.fill("gold")
    f.rect(0, 0, 240, 60)
    f.fill(30, 90, 200)
    f.opacity(128)
    f.blend_mode("multiply")
    f.text_size(36)
    f.text("Mixed", 20, 20)


def _gradient():
    f.text_size(48)
    f.fill(f.linear_gradient(10, 0, 230, 0, ["red", "blue"]))
    f.text("Rainbow", 10, 20)


def _shape_over_text():
    f.text_size(48)
    f.text("Under", 10, 20)
    f.no_stroke()
    f.fill("green")
    f.rect(60, 0, 40, 120)


def _shadow():
    f.shadow(4, 4, 3, f.color(0, 0, 0, 160))
    f.fill("orange")
    f.text_size(48)
    f.text("Shade", 10, 20)


def _picture():
    g = f.create_graphics(200, 80)
    g.fill("purple")
    g.text_size(30)
    g.text("Inside", 10, 10)
    inner = f.create_graphics(100, 40)
    inner.fill("teal")
    inner.text_size(20)
    inner.text("Nested", 0, 0)
    g.image(inner, 100, 40)
    f.image(g, 20, 20)


SCENES = {
    "rotated and scaled": (_rotated_and_scaled, "Turned"),
    "skewed": (_skewed, "Leaning"),
    "clipped": (_clipped, "Clipped"),
    "opacity and blend mode": (_opacity_and_blend, "Mixed"),
    "gradient": (_gradient, "Rainbow"),
    "shape over text": (_shape_over_text, "Under"),
    "shadow": (_shadow, "Shade"),
    "picture with a picture in it": (_picture, "Inside Nested"),
}


@pytest.mark.parametrize("scene", SCENES)
def test_it_looks_the_same_as_the_outlines(tmp_path, monkeypatch, scene):
    draw, expected = SCENES[scene]
    script()
    draw()
    real, outline = save_both(tmp_path, monkeypatch)
    assert fonts(real), "the text was written as real text"
    assert not fonts(outline)
    assert words(texts(real)[1][0]) == expected
    mean, worst = difference(render(real), render(outline))
    print(f"{scene}: mean {mean:.3f}, worst cell {worst}")
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


@pytest.mark.parametrize("other, x", [("Moved", 10.5), ("Move", 10)])
def test_a_misplaced_or_missing_glyph_would_be_caught(tmp_path, monkeypatch, other, x):
    """The looks check is not blind: text moved by half a pixel, or a missing letter, fails it."""
    script()
    f.text_size(30)
    f.text("Moved", 10, 20)
    real = tmp_path / "a.pdf"
    f.save(str(real))
    script()
    f.text_size(30)
    f.text(other, x, 20)
    with outlines_only(monkeypatch):
        f.save(str(tmp_path / "b.pdf"))
    mean, worst = difference(render(real), render(tmp_path / "b.pdf"))
    assert worst > CELL_LIMIT


# ---------------------------------------------------------------- every PDF route
def test_a_picture_saved_as_pdf(tmp_path, monkeypatch):
    script()
    g = f.create_graphics(160, 60)
    g.fill("navy")
    g.text_size(24)
    g.text("Picture text", 5, 5)
    g.save(str(tmp_path / "g.pdf"))
    with outlines_only(monkeypatch):
        g.save(str(tmp_path / "g_outlines.pdf"))
    for engine in texts(tmp_path / "g.pdf"):
        assert words(engine[0]) == "Picture text"
    mean, worst = difference(render(tmp_path / "g.pdf"), render(tmp_path / "g_outlines.pdf"))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


def test_a_sketch_saving_a_pdf_from_draw(tmp_path):
    out = tmp_path / "frame.pdf"

    def draw():
        f.background("white")
        f.fill("black")
        f.text("From draw", 10, 10)
        if f.frame_count == 1:
            f.save(str(out))

    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    api.active_sketch().run_namespace({"draw": draw}, max_frames=3)
    for engine in texts(out):
        assert words(engine[0]) == "From draw"


def test_fonts_are_embedded_once_per_document(tmp_path):
    script(200, 100)
    f.text("Page one", 10, 10)
    f.new_page()
    f.fill("black")
    f.text("Page two", 10, 10)
    f.new_page(300, 100)
    f.fill("black")
    f.text("Page three", 10, 10)
    f.save(str(tmp_path / "book.pdf"))
    by_pypdf, by_pdfium = texts(tmp_path / "book.pdf")
    assert [words(t) for t in by_pdfium] == ["Page one", "Page two", "Page three"]
    assert [words(t) for t in by_pypdf] == ["Page one", "Page two", "Page three"]
    assert len(fonts(tmp_path / "book.pdf")) == 1
    data = (tmp_path / "book.pdf").read_bytes()
    assert len(re.findall(rb"/FontFile2", data)) == 1


# ---------------------------------------------------------------- falling back to outlines
def test_a_font_that_forbids_embedding_is_drawn_as_outlines(tmp_path, monkeypatch):
    script(300, 60)
    f.text_font(f.load_font(make_static_font(tmp_path, "NoEmbed", fs_type=0x0002)), 30)
    f.text("ABC DE", 10, 10)
    real, outline = save_both(tmp_path, monkeypatch)
    assert fonts(real) == []
    assert words(texts(real)[1][0]) == ""
    mean, worst = difference(render(real), render(outline))
    assert mean == 0 and worst == 0


def test_only_the_restricted_run_falls_back(tmp_path):
    script(300, 60)
    fs = f.FormattedString()
    fs.append("Real ")
    fs.append("ABC", font=make_static_font(tmp_path, "NoEmbed", fs_type=0x0002))
    f.text(fs, 10, 10)
    f.save(str(tmp_path / "a.pdf"))
    assert words(texts(tmp_path / "a.pdf")[1][0]) == "Real"
    assert len(fonts(tmp_path / "a.pdf")) == 1


def test_if_writing_the_text_fails_the_pdf_has_outlines(tmp_path, monkeypatch):
    def broken(self, path):
        raise RuntimeError("boom")

    monkeypatch.setattr(pdf_text.PdfTextCollector, "finish", broken)
    script()
    f.text("Still saved", 10, 10)
    f.save(str(tmp_path / "a.pdf"))
    assert fonts(tmp_path / "a.pdf") == []
    image = render(tmp_path / "a.pdf")
    assert image.getextrema() != ((255, 255), (255, 255), (255, 255))    # the text is drawn


# ---------------------------------------------------------------- size and the rest unchanged
def test_a_text_heavy_page_is_much_smaller(tmp_path, monkeypatch):
    script(600, 820)
    f.text_size(12)
    line = "The quick brown fox jumps over the lazy dog while it sleeps, 0123456789."
    for i in range(50):
        f.text(line, 10, 10 + i * 16)
    real, outline = save_both(tmp_path, monkeypatch)
    real_size, outline_size = real.stat().st_size, outline.stat().st_size
    print(f"text-heavy page: real text {real_size} bytes, outlines {outline_size} bytes")
    assert real_size < outline_size / 3


def test_text_path_stays_a_path(tmp_path):
    script()
    f.draw_path(f.text_path("Path", 10, 10))
    f.save(str(tmp_path / "a.pdf"))
    assert fonts(tmp_path / "a.pdf") == []


def test_svg_and_png_keep_outlines(tmp_path):
    script()
    f.text("Shapes", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    svg = (tmp_path / "a.svg").read_text(encoding="utf-8")
    assert "<text" not in svg and "<path" in svg
    assert CairoRenderer().pdf_text is None           # the window and PNG never collect text
