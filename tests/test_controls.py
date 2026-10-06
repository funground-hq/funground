"""Controls: sliders, checkboxes, buttons and their panel (S-101, D-047, contract U1).

The model and the facade run headless. The panel's window, drawing and mouse routing are
checked with the real pygame platform on SDL's dummy video driver, as the HiDPI tests do.
"""
from __future__ import annotations

import pygame
import pytest

import funground as p
from funground import api
from funground.controls import ROW_HEIGHT, Button, Checkbox, ControlPanel, Slider, panel_ops
from funground.platform.headless import HeadlessPlatform
from funground.platform.pygame_platform import PygamePlatform
from funground.sketch import Sketch


def run(ns, frames=2, platform=None):
    s = api.use_sketch(Sketch(platform=platform or HeadlessPlatform()))
    ns.setdefault("setup", lambda: p.size(100, 60))
    ns.setdefault("draw", lambda: None)
    s.run_namespace(ns, max_frames=frames)
    return s


# ---------------------------------------------------------------- the objects

def test_slider_defaults_to_low_and_reads_back():
    assert Slider(0, 10).value() == 0
    assert Slider(0, 10, 4).value() == 4
    assert Slider(0.5, 2.5, 1.5).value() == 1.5


def test_slider_value_is_kept_between_low_and_high():
    s = Slider(0, 10, 50)
    assert s.value() == 10                       # the start value is kept in range too
    s.value(-3)
    assert s.value() == 0
    s.value(7.5)
    assert s.value() == 7.5


def test_slider_rounds_to_its_step():
    s = Slider(0, 10, step=2)
    s.value(4.9)
    assert s.value() == 4
    s.value(5.2)
    assert s.value() == 6
    f = Slider(0, 1, step=0.1)
    f.value(0.34)
    assert f.value() == 0.3
    f.value(0.1 + 0.2)
    assert f.value() == 0.3                      # no 0.30000000000000004


def test_slider_step_counts_from_low_and_never_passes_high():
    s = Slider(1, 10, step=4)                    # 1, 5, 9 and then 10 would be past the last step
    s.value(10)
    assert s.value() == 9
    assert Slider(3, 9, step=2, value=4.2).value() == 5


def test_slider_gives_whole_numbers_when_its_steps_are_whole():
    s = Slider(0, 10, step=1)
    s.value(3.4)
    assert s.value() == 3 and isinstance(s.value(), int)
    t = Slider(0, 1)
    t.value(0.25)
    assert t.value() == 0.25                      # no step: fractions allowed
    assert isinstance(Slider(0.0, 10.0, step=1).value(), float)


def test_slider_setter_returns_nothing():
    assert Slider(0, 1).value(0.5) is None


@pytest.mark.parametrize("low, high", [(5, 5), (6, 5), (0.0, -1.0)])
def test_slider_needs_low_below_high(low, high):
    with pytest.raises(ValueError, match="low"):
        Slider(low, high)


@pytest.mark.parametrize("step", [0, -1, -0.5])
def test_slider_step_must_be_more_than_zero(step):
    with pytest.raises(ValueError, match="step"):
        Slider(0, 10, step=step)


@pytest.mark.parametrize("bad", ["3", None, True, [1]])
def test_slider_numbers_must_be_numbers(bad):
    with pytest.raises(TypeError):
        Slider(0, 10, bad if bad is not None else "x")
    with pytest.raises(TypeError):
        Slider(0, 10).value(bad if bad is not None else "x")


def test_slider_refuses_nan_and_infinity():
    with pytest.raises(ValueError):
        Slider(0, float("inf"))
    with pytest.raises(ValueError):
        Slider(0, 1).value(float("nan"))


def test_checkbox_defaults_to_unchecked_and_can_be_set():
    c = Checkbox("grid")
    assert c.checked() is False
    assert c.checked(True) is None
    assert c.checked() is True
    assert Checkbox("on", True).checked() is True
    c.checked(0)
    assert c.checked() is False


