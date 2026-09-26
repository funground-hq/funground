"""Input events and callbacks (S-045, D-016, contract I3), driven by scripted headless input."""
from __future__ import annotations

import pytest

import funground as p
from funground import api
from funground.platform.base import InputEvent
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


class ScriptedPlatform(HeadlessPlatform):
    """Delivers script[n] at the n-th poll(), i.e. just before loop iteration n - like real input."""

    def __init__(self, script):
        super().__init__()
        self._script, self._polls = script, 0

    def poll(self):
        if self._script.get(self._polls):
            self.post(*self._script[self._polls])
        self._polls += 1
        return super().poll()


def run(ns, script, frames=None):
    """Run a sketch headless; script maps loop iteration -> events delivered before it."""
    s = api.use_sketch(Sketch(platform=ScriptedPlatform(script)))
    ns.setdefault("setup", lambda: p.size(100, 100))
    ns.setdefault("draw", lambda: None)
    s.run_namespace(ns, max_frames=frames or (max(script) + 2 if script else 3))
    return s


def test_old_name_fails_with_a_pointer_to_the_new_one():
    with pytest.raises(AttributeError, match="is_mouse_pressed"):
        p.mouse_pressed  # noqa: B018


def test_mouse_callbacks_fire_once_per_event_in_order():
    log = []
    ns = {name: (lambda n=name: log.append((n, p.mouse_x, p.mouse_y, p.mouse_button)))
          for name in ("mouse_pressed", "mouse_released", "mouse_clicked", "mouse_moved", "mouse_dragged")}
    run(ns, {1: [InputEvent("mouse_moved", 10, 20), InputEvent("mouse_pressed", 10, 20, button="left"),
                 InputEvent("mouse_dragged", 30, 40), InputEvent("mouse_released", 30, 40, button="left")]})
    assert [e[0] for e in log] == ["mouse_moved", "mouse_pressed", "mouse_dragged", "mouse_released", "mouse_clicked"]
    assert log[1][3] == "left" and log[-1][1:3] == (30, 40)


def test_mouse_wheel_gets_the_delta_if_it_wants_it():
    got = []

    def mouse_wheel(delta):
        got.append(delta)

    run({"mouse_wheel": mouse_wheel}, {1: [InputEvent("mouse_wheel", delta=2.0)]})
    assert got == [2.0]
    count = []
    run({"mouse_wheel": lambda: count.append(1)}, {1: [InputEvent("mouse_wheel", delta=-1.0)]})
    assert count == [1]


def test_key_callbacks_and_live_values():
    log = []

    def key_pressed():
        log.append(("pressed", p.key, p.key_code, p.is_key_pressed))

    def key_typed():
        log.append(("typed", p.key))

    def key_released():
        log.append(("released", p.key, p.is_key_pressed))

    run({"key_pressed": key_pressed, "key_typed": key_typed, "key_released": key_released},
        {1: [InputEvent("key_pressed", key="a", key_code=97)],
         3: [InputEvent("key_released", key="a", key_code=97), InputEvent("key_pressed", key="left", key_code=1073741904)]})
    assert log[0] == ("pressed", "a", 97, True)
    assert log[1] == ("typed", "a")
    assert log[2][0:2] == ("released", "a")
    assert ("typed", "left") not in log            # names of special keys are not typed characters


def test_pmouse_is_the_previous_frame_position():
    seen = []
    run({"draw": lambda: seen.append((p.pmouse_x, p.pmouse_y, p.mouse_x, p.mouse_y))},
        {1: [InputEvent("mouse_moved", 10, 10)], 2: [InputEvent("mouse_moved", 50, 60)]})
    assert seen[1] == (0, 0, 10, 10) and seen[2] == (10, 10, 50, 60)


def test_is_mouse_pressed_and_key_down_follow_the_events():
    seen = []
    run({"draw": lambda: seen.append((p.is_mouse_pressed, p.key_down("left")))},
        {1: [InputEvent("mouse_pressed", 5, 5, button="right"), InputEvent("key_pressed", key="left", key_code=1)],
         2: [InputEvent("mouse_released", 5, 5, button="right")]})
    assert seen[0] == (False, False) and seen[1] == (True, True) and seen[2] == (False, True)


def test_a_key_press_can_redraw_a_non_looping_sketch():
    draws = []

    def setup():
        p.size(100, 100)
        p.no_loop()

    def key_pressed():
        p.redraw()

    run({"setup": setup, "draw": lambda: draws.append(p.frame_count), "key_pressed": key_pressed},
        {0: [], 2: [InputEvent("key_pressed", key=" ", key_code=32)]}, frames=6)
    assert draws == [0, 1]


def test_a_non_callable_callback_name_is_a_clear_error():
    with pytest.raises(TypeError, match="mouse_pressed"):
        run({"mouse_pressed": 3}, {})
