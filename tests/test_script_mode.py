"""Script mode (S-076, D-029, contract R13-R15): a file is an animated sketch or a script.

A script has no setup() or draw(). A top-level f.size() makes a canvas with no window,
f.save() writes at once, and f.show() opens a window to look at the result.
"""
from __future__ import annotations

import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pygame
import pytest

import funground as p
from funground import api
from funground import sketch as sketch_module
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from conftest import ROOT, run_sketch


class RecordingPlatform(HeadlessPlatform):
    """Headless, and it remembers every window it was asked to open."""

    def __init__(self) -> None:
        super().__init__()
        self.opened: list[tuple[int, int, str]] = []

    def open_window(self, width, height, title):
        self.opened.append((width, height, title))
        return super().open_window(width, height, title)


class WindowPlatform:
    """A platform that is not headless: show() must open a window, present, poll and close."""

    def __init__(self, scale: float = 1.0, polls: int = 3) -> None:
        self._scale = scale
        self._polls = polls
        self.calls: list[str] = []
        self.presented = []
        self.size = None

    @property
    def backing_scale(self):
        return self._scale

    def open_window(self, width, height, title):
        self.calls.append("open_window")
        self.size = (round(width * self._scale), round(height * self._scale))
        return self.size

    def set_cursor(self, kind):
        pass

    def start(self):
        self.calls.append("start")

    def poll(self):
        self.calls.append("poll")
        self._polls -= 1
        return self._polls > 0

    def present(self, pixels):
        self.calls.append("present")
        self.presented.append((pixels.width, pixels.height, bytes(pixels.data)))

    def tick(self, fps):
        self.calls.append("tick")
        return 0.0

    def close(self):
        self.calls.append("close")


def script_sketch(platform=None) -> Sketch:
    return api.use_sketch(Sketch(platform=platform or RecordingPlatform()))


def rgba(path, x, y):
    return tuple(pygame.image.load(str(path)).get_at((x, y)))


# ---------------------------------------------------------------- R14: a canvas with no window
def test_top_level_size_opens_no_window(tmp_path):
    platform = RecordingPlatform()
    script_sketch(platform)
    p.size(200, 100, title="quiet")
    p.background("white")
    p.circle(50, 50, 20)
    p.save(str(tmp_path / "a.png"))
    assert platform.opened == []
    assert not pygame.display.get_init()
    assert (p.width, p.height) == (200, 100)


def test_top_level_size_never_touches_the_platform(tmp_path):
    class Untouchable:
        def __getattr__(self, name):
            raise AssertionError(f"a script must not call platform.{name}")

    script_sketch(Untouchable())
    p.size(50, 50)
    p.background("red")
    p.save(str(tmp_path / "a.png"))
    p.create_graphics(10, 10)


def test_drawing_before_size_is_an_error_naming_size():
    script_sketch()
    with pytest.raises(RuntimeError, match=r"f\.size"):
        p.circle(10, 10, 5)
    with pytest.raises(RuntimeError, match=r"f\.size"):
        p.background("white")


def test_everything_drawn_is_kept_as_the_canvas_drawing():
    s = script_sketch()
    p.size(100, 100)
    p.background("white")
    p.rect(0, 0, 10, 10)
    assert len(s.frame) == 2
    s._script_flush()
    p.circle(50, 50, 10)
    assert len(s.frame) == 3          # flushing pixels never forgets the drawing


def test_a_second_size_starts_a_new_blank_canvas(tmp_path):
    s = script_sketch()
    p.size(60, 40)
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.rect(0, 0, 30, 30)
    p.save(str(tmp_path / "one.png"))
    p.size(80, 50)
    assert (p.width, p.height) == (80, 50)
    assert len(s.frame) == 0
    p.save(str(tmp_path / "two.png"))
    assert rgba(tmp_path / "one.png", 5, 5) == (255, 0, 0, 255)
    image = pygame.image.load(str(tmp_path / "two.png"))
    assert image.get_size() == (80, 50)
    assert tuple(image.get_at((5, 5))) == (0, 0, 0, 0)         # blank: transparent, as a new picture is