def test_button_click_is_true_once_per_click():
    panel = ControlPanel()
    b = panel.add(Button("go"))
    assert b.clicked() is False
    row = panel.layout(200)[0]["button"]
    x, y = row[0] + 2, row[1] + 2
    panel.press(x, y, 200)
    assert b.clicked() is False                  # only a full click counts
    panel.release(x, y, 200)
    assert b.clicked() is True
    assert b.clicked() is False
    panel.press(x, y, 200)
    panel.release(x, y, 200)
    assert b.clicked() is True and b.clicked() is False


def test_button_released_away_from_the_button_is_not_a_click():
    panel = ControlPanel()
    b = panel.add(Button("go"))
    bx, by, bw, bh = panel.layout(200)[0]["button"]
    panel.press(bx + 2, by + 2, 200)
    panel.release(bx + bw + 40, by + 2, 200)
    assert b.clicked() is False


# ---------------------------------------------------------------- the panel model

def test_panel_height_is_one_row_for_each_control():
    panel = ControlPanel()
    assert panel.height == 0 and not panel
    panel.add(Slider(0, 1))
    panel.add(Checkbox("a"))
    panel.add(Button("b"))
    assert panel.height == 3 * ROW_HEIGHT
    assert 28 <= ROW_HEIGHT <= 32


def test_dragging_a_slider_moves_its_value():
    panel = ControlPanel()
    s = panel.add(Slider(0, 100, label="size"))
    r = panel.layout(300)[0]
    mid = (r["x0"] + r["x1"]) / 2
    panel.press(mid, 10, 300)
    assert s.value() == pytest.approx(50)
    panel.drag(r["x1"] + 500, 10, 300)           # far past the end: stays at high
    assert s.value() == 100
    panel.drag(r["x0"] - 500, 10, 300)
    assert s.value() == 0
    panel.release(0, 10, 300)
    panel.drag(mid, 10, 300)                     # not held any more
    assert s.value() == 0


def test_a_slider_with_a_step_snaps_while_dragging():
    panel = ControlPanel()
    s = panel.add(Slider(0, 10, step=1))
    r = panel.layout(300)[0]
    panel.press(r["x0"] + 0.37 * (r["x1"] - r["x0"]), 10, 300)
    assert s.value() == 4


def test_clicking_a_checkbox_toggles_it_and_the_panel_notices():
    panel = ControlPanel()
    c = panel.add(Checkbox("show"))
    v = panel.version
    panel.press(12, 12, 200)
    panel.release(12, 12, 200)
    assert c.checked() is True and panel.version > v
    panel.press(12, 12, 200)
    panel.release(12, 12, 200)
    assert c.checked() is False


def test_each_row_answers_only_to_its_own_clicks():
    panel = ControlPanel()
    a = panel.add(Checkbox("a"))
    b = panel.add(Checkbox("b"))
    panel.press(12, ROW_HEIGHT + 12, 200)
    assert (a.checked(), b.checked()) == (False, True)


def test_changing_a_value_from_code_makes_the_panel_draw_again():
    panel = ControlPanel()
    s = panel.add(Slider(0, 10))
    v = panel.version
    s.value(0)
    assert panel.version == v                    # nothing changed
    s.value(4)
    assert panel.version > v


def test_panel_ops_draw_on_a_renderer_with_the_panel_colours():
    from funground.renderers.cairo2d import CairoRenderer
    from funground import ir

    panel = ControlPanel()
    panel.add(Slider(0, 10, 5, label="size"))
    panel.add(Checkbox("grid", True))
    panel.add(Button("go"))
    r = CairoRenderer()
    r.attach(300, panel.height, 1.0)
    ops = panel_ops(panel, 300)
    r.render(ir.Frame(ops))
    data = bytes(r.pixels().data)
    assert len(data) == 300 * panel.height * 4
    assert len(set(data[i:i + 4] for i in range(0, len(data), 4))) > 6      # text, track, box, button
    at = 4 * (300 * 5 + 290)                                               # row 5: below the top edge line
    assert data[at:at + 3] == bytes((238, 238, 238))                       # the panel's own background


