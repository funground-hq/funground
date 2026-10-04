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
    spec = importlib.util.spec_from_file_location("gallery_browser_under_test", ROOT / "funground" / "gallery.py")
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
    examples = browser.list_examples(browser.LOCATIONS.examples)
    app = browser.app
    assert len(app.entries) == len(examples)
    assert [e.path for e in app.entries] == examples
    assert app.areas[0] == (None, "All", len(app.entries))
    real = app.areas[1:]
    assert sum(count for _, _, count in real) == len(app.entries)
    assert [key for key, _, _ in real] == sorted({e.area for e in app.entries},
                                                  key=lambda a: (browser.area_rank(a), a))
    for key, title, _ in real:
        assert title == browser.AREAS.get(key, key.title())
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
    examples = browser.list_examples(browser.LOCATIONS.examples)
    first_area = examples[0].parent.name
    count = sum(1 for p in examples if p.parent.name == first_area)
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
    browser.LOCATIONS = browser.Locations(browser.LOCATIONS.examples, tmp_path / "no_images_here")
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


def test_c_and_the_copy_button_copy_the_example_and_never_overwrite(browser, tmp_path):
    keys = sorted({p.parent.name for p in browser.list_examples(browser.LOCATIONS.examples)},
                  key=lambda a: (browser.area_rank(a), a))
    images_area = 1 + keys.index("images")
    script = {1: click(*centre(browser.area_rect(images_area))), 2: click(*centre(browser.card_rect(0))),
              3: press("c"), 4: click(*centre(browser.BUTTONS["copy"]))}
    seen = {}

    def after(n, app):
        if n == 0:
            app.copy_dir = tmp_path
        seen[n] = app.status[0]

    run(browser, script, after)
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["01_load_image.py", "01_load_image_2.py", "data"]
    assert (tmp_path / "data" / "photo.jpg").is_file()
    assert seen[3].startswith("Copied to") and "01_load_image.py" in seen[3]
    assert str(tmp_path) in seen[3]
    assert "C: copy" in (ROOT / "funground" / "gallery.py").read_text(encoding="utf-8")


# ---- saved files: where did my file go?
def fake_saver(files):
    """A Popen stand-in that 'runs' an example by writing ``files`` into its folder."""
    class Saver(FakePopen):
        def __init__(self, args, **kwargs):
            super().__init__(args, **kwargs)
            for name in files:
                (Path(kwargs["cwd"]) / name).write_bytes(b"x")

        def poll(self):
            return 0
    return Saver


def detail_script(browser, extra):
    script = {1: click(*centre(browser.area_rect(1))), 2: click(*centre(browser.card_rect(0)))}
    script.update(extra)
    return script


def test_a_saved_file_is_named_in_the_status_with_its_folder(browser, monkeypatch, capsys):
    FakePopen.calls = []
    monkeypatch.setattr(browser.subprocess, "Popen", fake_saver(["poster.pdf", "poster.svg"]))
    seen = {}
    run(browser, detail_script(browser, {3: press("enter")}), lambda n, app: seen.__setitem__(n, app.status[0]))
    folder = Path(FakePopen.calls[0].kwargs["cwd"])
    message = seen[max(seen)]
    assert message.startswith("Saved: poster.pdf, poster.svg")
    assert str(folder) in message
    out = capsys.readouterr().out
    assert str(folder) in out and "poster.pdf" in out and "poster.svg" in out
    assert out.count("Saved in") == 1                    # printed once, not every frame


def test_a_long_list_of_saved_files_is_shortened(browser, tmp_path):
    names = [f"frame_{i}.png" for i in range(6)]
    message = browser.saved_message(names, tmp_path)
    assert "frame_0.png, frame_1.png, frame_2.png + 3 more" in message
    assert str(tmp_path) in message


def test_o_and_the_folder_button_open_the_folder_when_asked(browser, monkeypatch):
    FakePopen.calls = []
    monkeypatch.setattr(browser.subprocess, "Popen", fake_saver(["a.png"]))
    opened = []
    monkeypatch.setattr(browser, "open_in_file_browser", opened.append)
    script = detail_script(browser, {3: press("enter"), 4: press("o"), 5: click(*centre(browser.BUTTONS["folder"]))})
    run(browser, script)
    folder = Path(FakePopen.calls[0].kwargs["cwd"])
    assert opened == [folder, folder]
    assert "O: open" in (ROOT / "funground" / "gallery.py").read_text(encoding="utf-8")


