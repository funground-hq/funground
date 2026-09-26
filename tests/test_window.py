"""Window control (S-057, contract R12): cursor, full screen, resize while running."""
from __future__ import annotations

import pytest

import funground as p
from funground import api
from funground.platform.base import CURSOR_KINDS
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch


def run(setup, draw, frames=3):
    platform = HeadlessPlatform()
    s = api.use_sketch(Sketch(platform=platform))
    s.run_namespace({"setup": setup, "draw": draw}, max_frames=frames)
    return s, platform


def test_cursor_defaults_to_arrow_and_can_change_or_hide():
    platform = HeadlessPlatform()
    seen = []

    def draw():
        seen.append(platform.cursor)
        if p.frame_count == 0:
            p.cursor("hand")
        elif p.frame_count == 1:
            p.no_cursor()

    s = api.use_sketch(Sketch(platform=platform))
    s.run_namespace({"setup": lambda: p.size(20, 20), "draw": draw}, max_frames=3)
    assert seen == ["arrow", "hand", None]


def test_a_cursor_chosen_before_the_window_is_applied_when_it_opens():
    def setup():
        p.cursor("wait")
        p.size(20, 20)

    _, platform = run(setup, lambda: None, frames=1)
    assert platform.cursor == "wait"


def test_resize_canvas_while_running_updates_width_height_and_pixels(monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    sizes = []

    def draw():
        if p.frame_count == 1:
            p.resize_canvas(30, 10)
        p.background("red")
        sizes.append((p.width, p.height))

    s, _ = run(lambda: p.size(20, 20), draw)
    assert sizes == [(20, 20), (30, 10), (30, 10)]
    (w, h), rgb = s.last_frame
    assert (w, h) == (60, 20)                               # still sharp: physical = 2 x logical
    assert rgb[:3] == b"\xff\x00\x00" and rgb[-3:] == b"\xff\x00\x00"


def test_full_screen_headless_is_a_fixed_repeatable_size():
    seen = []

    def draw():
        seen.append((p.width, p.height))
        p.background("navy")

    _, platform = run(p.full_screen, draw, frames=1)
    assert seen == [HeadlessPlatform.SCREEN_SIZE] and platform.full_screen


def test_sketch_and_platforms_agree_on_cursor_names():
    assert Sketch.CURSOR_KINDS == CURSOR_KINDS


def test_unknown_cursor_is_explained():
    api.use_sketch(Sketch(platform=HeadlessPlatform()))
    with pytest.raises(ValueError, match="'arrow', 'cross', 'hand'"):
        p.cursor("pointer")
    with pytest.raises(ValueError):
        p.resize_canvas(0, 10)


def test_pygame_platform_resizes_one_window_and_goes_full_screen():
    """With SDL's dummy video driver (conftest): the real platform code paths run without a display."""
    from funground.platform.pygame_platform import PygamePlatform

    plat = PygamePlatform()
    try:
        first = plat.open_window(100, 80, "t")
        second = plat.open_window(120, 90, "t")
        assert second == (round(120 * plat.backing_scale), round(90 * plat.backing_scale)) and first != second
        for kind in CURSOR_KINDS:
            plat.set_cursor(kind)
        plat.set_cursor(None)
        full = plat.open_full_screen("t")
        assert full[0] > 0 and full[1] > 0
    finally:
        plat.close()
