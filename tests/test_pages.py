"""Pages (S-084, contract R16, R17, D1): a script can make a document of several pages.

new_page() ends one page and starts a blank one, page_count() counts them, page_size() names the
sizes, save() writes every page (one PDF, or numbered PNG/SVG files) and show() flips between them.
"""
from __future__ import annotations

import re
import threading
import time
import warnings
import zlib

import pygame
import pytest

import funground as p
from funground import api
from funground.capabilities import FungroundWarning
from funground.platform.base import InputEvent
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def script() -> Sketch:
    return api.use_sketch(Sketch(platform=HeadlessPlatform()))


def pixel(path, x, y):
    return tuple(pygame.image.load(str(path)).get_at((x, y)))


def pdf_text(path) -> bytes:
    """A PDF's bytes with its compressed streams opened, so its page objects can be read."""
    data = path.read_bytes()
    parts = [data]
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        try:
            parts.append(zlib.decompressobj().decompress(m.group(1)))   # keeps a final CR/LF data byte
        except zlib.error:
            pass
    return b"\n".join(parts)


def pdf_pages(path) -> list[tuple[float, float]]:
    """The (width, height) of each page, read from the /MediaBox of each /Type /Page object."""
    text = pdf_text(path)
    count = len(re.findall(rb"/Type\s*/Page\b(?!s)", text))
    boxes = [tuple(float(v) for v in m.group(1).split()[2:4])
             for m in re.finditer(rb"/MediaBox\s*\[([^\]]*)\]", text)]
    assert count == len(boxes)
    return boxes


# ---------------------------------------------------------------- D1: page sizes
@pytest.mark.parametrize("name, size", [
    ("A3", (842, 1191)), ("A4", (595, 842)), ("A5", (420, 595)), ("B5", (499, 709)),
    ("Letter", (612, 792)), ("Legal", (612, 1008)), ("Tabloid", (792, 1224)), ("Square", (600, 600)),
])
def test_page_size_table(name, size):
    assert p.page_size(name) == size
    assert p.page_size(name, landscape=True) == (size[1], size[0])


def test_page_size_names_ignore_case():
    assert p.page_size("a4") == (595, 842)
    assert p.page_size("LETTER") == (612, 792)
    assert p.page_size("square", landscape=True) == (600, 600)


def test_a_landscape_suffix_turns_the_page_on_its_side():
    assert p.page_size("A4Landscape") == (842, 595)
    assert p.page_size("letterlandscape") == (792, 612)
    assert p.page_size("A4Landscape", landscape=True) == (842, 595)      # not turned back again


def test_unknown_page_size_lists_the_names():
    with pytest.raises(ValueError) as err:
        p.page_size("A9")
    for name in ("A3", "A4", "A5", "B5", "Letter", "Legal", "Tabloid", "Square"):
        assert name in str(err.value)
    with pytest.raises(ValueError):
        p.page_size("")
    with pytest.raises(TypeError):
        p.page_size(4)


def test_page_size_is_a_size_for_size():
    script()
    p.size(*p.page_size("A5"))
    assert (p.width, p.height) == (420, 595)


# ---------------------------------------------------------------- R16: pages
def test_one_page_is_a_plain_script():
    script()
    assert p.page_count() == 0
    p.size(40, 30)
    assert p.page_count() == 1


def test_new_page_before_size_starts_the_first_page():
    script()
    p.new_page("A4")
    assert p.page_count() == 1
    assert (p.width, p.height) == (595, 842)
    p.background("red")                                   # a canvas now exists
    assert p.get(10, 10).r == 255


def test_new_page_before_size_without_a_size_uses_the_default_canvas():
    script()
    p.new_page()
    assert p.page_count() == 1
    assert (p.width, p.height) == (640, 480)


def test_new_page_counts_and_follows_the_size():
    script()
    p.size(40, 30)
    p.new_page()
    assert (p.page_count(), p.width, p.height) == (2, 40, 30)          # keeps the size
    p.new_page(100, 60)
    assert (p.page_count(), p.width, p.height) == (3, 100, 60)
    p.new_page("A5")
    assert (p.page_count(), p.width, p.height) == (4, 420, 595)
    p.new_page("A5Landscape")
    assert (p.page_count(), p.width, p.height) == (5, 595, 420)
    p.new_page()
    assert (p.width, p.height) == (595, 420)                           # the current page's size


def test_new_page_starts_blank_and_the_old_page_is_kept(tmp_path):
    script()
    p.size(20, 20)
    p.background("red")
    p.new_page()
    assert p.get(5, 5).a == 0                                         # blank (transparent), not red
    p.background("blue")
    p.save(str(tmp_path / "d.png"))
    assert pixel(tmp_path / "d_1.png", 5, 5) == (255, 0, 0, 255)
    assert pixel(tmp_path / "d_2.png", 5, 5) == (0, 0, 255, 255)


