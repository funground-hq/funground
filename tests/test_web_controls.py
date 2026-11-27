"""Controls in Play (S-329, contract U1): the browser platform shows the panel below the canvas and routes the mouse to it."""
from __future__ import annotations

from funground import api
from funground.controls import ROW_HEIGHT
from funground.web import Session
from test_web_session import FRAME, Frames

SOURCE = (
    "import funground as f\n"
    "seen = []\n"
    "def setup():\n"
    "    f.size(100, 60)\n"
    "    global button, slider\n"
    "    button = f.create_button('go')\n"
    "    slider = f.create_slider(0, 10, 0, label='n')\n"
    "def draw():\n"
    "    f.background('white')\n"
    "def mouse_pressed():\n"
    "    seen.append(('press', f.mouse_y))\n"
    "f.run()\n"
)
PLAIN = SOURCE.replace("    global button, slider\n", "").replace("    button = f.create_button('go')\n", "") \
    .replace("    slider = f.create_slider(0, 10, 0, label='n')\n", "")


def start(source=SOURCE):
    got = Frames()
    session = Session(640, 480, on_frame=got)
    session.start(source, "sketch.py")
    ns = api.canvas_sketch()._callbacks["mouse_pressed"].__globals__
    return session, got, ns


def test_frames_and_canvas_size_include_the_panel():
    session, got, ns = start()
    assert session.canvas_size == (100, 60 + 2 * ROW_HEIGHT)
    assert session.step(0.0)
    data, width, height, stride = got.calls[-1]
    assert (width, height) == (100, 60 + 2 * ROW_HEIGHT)
    assert stride == width * 4 and len(data) == stride * height
    session.stop()


def test_capture_is_the_canvas_alone():
    session, got, ns = start()
    session.step(0.0)
    assert (session._sketch._platform._last.width, session._sketch._platform._last.height) == (100, 60)
    session.stop()


def test_a_click_on_the_button_clicks_it_and_the_sketch_does_not_see_it():
    session, got, ns = start()
    session.step(0.0)
    panel = api.canvas_sketch()._panel
    bx, by, bw, bh = panel.layout(100)[0]["button"]
    x, y = round(bx + bw / 2), 60 + round(by + bh / 2)
    session.push_event("mouse_pressed", x, y, button="left")
    session.push_event("mouse_released", x, y, button="left")
    session.step(FRAME)
    assert ns["button"].clicked() is True
    assert ns["seen"] == []
    session.stop()


def test_a_drag_on_the_slider_changes_it():
    session, got, ns = start()
    session.step(0.0)
    r = api.canvas_sketch()._panel.layout(100)[1]
    y = 60 + ROW_HEIGHT + ROW_HEIGHT // 2
    session.push_event("mouse_pressed", round(r["x0"]), y, button="left")
    session.push_event("mouse_dragged", 500, 20, button="left")    # far past the end and out of the row: the panel still has it
    session.push_event("mouse_released", 500, 20, button="left")
    session.step(FRAME)
    assert ns["slider"].value() == 10
    assert ns["seen"] == []
    session.stop()


def test_a_press_in_the_canvas_reaches_the_sketch_even_if_dragged_into_the_panel():
    session, got, ns = start()
    session.step(0.0)
    session.push_event("mouse_pressed", 10, 20, button="left")
    session.step(FRAME)
    session.push_event("mouse_dragged", 10, 70, button="left")
    session.push_event("mouse_released", 10, 70, button="left")
    session.step(FRAME * 2)
    assert ns["seen"] == [("press", 20)]
    assert ns["button"].clicked() is False
    session.stop()


def test_a_sketch_without_controls_is_unchanged():
    session, got, ns = start(PLAIN)
    assert session.canvas_size == (100, 60)
    session.step(0.0)
    assert got.calls[-1][1:3] == (100, 60)
    session.push_event("mouse_pressed", 10, 59, button="left")
    session.step(FRAME)
    assert ns["seen"] == [("press", 59)]
    session.stop()
