"""Print-ready PDF (story S-164, contract row D2): f.save("x.pdf", bleed=..., marks=...).

The boxes are read back with pypdf. What is drawn where is read back by drawing the PDF with pdfium
(pypdfium2, the engine in Chrome and Edge) at one pixel to the point.
"""
from __future__ import annotations

import pytest

pypdfium2 = pytest.importorskip("pypdfium2")
from pypdf import PdfReader  # noqa: E402

import funground as f  # noqa: E402
from funground import api  # noqa: E402
from funground.platform.headless import HeadlessPlatform  # noqa: E402
from funground.sketch import Sketch  # noqa: E402
from funground.web import Session  # noqa: E402

MM3 = f.mm(3)
SLUG = f.mm(1) + f.mm(5)                    # the strip beyond the bleed that holds the marks
WHITE, RED, BLUE = (255, 255, 255), (255, 0, 0), (0, 0, 255)


def script(width=200, height=120) -> Sketch:
    sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    sketch.size(width, height)
    return sketch


def box(rectangle) -> tuple[float, float, float, float]:
    return tuple(round(float(v), 3) for v in (rectangle.left, rectangle.bottom, rectangle.right, rectangle.top))


def picture(path, page=0):
    """The PDF page drawn by pdfium, one pixel to the point, as an RGB image."""
    return pypdfium2.PdfDocument(str(path))[page].render(scale=1).to_pil().convert("RGB")


def poster() -> None:
    """A red band drawn past the top-left corner, and a blue square past the bottom-right one."""
    f.no_stroke()
    f.background("white")
    f.fill("red")
    f.rect(-40, -40, 100, 80)
    f.fill("blue")
    f.rect(150, 90, 100, 80)


# ---------------------------------------------------------------- the boxes
def test_an_a4_pdf_with_3_mm_bleed_and_marks(tmp_path):
    script(*f.page_size("A4"))
    poster()
    f.save(str(tmp_path / "a4.pdf"), bleed=MM3, marks=True)
    page = PdfReader(tmp_path / "a4.pdf").pages[0]
    margin = MM3 + SLUG
    assert box(page.mediabox) == (0, 0, round(595 + 2 * margin, 3), round(842 + 2 * margin, 3))
    assert box(page.trimbox) == (round(margin, 3), round(margin, 3), round(margin + 595, 3), round(margin + 842, 3))
    assert box(page.bleedbox) == (round(margin - MM3, 3), round(margin - MM3, 3),
                                  round(margin + 595 + MM3, 3), round(margin + 842 + MM3, 3))
    trim = page.trimbox
    assert (float(trim.width), float(trim.height)) == pytest.approx((595, 842))
    assert page.mediabox.width > page.bleedbox.width > page.trimbox.width


def test_bleed_without_marks_makes_the_sheet_the_bleed_box(tmp_path):
    script(200, 120)
    f.save(str(tmp_path / "b.pdf"), bleed=10)
    page = PdfReader(tmp_path / "b.pdf").pages[0]
    assert box(page.mediabox) == box(page.bleedbox) == (0, 0, 220, 140)
    assert box(page.trimbox) == (10, 10, 210, 130)


def test_marks_without_bleed_put_the_trim_inside_the_slug(tmp_path):
    script(200, 120)
    f.save(str(tmp_path / "m.pdf"), marks=True)
    page = PdfReader(tmp_path / "m.pdf").pages[0]
    assert box(page.bleedbox) == box(page.trimbox)
    assert float(page.trimbox.left) == pytest.approx(SLUG)
    assert float(page.mediabox.width) == pytest.approx(200 + 2 * SLUG)


def test_a_plain_pdf_is_unchanged(tmp_path):
    script(200, 120)
    poster()
    f.save(str(tmp_path / "plain.pdf"))
    f.save(str(tmp_path / "zero.pdf"), bleed=0, marks=False)
    for name in ("plain.pdf", "zero.pdf"):
        page = PdfReader(tmp_path / name).pages[0]
        assert box(page.mediabox) == (0, 0, 200, 120)
        assert "/TrimBox" not in page and "/BleedBox" not in page
    assert (tmp_path / "plain.pdf").read_bytes() == (tmp_path / "zero.pdf").read_bytes()


