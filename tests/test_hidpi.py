"""HiDPI (S-024, contract C3): logical coordinates, physical-resolution rendering."""
from __future__ import annotations

import sys

import pygame
import pytest

import playground as p
from playground import api
from playground.platform.pygame_platform import detect_backing_scale
from playground.sketch import Sketch


def test_dummy_driver_reports_scale_one(monkeypatch):
    monkeypatch.delenv("PLAYGROUND_BACKING_SCALE", raising=False)
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    assert detect_backing_scale() == 1.0


def test_forced_scale_is_honoured(monkeypatch):
    monkeypatch.setenv("PLAYGROUND_BACKING_SCALE", "2")
    assert detect_backing_scale() == 2.0


def test_window_is_physical_but_width_height_stay_logical(monkeypatch):
    monkeypatch.setenv("PLAYGROUND_BACKING_SCALE", "2")
    api.use_sketch(Sketch())
    pygame.init()
    p.size(100, 50)
    s = api.active_sketch()
    assert (p.width, p.height) == (100, 50)
    assert s._platform.target.get_size() == (200, 100)
    assert s._renderer.surface.get_width() == 200


def test_a_logical_rect_covers_scaled_physical_pixels(monkeypatch):
    monkeypatch.setenv("PLAYGROUND_BACKING_SCALE", "2")
    api.use_sketch(Sketch())
    pygame.init()
    p.size(100, 50)
    p.background("white")
    p.no_stroke()
    p.fill("red")
    p.rect(0, 0, 10, 10)
    s = api.active_sketch()
    s._render()
    surf = s._platform.target
    assert tuple(surf.get_at((19, 19))[:3]) == (255, 0, 0)     # 10 logical px == 20 physical px
    assert tuple(surf.get_at((20, 20))[:3]) == (255, 255, 255)


def test_mouse_is_reported_in_logical_pixels(monkeypatch):
    from playground.platform.pygame_platform import PygamePlatform

    monkeypatch.setenv("PLAYGROUND_BACKING_SCALE", "2")
    plat = PygamePlatform()
    pygame.init()
    plat.open_window(100, 50, "t")
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (150, 80))
    st = plat.input_state()
    assert (st.mouse_x, st.mouse_y) == (75, 40)
    plat.close()


# ---- S-038: macOS / Linux via SDL's high-DPI window (drawable / window ratio).
# The teaching machine is Windows, so the pygame calls the route relies on are
# simulated here: a fake pygame.Window whose surface is *ratio* times its size.
# Real-hardware verification is pending (sprint-04/stories.md S-038.2).

class _FakeWindow:
    """Stand-in for pygame.Window(size, allow_high_dpi=True) on a 2x display."""

    ratio = 2
    created: list["_FakeWindow"] = []

    def __init__(self, title="pygame window", size=(640, 480), position=None, **flags):
        self.title = title
        self.size = tuple(size)
        self.flags = flags
        self.flips = 0
        self.destroyed = False
        self._surface = pygame.Surface((size[0] * self.ratio, size[1] * self.ratio))
        _FakeWindow.created.append(self)

    def get_surface(self):
        return self._surface

    def flip(self):
        self.flips += 1

    def destroy(self):
        self.destroyed = True


@pytest.fixture(params=["darwin", "linux"])
def sdl_highdpi(monkeypatch, request):
    """Pretend to be macOS / Linux with a real display and a 2x pygame.Window."""
    monkeypatch.delenv("PLAYGROUND_BACKING_SCALE", raising=False)
    monkeypatch.setenv("SDL_VIDEODRIVER", "x11")     # not "dummy": the probe path is taken
    monkeypatch.setattr(sys, "platform", request.param)
    monkeypatch.setattr(pygame, "Window", _FakeWindow)
    monkeypatch.setattr(pygame.display, "init", lambda: None)   # x11 is not available here
    _FakeWindow.created = []
    _FakeWindow.ratio = 2
    return request.param


def test_probe_window_measures_drawable_ratio(sdl_highdpi):
    assert detect_backing_scale() == 2.0
    (probe,) = _FakeWindow.created
    assert probe.flags == {"hidden": True, "allow_high_dpi": True}
    assert probe.destroyed


def test_ratio_one_display_reports_scale_one(sdl_highdpi):
    _FakeWindow.ratio = 1
    assert detect_backing_scale() == 1.0


def test_open_window_returns_physical_size_and_keeps_mouse_logical(sdl_highdpi, monkeypatch):
    from playground.platform.base import Pixels
    from playground.platform.pygame_platform import PygamePlatform

    plat = PygamePlatform()
    assert plat.open_window(100, 50, "t") == (200, 100)
    assert plat.backing_scale == 2.0
    (win,) = _FakeWindow.created
    assert win.size == (100, 50) and win.title == "t" and win.flags == {"allow_high_dpi": True}
    assert plat.target.get_size() == (200, 100)
    # SDL reports the mouse in screen units on this route: already logical.
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (75, 40))
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda n: (False, False, False))
    st = plat.input_state()
    assert (st.mouse_x, st.mouse_y) == (75, 40)
    plat.present(Pixels(bytes(200 * 100 * 4), 200, 100))
    assert win.flips == 1
    plat.close()
    assert win.destroyed and plat.target is None


def test_probe_failure_degrades_to_scale_one(sdl_highdpi, monkeypatch):
    def broken(*a, **k):
        raise pygame.error("no display")

    monkeypatch.setattr(pygame, "Window", broken)
    assert detect_backing_scale() == 1.0


def test_forced_scale_bypasses_the_sdl_window_route(sdl_highdpi, monkeypatch):
    from playground.platform.pygame_platform import _uses_sdl_highdpi_window

    monkeypatch.setenv("PLAYGROUND_BACKING_SCALE", "2")
    assert detect_backing_scale() == 2.0
    assert not _uses_sdl_highdpi_window()
    assert _FakeWindow.created == []


def test_windows_path_is_unchanged_by_platform_guard(monkeypatch):
    from playground.platform.pygame_platform import _uses_sdl_highdpi_window

    monkeypatch.delenv("PLAYGROUND_BACKING_SCALE", raising=False)
    monkeypatch.setenv("SDL_VIDEODRIVER", "windows")
    monkeypatch.setattr(sys, "platform", "win32")
    assert not _uses_sdl_highdpi_window()
