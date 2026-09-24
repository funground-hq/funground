"""HiDPI (S-024, contract C3): logical coordinates, physical-resolution rendering."""
from __future__ import annotations

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
