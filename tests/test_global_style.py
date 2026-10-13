"""The global style (D-088, S-176): ``from funground import *`` is safe, live values are current, run() is optional."""
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
    assert set(f.__all__) == set(f._PUBLIC_NAMES) - set(f.STAR_LEAVES_OUT)
    for other in f.STAR_NAMES_FOR.values():                 # each left-out name has one that is brought in
        assert other in namespace
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
    (tmp_path / "helper_s176.py").write_text("from funground import *\n\ndef where():\n    return mouse_x\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    import helper_s176

    namespace = star_namespace()
    namespace.update(setup=lambda: None, draw=lambda: None)
    sketch = api.use_sketch(Sketch(platform=ScriptedPlatform({1: [InputEvent("mouse_moved", 33, 44)]})))
    sketch.run_namespace(namespace, max_frames=3)
    assert namespace["mouse_x"] == 33
    assert helper_s176.where() != 33            # stale: the helper holds the value copied at its import
    sys.modules.pop("helper_s176")


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
            background("white")
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


def test_a_script_reads_its_new_size_at_once():
    """A script (no draw()) in the global style: width and height are current right after size()."""
    namespace = {"__name__": "__main__"}
    api.use_sketch(Sketch(platform=ScriptedPlatform({})))
    exec("from funground import *\nsize(300, 200)\nseen = (width, height)\n"
         "new_page(120, 90)\nseen_after = (width, height)\n", namespace)
    assert namespace["seen"] == (300, 200)
    assert namespace["seen_after"] == (120, 90)


def test_pixels_are_current_right_after_load_pixels():
    namespace = star_namespace()
    seen = []

    def draw():
        namespace["background"]("red")
        namespace["load_pixels"]()
        seen.append(bytes(namespace["pixels"][:4]))
        namespace["stop"]()

    namespace.update(setup=lambda: namespace["size"](20, 10), draw=draw)
    api.use_sketch(Sketch(platform=ScriptedPlatform({}))).run_namespace(namespace, max_frames=2)
    assert seen == [bytes((255, 0, 0, 255))]


def test_a_variable_that_hides_a_funground_function_is_named_in_the_error():
    namespace = star_namespace()
    namespace["size"] = 40

    def setup():
        namespace["size"](640, 400)

    namespace.update(setup=setup, draw=lambda: None)
    sketch = api.use_sketch(Sketch(platform=ScriptedPlatform({})))
    try:
        sketch.run_namespace(namespace, max_frames=1)
    except TypeError as error:
        notes = getattr(error, "__notes__", [])
    else:
        raise AssertionError("size(640, 400) on an int should fail")
    assert notes == ["Your sketch has a variable called size, which hides funground's size(). Give the variable "
                     "another name (for example my_size)."]


def test_an_import_as_f_sketch_gets_no_clash_sentence():
    namespace = {"f": f, "size": 40}

    def draw():
        namespace["size"]()

    namespace.update(draw=draw)
    sketch = api.use_sketch(Sketch(platform=ScriptedPlatform({})))
    try:
        sketch.run_namespace(namespace, max_frames=1)
    except TypeError as error:
        assert not getattr(error, "__notes__", None)
    else:
        raise AssertionError("calling an int should fail")


def test_the_other_names_do_what_the_left_out_ones_do():
    api.use_sketch(Sketch(platform=ScriptedPlatform({})))
    f.random_seed(3)
    first = f.random(5, 10)
    f.random_seed(3)
    assert f.random_number(5, 10) == first
    namespace = {"__name__": "__main__"}
    exec("from funground import *\nsize(20, 10)\nset_pixel(3, 4, 'red')\napply_filter('invert')\n"
         "colour = get(3, 4)\n", namespace)
    assert namespace["colour"] == f.color(0, 255, 255)


def test_random_without_the_prefix_points_to_funground_random():
    namespace = star_namespace()
    exec("def draw():\n    circle(random(640), 100, 20)\n", namespace)
    sketch = api.use_sketch(Sketch(platform=ScriptedPlatform({})))
    try:
        sketch.run_namespace(namespace, max_frames=1)
    except NameError as error:
        notes = getattr(error, "__notes__", [])
    else:
        raise AssertionError("random is not brought in by the star")
    assert notes == ["funground's random() is not brought in by from funground import *, because it would hide "
                     "Python's random module. Write random_number() instead: the same function."]


def test_a_top_level_error_in_a_global_style_web_script_gets_the_sentence():
    from funground.web import Session

    session = Session(640, 480, on_frame=lambda *a: None)
    try:
        session.start("from funground import *\nsize(100, 100)\nx = random(10)\n", "sketch.py")
    except NameError as error:
        assert any("random_number()" in note for note in getattr(error, "__notes__", []))
    else:
        raise AssertionError("random is not brought in by the star")
