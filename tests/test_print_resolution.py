"""Print resolution (story S-163, contract row D3): f.save("x.png", dpi=300).

A page is drawn again at dpi / 72 pixels to the point, so it is sharp, not a stretched screen picture. The
PNG states its resolution in a pHYs chunk.
"""
from __future__ import annotations

import struct

import pytest
from PIL import Image, ImageChops, ImageStat

import funground as f
from funground import api
from funground.export import MAX_PNG_PIXELS, pixel_size
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch
from funground.web import Session


def script(width, height) -> Sketch:
    sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    sketch.size(width, height)
    return sketch


def physical_resolution(path) -> tuple[int, int, int] | None:
    """The pHYs chunk of a PNG: (pixels per metre across, down, unit), or None when it has none."""
    data = path.read_bytes()
    at = data.find(b"pHYs")
    return None if at < 0 else struct.unpack(">IIB", data[at + 4:at + 13])


def a3_poster() -> None:
    f.background("white")
    f.no_stroke()
    f.fill("tomato")
    f.circle(300, 400, 300)
    f.fill("navy")
    f.rect(500, 800, 250, 300)
    f.stroke("black")
    f.stroke_width(1)
    f.line(40, 40, 800, 1150)
    f.fill("black")
    f.text_size(60)
    f.text("A3 poster", 60, 900)


# ---------------------------------------------------------------- size and metadata
def test_an_a3_page_at_300_dpi(tmp_path):
    script(*f.page_size("A3"))                               # 842 x 1191 points
    a3_poster()
    f.save(str(tmp_path / "a3.png"), dpi=300)
    image = Image.open(tmp_path / "a3.png")
    assert image.size == (3508, 4963)                        # 842 x 300 / 72 = 3508.3; 1191 x 300 / 72 = 4962.5, a half up
    assert physical_resolution(tmp_path / "a3.png") == (11811, 11811, 1)
    assert [round(d) for d in image.info["dpi"]] == [300, 300]


def test_an_a_series_size_in_millimetres_gives_the_printers_pixels(tmp_path):
    script(842, 1190)                                        # A3 as the printers round it: 297 x 420 mm
    f.save(str(tmp_path / "a3.png"), dpi=300)
    assert Image.open(tmp_path / "a3.png").size == (3508, 4958)


def test_sizes_are_rounded_to_the_nearest_pixel_a_half_going_up():
    assert pixel_size(842, 1191, 300) == (3508, 4963)        # 3508.33 down, 4962.5 up
    assert pixel_size(10, 10, 72) == (10, 10)
    assert pixel_size(1, 1, 150) == (2, 2)                   # 2.08
    assert pixel_size(3, 6, 12) == (1, 1)                    # 0.5 up; 1.0
    assert pixel_size(5, 5, 12) == (1, 1)                    # 0.83


def test_without_dpi_the_png_is_the_screens_resolution(tmp_path):
    script(120, 80)
    f.background("red")
    f.save(str(tmp_path / "plain.png"))
    assert Image.open(tmp_path / "plain.png").size == (120, 80)
    assert physical_resolution(tmp_path / "plain.png") is None


def test_a_fractional_dpi(tmp_path):
    script(144, 72)
    f.save(str(tmp_path / "x.png"), dpi=150.5)
    assert Image.open(tmp_path / "x.png").size == (301, 151)


# ---------------------------------------------------------------- it is the same drawing, drawn sharp
def test_it_matches_the_screen_picture_when_shrunk(tmp_path):
    script(*f.page_size("A3"))
    a3_poster()
    f.save(str(tmp_path / "ref.png"))
    f.save(str(tmp_path / "print.png"), dpi=300)
    reference = Image.open(tmp_path / "ref.png").convert("RGB")
    shrunk = Image.open(tmp_path / "print.png").convert("RGB").resize(reference.size, Image.Resampling.BOX)
    difference = ImageStat.Stat(ImageChops.difference(reference, shrunk))
    assert max(difference.mean) < 1.0                        # tiny: edges differ a little in anti-aliasing
    assert max(difference.extrema[i][1] for i in range(3)) < 255


def test_it_is_drawn_again_not_stretched(tmp_path):
    script(100, 50)
    f.background("white")
    f.stroke("black")
    f.stroke_width(1)
    f.line(10, 25, 90, 25)                                   # one point wide: 4.17 pixels at 300 dpi
    f.save(str(tmp_path / "sharp.png"), dpi=300)
    image = Image.open(tmp_path / "sharp.png").convert("L")
    column = [image.getpixel((200, y)) for y in range(image.height)]
    assert sum(1 for v in column if v == 0) >= 3             # solid black rows, not a grey smear
    assert sum(1 for v in column if 0 < v < 255) <= 2        # and only the two edge pixels are partly covered


