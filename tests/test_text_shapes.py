"""Live text or shapes, per file (S-116, contract T20, decision D-060).

``f.save(path, text="shapes")`` and ``picture.save(path, text="shapes")`` write a PDF or SVG whose
letters are exact vector outlines: no fonts embedded, nothing to install, nothing to edit. The
default, ``"live"``, is real text (T15, T19). Looks are checked as test_pdf_text does: both PDFs
drawn by pdfium at 4x and compared within the same limits.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

pypdfium2 = pytest.importorskip("pypdfium2")
from PIL import Image, ImageChops, ImageStat  # noqa: E402
from pypdf import PdfReader  # noqa: E402

import funground as f  # noqa: E402
from funground import api  # noqa: E402
from funground.platform.headless import HeadlessPlatform  # noqa: E402
from funground.sketch import Sketch  # noqa: E402

SVG = "{http://www.w3.org/2000/svg}"
INKSCAPE = "{http://www.inkscape.org/namespaces/inkscape}"
SCALE = 4
MEAN_LIMIT = 0.3          # the limits test_pdf_text.py uses
CELL_LIMIT = 96
HINDI = "नमस्ते"


def script(width=240, height=120):
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    f.size(width, height)
    f.background("white")
    f.fill("black")
    f.text_size(20)


def has_font(path) -> bool:
    """True when any page, or anything nested in one, lists a /Font resource."""
    reader = PdfReader(str(path))
    seen: set = set()

    def walk(resources) -> bool:
        if resources is None:
            return False
        res = resources.get_object()
        if res.get("/Font"):
            return True
        for ref in (res.get("/XObject") or {}).values():
            key = getattr(ref, "idnum", id(ref))
            if key not in seen:
                seen.add(key)
                if walk(ref.get_object().get("/Resources")):
                    return True
        return False

    return any(walk(page.get("/Resources")) for page in reader.pages)


def pdf_words(path) -> str:
    return " ".join(" ".join(p.extract_text() for p in PdfReader(str(path)).pages).split())


def render(path, page=0) -> Image.Image:
    doc = pypdfium2.PdfDocument(str(path))
    image = doc[page].render(scale=SCALE).to_pil().convert("RGB")
    doc.close()
    return image


def difference(a, b) -> tuple[float, int]:
    diff = ImageChops.difference(a, b)
    mean = sum(ImageStat.Stat(diff).mean) / 3
    small = ImageChops.difference(a.reduce(SCALE), b.reduce(SCALE))
    return mean, max(hi for _, hi in small.getextrema())


def same_look(a, b, page=0) -> None:
    mean, worst = difference(render(a, page), render(b, page))
    assert mean < MEAN_LIMIT and worst < CELL_LIMIT


def ink(path) -> int:
    """How many pixels of the first page are not white."""
    gray = render(path).convert("L")
    return sum(gray.histogram()[:200])


def svg_root(path):
    return ET.parse(str(path)).getroot()


def svg_texts(path) -> list:
    return list(svg_root(path).iter(f"{SVG}text"))


def glyph_paths(path) -> int:
    return len(list(svg_root(path).iter(f"{SVG}path")))


def layer_labels(path) -> list[str]:
    return [g.get(INKSCAPE + "label") for g in svg_root(path).iter(f"{SVG}g")
            if g.get(INKSCAPE + "groupmode") == "layer"]


def pdf_layer_names(path) -> list[str]:
    props = PdfReader(str(path)).trailer["/Root"]["/OCProperties"]
    return sorted(str(o.get_object()["/Name"]) for o in props["/OCGs"])


# ---------------------------------------------------------------- PDF
def test_the_default_pdf_has_fonts_and_text(tmp_path):
    script()
    f.text("Live words", 10, 10)
    f.save(str(tmp_path / "a.pdf"))
    assert has_font(tmp_path / "a.pdf")
    assert pdf_words(tmp_path / "a.pdf") == "Live words"


def test_live_given_by_name_is_the_default(tmp_path):
    script()
    f.text("Live words", 10, 10)
    f.save(str(tmp_path / "a.pdf"))
    f.save(str(tmp_path / "b.pdf"), text="live")
    assert has_font(tmp_path / "b.pdf") and pdf_words(tmp_path / "b.pdf") == "Live words"


def test_a_shapes_pdf_has_no_font_and_no_text(tmp_path):
    script()
    f.text("Shape words", 10, 10)
    f.save(str(tmp_path / "s.pdf"), text="shapes")
    assert not has_font(tmp_path / "s.pdf")
    assert pdf_words(tmp_path / "s.pdf") == ""
    data = (tmp_path / "s.pdf").read_bytes()
    assert b"/FontFile" not in data
    assert ink(tmp_path / "s.pdf") > 100


def test_a_shapes_pdf_looks_like_the_live_one(tmp_path):
    script(300, 80)
    f.text_size(30)
    f.text("Same look: fi office", 10, 10)
    f.save(str(tmp_path / "live.pdf"))
    f.save(str(tmp_path / "shapes.pdf"), text="shapes")
    same_look(tmp_path / "live.pdf", tmp_path / "shapes.pdf")


def test_hindi_and_emoji_are_drawn_as_shapes(tmp_path):
    script(300, 120)
    f.text_size(32)
    f.text(HINDI, 10, 10)
    f.text("🎉", 10, 60)
    f.save(str(tmp_path / "live.pdf"))
    f.save(str(tmp_path / "shapes.pdf"), text="shapes")
    assert not has_font(tmp_path / "shapes.pdf")
    assert pdf_words(tmp_path / "shapes.pdf") == ""
    assert ink(tmp_path / "shapes.pdf") > 200
    same_look(tmp_path / "live.pdf", tmp_path / "shapes.pdf")


def test_hindi_and_emoji_are_drawn_as_shapes_in_svg(tmp_path):
    script(300, 120)
    f.text_size(32)
    f.text(HINDI, 10, 10)
    f.text("🎉", 10, 60)
    f.save(str(tmp_path / "s.svg"), text="shapes")
    text = (tmp_path / "s.svg").read_text(encoding="utf-8")
    assert not svg_texts(tmp_path / "s.svg")
    assert "@font-face" not in text
    assert glyph_paths(tmp_path / "s.svg") > 3


# ---------------------------------------------------------------- SVG
def test_the_default_svg_has_text(tmp_path):
    script()
    f.text("Live words", 10, 10)
    f.save(str(tmp_path / "a.svg"))
    assert [t for t in svg_texts(tmp_path / "a.svg")]
    assert "@font-face" in (tmp_path / "a.svg").read_text(encoding="utf-8")


def test_a_shapes_svg_has_glyph_paths_and_no_text(tmp_path):
    script()
    f.text("Shape words", 10, 10)
    f.save(str(tmp_path / "s.svg"), text="shapes")
    text = (tmp_path / "s.svg").read_text(encoding="utf-8")
    assert not svg_texts(tmp_path / "s.svg")
    assert "@font-face" not in text and "<text" not in text
    assert glyph_paths(tmp_path / "s.svg") > 3


# ---------------------------------------------------------------- layers
@pytest.mark.parametrize("mode", ["live", "shapes"])
def test_layers_stay_layers_in_a_pdf(tmp_path, mode):
    script()
    with f.layer("words"):
        f.fill("black")
        f.text("In a layer", 10, 10)
    with f.layer("hidden"):
        f.fill("black")
        f.text("Hidden", 10, 60)
    f.hide_layer("hidden")
    f.save(str(tmp_path / "a.pdf"), text=mode)
    assert pdf_layer_names(tmp_path / "a.pdf") == ["hidden", "words"]
    assert has_font(tmp_path / "a.pdf") == (mode == "live")


@pytest.mark.parametrize("mode", ["live", "shapes"])
def test_layers_stay_layers_in_an_svg(tmp_path, mode):
    script()
    with f.layer("words"):
        f.fill("black")
        f.text("In a layer", 10, 10)
    with f.layer("hidden"):
        f.fill("black")
        f.text("Hidden", 10, 60)
    f.hide_layer("hidden")
    f.save(str(tmp_path / "a.svg"), text=mode)
    assert layer_labels(tmp_path / "a.svg") == ["words", "hidden"]
    assert bool(svg_texts(tmp_path / "a.svg")) == (mode == "live")


# ---------------------------------------------------------------- every route
def test_every_page_of_a_document(tmp_path):
    script(200, 100)
    f.text("Page one", 10, 10)
    f.new_page()
    f.fill("black")
    f.text("Page two", 10, 10)
    f.new_page(300, 100)
    f.fill("black")
    f.text("Page three", 10, 10)
    f.save(str(tmp_path / "live.pdf"))
    f.save(str(tmp_path / "shapes.pdf"), text="shapes")
    assert "Page three" in pdf_words(tmp_path / "live.pdf")
    assert not has_font(tmp_path / "shapes.pdf")
    assert pdf_words(tmp_path / "shapes.pdf") == ""
    assert len(PdfReader(str(tmp_path / "shapes.pdf")).pages) == 3
    for page in range(3):
        same_look(tmp_path / "live.pdf", tmp_path / "shapes.pdf", page)


def test_numbered_svg_pages(tmp_path):
    script(200, 100)
    f.text("Page one", 10, 10)
    f.new_page()
    f.fill("black")
    f.text("Page two", 10, 10)
    f.save(str(tmp_path / "book.svg"), text="shapes")
    for n in (1, 2):
        assert not svg_texts(tmp_path / f"book_{n}.svg")
        assert glyph_paths(tmp_path / f"book_{n}.svg") > 3


def test_a_picture_saved_as_shapes(tmp_path):
    script()
    g = f.create_graphics(160, 60)
    g.fill("navy")
    g.text_size(24)
    g.text("Picture text", 5, 5)
    g.save(str(tmp_path / "live.pdf"))
    g.save(str(tmp_path / "shapes.pdf"), text="shapes")
    g.save(str(tmp_path / "live.svg"))
    g.save(str(tmp_path / "shapes.svg"), text="shapes")
    assert pdf_words(tmp_path / "live.pdf") == "Picture text"
    assert not has_font(tmp_path / "shapes.pdf") and pdf_words(tmp_path / "shapes.pdf") == ""
    same_look(tmp_path / "live.pdf", tmp_path / "shapes.pdf")
    assert svg_texts(tmp_path / "live.svg") and not svg_texts(tmp_path / "shapes.svg")
    assert "@font-face" not in (tmp_path / "shapes.svg").read_text(encoding="utf-8")


def test_an_animated_sketch_remembers_the_mode_for_the_queued_save(tmp_path):
    def draw():
        f.background("white")
        f.fill("black")
        f.text("From draw", 10, 10)
        if f.frame_count == 1:
            f.save(str(tmp_path / "shapes.pdf"), text="shapes")
            f.save(str(tmp_path / "live.pdf"))
            f.save(str(tmp_path / "shapes.svg"), text="shapes")
            f.save(str(tmp_path / "live.svg"))

    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    api.active_sketch().run_namespace({"draw": draw}, max_frames=3)
    assert not has_font(tmp_path / "shapes.pdf") and has_font(tmp_path / "live.pdf")
    assert pdf_words(tmp_path / "live.pdf") == "From draw"
    assert not svg_texts(tmp_path / "shapes.svg") and svg_texts(tmp_path / "live.svg")


# ---------------------------------------------------------------- errors and ignored cases
@pytest.mark.parametrize("bad", ["outline", "", "LIVE", None, True, 1])
def test_a_bad_value_is_an_error_naming_both(tmp_path, bad):
    script()
    with pytest.raises(ValueError) as error:
        f.save(str(tmp_path / "a.pdf"), text=bad)
    assert '"live"' in str(error.value) and '"shapes"' in str(error.value)
    assert not (tmp_path / "a.pdf").exists()


def test_a_bad_value_is_an_error_for_a_picture_and_for_png(tmp_path):
    script()
    g = f.create_graphics(40, 40)
    with pytest.raises(ValueError, match="shapes"):
        g.save(str(tmp_path / "g.svg"), text="nope")
    with pytest.raises(ValueError, match="shapes"):
        g.save(str(tmp_path / "g.png"), text="nope")
    with pytest.raises(ValueError, match="shapes"):
        f.save(str(tmp_path / "a.png"), text="nope")


def test_a_bad_value_in_a_queued_save_fails_at_the_call(tmp_path):
    seen = []

    def draw():
        try:
            f.save(str(tmp_path / "a.pdf"), text="nope")
        except ValueError as error:
            seen.append(str(error))

    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    api.active_sketch().run_namespace({"draw": draw}, max_frames=1)
    assert seen and "shapes" in seen[0]


def test_png_ignores_the_option(tmp_path):
    script()
    f.text("Pixels", 10, 10)
    f.save(str(tmp_path / "plain.png"))
    f.save(str(tmp_path / "shapes.png"), text="shapes")
    assert (tmp_path / "plain.png").read_bytes() == (tmp_path / "shapes.png").read_bytes()
    g = f.create_graphics(60, 40)
    g.text("Hi", 2, 2)
    g.save(str(tmp_path / "g1.png"))
    g.save(str(tmp_path / "g2.png"), text="shapes")
    assert (tmp_path / "g1.png").read_bytes() == (tmp_path / "g2.png").read_bytes()
