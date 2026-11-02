"""Say when a loaded font is never chosen (story S-244; contract row T11)."""
from __future__ import annotations

import pytest

from funground import api, typography
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch
from funground.web import Session

from fontmaker import make_static_font

LINE = "Boxy was loaded but never chosen: add f.text_font(...) to use it"


@pytest.fixture(autouse=True)
def clean_fonts():
    mark = typography.file_font_mark()
    typography._loaded.clear()
    typography._chosen.clear()
    yield
    typography.forget_file_fonts(mark)
    typography._loaded.clear()
    typography._chosen.clear()


@pytest.fixture
def font_file(tmp_path):
    return make_static_font(tmp_path, name="Boxy").replace("\\", "/")


def sketch_source(font_file: str, body: str, frames: int = 5) -> str:
    return (f"import funground as f\n"
            f"face = f.load_font({font_file!r})\n"
            f"def setup():\n    f.size(100, 60)\n"
            f"def draw():\n{body}\n"
            f"f.run(max_frames={frames})\n")


def run_desktop(source: str) -> None:
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    exec(compile(source, "sketch.py", "exec"), {"__name__": "__main__", "__file__": "sketch.py"})


def run_web(source: str, frames: int = 5) -> None:
    session = Session(100, 60)
    session.start(source.replace("f.run(max_frames=5)", "f.run()"), "sketch.py")
    for n in range(frames):
        session.step(n / 60)
    session.stop()


RUNNERS = [run_desktop, run_web]
USES = {
    "text_font": "    f.text_font(face)\n    f.text('a', 10, 30)",
    "text_font_after_text": "    f.text('a', 10, 30)\n    f.text_font(face)",
    "text_font_path": "    f.text_font(%(path)r)\n    f.text('a', 10, 30)",
    "text_fallback": "    f.text_fallback(face)\n    f.text('a', 10, 30)",
    "formatted_string": "    s = f.FormattedString()\n    s.append('a', font=face)\n    f.text(s, 10, 30)",
    "measuring": "    face.family()\n    f.text('a', 10, 30)",
    "variations": "    face.variations()\n    f.text('a', 10, 30)",
}


@pytest.mark.parametrize("run", RUNNERS)
def test_said_once_across_many_frames(run, font_file, capsys):
    run(sketch_source(font_file, "    f.text('a', 10, 30)", frames=5))
    assert capsys.readouterr().out.splitlines() == [LINE]


@pytest.mark.parametrize("run", RUNNERS)
@pytest.mark.parametrize("use", sorted(USES))
def test_quiet_when_the_font_is_used(run, use, font_file, capsys):
    run(sketch_source(font_file, USES[use].replace("%(path)r", repr(font_file))))
    assert LINE not in capsys.readouterr().out


@pytest.mark.parametrize("run", RUNNERS)
def test_quiet_when_no_text_is_drawn(run, font_file, capsys):
    run(sketch_source(font_file, "    f.background(200)\n    f.circle(50, 30, 10)"))
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("run", RUNNERS)
def test_quiet_when_no_font_is_loaded(run, tmp_path, capsys):
    run("import funground as f\ndef draw():\n    f.text('a', 10, 30)\nf.run(max_frames=3)\n")
    assert capsys.readouterr().out == ""


def test_said_again_in_the_next_run(font_file, capsys):
    run_desktop(sketch_source(font_file, "    f.text('a', 10, 30)"))
    run_desktop(sketch_source(font_file, "    f.text('a', 10, 30)"))
    assert capsys.readouterr().out.splitlines() == [LINE, LINE]


@pytest.mark.parametrize("run", RUNNERS)
def test_quiet_after_an_error(run, font_file, capsys):
    """A run that ends in an error shows the traceback, not a hint about fonts underneath it."""
    body = "    f.text('a', 10, 30)\n    if f.frame_count == 2:\n        1 / 0"
    with pytest.raises(ZeroDivisionError):
        run(sketch_source(font_file, body))
    assert LINE not in capsys.readouterr().out