# ---------------------------------------------------------------- the facade

def test_the_facade_makes_controls_in_order_and_the_sketch_owns_them():
    got = {}

    def setup():
        p.size(100, 60)
        got["s"] = p.create_slider(0, 5, 2, label="n")
        got["c"] = p.create_checkbox("tick", True)
        got["b"] = p.create_button("go")

    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": setup, "draw": lambda: None}, max_frames=1)
    assert [type(c) for c in (got["s"], got["c"], got["b"])] == [Slider, Checkbox, Button]
    assert got["s"].value() == 2 and got["c"].checked() is True


def test_controls_can_be_made_at_the_top_level_before_run():
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    slider = p.create_slider(0, 1)
    p.size(80, 40)                               # a top-level size() is not drawing: still fine
    box = p.create_checkbox("x")
    assert [c for c in s._panel.controls] == [slider, box]
    seen = []
    s.run_namespace({"draw": lambda: seen.append(slider.value())}, max_frames=1)
    assert seen == [0]


def test_headless_controls_keep_their_values_and_can_be_set():
    seen = []

    def draw():
        s.value(p.frame_count + 1)
        seen.append(s.value())

    s = p.create_slider(0, 10)
    run({"draw": draw}, frames=3)
    assert seen == [1, 2, 3]


def test_a_control_made_in_draw_is_refused_and_the_message_names_setup():
    def draw():
        p.create_button("again")

    with pytest.raises(RuntimeError, match="setup"):
        run({"draw": draw})


def test_a_control_in_a_script_is_refused():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(100, 100)
    p.circle(50, 50, 20)                          # now it is a script
    with pytest.raises(RuntimeError, match="animated"):
        p.create_slider(0, 1)


def test_a_script_that_made_controls_cannot_show():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    p.size(100, 100)
    p.create_checkbox("x")
    with pytest.raises(RuntimeError, match="animated"):
        p.show()


def test_bad_ranges_through_the_facade_raise_value_error():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with pytest.raises(ValueError):
        p.create_slider(3, 3)
    with pytest.raises(ValueError):
        p.create_slider(0, 3, step=0)


def test_controls_do_not_outlive_the_run():
    s = run({"setup": lambda: (p.size(50, 50), p.create_button("x"))})
    assert len(s._panel) == 0


# ---------------------------------------------------------------- nothing reaches the canvas

def _canvas_run(tmp_path, tag, with_controls):
    def setup():
        p.size(120, 80)
        if with_controls:
            p.create_slider(0, 1, label="a")
            p.create_checkbox("b")
            p.create_button("c")

    def draw():
        p.background(30)
        p.fill("tomato")
        p.circle(60 + p.frame_count, 40, 30)
        p.save(str(tmp_path / f"{tag}.png"))
        if p.frame_count == 1:
            draw.px = p.get(60, 40)
            draw.size = (p.width, p.height)

    s = run({"setup": setup, "draw": draw}, frames=2)
    return s, draw.px, draw.size, (tmp_path / f"{tag}.png").read_bytes()


def test_controls_leave_the_ir_the_saves_get_and_the_size_unchanged(tmp_path):
    a, px_a, size_a, png_a = _canvas_run(tmp_path, "a", False)
    b, px_b, size_b, png_b = _canvas_run(tmp_path, "b", True)
    assert a.last_ops == b.last_ops
    assert (px_a, size_a, png_a) == (px_b, size_b, png_b)
    assert size_b == (120, 80)
    assert a.last_frame == b.last_frame


# ---------------------------------------------------------------- the real platform (dummy video)

@pytest.fixture
def pg(monkeypatch):
    monkeypatch.delenv("FUNGROUND_HEADLESS", raising=False)
    monkeypatch.delenv("FUNGROUND_BACKING_SCALE", raising=False)
    return PygamePlatform