def test_state_and_transform_carry_on_between_saves(tmp_path):
    script_sketch()
    p.size(100, 50)
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.translate(40, 0)
    p.save(str(tmp_path / "a.png"))
    p.rect(0, 0, 10, 10)               # still red, still shifted 40 to the right
    p.save(str(tmp_path / "b.png"))
    assert rgba(tmp_path / "b.png", 5, 5) == (255, 255, 255, 255)
    assert rgba(tmp_path / "b.png", 45, 5) == (255, 0, 0, 255)


def test_push_depth_carries_on_and_pop_works_after_a_save(tmp_path):
    s = script_sketch()
    p.size(100, 50)
    p.background("white")
    p.no_stroke()
    p.push()
    p.fill("red")
    p.translate(40, 0)
    p.save(str(tmp_path / "a.png"))
    assert s._states.depth == 1
    p.pop()
    p.fill("blue")
    p.rect(0, 0, 10, 10)               # the shift was popped: drawn at the left edge
    p.save(str(tmp_path / "b.png"))
    assert s._states.depth == 0
    assert rgba(tmp_path / "b.png", 5, 5) == (0, 0, 255, 255)


def test_input_values_are_idle_and_the_clock_counts_from_size():
    script_sketch()
    p.size(20, 20)
    assert (p.mouse_x, p.mouse_y, p.is_mouse_pressed, p.is_key_pressed) == (0, 0, False, False)
    assert p.frame_count == 0
    time.sleep(0.05)
    assert 40 <= p.millis() < 2000
    p.size(20, 20)
    assert p.millis() < 40             # a new canvas restarts the clock


def test_create_graphics_and_image_work_in_a_script(tmp_path):
    script_sketch()
    p.size(60, 40)
    p.background("white")
    g = p.create_graphics(20, 20)
    g.no_stroke()
    g.fill("blue")
    g.rect(0, 0, 20, 20)
    p.image(g, 10, 10)
    p.save(str(tmp_path / "a.png"))
    assert rgba(tmp_path / "a.png", 15, 15) == (0, 0, 255, 255)
    assert rgba(tmp_path / "a.png", 5, 5) == (255, 255, 255, 255)


def test_text_and_fonts_work_in_a_script(tmp_path):
    script_sketch()
    p.size(120, 40)
    p.background("white")
    p.fill("black")
    p.text_size(24)
    p.text("Hi", 5, 5)
    p.save(str(tmp_path / "a.png"))
    image = pygame.image.load(str(tmp_path / "a.png"))
    assert any(tuple(image.get_at((x, y)))[:3] != (255, 255, 255) for x in range(5, 30) for y in range(5, 30))


# ---------------------------------------------------------------- R14: save writes at once
def test_png_is_written_at_once_with_the_pixels_so_far(tmp_path):
    script_sketch()
    p.size(100, 50)
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.rect(0, 0, 10, 10)
    p.save(str(tmp_path / "early.png"))
    assert (tmp_path / "early.png").exists()            # before anything else happens
    p.fill("blue")
    p.rect(50, 0, 10, 10)
    p.save(str(tmp_path / "late.png"))
    assert rgba(tmp_path / "early.png", 55, 5) == (255, 255, 255, 255)
    assert rgba(tmp_path / "late.png", 55, 5) == (0, 0, 255, 255)
    assert rgba(tmp_path / "late.png", 5, 5) == (255, 0, 0, 255)


