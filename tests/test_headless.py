"""HeadlessPlatform (S-034): a sketch runs with no window at all."""
from __future__ import annotations

import funground as p
from funground import api
from funground.platform.headless import HeadlessPlatform
from funground.sketch import Sketch, default_platform


def test_env_selects_headless(monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    assert isinstance(default_platform(), HeadlessPlatform)


def test_headless_run_captures_pixels_and_never_needs_a_display(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "no-such-driver")   # would fail if pygame were touched
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    seen = []

    def setup():
        p.size(40, 30)

    def draw():
        p.background("white")
        p.no_stroke()
        p.fill("red")
        p.rect(0, 0, 40, 15)
        seen.append((p.mouse_x, p.mouse_y, p.is_mouse_pressed, p.key_down("left")))

    s.run_namespace({"setup": setup, "draw": draw}, max_frames=3)
    (w, h), rgb = s.last_frame
    assert (w, h) == (40, 30) and len(rgb) == 40 * 30 * 3
    assert rgb[:3] == b"\xff\x00\x00" and rgb[-3:] == b"\xff\xff\xff"
    assert seen == [(0, 0, False, False)] * 3
    assert p.frame_count == 3 and p.delta_time >= 0.0


def test_headless_honours_forced_scale(monkeypatch):
    monkeypatch.setenv("FUNGROUND_BACKING_SCALE", "2")
    s = api.use_sketch(Sketch(platform=HeadlessPlatform()))
    s.run_namespace({"setup": lambda: p.size(10, 10), "draw": lambda: p.background("black")}, max_frames=1)
    assert s.last_frame[0] == (20, 20)