def test_every_page_of_a_document_gets_the_same_treatment(tmp_path):
    script(200, 120)
    poster()
    f.new_page(100, 300)
    poster()
    f.save(str(tmp_path / "doc.pdf"), bleed=10, marks=True)
    margin = 10 + SLUG
    first, second = PdfReader(tmp_path / "doc.pdf").pages
    for page, (w, h) in ((first, (200, 120)), (second, (100, 300))):
        assert box(page.trimbox) == (round(margin, 3), round(margin, 3), round(margin + w, 3), round(margin + h, 3))
        assert float(page.mediabox.width) == pytest.approx(w + 2 * margin)
        assert float(page.bleedbox.width) == pytest.approx(w + 20)


# ---------------------------------------------------------------- what is drawn where
def test_drawing_past_the_edges_is_in_the_bleed_and_the_slug_is_clear(tmp_path):
    script(200, 120)
    poster()
    f.save(str(tmp_path / "x.pdf"), bleed=20)
    image = picture(tmp_path / "x.pdf")                      # the sheet is 240 x 160, the trim at (20, 20)
    assert image.size == (240, 160)
    assert image.getpixel((5, 5)) == RED                     # at (-15, -15) of the canvas: in the bleed
    assert image.getpixel((30, 30)) == RED                   # at (10, 10): on the page
    assert image.getpixel((100, 100)) == WHITE               # the background, on the page
    assert image.getpixel((235, 155)) == BLUE                # at (215, 135): in the bleed, bottom right


def test_a_background_fills_the_bleed_but_not_the_slug(tmp_path):
    script(200, 120)
    f.background("red")
    f.save(str(tmp_path / "bg.pdf"), bleed=20, marks=True)
    image = picture(tmp_path / "bg.pdf")
    edge = round(SLUG)
    assert image.getpixel((edge + 2, edge + 2)) == RED       # the outermost bleed
    assert image.getpixel((edge - 3, edge + 60)) == WHITE    # the slug
    assert image.getpixel((3, 3)) == WHITE


def test_clearing_the_clip_does_not_open_the_slug(tmp_path):
    script(200, 120)
    f.push()
    f.clip(f.path().rect(10, 10, 20, 20))
    f.no_clip()
    f.fill("red")
    f.rect(-500, -500, 1200, 1200)
    f.pop()
    f.save(str(tmp_path / "noclip.pdf"), bleed=20, marks=True)
    image = picture(tmp_path / "noclip.pdf")
    edge = round(SLUG)
    assert image.getpixel((edge + 2, edge + 2)) == RED
    assert image.getpixel((edge - 3, edge + 60)) == WHITE