def run_pg(setup, draw, frames=4, **ns):
    platform = PygamePlatform()
    s = api.use_sketch(Sketch(platform=platform))
    s.run_namespace({"setup": setup, "draw": draw, **ns}, max_frames=frames)
    return s, platform


def click(x, y, scale=1):
    """Post a left click at logical (x, y); the next poll() reads it."""
    pos = (round(x * scale), round(y * scale))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))


def test_window_is_taller_by_the_panel_and_the_canvas_keeps_its_size(pg):
    seen = {}

    def setup():
        p.create_slider(0, 1)
        p.create_button("go")
        p.size(200, 100)

    def draw():
        seen["screen"] = pygame.display.get_surface().get_size()
        seen["canvas"] = (p.width, p.height)

    run_pg(setup, draw, frames=1)
    assert seen["screen"] == (200, 100 + 2 * ROW_HEIGHT)
    assert seen["canvas"] == (200, 100)


def test_controls_made_after_size_grow_the_open_window(pg):
    seen = {}

    def setup():
        p.size(200, 100)
        seen["before"] = pygame.display.get_surface().get_size()
        p.create_checkbox("x")
        p.create_slider(0, 1)
        p.create_button("go")

    def draw():
        seen["after"] = pygame.display.get_surface().get_size()

    run_pg(setup, draw, frames=1)
    assert seen["before"] == (200, 100) and seen["after"] == (200, 100 + 3 * ROW_HEIGHT)


def test_the_window_is_sized_in_physical_pixels_on_a_hidpi_screen(pg, monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    seen = {}

    def setup():
        p.size(200, 100)
        p.create_slider(0, 1)

    def draw():
        seen["screen"] = pygame.display.get_surface().get_size()
        seen["panel_row"] = pygame.display.get_surface().get_at((399, 100 * 2 + 4))[:3]

    s, _ = run_pg(setup, draw, frames=2)
    assert seen["screen"] == (400, 200 + 2 * ROW_HEIGHT)
    assert seen["panel_row"] == (238, 238, 238)         # the panel is drawn below the canvas, at 2x
    assert (s.width, s.height) == (200, 100)


def test_the_panel_is_drawn_below_the_canvas_and_the_canvas_stays_clean(pg):
    seen = {}

    def setup():
        p.size(200, 100)
        p.create_checkbox("grid", True)

    def draw():
        p.background(10, 20, 30)
        if p.frame_count == 1:
            surf = pygame.display.get_surface()
            seen["canvas"] = surf.get_at((100, 99))[:3]
            seen["panel"] = surf.get_at((199, 100 + 25))[:3]

    run_pg(setup, draw, frames=2)
    assert seen["canvas"] == (10, 20, 30)
    assert seen["panel"] == (238, 238, 238)


def test_panel_clicks_update_controls_and_never_reach_the_sketch(pg):
    log = []
    got = {}

    def setup():
        p.size(200, 100)
        got["box"] = p.create_checkbox("x")
        got["btn"] = p.create_button("go")

    def draw():
        if p.frame_count == 0:
            click(12, 100 + 12)                                   # the checkbox row
            r = got["s"]._panel.layout(200)[1]["button"]
            click(r[0] + 4, 100 + r[1] + 4)                       # the button row
        log.append((p.is_mouse_pressed, got["box"].checked(), got["btn"].clicked()))

    s = api.use_sketch(Sketch(platform=PygamePlatform()))
    got["s"] = s
    seen = []
    s.run_namespace({"setup": setup, "draw": draw,
                     "mouse_pressed": lambda: seen.append("pressed"),
                     "mouse_released": lambda: seen.append("released"),
                     "mouse_clicked": lambda: seen.append("clicked"),
                     "mouse_moved": lambda: seen.append("moved"),
                     "mouse_dragged": lambda: seen.append("dragged")}, max_frames=3)
    assert seen == []
    assert log[1][1:] == (True, True)                # toggled once, clicked once
    assert log[2][1:] == (True, False)
    assert all(not pressed for pressed, *_ in log)


def test_a_click_on_the_canvas_still_reaches_the_sketch(pg):
    seen = []

    def draw():
        if p.frame_count == 0:
            pygame.mouse.set_pos((50, 50))
            click(50, 50)

    run_pg(lambda: (p.size(200, 100), p.create_button("go")), draw, frames=3,
           mouse_pressed=lambda: seen.append((p.mouse_x, p.mouse_y)),
           mouse_released=lambda: seen.append("up"))
    assert seen == [(50, 50), "up"]


def test_a_drag_that_began_on_the_canvas_and_ends_over_the_panel_still_releases(pg):
    seen = []

    def draw():
        if p.frame_count == 0:
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(50, 50), button=1))
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(50, 115), button=1))

    run_pg(lambda: (p.size(200, 100), p.create_button("go")), draw, frames=3,
           mouse_pressed=lambda: seen.append("down"), mouse_released=lambda: seen.append("up"))
    assert seen == ["down", "up"]