def test_nothing_is_opened_until_the_learner_asks(browser, monkeypatch):
    FakePopen.calls = []
    monkeypatch.setattr(browser.subprocess, "Popen", fake_saver(["a.png"]))
    opened = []
    monkeypatch.setattr(browser, "open_in_file_browser", opened.append)
    run(browser, detail_script(browser, {3: press("enter")}))
    assert opened == []


def test_an_example_that_saves_nothing_gives_no_message_and_o_does_nothing(browser, monkeypatch, capsys):
    FakePopen.calls = []
    monkeypatch.setattr(browser.subprocess, "Popen", fake_saver([]))
    opened = []
    monkeypatch.setattr(browser, "open_in_file_browser", opened.append)
    seen = {}
    run(browser, detail_script(browser, {3: press("enter"), 6: press("o")}),
        lambda n, app: seen.__setitem__(n, app.status[0]))
    assert not any(m.startswith("Saved") for m in seen.values())
    assert seen[4].startswith("Started")
    assert opened == []
    assert "Saved in" not in capsys.readouterr().out


def test_each_run_gets_its_own_folder(browser, monkeypatch):
    FakePopen.calls = []
    monkeypatch.setattr(browser.subprocess, "Popen", fake_saver(["a.png"]))
    run(browser, detail_script(browser, {3: press("enter"), 4: press("enter")}))
    first, second = (Path(c.kwargs["cwd"]) for c in FakePopen.calls)
    assert first != second and first.parent == second.parent
    assert first.name == browser.app.entry.path.stem
    assert (first / "a.png").is_file() and (second / "a.png").is_file()


def test_the_detail_view_shows_how_it_works_and_make_it_yours(browser, tmp_path):
    """S-120: an explained example opens on its explanation; E and S (or the tabs) switch panels."""
    probe = {}

    def after(n, app):
        if n == 0:
            probe["entry"] = next(e for e in app.entries if e.how)
            probe["plain"] = next((e for e in app.entries if not e.how), None)
            app.open(probe["entry"])
        if n == 2:
            probe["after_open"] = app.panel
            browser.f.save(str(tmp_path / "explain.png"))
        if n == 4:
            probe["after_s"] = app.panel
        if n == 6:
            probe["after_tab"] = app.panel

    script = {3: press("s"), 5: click(*centre(browser.TABS["explain"]))}
    run(browser, script, after)
    entry = probe["entry"]
    assert 3 <= len(entry.how) <= 6 and 3 <= len(entry.make) <= 5
    assert probe["after_open"] == "explain"
    assert probe["after_s"] == "code"
    assert probe["after_tab"] == "explain"
    assert (tmp_path / "explain.png").stat().st_size > 1000
    assert "How it works" in entry.path.read_text(encoding="utf-8")
    assert entry.description and "How it works" not in entry.description


def test_an_example_without_sections_opens_on_its_code(browser):
    seen = {}

    def after(n, app):
        if n == 0:
            plain = next((e for e in app.entries if not e.how), None)
            if plain is None:
                seen["panel"] = "code"            # every example is explained: nothing to check
            else:
                app.open(plain)
        if n == 2 and "panel" not in seen:
            seen["panel"] = app.panel

    run(browser, {}, after)
    assert seen["panel"] == "code"


def test_the_explanation_scrolls_when_it_is_long(browser):
    seen = {}

    def after(n, app):
        if n == 0:
            app.open(next(e for e in app.entries if e.how))
            app.entry.how = app.entry.how + ("An extra point that is long enough to wrap onto more than one line of the panel. " * 3,) * 8
        if n == 1:
            seen["top"] = app.max_code_scroll()
            app.wheel(2)
        if n == 2:
            seen["scroll"] = app.code_scroll

    run(browser, {}, after)
    assert seen["top"] > 0 and 0 < seen["scroll"] <= seen["top"]