def test_drawing_get_and_pixels_act_on_the_current_page():
    script()
    p.size(10, 10)
    p.background("red")
    p.new_page(6, 4)
    p.background("lime")
    p.load_pixels()
    assert len(p.pixels) == 6 * 4 * 4
    assert tuple(p.pixels[:4]) == (0, 255, 0, 255)
    assert p.get(0, 0) == p.get(5, 3)
    p.set(1, 1, "blue")
    assert (p.get(1, 1).r, p.get(1, 1).b) == (0, 255)
    p.filter("invert")
    assert p.get(0, 0).r == 255                                       # inverted green -> magenta
    p.new_page()
    assert p.pixels is None                                           # a new page, nothing loaded


def test_transform_clip_and_open_pushes_start_afresh_but_style_carries_over(tmp_path):
    s = script()
    p.size(40, 40)
    p.fill("red")
    p.stroke_width(5)
    p.text_size(33)
    p.translate(30, 0)
    p.clip(p.path().move_to(0, 0).line_to(5, 0).line_to(5, 5).line_to(0, 5).close())
    p.push()
    p.new_page()
    assert s.style.stroke_width == 5 and s.style.text_size == 33      # settings carry over
    assert s.style.fill == s.read_color("red")
    p.no_stroke()
    p.rect(0, 0, 10, 10)                                              # no translate, no clip
    p.rect(20, 20, 10, 10)
    p.save(str(tmp_path / "s.png"))
    assert pixel(tmp_path / "s_2.png", 5, 5) == (255, 0, 0, 255)
    assert pixel(tmp_path / "s_2.png", 25, 25) == (255, 0, 0, 255)
    with pytest.warns(FungroundWarning):
        p.pop()                                                       # the push stayed on page 1


def test_a_fill_set_inside_an_open_push_is_undone_on_the_new_page():
    s = script()
    p.size(10, 10)
    p.fill("red")
    p.push()
    p.fill("blue")
    p.new_page()
    assert s.style.fill == s.read_color("red")


def test_new_page_in_an_animated_sketch_is_an_error():
    s = script()

    def draw():
        p.new_page()

    with pytest.raises(RuntimeError, match="script"):
        s.run_namespace({"draw": draw}, max_frames=1)
    s = script()
    with pytest.raises(RuntimeError, match="script"):
        s.run_namespace({"setup": lambda: (p.size(20, 20), p.new_page("A4")), "draw": lambda: None},
                        max_frames=1)


def test_new_page_checks_its_numbers():
    script()
    p.size(10, 10)
    with pytest.raises(ValueError):
        p.new_page(0, 10)
    with pytest.raises(ValueError):
        p.new_page(10, -1)
    with pytest.raises(ValueError):
        p.new_page(10)                      # one number alone
    with pytest.raises(ValueError):
        p.new_page("A4", 10)                # a name stands alone
    with pytest.raises(ValueError, match="A4"):
        p.new_page("A9")                    # unknown name: the message lists the known ones
    with pytest.raises(TypeError):
        p.new_page([10], 10)
    assert p.page_count() == 1              # none of those added a page


def test_size_again_starts_a_new_document():
    script()
    p.new_page("A4")
    p.new_page()
    assert p.page_count() == 2
    p.size(10, 10)
    assert p.page_count() == 1


# ---------------------------------------------------------------- R17: saving
def test_pdf_has_every_page_at_its_own_size(tmp_path):
    script()
    p.new_page("A5")
    p.background("ivory")
    p.circle(100, 100, 50)
    p.new_page()
    p.text("inside", 20, 20)
    p.new_page("A4Landscape")
    p.rect(10, 10, 100, 100)
    p.save(str(tmp_path / "book.pdf"))
    assert pdf_pages(tmp_path / "book.pdf") == [(420, 595), (420, 595), (842, 595)]
    assert not (tmp_path / "book_1.pdf").exists()


def test_pdf_pages_with_different_sizes_in_any_order(tmp_path):
    script()
    p.size(100, 50)
    p.new_page(30, 70)
    p.new_page(100, 50)
    p.new_page("Letter")
    p.save(str(tmp_path / "m.pdf"))
    assert pdf_pages(tmp_path / "m.pdf") == [(100, 50), (30, 70), (100, 50), (612, 792)]


def test_a_single_page_pdf_is_as_before(tmp_path):
    script()
    p.size(70, 40)
    p.background("red")
    p.save(str(tmp_path / "one.pdf"))
    assert pdf_pages(tmp_path / "one.pdf") == [(70, 40)]