def test_a_page_of_text_is_drawn_at_the_resolution(tmp_path):
    script(200, 100)
    f.background("white")
    f.fill("black")
    f.text_size(40)
    f.text("Hi", 10, 10)
    f.save(str(tmp_path / "t.png"), dpi=288)                 # 4 pixels to the point
    image = Image.open(tmp_path / "t.png").convert("L")
    assert image.size == (800, 400)
    ink = [(x, y) for x in range(0, 800, 2) for y in range(0, 400, 2) if image.getpixel((x, y)) < 128]
    assert ink and min(x for x, _ in ink) >= 40 - 8 and max(x for x, _ in ink) < 4 * 200


# ---------------------------------------------------------------- pages and animated sketches
def test_every_page_of_a_document_is_written_at_the_resolution(tmp_path):
    script(100, 50)
    f.background("red")
    f.new_page(60, 40)
    f.background("blue")
    f.save(str(tmp_path / "doc.png"), dpi=144)
    first, second = Image.open(tmp_path / "doc_1.png"), Image.open(tmp_path / "doc_2.png")
    assert first.size == (200, 100) and second.size == (120, 80)
    assert first.convert("RGB").getpixel((5, 5)) == (255, 0, 0)
    assert second.convert("RGB").getpixel((5, 5)) == (0, 0, 255)
    assert physical_resolution(tmp_path / "doc_1.png") == (5669, 5669, 1)


def test_an_animated_sketch_saves_at_the_end_of_the_frame(tmp_path):
    out = tmp_path / "anim.png"

    def draw():
        f.background("white")
        f.save(str(out), dpi=144)
        f.fill("red")
        f.rect(0, 0, 30, 30)                                 # drawn after the call: still in the file

    sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    sketch.run_namespace({"setup": lambda: f.size(100, 50), "draw": draw}, max_frames=1)
    image = Image.open(out).convert("RGB")
    assert image.size == (200, 100)
    assert image.getpixel((20, 20)) == (255, 0, 0) and image.getpixel((150, 80)) == (255, 255, 255)
    assert physical_resolution(out) == (5669, 5669, 1)

def run_in_session(source, width, height):
    """Run a script as the browser runner does; the host always ends a Session with stop() (web.py)."""
    session = Session(width, height)
    try:
        session.start(source, "sketch.py")
    finally:
        session.stop()


def test_it_works_under_a_web_session(tmp_path):
    out = tmp_path / "web.png"
    source = f"""
import funground as f
f.size(100, 50)
f.background("red")
f.save({str(out)!r}, dpi=216)
f.show()
"""
    run_in_session(source, 100, 50)
    image = Image.open(out)
    assert image.size == (300, 150)
    assert physical_resolution(out) == (8504, 8504, 1)


# ---------------------------------------------------------------- the guard
def test_a_page_too_big_for_memory_is_refused_before_it_is_drawn(tmp_path):
    script(2384, 3370)                                       # A0: 9933 x 14042 pixels at 300 dpi, 139 million
    with pytest.raises(ValueError) as error:
        f.save(str(tmp_path / "a0.png"), dpi=300)
    message = str(error.value)
    assert "9933 x 14042" in message and "120 million" in message and "PDF" in message
    assert not list(tmp_path.iterdir())
    f.save(str(tmp_path / "a0_150.png"), dpi=150)            # a quarter of the pixels: allowed
    assert Image.open(tmp_path / "a0_150.png").size == (4967, 7021)


def test_the_limit_is_in_pixels_not_dpi():
    assert MAX_PNG_PIXELS == 120_000_000
    assert 4961 * 7016 < MAX_PNG_PIXELS                      # A2 at 300 dpi is allowed
    assert 9933 * 14042 > MAX_PNG_PIXELS                     # A0 at 300 dpi is not


def test_an_animated_sketch_is_refused_at_the_call(tmp_path):
    seen: list[str] = []

    def draw():
        try:
            f.save(str(tmp_path / "huge.png"), dpi=3000)
        except ValueError as error:
            seen.append(str(error))

    sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    sketch.run_namespace({"setup": lambda: f.size(400, 300), "draw": draw}, max_frames=1)
    assert seen and "120 million" in seen[0]


# ---------------------------------------------------------------- asking for it
@pytest.mark.parametrize("name", ["a.pdf", "a.svg", "a.PDF", "a.gif", "a.mp4"])
def test_vectors_and_movies_have_no_resolution(tmp_path, name):
    script(100, 50)
    with pytest.raises(ValueError, match="no resolution"):
        f.save(str(tmp_path / name), dpi=300)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("dpi, error", [(0, ValueError), (-300, ValueError), (float("inf"), ValueError),
                                         (float("nan"), ValueError), ("300", TypeError), (True, TypeError)])
def test_a_bad_dpi(tmp_path, dpi, error):
    script(100, 50)
    with pytest.raises(error, match="dpi"):
        f.save(str(tmp_path / "a.png"), dpi=dpi)


def test_dpi_and_bleed_are_each_for_their_own_file(tmp_path):
    script(100, 50)
    with pytest.raises(ValueError, match="PDF"):
        f.save(str(tmp_path / "a.png"), dpi=300, bleed=10)
