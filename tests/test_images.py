"""Loading images (S-077, contract P4, ADR-004): f.load_image() and the pictures it makes.

Every test image is made here, from pygame or by hand; nothing is downloaded.
"""
from __future__ import annotations

import os
import struct
import subprocess
import sys

import pygame
import pytest

import funground as p
from funground import api, imaging, ir
from funground.picture import Picture
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from conftest import ROOT, run_sketch

W, H = 48, 32                       # the test picture: red top-left block, blue top-right block
RED, BLUE, WHITE = (255, 0, 0), (0, 0, 255), (255, 255, 255)


def fresh(width=100, height=100):
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(width, height)
    return s


def script_sketch():
    return api.use_sketch(Sketch(platform=HeadlessPlatform()))


def make_surface(alpha=False) -> "pygame.Surface":
    surf = pygame.Surface((W, H), pygame.SRCALPHA if alpha else 0, 32 if alpha else 24)
    surf.fill(WHITE + (255,) if alpha else WHITE)
    surf.fill(RED, (0, 0, 16, 16))
    surf.fill(BLUE, (W - 16, 0, 16, 16))
    return surf


def px(pic: Picture, x: int, y: int) -> tuple[int, int, int, int]:
    """One pixel of a picture's own surface, (r, g, b, a) as stored (premultiplied)."""
    pic._flush()
    surf = pic._sketch._renderer.surface
    surf.flush()
    data = surf.get_data()
    i = y * surf.get_stride() + x * 4
    return (data[i + 2], data[i + 1], data[i], data[i + 3])


def near(a, b, tol=0):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def gif_bytes(surface) -> bytes:
    """A tiny GIF (pygame cannot write one): 4 colours, every pixel sent after a clear code."""
    palette = [WHITE, RED, BLUE, (0, 0, 0)]
    w, h = surface.get_size()
    bits, nbits = 0, 0
    out = bytearray()

    def put(code):
        nonlocal bits, nbits
        bits |= code << nbits
        nbits += 3
        while nbits >= 8:
            out.append(bits & 255)
            bits >>= 8
            nbits -= 8

    for y in range(h):
        for x in range(w):
            put(4)                                           # clear code
            put(palette.index(tuple(surface.get_at((x, y)))[:3]))
    put(4)
    put(5)                                                   # end code
    if nbits:
        out.append(bits & 255)
    blocks = b"".join(bytes([len(out[i:i + 255])]) + bytes(out[i:i + 255]) for i in range(0, len(out), 255))
    table = b"".join(bytes(c) for c in palette)
    return (b"GIF89a" + struct.pack("<HHBBB", w, h, 0x80 | 1, 0, 0) + table
            + b"\x2c" + struct.pack("<HHHHB", 0, 0, w, h, 0) + b"\x02" + blocks + b"\x00" + b"\x3b")


def exif_segment(orientation: int, order: str = "II") -> bytes:
    """A minimal APP1 Exif segment whose only tag is the orientation (0x0112)."""
    e = "<" if order == "II" else ">"
    tiff = (order.encode() + struct.pack(e + "HI", 42, 8) + struct.pack(e + "H", 1)
            + struct.pack(e + "HHI", 0x0112, 3, 1) + struct.pack(e + "HH", orientation, 0)
            + struct.pack(e + "I", 0))
    body = b"Exif\x00\x00" + tiff
    return b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body


def with_segment(jpeg: bytes, segment: bytes) -> bytes:
    assert jpeg[:2] == b"\xff\xd8"
    return jpeg[:2] + segment + jpeg[2:]


def make_jpeg(tmp_path, name="photo.jpg") -> bytes:
    path = tmp_path / name
    pygame.image.save(make_surface(), str(path))
    return path.read_bytes()


# Where the stored pixel (x, y) of a W x H image lands once it is upright (the EXIF table).
UPRIGHT = {
    1: lambda x, y: (x, y),
    2: lambda x, y: (W - 1 - x, y),
    3: lambda x, y: (W - 1 - x, H - 1 - y),
    4: lambda x, y: (x, H - 1 - y),
    5: lambda x, y: (y, x),
    6: lambda x, y: (H - 1 - y, x),
    7: lambda x, y: (H - 1 - y, W - 1 - x),
    8: lambda x, y: (y, W - 1 - x),
}