def test_png_is_at_the_backing_scale(tmp_path, monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    script_sketch()
    p.size(100, 50)
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.rect(0, 0, 10, 10)
    p.save(str(tmp_path / "a.png"))
    image = pygame.image.load(str(tmp_path / "a.png"))
    assert image.get_size() == (200, 100)
    assert tuple(image.get_at((19, 19))) == (255, 0, 0, 255)
    assert tuple(image.get_at((21, 21))) == (255, 255, 255, 255)


def test_png_is_scale_one_without_an_override(tmp_path, monkeypatch):
    monkeypatch.delenv("FUNGROUND_BACKING_SCALE", raising=False)
    script_sketch()
    p.size(100, 50)
    p.save(str(tmp_path / "a.png"))
    assert pygame.image.load(str(tmp_path / "a.png")).get_size() == (100, 50)


def test_pdf_and_svg_are_written_at_once_as_vectors(tmp_path):
    script_sketch()
    p.size(100, 50)
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.rect(0, 0, 10, 10)
    p.save(str(tmp_path / "a.pdf"))
    p.save(str(tmp_path / "a.svg"))
    assert (tmp_path / "a.pdf").read_bytes().startswith(b"%PDF")
    svg = (tmp_path / "a.svg").read_text(encoding="utf-8")
    assert "<svg" in svg and "<path" in svg and "<image" not in svg      # shapes, not a pasted picture


def test_vector_saves_replay_everything_drawn_so_far(tmp_path):
    script_sketch()
    p.size(100, 50)
    p.no_stroke()
    p.fill("red")
    p.rect(0, 0, 10, 10)
    p.save(str(tmp_path / "one.svg"))
    p.fill("blue")
    p.rect(50, 0, 10, 10)
    p.save(str(tmp_path / "two.svg"))
    one = (tmp_path / "one.svg").read_text(encoding="utf-8")
    two = (tmp_path / "two.svg").read_text(encoding="utf-8")
    assert two.count("<path") > one.count("<path") >= 1
    p.save(str(tmp_path / "again.svg"))
    assert (tmp_path / "again.svg").read_text(encoding="utf-8").count("<path") == two.count("<path")


def test_save_checks_the_extension_at_the_call(tmp_path):
    script_sketch()
    p.size(10, 10)
    with pytest.raises(ValueError, match=r"\.png"):
        p.save(str(tmp_path / "a.gif"))


def test_save_before_size_is_an_error():
    script_sketch()
    with pytest.raises(RuntimeError, match=r"f\.size"):
        p.save("a.png")


# ---------------------------------------------------------------- R15: show()
def test_show_returns_at_once_with_a_headless_platform():
    platform = RecordingPlatform()
    script_sketch(platform)
    p.size(50, 50)
    p.background("white")
    started = time.perf_counter()
    p.show()
    assert time.perf_counter() - started < 1
    assert platform.opened == []


def test_show_returns_at_once_when_the_environment_says_headless(monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    api.use_sketch(Sketch())             # picks the headless platform from the environment
    p.size(50, 50)
    p.show()


def test_show_before_size_is_an_error():
    script_sketch()
    with pytest.raises(RuntimeError, match=r"f\.size"):
        p.show()


def test_show_in_an_animated_sketch_is_an_error():
    s = script_sketch()

    def draw():
        p.show()

    with pytest.raises(RuntimeError, match=r"already has its window"):
        s.run_namespace({"setup": lambda: p.size(20, 20), "draw": draw}, max_frames=1)
    with pytest.raises(RuntimeError, match=r"animated sketch"):
        s.run_namespace({"setup": lambda: (p.size(20, 20), p.show()), "draw": lambda: None}, max_frames=1)


def test_show_opens_a_window_draws_the_drawing_waits_then_closes():
    platform = WindowPlatform(scale=2.0, polls=3)
    script_sketch(platform)
    p.size(30, 20, title="look")
    p.background("red")
    p.show()
    assert platform.calls[0] == "open_window"
    assert platform.calls.count("poll") == 3                   # it waited until the window closed
    assert platform.calls[-1] == "close"
    width, height, data = platform.presented[0]
    assert (width, height) == (60, 40)                          # drawn at the window's backing scale
    assert data[:4] == bytes([0, 0, 255, 255])                  # BGRA red
    assert p.width == 30


def test_the_script_can_go_on_drawing_and_show_again():
    platform = WindowPlatform(polls=2)
    script_sketch(platform)
    p.size(10, 10)
    p.background("red")
    p.show()
    p.background("blue")
    p.show()
    assert platform.calls.count("open_window") == 2
    assert platform.calls.count("close") == 2
    assert platform.presented[0][2][:4] == bytes([0, 0, 255, 255])
    assert platform.presented[-1][2][:4] == bytes([255, 0, 0, 255])    # BGRA blue


def test_show_closes_the_window_even_when_polling_fails():
    class Broken(WindowPlatform):
        def poll(self):
            raise KeyboardInterrupt

    platform = Broken()
    script_sketch(platform)
    p.size(10, 10)
    with pytest.raises(KeyboardInterrupt):
        p.show()
    assert platform.calls[-1] == "close"


def test_show_with_the_real_platform_ends_on_escape(monkeypatch):
    """pygame's dummy driver has no window to close, so Escape is posted from a timer."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.delenv("FUNGROUND_HEADLESS", raising=False)
    api.use_sketch(Sketch())
    p.size(40, 30)
    p.background("green")

    def press_escape():
        for _ in range(50):
            if pygame.display.get_init():
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="", mod=0))
                return
            time.sleep(0.02)

    timer = threading.Thread(target=press_escape)
    timer.start()
    started = time.perf_counter()
    p.show()
    timer.join()
    assert time.perf_counter() - started < 5
    assert not pygame.display.get_init()             # the window was closed


# ---------------------------------------------------------------- R13: the two styles
def test_setup_without_draw_offers_both_styles():
    s = script_sketch()
    with pytest.raises(RuntimeError) as err:
        s.run_namespace({"setup": lambda: p.size(20, 20)}, max_frames=1)
    message = str(err.value)
    assert message.startswith("f.run()")
    assert "add a draw()" in message and "remove setup() and f.run()" in message and "script" in message


def test_run_without_setup_or_draw_keeps_its_old_message():
    s = script_sketch()
    with pytest.raises(RuntimeError, match=r"Define a draw\(\) function"):
        s.run_namespace({}, max_frames=1)


def test_run_after_top_level_drawing_says_the_file_mixes_the_styles():
    s = script_sketch()
    p.size(40, 40)
    p.background("white")
    with pytest.raises(RuntimeError, match=r"mixes the two styles") as err:
        s.run_namespace({"draw": lambda: None}, max_frames=1)
    assert "f.run()" in str(err.value) and "draw()" in str(err.value)
    # ... and a script with no draw() at all is mixed just the same
    with pytest.raises(RuntimeError, match=r"mixes the two styles"):
        s.run_namespace({}, max_frames=1)


def test_run_after_only_a_top_level_size_is_still_an_animated_sketch():
    s = script_sketch()
    p.size(120, 80)
    frames = []
    s.run_namespace({"draw": lambda: frames.append((p.width, p.height))}, max_frames=2)
    assert frames == [(120, 80), (120, 80)]
    assert not s._script


@pytest.mark.parametrize("name, args", [
    ("no_loop", ()), ("loop", ()), ("redraw", ()), ("save_frames", ("f####.png", 2)), ("exit", ()),
])
def test_animation_only_functions_raise_in_a_script(name, args):
    script_sketch()
    p.size(20, 20)
    with pytest.raises(RuntimeError) as err:
        getattr(p, name)(*args)
    message = str(err.value)
    assert message.startswith(f"f.{name}()")
    assert "animated" in message and "f.run()" in message


def test_animation_only_functions_still_work_in_an_animated_sketch(tmp_path):
    s = script_sketch()

    def draw():
        p.no_loop()
        p.loop()
        p.redraw()
        if p.frame_count == 1:
            p.exit()

    s.run_namespace({"setup": lambda: p.size(20, 20), "draw": draw}, max_frames=5)
    assert s.frame_count == 2


def test_a_size_in_setup_keeps_the_old_behaviour_a_window_opens():
    platform = RecordingPlatform()
    s = script_sketch(platform)
    s.run_namespace({"setup": lambda: p.size(30, 20, title="x"), "draw": lambda: p.background("red")},
                    max_frames=1)
    assert platform.opened == [(30, 20, "x")]


def test_a_size_in_draw_resizes_the_running_sketch_without_making_a_script():
    s = script_sketch()

    def draw():
        if p.frame_count == 1:
            p.size(50, 50)
            assert not s._script

    s.run_namespace({"setup": lambda: p.size(20, 20), "draw": draw}, max_frames=3)
    assert (p.width, p.height) == (50, 50)


def test_a_script_file_runs_through_the_gallery_harness(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "s.py"
    source.write_text(
        'import funground as f\nf.size(30, 20)\nf.background("red")\nf.save("s.pdf")\nf.show()\n',
        encoding="utf-8",
    )
    (w, h), data = run_sketch(source)
    assert (w, h) == (30, 20)
    assert data[:3] == bytes([255, 0, 0])
    assert (tmp_path / "s.pdf").exists()
    assert [type(op).__name__ for op in api.active_sketch().last_ops] == ["Clear"]


# ---------------------------------------------------------------- R13: the exit hint
@pytest.fixture
def at_exit(monkeypatch):
    """The state the atexit hook sees for a plain program run from a terminal."""
    monkeypatch.setattr(sketch_module, "_run_started", False)
    monkeypatch.delattr(sys, "ps1", raising=False)
    monkeypatch.setitem(sys.modules, "__main__", SimpleNamespace(draw=lambda: None))
    api.use_sketch(Sketch(platform=RecordingPlatform()))


def test_the_hint_is_the_line_from_the_contract(at_exit, capsys):
    api.exit_hint()
    captured = capsys.readouterr()
    assert captured.err == "Your sketch has a draw() function but never started. Add f.run() as the last line.\n"
    assert captured.out == ""


def test_no_hint_when_run_was_called(at_exit, capsys, monkeypatch):
    monkeypatch.setattr(sketch_module, "_run_started", True)
    api.exit_hint()
    assert capsys.readouterr().err == ""


def test_running_a_sketch_marks_it_as_started(at_exit, capsys):
    api.active_sketch().run_namespace({"setup": lambda: p.size(10, 10), "draw": lambda: None}, max_frames=1)
    api.exit_hint()
    assert capsys.readouterr().err == ""


def test_no_hint_without_a_draw_function(at_exit, capsys, monkeypatch):
    monkeypatch.setitem(sys.modules, "__main__", SimpleNamespace())
    api.exit_hint()
    assert capsys.readouterr().err == ""
    monkeypatch.setitem(sys.modules, "__main__", SimpleNamespace(draw=42))      # not callable
    api.exit_hint()
    assert capsys.readouterr().err == ""


def test_no_hint_in_an_interactive_session(at_exit, capsys, monkeypatch):
    monkeypatch.setattr(sys, "ps1", ">>> ", raising=False)
    api.exit_hint()
    assert capsys.readouterr().err == ""


def test_no_hint_when_python_was_started_interactively(at_exit, capsys, monkeypatch):
    monkeypatch.setattr(sys, "flags", SimpleNamespace(interactive=1))
    api.exit_hint()
    assert capsys.readouterr().err == ""


def test_no_hint_for_a_script(at_exit, capsys):
    p.size(10, 10)
    p.background("white")
    api.exit_hint()
    assert capsys.readouterr().err == ""


def test_the_hint_never_fires_under_the_test_harness(capsys):
    """pytest's __main__ has no draw(), so the real hook says nothing during the suite."""
    api.exit_hint()
    assert capsys.readouterr().err == ""


def _run_program(tmp_path, source: str):
    program = tmp_path / "program.py"
    program.write_text(source, encoding="utf-8")
    env = {**__import__("os").environ, "FUNGROUND_HEADLESS": "1", "PYTHONPATH": str(ROOT)}
    return subprocess.run([sys.executable, str(program)], capture_output=True, text=True, env=env,
                          cwd=tmp_path, timeout=60)


def test_a_real_program_that_forgot_run_gets_the_hint(tmp_path):
    done = _run_program(tmp_path, "import funground as f\n\ndef draw():\n    f.background('white')\n")
    assert done.returncode == 0
    assert done.stderr.strip() == "Your sketch has a draw() function but never started. Add f.run() as the last line."


def test_real_programs_that_are_fine_stay_quiet(tmp_path):
    animated = _run_program(
        tmp_path, "import funground as f\n\ndef draw():\n    f.background('white')\n\nf.run(max_frames=1)\n")
    script = _run_program(
        tmp_path, "import funground as f\nf.size(20, 20)\nf.background('white')\nf.save('a.png')\nf.show()\n")
    assert animated.returncode == 0 and animated.stderr == ""
    assert script.returncode == 0 and script.stderr == "" and (tmp_path / "a.png").exists()


# ---------------------------------------------------------------- the public surface
def test_show_is_public():
    assert "show" in p.__all__ and callable(p.show)


def test_exit_hint_stays_quiet_after_a_crash(tmp_path):
    """R13: a program that ended with an error gets its traceback, not a hint about f.run()."""
    import subprocess
    import sys

    script = tmp_path / "crashes.py"
    script.write_text(
        "import funground as f\n"
        "def draw():\n"
        "    pass\n"
        "raise ValueError('boom')\n",
        encoding="utf-8",
    )
    import os

    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                            env={**os.environ, "FUNGROUND_HEADLESS": "1"}, timeout=60)
    assert "ValueError: boom" in result.stderr
    assert "never started" not in result.stderr



# ---------------------------------------------------------------- S-085: full_screen() in a script
class FullScreenRecorder(RecordingPlatform):
    def __init__(self) -> None:
        super().__init__()
        self.full_screens: list[str] = []

    def open_full_screen(self, title):
        self.full_screens.append(title)
        return super().open_full_screen(title)


def test_top_level_full_screen_opens_no_window_and_sizes_the_canvas():
    platform = FullScreenRecorder()
    script_sketch(platform)
    p.full_screen()
    assert (p.width, p.height) == HeadlessPlatform.SCREEN_SIZE == (1920, 1080)
    assert platform.opened == [] and platform.full_screens == []
    p.background("white")
    p.circle(100, 100, 50)                      # a canvas: drawing works at once


def test_show_after_full_screen_takes_the_full_screen_route():
    platform = WindowPlatform(polls=2)
    platform.full_screens = []

    def open_full_screen(title):
        platform.calls.append("open_full_screen")
        platform.size = (640, 360)
        return platform.size

    platform.open_full_screen = open_full_screen
    platform.display_size = lambda: (640, 360)
    script_sketch(platform)
    p.full_screen()
    p.background("red")
    p.show()
    assert "open_full_screen" in platform.calls and "open_window" not in platform.calls
    assert platform.calls[-1] == "close"
    assert platform.presented[0][:2] == (640, 360)


def test_only_pages_made_by_full_screen_are_shown_full_screen():
    platform = WindowPlatform(polls=2)
    platform.open_full_screen = lambda title: (platform.calls.append("open_full_screen"), (320, 200))[1]
    platform.display_size = lambda: (320, 200)
    platform.events = lambda: []
    script_sketch(platform)
    p.full_screen()
    p.new_page(50, 50)
    p.show()                                        # opens on the current page: a normal window
    assert platform.calls.count("open_window") == 1 and "open_full_screen" not in platform.calls
    p.size(30, 30)
    p.full_screen()
    p.show()
    assert "open_full_screen" in platform.calls


def test_show_after_full_screen_with_the_real_platform_ends_on_escape(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.delenv("FUNGROUND_HEADLESS", raising=False)
    api.use_sketch(Sketch())
    p.full_screen()
    assert p.width > 0 and p.height > 0
    assert not pygame.display.get_init()             # the size was read without leaving a display open
    p.background("green")

    def press_escape():
        for _ in range(50):
            if pygame.display.get_init():
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="", mod=0))
                return
            time.sleep(0.02)

    timer = threading.Thread(target=press_escape)
    timer.start()
    started = time.perf_counter()
    p.show()
    timer.join()
    assert time.perf_counter() - started < 5
    assert not pygame.display.get_init()


def test_full_screen_in_an_animated_sketch_is_unchanged():
    seen = []
    platform = FullScreenRecorder()
    s = script_sketch(platform)
    s.run_namespace({"setup": p.full_screen, "draw": lambda: seen.append((p.width, p.height))}, max_frames=1)
    assert seen == [HeadlessPlatform.SCREEN_SIZE]
    assert len(platform.full_screens) == 1


# ---------------------------------------------------------------- S-085: memory (contract R14)
def test_a_script_keeps_about_a_hundred_bytes_per_simple_shape():
    import tracemalloc

    script_sketch()
    p.size(400, 400)
    p.fill("red")
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    for i in range(1000):
        p.circle(i % 400, (i * 7) % 400, 5)
    used = tracemalloc.get_traced_memory()[0] - before
    tracemalloc.stop()
    assert used < 300_000                           # measured: about 95 000; this catches a big regression
