"""The global style (S-175): ``from funground import *`` is safe, live values are current, run() is optional."""
from __future__ import annotations

import builtins
import keyword
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import funground as f
from funground import api
from funground.platform.base import InputEvent
from funground.sketch import Sketch
from test_events import ScriptedPlatform

ROOT = Path(__file__).resolve().parent.parent


def star_namespace() -> dict:
    namespace: dict = {}
    exec("from funground import *", namespace)
    return namespace


def test_star_hides_no_builtin_keyword_or_standard_library_module():
    namespace = star_namespace()
    clashes = [name for name in f.__all__
               if hasattr(builtins, name) or keyword.iskeyword(name) or name in sys.stdlib_module_names]
    assert clashes == []
    for name in ("set", "filter", "exit", "random"):
        assert name not in namespace                       # the four that would have been hidden...
        assert callable(getattr(f, name))                  # ...are still f.set, f.filter, f.exit, f.random


def test_live_values_are_current_in_draw_and_in_every_callback():
    namespace = star_namespace()
    seen = []

    def setup():
        namespace["size"](200, 120)
        seen.append(("setup", namespace["width"], namespace["height"]))

    def draw():
        seen.append(("draw", namespace["frame_count"], namespace["width"], namespace["mouse_x"],
                     namespace["pmouse_x"], namespace["is_mouse_pressed"]))

    def mouse_pressed():
        seen.append(("pressed", namespace["mouse_x"], namespace["mouse_y"], namespace["mouse_button"]))

    def key_pressed():
        seen.append(("key", namespace["key"], namespace["key_code"]))

    namespace.update(setup=setup, draw=draw, mouse_pressed=mouse_pressed, key_pressed=key_pressed)
    script = {1: [InputEvent("mouse_moved", 10, 20), InputEvent("mouse_pressed", 10, 20, button="left")],
              2: [InputEvent("key_pressed", key="a", key_code=97)],
              3: [InputEvent("mouse_moved", 70, 80)]}
    sketch = api.use_sketch(Sketch(platform=ScriptedPlatform(script)))
    sketch.run_namespace(namespace, max_frames=5)
    assert seen[0] == ("setup", 200, 120)
    assert [e[1] for e in seen if e[0] == "draw"] == [0, 1, 2, 3, 4]               # frame_count moves every frame
    assert all(e[2] == 200 for e in seen if e[0] == "draw")                       # width after size()
    assert ("pressed", 10, 20, "left") in seen
    assert ("key", "a", 97) in seen
    draws = [e for e in seen if e[0] == "draw"]
    assert draws[-1][3] == 70                                                    # mouse_x followed the mouse


def test_an_import_as_f_sketch_keeps_its_own_variables():
    """A variable called width in an ``import funground as f`` sketch is never overwritten."""
    namespace = {"f": f, "width": 5, "key": "mine", "setup": lambda: f.size(100, 100), "draw": lambda: None}
    api.use_sketch(Sketch(platform=ScriptedPlatform({}))).run_namespace(namespace, max_frames=3)
    assert namespace["width"] == 5 and namespace["key"] == "mine"


def test_a_helper_module_is_not_refreshed_and_uses_the_f_form(tmp_path, monkeypatch):
    (tmp_path / "helper_s175.py").write_text("from funground import *\n\ndef where():\n    return mouse_x\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    import helper_s175

    namespace = star_namespace()
    namespace.update(setup=lambda: None, draw=lambda: None)
    sketch = api.use_sketch(Sketch(platform=ScriptedPlatform({1: [InputEvent("mouse_moved", 33, 44)]})))
    sketch.run_namespace(namespace, max_frames=3)
    assert namespace["mouse_x"] == 33
    assert helper_s175.where() != 33            # stale: the helper holds the value copied at its import
    sys.modules.pop("helper_s175")


def test_a_sketch_that_defines_draw_and_never_calls_run_starts_when_the_file_ends(tmp_path):
    marker = tmp_path / "frames.txt"
    sketch = tmp_path / "sketch.py"
    sketch.write_text(textwrap.dedent(f"""
        from funground import *

        seen = []

        def draw():
            seen.append(frame_count)
            if frame_count == 3:
                open({str(marker)!r}, "w").write(str(seen))
                stop()
    """), encoding="utf-8")
    env = dict(os.environ, FUNGROUND_HEADLESS="1", SDL_VIDEODRIVER="dummy", PYTHONPATH=str(ROOT))
    done = subprocess.run([sys.executable, str(sketch)], env=env, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    assert marker.read_text() == "[0, 1, 2, 3]"
    assert done.stderr == ""                    # and no "never started" hint


def test_a_web_session_starts_a_sketch_that_never_called_run():
    from funground.web import Session

    source = textwrap.dedent("""
        from funground import *

        x = 0

        def setup():
            size(200, 100)

        def draw():
            global x
            background(colors.WHITE)
            circle(x, height / 2, 20)
            x = mouse_x + frame_count
    """)
    frames = []
    session = Session(640, 480, on_frame=lambda data, w, h, stride: frames.append((w, h)))
    try:
        session.start(source, "sketch.py")
        assert session.running
        session.push_event("mouse_moved", 50, 40)
        for n in range(3):
            assert session.step(n / 60)
        assert frames and frames[-1] == (200, 100)
    finally:
        session.stop()


def test_a_sketch_that_defines_its_own_circle_still_gets_live_values():
    namespace = star_namespace()
    seen = []
    namespace.update(circle=lambda *a: None, setup=lambda: None, draw=lambda: seen.append(namespace["frame_count"]))
    api.use_sketch(Sketch(platform=ScriptedPlatform({}))).run_namespace(namespace, max_frames=3)
    assert seen == [0, 1, 2]
