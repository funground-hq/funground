"""The gallery browser (S-083): a funground sketch driven by scripted headless input.

No window and no real process: Popen is replaced by a recorder.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from funground import api
from funground.platform.base import InputEvent
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch

from conftest import ROOT


class ScriptedPlatform(HeadlessPlatform):
    """Delivers script[n] just before loop iteration n, like real input."""

    def __init__(self, script):
        super().__init__()
        self._script, self._polls = script, 0

    def poll(self):
        if self._script.get(self._polls):
            self.post(*self._script[self._polls])
        self._polls += 1
        return super().poll()


@pytest.fixture
def browser(monkeypatch):
    spec = importlib.util.spec_from_file_location("gallery_browser_under_test", ROOT / "tools" / "gallery_browser.py")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)      # dataclasses look their module up here
    spec.loader.exec_module(module)
    return module


def click(x, y):
    return [InputEvent("mouse_pressed", int(x), int(y), button="left"),
            InputEvent("mouse_released", int(x), int(y), button="left")]


def centre(rect):
    x, y, w, h = rect
    return x + w / 2, y + h / 2


def press(name):
    return [InputEvent("key_pressed", key=name, key_code=1)]


def type_key(ch):
    return press(ch)


def run(browser, script, after=None):
    """Run the browser; return one state tuple per frame: (view, area, entry id, filter)."""
    states = []
    original = browser.draw

    def draw():
        original()
        app = browser.app
        states.append((app.view, app.area, app.entry.ident if app.entry else None, app.filter))
        if after:
            after(len(states) - 1, app)

    browser.draw = draw
    sketch = api.use_sketch(Sketch(platform=ScriptedPlatform(script)))
    sketch.run_namespace(vars(browser), max_frames=max(script) + 2 if script else 3)
    return states


def test_it_lists_every_gallery_example_grouped_by_area(browser):
    run(browser, {})
    gallery = browser.gallery
    app = browser.app
    assert len(app.entries) == len(gallery.examples())
    assert [e.path for e in app.entries] == gallery.examples()
    assert app.areas[0] == (None, "All", len(app.entries))
    real = app.areas[1:]
    assert sum(count for _, _, count in real) == len(app.entries)
    assert [key for key, _, _ in real] == sorted({e.area for e in app.entries},
                                                  key=lambda a: (gallery.area_rank(a), a))
    for key, title, _ in real:
        assert title == gallery.AREAS.get(key, key.title())
    assert app.view == "grid" and app.area is None


def test_clicks_and_keys_move_between_views(browser):
    script = {
        1: click(*centre(browser.area_rect(2))),        # the second real area
        2: click(*centre(browser.card_rect(1))),
        3: press("right"),
        4: press("left"),
        5: press("left"),
        6: press("backspace"),
        7: click(*centre(browser.area_rect(0))),
    }
    states = run(browser, script)
    app = browser.app
    area_key = app.areas[2][0]
    in_area = [e for e in app.entries if e.area == area_key]
    assert len(in_area) >= 3
    assert states[0][:2] == ("grid", None)
    assert states[1] == ("grid", area_key, None, "")
    assert states[2] == ("detail", area_key, in_area[1].ident, "")
    assert states[3][2] == in_area[2].ident
    assert states[4][2] == in_area[1].ident
    assert states[5][2] == in_area[0].ident
    assert states[6] == ("grid", area_key, None, "")
    assert states[7] == ("grid", None, None, "")


def test_previous_stops_at_the_first_example_and_next_at_the_last(browser):
    script = {1: click(*centre(browser.area_rect(1))), 2: click(*centre(browser.card_rect(0))),
              3: press("left")}
    first_area = browser.gallery.examples()[0].parent.name
    count = sum(1 for p in browser.gallery.examples() if p.parent.name == first_area)
    for n in range(4, 5 + count):
        script[n] = press("right")
    states = run(browser, script)
    app = browser.app
    in_area = [e for e in app.entries if e.area == app.areas[1][0]]
    assert states[3][2] == in_area[0].ident
    assert states[-1][2] == in_area[-1].ident


class FakePopen:
    calls: list = []

    def __init__(self, args, **kwargs):
        self.args, self.kwargs = args, kwargs
        FakePopen.calls.append(self)

    def poll(self):
        return None                                     # still running


def test_run_starts_the_example_in_a_scratch_folder_and_never_twice(browser, monkeypatch):
    FakePopen.calls = []
    monkeypatch.setattr(browser.subprocess, "Popen", FakePopen)
    run_button = centre(browser.BUTTONS["run"])
    script = {1: click(*centre(browser.area_rect(1))), 2: click(*centre(browser.card_rect(0))),
              3: press("enter"), 4: press("enter"), 5: click(*run_button)}
    run(browser, script)
    app = browser.app
    assert len(FakePopen.calls) == 1
    call = FakePopen.calls[0]
    path = [e for e in app.entries if e.area == app.areas[1][0]][0].path
    assert call.args == [sys.executable, str(path)]
    cwd = Path(call.kwargs["cwd"]).resolve()
    assert ROOT.resolve() not in (cwd, *cwd.parents)
    assert cwd.is_dir()


def test_a_finished_example_can_be_run_again(browser, monkeypatch):
    class Finished(FakePopen):
        def poll(self):
            return 0

    FakePopen.calls = []
    monkeypatch.setattr(browser.subprocess, "Popen", Finished)
    run(browser, {1: click(*centre(browser.area_rect(1))), 2: click(*centre(browser.card_rect(0))),
                  3: press("enter"), 4: press("enter")})
    assert len(FakePopen.calls) == 2


def test_a_missing_picture_shows_a_placeholder(browser, tmp_path):
    browser.IMAGES_DIR = tmp_path / "no_images_here"
    shot = tmp_path / "missing.png"

    def after(n, app):
        if n == 3:
            browser.f.save(str(shot))

    run(browser, {1: click(*centre(browser.area_rect(1))), 2: click(*centre(browser.card_rect(0)))}, after)
    app = browser.app
    assert all(e.image is None for e in app.entries)
    assert all(e.thumb is not None for e in app.entries)
    assert shot.exists() and shot.stat().st_size > 0
    assert "no picture yet" in browser.MISSING


def test_the_filter_narrows_the_grid(browser):
    script = {1: type_key("/"), 2: type_key("t"), 3: type_key("e"), 4: type_key("x"), 5: type_key("t"),
              6: press("enter"), 7: press("backspace")}
    states = run(browser, script)
    assert states[5][3] == "text"
    assert states[6][3] == "text"                       # Enter keeps it
    assert states[7][3] == ""                           # Backspace in the grid clears it
    app = browser.app
    app.filter = "text"
    assert app.visible() and all("text" in e.title.lower() for e in app.visible())


def test_wheel_scrolls_the_grid_and_the_code(browser):
    script = {1: [InputEvent("mouse_wheel", 400, 300, delta=3.0)],
              2: [InputEvent("mouse_wheel", 400, 300, delta=-30.0)],
              3: click(*centre(browser.area_rect(0))), 4: click(*centre(browser.card_rect(0))),
              5: [InputEvent("mouse_wheel", 400, 500, delta=2.0)]}
    seen = {}

    def after(n, app):
        seen[n] = (app.grid_scroll, app.code_scroll)

    run(browser, script, after)
    assert seen[1][0] == 3.0 * browser.WHEEL_STEP
    assert seen[2][0] == 0.0                            # never above the top
    assert 0.0 < seen[5][1] <= browser.app.max_code_scroll()


def test_screenshots_of_the_grid_and_a_detail_view(browser, tmp_path):
    grid, detail = tmp_path / "grid.png", tmp_path / "detail.png"

    def after(n, app):
        if n == 3:
            browser.f.save(str(grid))
        if n == 6:
            browser.f.save(str(detail))

    script = {1: [InputEvent("mouse_moved", *map(int, centre(browser.card_rect(1))))],
              4: click(*centre(browser.card_rect(1))),
              5: [InputEvent("mouse_wheel", 600, 500, delta=1.0)]}
    run(browser, script, after)
    assert grid.exists() and grid.stat().st_size > 1000
    assert detail.exists() and detail.stat().st_size > 1000