def test_dragging_the_slider_across_the_panel_and_off_it_follows_the_mouse(pg):
    got = {}

    def setup():
        p.size(300, 100)
        got["s"] = p.create_slider(0, 100)

    def draw():
        r = api.active_sketch()._panel.layout(300)[0]
        if p.frame_count == 0:
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(round(r["x0"]), 115), button=1))
            pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=(round(r["x1"]) + 30, 60), rel=(0, 0),
                                                 buttons=(1, 0, 0)))                 # up on the canvas, still held
        if p.frame_count == 1:
            got["held"] = got["s"].value()
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(round(r["x1"]), 60), button=1))

    seen = []
    run_pg(setup, draw, frames=4, mouse_dragged=lambda: seen.append("dragged"),
           mouse_released=lambda: seen.append("up"))
    assert got["held"] == 100
    assert seen == []


def test_the_capture_of_a_run_is_the_canvas_only(pg):
    s, _ = run_pg(lambda: (p.size(60, 40), p.create_slider(0, 1)), lambda: p.background("red"), frames=2)
    (w, h), rgb = s.last_frame
    assert (w, h) == (60, 40) and len(rgb) == 60 * 40 * 3
    assert rgb[:3] == b"\xff\x00\x00"


def test_the_panel_changes_show_even_when_draw_does_not_run(pg):
    seen = {}

    def setup():
        p.size(100, 60)
        seen["box"] = p.create_checkbox("x")
        p.no_loop()

    def draw():
        if p.frame_count == 0:
            click(12, 60 + 12)

    s = api.use_sketch(Sketch(platform=PygamePlatform()))
    shots = []
    real = s._platform.present_panel

    def spy(pixels):
        shots.append(bytes(pixels.data))
        real(pixels)

    s._platform.present_panel = spy
    s.run_namespace({"setup": setup, "draw": draw}, max_frames=4)
    assert seen["box"].checked() is True
    assert len(shots) == 2 and shots[0] != shots[1]      # drawn once, then again for the tick