# ---- formats ---------------------------------------------------------------------------
def check_upright_test_picture(pic, tol=0):
    assert (pic.width, pic.height) == (W, H)
    assert near(px(pic, 8, 8), RED + (255,), tol)
    assert near(px(pic, W - 8, 8), BLUE + (255,), tol)
    assert near(px(pic, 24, 24), WHITE + (255,), tol)


@pytest.mark.parametrize("ext", ["png", "bmp", "tga"])
def test_lossless_formats_load_exactly(tmp_path, ext):
    path = tmp_path / f"pic.{ext}"
    pygame.image.save(make_surface(), str(path))
    pic = p.load_image(str(path))
    assert isinstance(pic, Picture)
    check_upright_test_picture(pic)


def test_jpeg_loads(tmp_path):
    make_jpeg(tmp_path, "pic.jpg")
    check_upright_test_picture(p.load_image(str(tmp_path / "pic.jpg")), tol=40)


def test_gif_loads_its_first_frame(tmp_path):
    path = tmp_path / "pic.gif"
    path.write_bytes(gif_bytes(make_surface()))
    check_upright_test_picture(p.load_image(str(path)))


def test_transparency_is_kept(tmp_path):
    surf = pygame.Surface((4, 4), pygame.SRCALPHA, 32)       # fully transparent to start
    surf.set_at((1, 1), (255, 0, 0, 128))
    surf.set_at((2, 2), (0, 255, 0, 255))
    pygame.image.save(surf, str(tmp_path / "t.png"))
    pic = p.load_image(str(tmp_path / "t.png"))
    assert px(pic, 0, 0) == (0, 0, 0, 0)
    assert near(px(pic, 1, 1), (128, 0, 0, 128), 1)          # Cairo keeps colour premultiplied
    assert px(pic, 2, 2) == (0, 255, 0, 255)


def test_semi_transparent_image_blends_when_drawn(tmp_path):
    surf = pygame.Surface((4, 4), pygame.SRCALPHA, 32)
    surf.fill((0, 0, 255, 128))
    pygame.image.save(surf, str(tmp_path / "t.png"))
    pic = p.load_image(str(tmp_path / "t.png"))
    script_sketch()
    p.size(10, 10)
    p.background("white")
    p.image(pic, 0, 0)
    p.save(str(tmp_path / "out.png"))
    r, g, b, a = pygame.image.load(str(tmp_path / "out.png")).get_at((1, 1))
    assert (a, b) == (255, 255) and 120 <= r <= 135 and 120 <= g <= 135


# ---- orientation ---------------------------------------------------------------------
@pytest.mark.parametrize("order", ["II", "MM"])
@pytest.mark.parametrize("orientation", range(1, 9))
def test_exif_orientation_turns_a_jpeg_upright(tmp_path, orientation, order):
    jpeg = with_segment(make_jpeg(tmp_path), exif_segment(orientation, order))
    path = tmp_path / "turned.jpg"
    path.write_bytes(jpeg)
    pic = p.load_image(str(path))
    where = UPRIGHT[orientation]
    swapped = orientation >= 5
    assert (pic.width, pic.height) == ((H, W) if swapped else (W, H))
    for stored, colour in (((8, 8), RED), ((W - 8, 8), BLUE), ((24, 24), WHITE)):
        x, y = where(*stored)
        assert near(px(pic, x, y), colour + (255,), 40), (orientation, order, stored)


def test_orientation_is_read_from_the_tag(tmp_path):
    for orientation in range(1, 9):
        for order in ("II", "MM"):
            jpeg = with_segment(make_jpeg(tmp_path), exif_segment(orientation, order))
            path = tmp_path / "t.jpg"
            path.write_bytes(jpeg)
            assert imaging.exif_orientation(str(path)) == orientation