def test_pdf_embeds_rasters_on_their_own_page(tmp_path):
    script()
    p.size(20, 20)
    p.background("white")
    p.new_page(30, 30)
    p.load_pixels()
    for i in range(0, len(p.pixels), 4):
        p.pixels[i:i + 4] = bytes([200, 30, 30, 255])
    p.update_pixels()                                                 # a raster op on page 2
    pic = p.create_graphics(8, 8)
    pic.background("blue")
    p.image(pic, 2, 2)
    p.save(str(tmp_path / "r.pdf"))
    assert pdf_pages(tmp_path / "r.pdf") == [(20, 20), (30, 30)]
    assert b"/Subtype /Image" in pdf_text(tmp_path / "r.pdf")


def test_pdf_saved_twice_gives_the_same_pages(tmp_path):
    script()
    p.new_page("A5")
    p.new_page()
    p.save(str(tmp_path / "a.pdf"))
    p.save(str(tmp_path / "b.pdf"))
    assert pdf_pages(tmp_path / "a.pdf") == pdf_pages(tmp_path / "b.pdf")


def test_png_with_several_pages_is_numbered(tmp_path):
    script()
    p.size(12, 8)
    p.background("red")
    p.new_page(20, 10)
    p.background("lime")
    p.new_page(6, 6)
    p.background("blue")
    p.save(str(tmp_path / "shot.png"))
    names = sorted(f.name for f in tmp_path.iterdir())
    assert names == ["shot_1.png", "shot_2.png", "shot_3.png"]
    sizes = [pygame.image.load(str(tmp_path / n)).get_size() for n in names]
    assert sizes == [(12, 8), (20, 10), (6, 6)]
    assert pixel(tmp_path / "shot_1.png", 1, 1) == (255, 0, 0, 255)
    assert pixel(tmp_path / "shot_2.png", 1, 1) == (0, 255, 0, 255)
    assert pixel(tmp_path / "shot_3.png", 1, 1) == (0, 0, 255, 255)


def test_png_numbers_go_before_the_extension_in_the_same_folder(tmp_path):
    script()
    p.size(5, 5)
    p.new_page()
    folder = tmp_path / "a.b"
    folder.mkdir()
    p.save(str(folder / "x.png"))
    assert sorted(f.name for f in folder.iterdir()) == ["x_1.png", "x_2.png"]


def test_svg_with_several_pages_is_numbered(tmp_path):
    script()
    p.size(50, 30)
    p.circle(10, 10, 5)
    p.new_page(80, 40)
    p.rect(5, 5, 20, 20)
    p.save(str(tmp_path / "v.svg"))
    assert sorted(f.name for f in tmp_path.iterdir()) == ["v_1.svg", "v_2.svg"]
    one = (tmp_path / "v_1.svg").read_text(encoding="utf-8")
    two = (tmp_path / "v_2.svg").read_text(encoding="utf-8")
    assert 'viewBox="0 0 50 30"' in one and 'viewBox="0 0 80 40"' in two
    assert "<path" in one and "<path" in two


def test_one_page_png_and_svg_keep_the_plain_name(tmp_path):
    script()
    p.size(12, 8)
    p.background("red")
    p.save(str(tmp_path / "plain.png"))
    p.save(str(tmp_path / "plain.svg"))
    assert sorted(f.name for f in tmp_path.iterdir()) == ["plain.png", "plain.svg"]


def test_the_script_can_go_on_after_a_save(tmp_path):
    script()
    p.size(10, 10)
    p.new_page()
    p.save(str(tmp_path / "a.pdf"))
    p.new_page("A5")
    p.save(str(tmp_path / "b.pdf"))
    assert len(pdf_pages(tmp_path / "a.pdf")) == 2
    assert len(pdf_pages(tmp_path / "b.pdf")) == 3


# ---------------------------------------------------------------- R17: show()
def test_show_headless_returns_at_once_with_pages():
    script()
    p.new_page("A5")
    p.new_page()
    started = time.perf_counter()
    p.show()
    assert time.perf_counter() - started < 1


class Windows:
    """Record each window the real platform opens (size and title), without changing what it does."""

    def __init__(self, sketch: Sketch) -> None:
        self.opened: list[tuple[int, int, str]] = []
        platform = sketch._platform
        real = platform.open_window

        def open_window(width, height, title):
            self.opened.append((width, height, title))
            return real(width, height, title)

        platform.open_window = open_window

    def wait_for(self, count: int) -> bool:
        for _ in range(250):
            if len(self.opened) >= count:
                return True
            time.sleep(0.02)
        return False


def key(code):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=code, unicode="", mod=0))