def test_panel_clicks_are_read_in_logical_pixels_on_a_hidpi_screen(pg, monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    got = {}

    def setup():
        p.size(200, 100)
        got["box"] = p.create_checkbox("x")

    def draw():
        if p.frame_count == 0:
            click(12, 100 + 12, scale=2)         # the platform reports physical pixels; the panel reads logical ones

    seen = []
    run_pg(setup, draw, frames=3, mouse_pressed=lambda: seen.append(1))
    assert got["box"].checked() is True and seen == []


# ---------------------------------------------------------------- hiding controls (S-127, D-067)

def _panel_pixels(panel, width=300):
    from funground.renderers.cairo2d import CairoRenderer
    from funground import ir

    r = CairoRenderer()
    r.attach(width, panel.height, 1.0)
    r.render(ir.Frame(panel_ops(panel, width)))
    return bytes(r.pixels().data)


def test_a_control_is_visible_by_default_and_can_be_hidden_and_shown():
    for c in (Slider(0, 1), Checkbox("a"), Button("b")):
        assert c.visible() is True
        assert c.visible(False) is None
        assert c.visible() is False
        c.visible(True)
        assert c.visible() is True


def test_a_hidden_slider_ignores_press_and_drag_and_a_drag_in_progress_ends():
    panel = ControlPanel()
    s = panel.add(Slider(0, 100, 10, label="size"))
    r = panel.layout(300)[0]
    mid = (r["x0"] + r["x1"]) / 2
    s.visible(False)
    panel.press(mid, 10, 300)
    assert s.value() == 10 and not panel.holding
    s.visible(True)
    panel.press(mid, 10, 300)
    assert s.value() == pytest.approx(50) and panel.holding
    s.visible(False)
    assert not panel.holding
    panel.drag(r["x1"], 10, 300)
    assert s.value() == pytest.approx(50)


def test_a_hidden_button_and_checkbox_ignore_clicks_and_keep_a_pending_click():
    panel = ControlPanel()
    b = panel.add(Button("go"))
    box = panel.add(Checkbox("x"))
    bx, by, bw, bh = panel.layout(200)[0]["button"]
    panel.press(bx + 2, by + 2, 200)
    panel.release(bx + 2, by + 2, 200)           # a click is waiting
    b.visible(False)
    box.visible(False)
    panel.press(bx + 2, by + 2, 200)
    panel.release(bx + 2, by + 2, 200)
    panel.press(12, ROW_HEIGHT + 12, 200)
    assert box.checked() is False
    assert b.clicked() is True                   # the pending click stayed, no new one was made
    assert b.clicked() is False
    box.visible(True)
    panel.press(12, ROW_HEIGHT + 12, 200)
    assert box.checked() is True


def test_a_hidden_control_keeps_its_value_and_can_still_be_set():
    s = Slider(0, 10, 3)
    box = Checkbox("a", True)
    s.visible(False)
    box.visible(False)
    assert s.value() == 3 and box.checked() is True
    s.value(7)
    box.checked(False)
    assert s.value() == 7 and box.checked() is False


def test_hiding_a_control_keeps_the_panel_height_and_the_places():
    panel = ControlPanel()
    s = panel.add(Slider(0, 10))
    c = panel.add(Checkbox("a"))
    before = panel.height, [dict(r) for r in panel.layout(300)]
    s.visible(False)
    assert (panel.height, panel.layout(300)) == before
    c.visible(False)
    assert (panel.height, panel.layout(300)) == before


def test_a_hidden_control_is_not_drawn_and_its_row_is_blank():
    panel = ControlPanel()
    s = panel.add(Slider(0, 10, 5, label="size"))
    panel.add(Checkbox("grid", True))
    shown = _panel_pixels(panel)
    v = panel.version
    s.visible(False)
    assert panel.version > v                     # the panel draws again
    hidden = _panel_pixels(panel)
    assert hidden != shown
    stride = 300 * 4
    row0 = hidden[1 * stride: ROW_HEIGHT * stride]          # below the top edge line
    assert set(row0[i:i + 3] for i in range(0, len(row0), 4)) == {bytes((238, 238, 238))}
    assert hidden[ROW_HEIGHT * stride:] == shown[ROW_HEIGHT * stride:]     # the other row is the same
    s.visible(True)
    assert _panel_pixels(panel) == shown


def test_visible_can_be_called_in_draw(pg):
    got = {}

    def setup():
        p.size(200, 100)
        got["s"] = p.create_slider(0, 10, 4)

    def draw():
        got["s"].visible(p.frame_count < 1)
        got.setdefault("seen", []).append(got["s"].visible())

    run_pg(setup, draw, frames=3)
    assert got["seen"] == [True, False, False]
    assert got["s"].value() == 4