def broken_segments():
    good = exif_segment(6)
    body = good[4:]
    yield "no exif"
    yield "cut short", b"\xff\xe1" + struct.pack(">H", 14) + body[:12]
    yield "bad byte order", b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body[:6] + b"XX" + body[8:]
    yield "bad magic", b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body[:8] + b"\x00\x00" + body[10:]
    yield "value 9", exif_segment(9)
    yield "value 0", exif_segment(0)
    yield "ifd past the end", (b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body[:10]
                              + struct.pack("<I", 9999) + body[14:])
    yield "count too big", b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body[:14] + struct.pack("<H", 200) + b"" + body[18:]
    yield "not exif", b"\xff\xe1" + struct.pack(">H", 8) + b"ABCDEF"


@pytest.mark.parametrize("case", list(broken_segments()), ids=lambda c: c if isinstance(c, str) else c[0])
def test_malformed_exif_means_upright_never_an_error(tmp_path, case):
    jpeg = make_jpeg(tmp_path)
    if not isinstance(case, str):
        jpeg = with_segment(jpeg, case[1])
    path = tmp_path / "odd.jpg"
    path.write_bytes(jpeg)
    pic = p.load_image(str(path))
    check_upright_test_picture(pic, tol=40)


def test_png_is_never_turned(tmp_path):
    path = tmp_path / "pic.png"
    pygame.image.save(make_surface(), str(path))
    assert imaging.exif_orientation(str(path)) == 1