def dark(image, x, y) -> bool:
    """Is there ink within a pixel of (x, y)? A 0.25 pt line is a pale grey at one pixel to the point."""
    around = [image.getpixel((x + dx, y + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    return min(sum(pixel) for pixel in around) < 700


def test_marks_are_drawn_at_the_trim_corners_outside_the_bleed(tmp_path):
    script(200, 120)
    f.save(str(tmp_path / "marks.pdf"), bleed=f.mm(3), marks=True)
    image = picture(tmp_path / "marks.pdf")
    margin = MM3 + SLUG
    start, end = f.mm(3) + f.mm(1), f.mm(3) + f.mm(1) + f.mm(5)
    mid = round(margin - (start + end) / 2)
    top = round(margin)                                      # the trim's top edge: row of the horizontal marks
    assert dark(image, mid, top) and dark(image, round(margin + 200 + (start + end) / 2), top)
    assert dark(image, round(margin), mid)                   # a vertical mark above the top-left corner
    assert dark(image, round(margin + 200), round(margin + 120 + (start + end) / 2))
    assert not dark(image, round(margin - start / 2), top)   # nothing in the gap beside the trim, nor on the page
    assert not dark(image, round(margin + 10), round(margin + 10))


def test_marks_are_there_only_when_asked(tmp_path):
    script(200, 120)
    f.save(str(tmp_path / "with.pdf"), bleed=20, marks=True)
    f.save(str(tmp_path / "without.pdf"), bleed=20)
    with_marks, without = picture(tmp_path / "with.pdf"), picture(tmp_path / "without.pdf")
    assert with_marks.getextrema() != ((255, 255), (255, 255), (255, 255))
    assert without.getextrema() == ((255, 255), (255, 255), (255, 255))        # a white page, drawn nothing


def test_live_text_and_layers_still_work_with_a_bleed(tmp_path):
    script(300, 160)
    f.background("white")
    f.fill("black")
    f.text_size(30)
    f.text("Print me", 20, 20)
    with f.layer("extra"):
        f.fill("blue")
        f.rect(-10, 100, 50, 80)
    f.save(str(tmp_path / "live.pdf"), bleed=10, marks=True)
    reader = PdfReader(tmp_path / "live.pdf")
    assert "Print me" in reader.pages[0].extract_text()
    assert [layer["/Name"] for layer in reader.trailer["/Root"]["/OCProperties"]["/OCGs"].get_object()] == ["extra"]
    assert box(reader.pages[0].trimbox)[0] == pytest.approx(10 + SLUG, abs=0.001)


def test_shapes_text_works_too(tmp_path):
    script(300, 160)
    f.text("Shapes", 20, 20)
    f.save(str(tmp_path / "shapes.pdf"), text="shapes", bleed=10)
    assert box(PdfReader(tmp_path / "shapes.pdf").pages[0].trimbox) == (10, 10, 310, 170)


# ---------------------------------------------------------------- asking for it
@pytest.mark.parametrize("name", ["a.png", "a.svg", "a.PNG"])
def test_bleed_and_marks_are_for_pdf_only(tmp_path, name):
    script()
    with pytest.raises(ValueError, match="PDF"):
        f.save(str(tmp_path / name), bleed=10)
    with pytest.raises(ValueError, match="PDF"):
        f.save(str(tmp_path / name), marks=True)
    assert not list(tmp_path.iterdir())


def test_bleed_and_marks_are_not_for_a_movie(tmp_path):
    script()
    with pytest.raises(ValueError, match="PDF"):
        f.save(str(tmp_path / "a.gif"), bleed=10)


@pytest.mark.parametrize("bleed, error", [(-1, ValueError), (float("inf"), ValueError), (float("nan"), ValueError),
                                           ("3mm", TypeError), (True, TypeError), (None, TypeError)])
def test_a_bad_bleed(tmp_path, bleed, error):
    script()
    with pytest.raises(error, match="bleed"):
        f.save(str(tmp_path / "a.pdf"), bleed=bleed)


def test_marks_must_be_true_or_false(tmp_path):
    script()
    with pytest.raises(TypeError, match="marks"):
        f.save(str(tmp_path / "a.pdf"), marks="yes")


# ---------------------------------------------------------------- animated sketches and the browser
def test_an_animated_sketch_saves_at_the_end_of_the_frame(tmp_path):
    out = tmp_path / "anim.pdf"

    def draw():
        f.background("red")
        f.save(str(out), bleed=10, marks=True)
        f.rect(-5, -5, 20, 20)          # drawn after the call: still in the file

    sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    sketch.run_namespace({"setup": lambda: f.size(200, 120), "draw": draw}, max_frames=1)
    page = PdfReader(out).pages[0]
    assert box(page.trimbox) == (pytest.approx(10 + SLUG, abs=0.001), pytest.approx(10 + SLUG, abs=0.001),
                                 pytest.approx(210 + SLUG, abs=0.001), pytest.approx(130 + SLUG, abs=0.001))

def run_in_session(source, width, height):
    """Run a script as the browser runner does; the host always ends a Session with stop() (web.py)."""
    session = Session(width, height)
    try:
        session.start(source, "sketch.py")
    finally:
        session.stop()


def test_it_works_under_a_web_session(tmp_path):
    out = tmp_path / "web.pdf"
    source = f"""
import funground as f
f.size(200, 120)
f.background("red")
f.save({str(out)!r}, bleed=f.mm(3), marks=True)
f.show()
"""
    run_in_session(source, 200, 120)
    page = PdfReader(out).pages[0]
    assert float(page.bleedbox.width) == pytest.approx(200 + 2 * f.mm(3))
    assert picture(out).getpixel((round(SLUG + 1), round(SLUG + 1))) == RED
