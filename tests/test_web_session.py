"""The host API for the web runner (S-152, contract W1): funground.web.Session and BrowserPlatform.

A fake host drives a Session with its own clock, as a browser page would. Nothing here needs a window.
"""
from __future__ import annotations

import pytest

from conftest import EXAMPLES
from funground import api
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch
from funground.web import Session

FRAME = 1 / 60


class Frames:
    """The host's on_frame callback: keeps a copy of every frame (the view is valid only during the call)."""

    def __init__(self) -> None:
        self.calls: list[tuple[bytes, int, int, int]] = []

    def __call__(self, data, width, height, stride) -> None:
        self.calls.append((bytes(data), width, height, stride))

    @property
    def pixels(self) -> list[bytes]:
        return [c[0] for c in self.calls]


class DesktopFrames(HeadlessPlatform):
    """The desktop's headless run of a sketch, keeping every presented frame's bytes."""

    def __init__(self) -> None:
        super().__init__()
        self.frames: list[bytes] = []

    def present(self, pixels) -> None:
        super().present(pixels)
        self.frames.append(bytes(pixels.data))


def desktop_frames(source: str, frames: int) -> list[bytes]:
    """What `python sketch.py` presents in the first *frames* frames, headless."""
    platform = DesktopFrames()
    api.use_sketch(Sketch(platform=platform))
    exec(compile(source.replace("f.run()", f"f.run(max_frames={frames})"), "sketch.py", "exec"),
         {"__name__": "__main__", "__file__": "sketch.py"})
    return platform.frames


def run_session(source: str, steps: int, scale: float = 1.0) -> tuple[Session, Frames]:
    got = Frames()
    session = Session(640, 480, scale=scale, on_frame=got)
    session.start(source, "sketch.py")
    for n in range(steps):
        assert session.step(n * FRAME)
    return session, got


@pytest.mark.parametrize("name", ["02_shapes.py", "05_text.py", "06_animation.py", "07_bounce.py", "13_transforms.py"])
def test_frames_equal_the_desktops_byte_for_byte(name):
    source = (EXAMPLES / name).read_text(encoding="utf-8")
    steps = 6
    expected = desktop_frames(source, steps)
    session, got = run_session(source, steps)
    session.stop()
    assert len(got.pixels) == steps
    assert got.pixels == expected


def test_a_frame_comes_with_its_layout():
    session, got = run_session("import funground as f\nf.size(30, 20)\ndef draw():\n    f.background('red')\nf.run()\n", 1, scale=2.0)
    data, width, height, stride = got.calls[0]
    assert (width, height) == (60, 40)
    assert stride == width * 4 and len(data) == stride * height
    assert session.canvas_size == (30, 20)
    session.stop()


def test_run_returns_after_setup_and_the_host_steps():
    source = (
        "import funground as f\n"
        "log = []\n"
        "def setup():\n"
        "    log.append('setup')\n"
        "    f.size(20, 20)\n"
        "def draw():\n"
        "    log.append('draw')\n"
        "f.run()\n"
        "log.append('after run')\n"
    )
    session = Session(640, 480)
    session.start(source, "sketch.py")
    log = api.canvas_sketch()._draw_fn.__globals__["log"]
    assert log == ["setup", "after run"]            # f.run() came back before any frame
    assert session.running and session.canvas_size == (20, 20)
    assert session.step(0.0) and log[-1] == "draw"
    session.stop()


def test_show_presents_once_and_returns():
    got = Frames()
    session = Session(640, 480, on_frame=got)
    session.start("import funground as f\nf.size(40, 30)\nf.background('blue')\nf.show()\n", "sketch.py")
    assert len(got.calls) == 1 and got.calls[0][1:3] == (40, 30)
    assert not session.running and session.step(0.0) is False
    session.stop()


def test_show_presents_every_page_with_the_current_page_last():
    got = Frames()
    session = Session(640, 480, on_frame=got)
    session.start("import funground as f\nf.size(40, 30)\nf.new_page(50, 20)\nf.background('green')\nf.show()\n", "sketch.py")
    assert [c[1:3] for c in got.calls] == [(40, 30), (50, 20)]
    session.stop()