# ---- size, scaling and drawing ---------------------------------------------------------------
def test_width_and_height_are_the_image_size_in_pixels(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    pic = p.load_image(str(tmp_path / "pic.png"))
    assert (pic.width, pic.height) == (W, H)
    assert repr(pic) == f"<Picture {W} x {H}>"


def test_it_works_before_size_is_called(tmp_path):
    script_sketch()
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    pic = p.load_image(str(tmp_path / "pic.png"))
    assert pic.width == W


def test_image_draws_it_at_its_own_size_in_logical_pixels(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    fresh(100, 60)
    pic = p.load_image(str(tmp_path / "pic.png"))
    s = api.active_sketch()
    s.run_namespace({"draw": lambda: (p.background("white"), p.image(pic, 10, 5))}, max_frames=1)
    (w, _h), rgb = s.last_frame

    def at(x, y):
        return tuple(rgb[(y * w + x) * 3:(y * w + x) * 3 + 3])

    assert at(12, 7) == RED and at(10 + W - 2, 7) == BLUE
    assert at(10 + W + 2, 7) == WHITE and at(12, 5 + H + 2) == WHITE


def test_image_scales_a_loaded_picture(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    fresh(100, 60)
    pic = p.load_image(str(tmp_path / "pic.png"))
    s = api.active_sketch()
    s.run_namespace({"draw": lambda: (p.background("white"), p.image(pic, 0, 0, 24, 16))}, max_frames=1)
    (w, _h), rgb = s.last_frame

    def at(x, y):
        return tuple(rgb[(y * w + x) * 3:(y * w + x) * 3 + 3])

    assert at(2, 2) == RED and at(22, 2) == BLUE and at(12, 12) == WHITE
    assert at(30, 2) == WHITE            # nothing outside the 24 x 16 box


def test_on_a_scaled_display_its_pixels_are_stretched_over_the_same_logical_size(tmp_path, monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    script_sketch()
    p.size(100, 60)
    pic = p.load_image(str(tmp_path / "pic.png"))
    p.background("white")
    p.image(pic, 0, 0)
    p.save(str(tmp_path / "out.png"))
    out = pygame.image.load(str(tmp_path / "out.png"))
    assert out.get_size() == (200, 120)
    assert tuple(out.get_at((30, 30)))[:3] == RED               # logical (15, 15) is in the red block
    assert tuple(out.get_at((2 * W + 4, 30)))[:3] == WHITE      # logical width is still W


def test_a_loaded_picture_can_be_drawn_on(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    fresh()
    pic = p.load_image(str(tmp_path / "pic.png"))
    pic.no_stroke()
    pic.fill("green")
    pic.rect(20, 20, 8, 8)
    assert px(pic, 24, 24) == (0, 255, 0, 255)
    check_corners = (px(pic, 8, 8), px(pic, W - 8, 8))
    assert check_corners == (RED + (255,), BLUE + (255,))       # the rest of the image is still there


def test_drawing_on_a_loaded_picture_composes_with_its_pixels(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    fresh()
    pic = p.load_image(str(tmp_path / "pic.png"))
    pic.no_stroke()
    pic.fill((0, 0, 0, 128))
    pic.rect(0, 0, 16, 16)                                      # half-black over red
    r, g, b, a = px(pic, 8, 8)
    assert 120 <= r <= 135 and g == 0 and b == 0 and a == 255


def test_each_loaded_picture_has_its_own_name(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    fresh()
    a, b = p.load_image(str(tmp_path / "pic.png")), p.load_image(str(tmp_path / "pic.png"))
    g = p.create_graphics(5, 5)
    assert len({a.name, b.name, g.name}) == 3


def test_a_picture_method_list_does_not_include_load_image(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    fresh()
    pic = p.load_image(str(tmp_path / "pic.png"))
    with pytest.raises(AttributeError):
        pic.load_image


# ---- PDF / SVG (P3, P4) -----------------------------------------------------------------
@pytest.mark.parametrize("ext", ["pdf", "svg"])
def test_vector_export_embeds_the_pixels_of_a_loaded_picture(tmp_path, ext):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    script_sketch()
    p.size(100, 60)
    pic = p.load_image(str(tmp_path / "pic.png"))
    assert pic._snapshot().history is None
    p.image(pic, 0, 0)
    out = tmp_path / f"out.{ext}"
    p.save(str(out))
    data = out.read_bytes()
    assert (b"/Subtype /Image" in data) if ext == "pdf" else (b"<image" in data)


def test_picture_save_embeds_pixels_until_an_opaque_background_starts_a_history(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    fresh()
    pic = p.load_image(str(tmp_path / "pic.png"))
    pic.save(str(tmp_path / "a.pdf"))
    assert b"/Subtype /Image" in (tmp_path / "a.pdf").read_bytes()
    pic.background("white")
    pic.no_stroke()
    pic.fill("red")
    pic.rect(0, 0, 10, 10)
    assert pic._snapshot().history is not None
    pic.save(str(tmp_path / "b.pdf"))
    assert b"/Subtype /Image" not in (tmp_path / "b.pdf").read_bytes()


def test_drawing_a_loaded_picture_into_a_pdf_after_an_opaque_background_is_vector(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    script_sketch()
    p.size(100, 60)
    pic = p.load_image(str(tmp_path / "pic.png"))
    pic.background("white")
    pic.fill("red")
    pic.circle(10, 10, 8)
    p.image(pic, 0, 0)
    p.save(str(tmp_path / "out.pdf"))
    assert b"/Subtype /Image" not in (tmp_path / "out.pdf").read_bytes()


# ---- where files are looked for (T11) ------------------------------------------------------
def run_text(path, text):
    path.write_text(text, encoding="utf-8")
    return run_sketch(path, frames=2)


def test_a_relative_path_is_found_next_to_the_sketch_file_first(tmp_path, monkeypatch):
    sketch_dir, other = tmp_path / "sketch", tmp_path / "elsewhere"
    sketch_dir.mkdir(), other.mkdir()
    pygame.image.save(make_surface(), str(sketch_dir / "pic.png"))          # red top-left
    odd = pygame.Surface((W, H))
    odd.fill((0, 255, 0))
    pygame.image.save(odd, str(other / "pic.png"))                          # all green
    monkeypatch.chdir(other)
    (w, _h), rgb = run_text(sketch_dir / "s.py", (
        "import funground as f\n"
        "pic = f.load_image('pic.png')\n"
        "def setup():\n    f.size(60, 40)\n"
        "def draw():\n    f.image(pic, 0, 0)\n"
        "f.run()\n"))
    assert tuple(rgb[(4 * w + 4) * 3:(4 * w + 4) * 3 + 3]) == RED          # not the green one


def test_then_the_current_folder(tmp_path, monkeypatch):
    sketch_dir, other = tmp_path / "sketch", tmp_path / "elsewhere"
    sketch_dir.mkdir(), other.mkdir()
    pygame.image.save(make_surface(), str(other / "only_here.png"))
    monkeypatch.chdir(other)
    (w, _h), rgb = run_text(sketch_dir / "s.py", (
        "import funground as f\n"
        "def setup():\n    f.size(60, 40)\n"
        "def draw():\n    f.image(f.load_image('only_here.png'), 0, 0)\n"
        "f.run()\n"))
    assert tuple(rgb[(4 * w + 4) * 3:(4 * w + 4) * 3 + 3]) == RED


def test_a_missing_file_names_both_places(tmp_path, monkeypatch):
    sketch_dir, other = tmp_path / "sketch", tmp_path / "elsewhere"
    sketch_dir.mkdir(), other.mkdir()
    monkeypatch.chdir(other)
    with pytest.raises(FileNotFoundError) as caught:
        run_text(sketch_dir / "s.py", "import funground as f\nf.load_image('nope.png')\nf.size(10, 10)\n")
    message = str(caught.value)
    assert str(sketch_dir) in message and str(other) in message and "nope.png" in message


def test_a_missing_absolute_path_is_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="nope.png"):
        p.load_image(str(tmp_path / "nope.png"))


# ---- errors ------------------------------------------------------------------------------------
def test_an_svg_file_raises_value_error_pointing_to_load_svg(tmp_path):
    (tmp_path / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"/>')
    with pytest.raises(ValueError, match="load_svg"):
        p.load_image(str(tmp_path / "a.svg"))


def test_an_svg_with_the_wrong_extension_is_still_refused(tmp_path):
    (tmp_path / "a.png").write_text('<?xml version="1.0"?>\n<svg width="4" height="4"/>')
    with pytest.raises(ValueError, match="SVG"):
        p.load_image(str(tmp_path / "a.png"))


@pytest.mark.parametrize("content", [b"hello, I am not a picture", b""])
def test_a_file_that_is_not_an_image_raises_value_error(tmp_path, content):
    (tmp_path / "words.png").write_bytes(content)
    with pytest.raises(ValueError, match="not an image"):
        p.load_image(str(tmp_path / "words.png"))


def test_a_truncated_png_raises_value_error(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    data = (tmp_path / "pic.png").read_bytes()
    (tmp_path / "cut.png").write_bytes(data[:20])
    with pytest.raises(ValueError):
        p.load_image(str(tmp_path / "cut.png"))


# ---- headless, scripts, animated sketches ------------------------------------------------------
def test_it_works_with_no_display_at_all(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    script = tmp_path / "s.py"
    script.write_text(
        "import funground as f\n"
        "f.size(60, 40)\n"
        "pic = f.load_image('pic.png')\n"
        "f.background('white')\n"
        "f.image(pic, 0, 0)\n"
        "f.save('out.png')\n", encoding="utf-8")
    env = dict(os.environ, SDL_VIDEODRIVER="no-such-driver", FUNGROUND_HEADLESS="1", PYTHONPATH=str(ROOT))
    done = subprocess.run([sys.executable, str(script)], cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    out = pygame.image.load(str(tmp_path / "out.png"))
    assert tuple(out.get_at((4, 4)))[:3] == RED


def test_it_works_in_a_script(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    (w, _h), rgb = run_text(tmp_path / "script.py", (
        "import funground as f\n"
        "f.size(60, 40)\n"
        "f.background('white')\n"
        "f.image(f.load_image('pic.png'), 0, 0)\n"))
    assert tuple(rgb[(4 * w + 4) * 3:(4 * w + 4) * 3 + 3]) == RED


def test_it_works_in_an_animated_sketch(tmp_path):
    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    (w, _h), rgb = run_text(tmp_path / "sketch.py", (
        "import funground as f\n"
        "def setup():\n    f.size(60, 40)\n"
        "def draw():\n"
        "    f.background('white')\n"
        "    f.image(f.load_image('pic.png'), 0, 0)\n"
        "f.run()\n"))
    assert tuple(rgb[(4 * w + 4) * 3:(4 * w + 4) * 3 + 3]) == RED


def test_the_image_op_names_the_picture_and_records_no_pixels(tmp_path):
    import json

    pygame.image.save(make_surface(), str(tmp_path / "pic.png"))
    s = fresh(60, 40)
    pic = p.load_image(str(tmp_path / "pic.png"))
    s.run_namespace({"draw": lambda: p.image(pic, 1, 2)}, max_frames=1)
    text = json.dumps(ir.Frame(list(s.last_ops)).to_jsonable())
    assert pic.name in text and "pixels" not in text
