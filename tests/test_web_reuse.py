"""Running again in the same Python (S-157, decision D-083): a later Session draws what a fresh one draws.

The browser runner runs the next file in the interpreter that ran the last one. These tests run
several files one after another through new Sessions, as a host would, and check what is started
afresh (fonts loaded from files, modules from the sketch's folder, a run that raised an error) and
that nothing a sketch draws changes because of an earlier run.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from conftest import EXAMPLES, GOLDEN
from funground import api, typography
from funground.sketch import Sketch
from funground.web import Session
from test_web_session import FRAME, DesktopFrames, Frames, desktop_frames

FRAMES = 30                                         # the frame the golden tests compare
SKETCHES = sorted(p for p in EXAMPLES.glob("*.py") if (GOLDEN / f"{p.stem}.png").exists())


def desktop_frame(source: str, frames: int) -> bytes:
    """The last of the first *frames* frames that `python sketch.py` presents, headless, with random seeded."""
    platform = DesktopFrames()
    api.use_sketch(Sketch(platform=platform)).random_seed(0)
    exec(compile(source.replace("f.run()", f"f.run(max_frames={frames})"), "sketch.py", "exec"),
         {"__name__": "__main__", "__file__": "sketch.py"})
    return platform.frames[-1]


def run_file(path: Path, steps: int = 1) -> tuple[list[bytes], dict]:
    """Run a sketch file through a new Session for *steps* frames: its frames and its namespace."""
    got = Frames()
    session = Session(640, 480, on_frame=got)
    api.canvas_sketch().random_seed(0)              # so a sketch that uses random() can be compared
    session.start(path.read_text(encoding="utf-8"), str(path))
    namespace = api.canvas_sketch()._draw_fn.__globals__
    try:
        for n in range(steps):
            assert session.step(n * FRAME)
    finally:
        session.stop()
    return got.pixels, namespace


def test_every_golden_example_draws_the_same_after_other_runs():
    # One interpreter, one fresh Session per run: in order, then in reverse. About 15 seconds.
    expected = {p.name: desktop_frame(p.read_text(encoding="utf-8"), FRAMES) for p in SKETCHES}
    assert len(expected) >= 12
    for order in (SKETCHES, SKETCHES[::-1]):
        for path in order:
            frames, _ = run_file(path, FRAMES)
            assert frames[-1] == expected[path.name], f"{path.name} differs after earlier runs"


def test_a_font_file_replaced_between_runs_is_read_again(tmp_path):
    fonts = Path(typography.FONT_DIR)
    (tmp_path / "data").mkdir()
    font_file = tmp_path / "data" / "x.ttf"
    sketch = tmp_path / "sketch.py"
    sketch.write_text(
        "import funground as f\n"
        "font = f.load_font('data/x.ttf')\n"
        "def setup():\n    f.size(200, 80)\n"
        "def draw():\n    f.background('white')\n    f.fill('black')\n    f.text_font(font)\n    f.text_size(40)\n    f.text('Hello', 10, 50)\n"
        "f.run()\n", encoding="utf-8")

    font_file.write_bytes((fonts / "DejaVuSans.ttf").read_bytes())
    first, namespace = run_file(sketch)
    assert namespace["font"].name == "x.ttf"

    font_file.write_bytes((fonts / "DejaVuSans-Bold.ttf").read_bytes())
    second, namespace = run_file(sketch)
    assert namespace["font"].name == "x.ttf"
    assert second != first

    fresh = tmp_path / "fresh"
    (fresh / "data").mkdir(parents=True)
    (fresh / "data" / "x.ttf").write_bytes((fonts / "DejaVuSans-Bold.ttf").read_bytes())
    (fresh / "sketch.py").write_text(sketch.read_text(encoding="utf-8"), encoding="utf-8")
    assert run_file(fresh / "sketch.py")[0] == second


def test_the_bundled_fonts_stay_loaded_when_a_run_ends():
    mark = typography.file_font_mark()
    typography.default_font()                                # registers the default family lazily
    typography.forget_file_fonts(mark)
    assert typography.file_font_mark() == mark
    assert typography._registry                              # still there


def test_a_helper_beside_the_sketch_is_read_again(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(tmp_path))
    helpers = tmp_path / "helpers.py"
    sketch = tmp_path / "sketch.py"
    sketch.write_text(
        "import colorsys\nimport json\nimport funground as f\nimport helpers\n"
        "def setup():\n    f.size(20, 20)\n"
        "def draw():\n    f.background(*helpers.COLOUR)\n"
        "f.run()\n", encoding="utf-8")

    helpers.write_text("COLOUR = (255, 0, 0)\n", encoding="utf-8")
    first, _ = run_file(sketch)
    assert first[0][:4] == bytes([0, 0, 255, 255])                 # BGRA: red
    assert "helpers" not in sys.modules

    helpers.write_text("COLOUR = (0, 128, 255)\n", encoding="utf-8")   # a different size, so no stale .pyc is used
    second, _ = run_file(sketch)
    assert second[0][:4] == bytes([255, 128, 0, 255])              # BGRA: the new colour

    # Modules that are not from the sketch's folder stay.
    assert "json" in sys.modules and "colorsys" in sys.modules and "funground.web" in sys.modules


SETUP_ERROR = (
    "import funground as f\n"
    "def setup():\n    f.size(50, 50)\n    f.fill('red')\n    f.push()\n    raise ZeroDivisionError\n"
    "def draw():\n    pass\n"
    "f.run()\n")
MARK_ERROR = (
    "import funground as f\n"
    "def setup():\n    f.size(50, 50)\n"
    "    with f.mark() as m:\n        f.circle(10, 10, 5)\n        raise ZeroDivisionError\n"
    "def draw():\n    pass\n"
    "f.run()\n")


@pytest.mark.parametrize("broken", [SETUP_ERROR, MARK_ERROR], ids=["setup", "inside a mark"])
def test_a_run_that_raised_leaves_nothing_behind(broken):
    source = (EXAMPLES / "06_animation.py").read_text(encoding="utf-8")
    steps = 6
    expected = desktop_frames(source, steps)
    with pytest.raises(ZeroDivisionError):
        Session(640, 480).start(broken, "sketch.py")
    session = Session(640, 480, on_frame=(got := Frames()))
    session.start(source, "sketch.py")
    for n in range(steps):
        assert session.step(n * FRAME)
    session.stop()
    assert got.pixels == expected