def test_show_flips_pages_with_the_arrow_keys(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.delenv("FUNGROUND_HEADLESS", raising=False)
    s = api.use_sketch(Sketch())
    p.size(30, 20, title="book")
    p.background("red")
    p.new_page(40, 30)
    p.background("lime")
    p.new_page(50, 40)
    p.background("blue")
    windows = Windows(s)
    seen = []

    def keys():
        for _ in range(250):
            if pygame.display.get_init() and windows.opened:
                break
            time.sleep(0.02)
        for code in (pygame.K_LEFT, pygame.K_LEFT, pygame.K_RIGHT):
            expected = len(windows.opened) + 1
            key(code)
            seen.append(windows.wait_for(expected))
        key(pygame.K_ESCAPE)

    timer = threading.Thread(target=keys)
    timer.start()
    started = time.perf_counter()
    p.show()
    timer.join()
    assert time.perf_counter() - started < 10
    assert seen == [True, True, True]
    assert windows.opened == [
        (50, 40, "book - page 3 of 3"),          # it starts on the current page
        (40, 30, "book - page 2 of 3"),
        (30, 20, "book - page 1 of 3"),
        (40, 30, "book - page 2 of 3"),
    ]
    assert not pygame.display.get_init()          # closed
    assert p.page_count() == 3 and (p.width, p.height) == (50, 40)    # the document is unchanged


def test_show_stops_at_the_first_and_last_page(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.delenv("FUNGROUND_HEADLESS", raising=False)
    s = api.use_sketch(Sketch())
    p.size(30, 20)
    p.new_page(40, 30)
    windows = Windows(s)

    def keys():
        for _ in range(250):
            if pygame.display.get_init() and windows.opened:
                break
            time.sleep(0.02)
        key(pygame.K_RIGHT)                       # already on the last page
        time.sleep(0.3)
        key(pygame.K_LEFT)
        windows.wait_for(2)
        time.sleep(0.3)
        key(pygame.K_LEFT)                        # already on the first page
        time.sleep(0.3)
        pygame.event.post(pygame.event.Event(pygame.QUIT))    # closing the window ends show()

    timer = threading.Thread(target=keys)
    timer.start()
    p.show()
    timer.join()
    assert [w[:2] for w in windows.opened] == [(40, 30), (30, 20)]


def test_show_draws_each_page_and_closes_the_window():
    class Recorder:
        backing_scale = 1.0

        def __init__(self):
            self.calls, self.presented, self.titles, self.polls = [], [], [], 0

        def open_window(self, w, h, title):
            self.titles.append(title)
            return (w, h)

        def set_cursor(self, kind):
            pass

        def start(self):
            pass

        def poll(self):
            self.polls += 1
            return self.polls < 3

        def events(self):
            return [InputEvent("key_pressed", key="left")] if self.polls == 1 else []

        def present(self, pixels):
            self.presented.append((pixels.width, pixels.height, bytes(pixels.data)[:4]))

        def tick(self, fps):
            return 0.0

        def close(self):
            self.calls.append("close")

    platform = Recorder()
    api.use_sketch(Sketch(platform=platform))
    p.size(10, 10)
    p.background("red")
    p.new_page(20, 5)
    p.background("blue")
    p.show()
    assert platform.titles == ["funground - page 2 of 2", "funground - page 1 of 2"]
    assert platform.presented[0] == (20, 5, bytes([255, 0, 0, 255]))      # page 2 first (BGRA blue)
    assert (10, 10, bytes([0, 0, 255, 255])) in platform.presented        # then page 1 (BGRA red)
    assert platform.calls == ["close"]


def test_show_of_one_page_keeps_its_title(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.delenv("FUNGROUND_HEADLESS", raising=False)
    s = api.use_sketch(Sketch())
    p.size(30, 20, title="solo")
    windows = Windows(s)

    def esc():
        for _ in range(250):
            if pygame.display.get_init():
                break
            time.sleep(0.02)
        key(pygame.K_ESCAPE)

    timer = threading.Thread(target=esc)
    timer.start()
    p.show()
    timer.join()
    assert windows.opened == [(30, 20, "solo")]


# ---------------------------------------------------------------- public names
def test_pages_are_public_module_functions_only():
    for name in ("new_page", "page_count", "page_size"):
        assert name in p.__all__ and callable(getattr(p, name))
    script()
    p.size(10, 10)
    pic = p.create_graphics(5, 5)
    for name in ("new_page", "page_count", "page_size"):
        assert not hasattr(pic, name)


def test_a_plain_document_raises_no_warnings(tmp_path):
    script()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        p.new_page("A5")
        p.new_page()
        p.save(str(tmp_path / "q.pdf"))