def test_pushed_events_reach_the_sketch():
    source = (
        "import funground as f\n"
        "seen = []\n"
        "def setup():\n    f.size(100, 100)\n"
        "def draw():\n    f.background('white')\n"
        "def key_pressed():\n    seen.append(('key', f.key))\n"
        "def mouse_pressed():\n    seen.append(('mouse', f.mouse_x, f.mouse_y))\n"
        "f.run()\n"
    )
    got = Frames()
    session = Session(640, 480, on_frame=got)
    session.start(source, "sketch.py")
    namespace_seen = api.canvas_sketch()._callbacks["key_pressed"].__globals__["seen"]
    session.push_event("mouse_moved", 30, 40)
    session.push_event("mouse_pressed", 30, 40, button="left")
    session.push_event("key_pressed", key="a", key_code=97)
    session.push_event("key_pressed", key=" ", key_code=32)
    assert session.step(0.0)
    sketch = api.canvas_sketch()
    assert (sketch.mouse_x, sketch.mouse_y) == (30, 40) and sketch.is_mouse_pressed and sketch.is_key_pressed
    assert namespace_seen == [("mouse", 30, 40), ("key", "a"), ("key", " ")]
    assert sketch.key_down("space") and sketch.key_down("a")
    session.push_event("key_released", key=" ")
    assert session.step(FRAME) and not sketch.key_down("space")
    session.stop()


def test_bad_events_are_refused():
    session = Session(640, 480)
    with pytest.raises(ValueError, match="event kind"):
        session.push_event("tap")
    with pytest.raises(ValueError, match="mouse button"):
        session.push_event("mouse_pressed", button="thumb")


def test_escape_does_not_stop_the_sketch():
    session, _ = run_session("import funground as f\ndef draw():\n    pass\nf.run()\n", 1)
    session.push_event("key_pressed", key="escape")
    assert session.step(FRAME) and session.running
    session.stop()


def test_delta_time_follows_the_host_clock():
    source = "import funground as f\ndeltas = []\ndef draw():\n    deltas.append(f.delta_time)\nf.run()\n"
    session = Session(640, 480)
    session.start(source, "sketch.py")
    deltas = api.canvas_sketch()._draw_fn.__globals__["deltas"]
    for now in (1.0, 1.25, 1.5, 2.5):
        assert session.step(now)
    # draw() sees the time the previous step measured; the first step measured 1/fps (fps is 60)
    assert deltas == [0.0, pytest.approx(1 / 60), pytest.approx(0.25), pytest.approx(0.25)]
    assert api.canvas_sketch().delta_time == pytest.approx(1.0)
    session.stop()


def test_stop_runs_finish_and_is_safe_twice():
    session, _ = run_session("import funground as f\ndef draw():\n    pass\nf.run()\n", 2)
    sketch = api.canvas_sketch()
    session.stop()
    assert not sketch.running and not sketch._has_window
    assert session.step(1.0) is False
    session.stop()


def test_f_stop_ends_the_run_and_finishes():
    session, _ = run_session("import funground as f\ndef draw():\n    if f.frame_count == 1:\n        f.stop()\nf.run()\n", 1)
    sketch = api.canvas_sketch()
    assert session.step(FRAME) is False
    assert not sketch._has_window                  # finish() ran
    assert session.step(2 * FRAME) is False


def test_an_error_in_draw_finishes_and_reaches_the_host():
    session = Session(640, 480)
    session.start("import funground as f\ndef draw():\n    1 / 0\nf.run()\n", "sketch.py")
    with pytest.raises(ZeroDivisionError):
        session.step(0.0)
    assert not session.running


def test_an_error_in_the_file_reaches_the_host():
    session = Session(640, 480)
    with pytest.raises(NameError):
        session.start("import funground as f\nnope\n", "sketch.py")


def test_desktop_only_features_say_so():
    session = Session(640, 480)
    session.start("import funground as f\nf.size(20, 20)\n", "sketch.py")
    with pytest.raises(RuntimeError, match="system_font.*browser"):
        api.system_font("Arial")
    with pytest.raises(RuntimeError, match="MP4.*browser"):
        api.canvas_sketch()._require_encoder("mp4")
    session.stop()


def test_without_a_session_nothing_is_host_driven():
    assert api.canvas_sketch()._host_driven is False
    sketch = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    ns = {"setup": lambda: api.size(20, 20), "draw": lambda: None}
    sketch.run_namespace(ns, max_frames=3)
    assert sketch.frame_count == 3 and not sketch.running      # the loop ran to its end
