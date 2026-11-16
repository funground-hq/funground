"""A library's wait shown in the window's title (S-307, D-149): host_services.waiting, set by the running sketch."""
from __future__ import annotations

import pytest

import funground as p
from funground import api, host_services
from funground.platform.headless import HeadlessPlatform
from funground.platform.pygame_platform import PygamePlatform
from funground.sketch import Sketch


class Recorder(HeadlessPlatform):
    host_driven = False

    def __init__(self):
        super().__init__()
        self.waits = []

    def show_wait(self, text):
        self.waits.append(text)


def test_a_running_sketch_gives_libraries_a_way_to_show_a_wait_and_takes_it_back():
    platform = Recorder()
    seen = []

    def draw():
        host_services.waiting("Downloading the hand model: 2 of 8 MB")
        host_services.waiting(None)
        seen.append(host_services.waiting)

    s = api.use_sketch(Sketch(platform=platform))
    s.run_namespace({"setup": lambda: p.size(20, 20), "draw": draw}, max_frames=1)
    assert platform.waits == ["Downloading the hand model: 2 of 8 MB", None]
    assert seen[0] is not None
    assert host_services.waiting is None            # the run is over


def test_a_headless_sketch_can_be_told_to_wait_and_nothing_happens():
    HeadlessPlatform().show_wait("anything")


def test_the_window_title_has_the_wait_after_the_sketch_title_and_goes_back():
    pygame = pytest.importorskip("pygame")
    platform = PygamePlatform()
    try:
        platform.show_wait("too early")             # no window yet: nothing happens
        platform.open_window(40, 30, "my sketch")
        platform.start()
        platform.show_wait("Starting the body model")
        assert pygame.display.get_caption()[0] == "my sketch - Starting the body model"
        platform.show_wait(None)
        assert pygame.display.get_caption()[0] == "my sketch"
    finally:
        platform.close()
